import datetime as dt
import gzip
import json
import os
import tempfile
import unittest
from pathlib import Path

from data_pulls import fetch_release, publish_release, wrds_pull


class PublishFetchRoundTrip(unittest.TestCase):
    def test_build_then_offline_restore(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp, 'stock')
            data = root / 'wrds_studies' / 'research7_data'
            (data / 'options').mkdir(parents=True)
            (data / 'stocks').mkdir()
            files = {'universe.csv': b'secid\n1\n', 'options/quotes_original_2024_000.csv.gz': gzip.compress(b'a,b\n1,2\n'),
                     'options/quotes_original_2025_000.csv.gz': gzip.compress(b'a,b\n3,4\n'),
                     'stocks/stocks_original_2024.csv.gz': gzip.compress(b'x\n')}
            for rel, blob in files.items():
                (data / rel).write_bytes(blob)
            staging = Path(tmp, 'staging')
            manifest = publish_release.build(str(data), str(root), str(staging), 'test-tag', 'test-tag')
            self.assertEqual({a['name'].split('-')[2] for a in manifest['archives']}, {'meta', 'options', 'stocks'})
            self.assertEqual(len(manifest['files']), 4)
            mpath = Path(tmp, 'manifest.json')
            mpath.write_text(json.dumps(manifest))
            out = Path(tmp, 'cloud')
            fetch_release.main(['--manifest', str(mpath), '--output', str(out), '--cache-dir', str(staging), '--offline'])
            for rel, blob in files.items():
                self.assertEqual((out / 'wrds_studies' / 'research7_data' / rel).read_bytes(), blob)
            # A second restore is a verified no-op; a tampered file is refused.
            fetch_release.main(['--manifest', str(mpath), '--output', str(out), '--cache-dir', str(staging), '--offline'])
            (out / 'wrds_studies' / 'research7_data' / 'universe.csv').write_bytes(b'changed')
            with self.assertRaises(FileExistsError):
                fetch_release.main(['--manifest', str(mpath), '--output', str(out), '--cache-dir', str(staging), '--offline'])

    def test_offline_refuses_missing_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            m = {'tag': 't', 'files': [], 'archives': [{'name': 'x.tar.gz', 'files': 0, 'bytes': 1, 'sha256': '0'}]}
            path = Path(tmp, 'm.json')
            path.write_text(json.dumps(m))
            with self.assertRaises(ValueError):
                fetch_release.main(['--manifest', str(path), '--output', tmp, '--cache-dir', tmp, '--offline'])


class PullHelpers(unittest.TestCase):
    def test_event_windows_and_sql(self):
        sessions = [dt.date(2024, 1, 1) + dt.timedelta(days=i) for i in range(40)]
        wins = wrds_pull.event_windows([(7, dt.date(2024, 1, 15)), (8, dt.date(2024, 1, 3))], sessions, 10, 5, 45)
        self.assertEqual(wins, [(7, dt.date(2024, 1, 5), dt.date(2024, 1, 20), dt.date(2024, 2, 29))])
        sql = wrds_pull.options_sql(2024, wins, 0.7, 1.4)
        self.assertIn("(7, date '2024-01-05', date '2024-01-20', date '2024-02-29')", sql)
        self.assertIn('optionm_all.opprcd2024', sql)
        self.assertIn('700 * abs(s.close)', sql)
        self.assertIn('select o."secid", o."date"', sql)

    def test_stream_query_uses_transaction_and_restores_autocommit(self):
        class Cursor:
            def __init__(self, conn):
                self.conn, self.itersize, self.description = conn, None, None
                self.batches = [[(1, dt.date(2018, 1, 2), 1.5)], [(2, dt.date(2018, 1, 3), None)], []]

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def execute(self, query):
                assert not self.conn.autocommit, 'named cursor needs a transaction'
                self.query = query

            def fetchmany(self, n):
                self.description = [('secid',), ('date',), ('best_bid',)]
                return self.batches.pop(0)

        class DBAPI:
            autocommit = True
            closed = False

            def cursor(self, name=None):
                assert name, 'must be a server-side (named) cursor'
                return Cursor(self)

            def rollback(self):
                pass

        class Raw:
            def __init__(self):
                self.driver_connection = DBAPI()

            def close(self):
                self.driver_connection.closed = True

        with tempfile.TemporaryDirectory() as tmp:
            raw = Raw()
            path = os.path.join(tmp, 'q.csv.gz')
            self.assertEqual(wrds_pull.stream_query(raw, 'select 1', path, 1), 2)
            self.assertEqual(gzip.open(path, 'rt').read().splitlines(),
                             ['secid,date,best_bid', '1,2018-01-02,1.5', '2,2018-01-03,'])
            self.assertTrue(raw.driver_connection.autocommit)
            self.assertTrue(raw.driver_connection.closed)
            self.assertEqual(os.listdir(tmp), ['q.csv.gz'])

    def test_daily_sql(self):
        sql = wrds_pull.daily_sql(2019, [101310, 109820], 120, 0.7, 1.3)
        self.assertIn('optionm_all.opprcd2019 o', sql)
        self.assertIn('o.secid in (101310,109820)', sql)
        self.assertIn('o.exdate <= o.date + 120', sql)
        self.assertIn('1300 * abs(s.close)', sql)

    def test_columns_skip_missing_optional_and_require_required(self):
        class FakeDB:
            def describe_table(self, library, table):
                return {'name': ['ticker', 'statpers', 'fpedats', 'fpi', 'meanest', 'numest', 'STDEV']}

        class Args:
            out = tempfile.mkdtemp()

        puller = wrds_pull.Puller(Args())
        puller._db = FakeDB()
        cols = puller.columns('ibes', 'statsumu_epsus', ('ticker', 'statpers', 'fpedats', 'fpi', 'meanest'),
                              ('numest', 'stdev', 'actual', 'anndats_act'))
        self.assertEqual(cols, ['ticker', 'statpers', 'fpedats', 'fpi', 'meanest', 'numest', 'stdev'])
        with self.assertRaises(SystemExit):
            puller.columns('ibes', 'statsumu_epsus', ('ticker', 'actual'))
        self.assertEqual(wrds_pull.select_list(['secid', 'return'], 'p.'), 'p."secid", p."return"')


if __name__ == '__main__':
    unittest.main()
