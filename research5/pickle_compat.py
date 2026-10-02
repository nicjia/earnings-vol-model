"""Read the research cache's pandas DataFrame pickles without numpy or pandas.

The cloud environment cannot install numpy/pandas, so this unpickler maps the
handful of numpy/pandas reconstruction globals used by those files onto plain
Python stand-ins and rebuilds each frame as a list of column-name -> list
dicts.  Only float64/int64 buffers, object arrays, StringArray, Index,
RangeIndex and BlockManager blocks are supported; anything else raises.
"""
import datetime
import pickle
import struct


class _Dtype:
    def __init__(self, code, *_):
        self.code = code
        self.state = None

    def __setstate__(self, state):
        self.state = state


class _Array:
    """1-D or 2-D array stand-in holding a flat row-major list and a shape."""

    def __init__(self, values=None, shape=None):
        self.values = values
        self.shape = shape

    def __setstate__(self, state):
        # numpy ndarray state: (version, shape, dtype, is_fortran, data)
        _, shape, dtype, fortran, data = state
        if isinstance(data, (bytes, bytearray)):
            values = _decode(bytes(data), dtype.code)
        else:
            values = list(data)
        if fortran and len(shape) == 2:
            rows, cols = shape
            values = [values[c * rows + r] for r in range(rows) for c in range(cols)]
        self.values, self.shape = values, tuple(shape)

    def rows(self):
        if len(self.shape) == 1:
            return [self.values]
        n = self.shape[1]
        return [self.values[i * n:(i + 1) * n] for i in range(self.shape[0])]


def _decode(buffer, code):
    fmt = {'f8': 'd', 'i8': 'q', 'u8': 'Q', 'f4': 'f', 'i4': 'i', 'b1': '?'}.get(code)
    if fmt is None:
        raise ValueError('Unsupported numpy dtype in pickle: ' + str(code))
    size = struct.calcsize(fmt)
    return list(struct.unpack('<%d%s' % (len(buffer) // size, fmt), buffer))


def _reconstruct(cls, shape, typecode):
    return _Array()


def _frombuffer(buffer, dtype, shape, order):
    values = _decode(bytes(buffer), dtype.code)
    if order == 'F' and len(shape) == 2:
        rows, cols = shape
        values = [values[c * rows + r] for r in range(rows) for c in range(cols)]
    return _Array(values, tuple(shape))


class _Block:
    def __init__(self, values, placement, ndim):
        if isinstance(values, _StringArray):
            values = values.array
        self.values, self.placement = values, placement


def _unpickle_block(values, placement, ndim):
    return _Block(values, placement, ndim)


class _StringArray:
    def __init__(self, array=None):
        self.array = array

    def __setstate__(self, state):
        # Cython auto-pickle state is (_dtype, _ndarray[, __dict__]); keep the array.
        parts = state if isinstance(state, tuple) else (state,)
        arrays = [p for p in parts if isinstance(p, _Array)]
        if len(arrays) != 1:
            raise ValueError('Unsupported StringArray pickle state')
        self.array = arrays[0]


def _unpickle_ndarray_backed(cls, checksum, state):
    obj = cls()
    if state is not None:  # otherwise a later BUILD opcode supplies it
        obj.__setstate__(state)
    return obj


class _Index:
    def __init__(self, data=None, name=None, start=None, stop=None, step=None):
        if start is not None or stop is not None:
            data = list(range(start or 0, stop, step or 1))
        elif isinstance(data, _Array):
            data = data.values
        elif isinstance(data, _StringArray):
            data = data.array.values
        self.data = list(data)
        self.name = name


class _RangeIndex(_Index):
    pass


def _new_index(cls, d):
    return cls(**d)


class _BlockManager:
    """pandas 2.x pickles BlockManager(blocks, axes) as constructor arguments."""

    def __init__(self, blocks=(), axes=()):
        self.blocks, self.axes = list(blocks), list(axes)


class _Frame:
    def __setstate__(self, state):
        self.mgr = state['_mgr']


class _Series(_Frame):
    pass


_GLOBALS = {
    ('pandas', 'DataFrame'): _Frame,
    ('pandas.core.frame', 'DataFrame'): _Frame,
    ('pandas.core.internals.managers', 'BlockManager'): _BlockManager,
    ('pandas._libs.internals', '_unpickle_block'): _unpickle_block,
    ('numpy._core.numeric', '_frombuffer'): _frombuffer,
    ('numpy.core.numeric', '_frombuffer'): _frombuffer,
    ('numpy._core.multiarray', '_reconstruct'): _reconstruct,
    ('numpy.core.multiarray', '_reconstruct'): _reconstruct,
    ('numpy', 'ndarray'): _Array,
    ('numpy', 'dtype'): _Dtype,
    ('pandas._libs.arrays', '__pyx_unpickle_NDArrayBacked'): _unpickle_ndarray_backed,
    ('pandas.arrays', 'StringArray'): _StringArray,
    ('pandas.core.arrays.string_', 'StringArray'): _StringArray,
    ('pandas.arrays', 'StringDtype'): _Dtype,
    ('pandas', 'StringDtype'): _Dtype,
    ('pandas.core.arrays.string_', 'StringDtype'): _Dtype,
    ('pandas.core.indexes.base', '_new_Index'): _new_index,
    ('pandas.core.indexes.base', 'Index'): _Index,
    ('pandas', 'Index'): _Index,
    ('pandas.core.indexes.range', 'RangeIndex'): _RangeIndex,
    ('pandas', 'RangeIndex'): _RangeIndex,
    ('builtins', 'slice'): slice,
    ('datetime', 'date'): datetime.date,
    ('datetime', 'datetime'): datetime.datetime,
}


class _Unpickler(pickle.Unpickler):
    def find_class(self, module, name):
        try:
            return _GLOBALS[(module, name)]
        except KeyError:
            raise pickle.UnpicklingError(f'Unsupported global in data pickle: {module}.{name}') from None


def _placement(placement, count):
    if isinstance(placement, slice):
        return list(range(*placement.indices(count)))
    if isinstance(placement, _Array):
        return list(placement.values)
    return list(placement)


def load_frame(path):
    """Return (columns, rows) where rows is a list of dicts, in original row order."""
    with open(path, 'rb') as stream:
        frame = _Unpickler(stream).load()
    if not isinstance(frame, _Frame):
        raise TypeError('Pickle does not contain a DataFrame: ' + str(path))
    mgr = frame.mgr
    if not isinstance(mgr, _BlockManager):
        raise TypeError('Unsupported frame manager in ' + str(path))
    columns_index, row_index = mgr.axes
    columns = list(columns_index.data)
    nrows = len(row_index.data)
    data = {}
    for block in mgr.blocks:
        locs = _placement(block.placement, len(columns))
        values = block.values
        if isinstance(values, _StringArray):
            values = values.array
        block_rows = values.rows() if len(values.shape) == 2 else [values.values]
        if len(block_rows) != len(locs):
            raise ValueError('Block placement mismatch in ' + str(path))
        for loc, series in zip(locs, block_rows):
            if len(series) != nrows:
                raise ValueError('Column length mismatch in ' + str(path))
            data[columns[loc]] = series
    if set(data) != set(columns):
        raise ValueError('Missing columns after unpickling ' + str(path))
    rows = [{c: data[c][i] for c in columns} for i in range(nrows)]
    return columns, rows
