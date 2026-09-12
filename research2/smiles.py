"""Smooth strike-constrained projection of reference-only smile priors.

This builds on established constrained spline/smile interpolation. No novelty
claim. Constraints guarantee decreasing, convex call prices within the anchor
range; explicit convex tails preserve the same restrictions outside it. This
is not a cross-expiry no-arbitrage construction or an American-option model.
"""
import numpy as np
from scipy.interpolate import CubicSpline, PchipInterpolator
from scipy.optimize import minimize, LinearConstraint, least_squares
from strategy_lab.model import bsm


class ConvexSmile:
    def __init__(self,x,call,scale,prior,prior_weight=1.):
        x=np.asarray(x); call=np.asarray(call); scale=np.maximum(scale,1e-6)
        knots=np.sort(np.r_[x,(x[:-1]+x[1:])/2]); n=len(knots)
        basis=CubicSpline(knots,np.eye(n),bc_type='natural',axis=0)
        A=basis(x); mids=(x[:-1]+x[1:])/2; P=basis(mids)
        # Smooth reference-consistent prior acts only between observed anchors.
        midscale=np.interp(mids,x,scale)
        design=np.vstack([A/scale[:,None],np.sqrt(prior_weight)*P/midscale[:,None]])
        target=np.r_[call/scale,np.sqrt(prior_weight)*prior(mids)/midscale]
        H=design.T@design; f=design.T@target
        # Scale objective for SLSQP; constraints remain in normalized prices.
        norm=max(np.linalg.norm(H,2),1.); H/=norm; f/=norm
        second=basis(knots[1:-1],2); left=basis(knots[0],1); right=basis(knots[-1],1)
        lower_tail=knots[0]*left-basis(knots[0])
        matrix=np.vstack([second,left,right,lower_tail])
        lower=np.r_[np.zeros(n-2),-1.,-np.inf,-1.]
        upper=np.r_[np.full(n-2,np.inf),np.inf,-1e-10,np.inf]
        row_scale=np.maximum(np.linalg.norm(matrix,axis=1),1e-12)
        matrix=matrix/row_scale[:,None];lower=lower/row_scale;upper=upper/row_scale
        bounds=list(zip(np.maximum(1-knots,0)+1e-10,np.ones(n)))
        initial=np.clip(prior(knots),[b[0] for b in bounds],[b[1] for b in bounds])
        fit=minimize(lambda y:.5*y@H@y-f@y,initial,jac=lambda y:H@y-f,
            method='SLSQP',bounds=bounds,constraints=[LinearConstraint(matrix,lower,upper)],
            options=dict(maxiter=200,ftol=1e-13))
        residual=matrix@fit.x
        if not fit.success or np.any(residual<lower-1e-8) or np.any(residual>upper+1e-8):
            feasible=1.-knots/(2*max(knots))
            fit=minimize(lambda y:.5*y@H@y-f@y,feasible,jac=lambda y:H@y-f,
                method='SLSQP',bounds=bounds,constraints=[LinearConstraint(matrix,lower,upper)],
                options=dict(maxiter=1000,ftol=1e-13))
            residual=matrix@fit.x
        self.ok=bool(fit.success and np.all(residual>=lower-1e-8) and np.all(residual<=upper+1e-8))
        self.x=knots; self.spline=CubicSpline(knots,fit.x,bc_type='natural')
        self.message=str(fit.message)

    def __call__(self,x):
        x=np.asarray(x,dtype=float); clipped=np.clip(x,self.x[0],self.x[-1]); out=self.spline(clipped)
        a,b=self.x[0],self.x[-1]; ca,cb=self.spline(a),self.spline(b)
        da,db=self.spline(a,1),self.spline(b,1)
        pa=max(ca-1+a,1e-12); power=max(1.,a*(da+1)/pa)
        out=np.where(x<a,1-x+pa*(np.clip(x,0,a)/a)**power,out)
        out=np.where(x>b,cb*np.exp(np.clip(db/max(cb,1e-12)*(x-b),-700,0)),out)
        return out


def ssvi_fit(logm,iv,T,scale):
    """SSVI slice with sufficient butterfly restrictions, a standard benchmark."""
    theta0=max(float(np.interp(0,logm,iv))**2*T,1e-5)
    def variance(k,p):
        theta,rho,eta=p
        # Map eta in (0,1) below both sufficient SSVI bounds.
        phi=eta*min(4/(theta*(1+abs(rho))),np.sqrt(4/(theta*(1+abs(rho)))))
        z=phi*k+rho
        return theta/2*(1+rho*phi*k+np.sqrt(z*z+1-rho*rho))
    def residual(p): return (np.sqrt(variance(logm,p)/T)-iv)/np.maximum(scale,.002)
    fit=least_squares(residual,[theta0,-.3,.4],bounds=([1e-6,-.98,.001],[4.,.98,.999]),max_nfev=100)
    return lambda k:np.sqrt(variance(np.asarray(k),fit.x)/T),bool(fit.success)


def call_prior(logm,iv,T,kind='pchip'):
    if kind=='pchip':
        interp=PchipInterpolator(logm,iv,extrapolate=False)
        fn=lambda k:interp(np.clip(k,min(logm),max(logm)))
    else: fn=lambda k:np.interp(k,logm,iv)
    return lambda x:bsm(1.,np.asarray(x),T,0,np.maximum(fn(np.log(x)),.001),True)
