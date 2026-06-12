"""The spatial lag model (SAR): y = rho W y + X beta + epsilon.

rho is the transmission coefficient — the fraction of a county's outcome
that arrives from its neighbors' outcomes after its own covariates have
spoken. This is the Wave Predictor's core quantity: rho = 0 means the map's
clustering is fully explained by demographics sitting next to similar
demographics; rho > 0 means change itself propagates across borders.

Estimation is maximum likelihood. OLS with W y on the right is biased
because the lag is endogenous by construction (each county's y appears in
its neighbors' lags). The standard concentration makes ML cheap without
scipy or pysal:

  - Regress y on X (residual e_y) and W y on X (residual e_Wy) ONCE.
    For any rho, the SAR residual is e(rho) = e_y - rho * e_Wy, so the
    error sum of squares is an exact quadratic in rho.
  - The Jacobian term ln|I - rho W| equals sum(ln(1 - rho * lambda_i)) over
    the eigenvalues of W. Row-standardized W from symmetric adjacency is
    similar to the symmetric D^(-1/2) A D^(-1/2), so the eigenvalues are
    real and computed stably with eigvalsh.
  - Maximize the concentrated log-likelihood over rho on a fine grid with
    parabolic refinement — deterministic, derivative-free, single-peaked
    in practice.

The likelihood-ratio test against rho = 0 uses the chi-square(1) survival
function, which is erfc(sqrt(LR/2)) — no scipy needed.
"""

import math
from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np
import pandas as pd

from geofluid.spatial.weights import spatial_weights

# Floor for sigma^2 inside the log — keeps the noise-free recovery worlds
# (residual exactly zero at the true rho) finite instead of crashing ln(0),
# while making the true parameters the unambiguous maximizer.
_SIGMA2_FLOOR = 1e-300


@dataclass(frozen=True)
class SpatialLagFit:
    rho: float
    beta: dict[str, float]
    sigma2: float
    loglik: float
    loglik_null: float  # the same model with rho fixed at 0
    lr_pvalue: float  # likelihood-ratio test of rho = 0, chi-square(1)
    n: int


def _ols_residuals(design: "np.ndarray", target: "np.ndarray") -> tuple[np.ndarray, np.ndarray]:
    coef, *_ = np.linalg.lstsq(design, target, rcond=None)
    return coef, target - design @ coef


def fit_spatial_lag(
    y: "pd.Series[float]",
    covariates: pd.DataFrame,
    adjacency: Mapping[str, frozenset[str]],
) -> SpatialLagFit:
    """Fit y = rho W y + X beta + eps by concentrated maximum likelihood.

    y and the covariate frame are fips-indexed; alignment is internal, and
    an intercept column is always added. Counties with a missing value in
    y or any covariate are excluded listwise along with their orphaned
    neighbors (same closure as Moran's I).
    """
    frame = covariates.copy()
    frame["__y__"] = y
    complete = frame.dropna()
    usable = {fips for fips in adjacency if fips in complete.index}
    kept = {fips for fips in usable if adjacency[fips] & usable}
    sub_adjacency = {fips: frozenset(adjacency[fips] & usable) for fips in kept}

    matrix, order = spatial_weights(sub_adjacency)
    n = len(order)
    target = complete.loc[order, "__y__"].to_numpy(dtype=float)
    names = ["intercept", *covariates.columns]
    design = np.column_stack(
        [np.ones(n), complete.loc[order, list(covariates.columns)].to_numpy(dtype=float)]
    )

    lag = matrix @ target
    beta_y, resid_y = _ols_residuals(design, target)
    beta_lag, resid_lag = _ols_residuals(design, lag)

    # Eigenvalues of W via the similar symmetric matrix (degrees are the
    # neighbor counts; no islands exist in the kept closure by construction).
    degrees = np.array([len(sub_adjacency[fips]) for fips in order], dtype=float)
    inv_sqrt = 1.0 / np.sqrt(degrees)
    symmetric = matrix * degrees[:, None] * inv_sqrt[:, None] * inv_sqrt[None, :]
    eigenvalues = np.linalg.eigvalsh(symmetric)

    def concentrated_loglik(rho: float) -> float:
        sse = float(
            resid_y @ resid_y
            - 2 * rho * (resid_y @ resid_lag)
            + rho * rho * (resid_lag @ resid_lag)
        )
        sigma2 = max(sse / n, _SIGMA2_FLOOR)
        jacobian = float(np.log(1.0 - rho * eigenvalues).sum())
        return jacobian - (n / 2.0) * math.log(sigma2)

    # rho must keep I - rho W nonsingular: (1/lambda_min, 1) for
    # row-standardized W (largest eigenvalue is exactly 1).
    lower = 1.0 / float(eigenvalues.min()) + 1e-6
    upper = 1.0 - 1e-6
    grid = np.linspace(lower, upper, 2001)
    values = np.array([concentrated_loglik(r) for r in grid])
    best = int(values.argmax())
    # Parabolic refinement around the best grid point.
    if 0 < best < len(grid) - 1:
        x0, x1, x2 = grid[best - 1 : best + 2]
        f0, f1, f2 = values[best - 1 : best + 2]
        denominator = (f0 - 2 * f1 + f2) or 1.0
        rho_hat = float(x1 + 0.5 * (x0 - x2) * (f0 - f2) / (2 * denominator))
        rho_hat = float(np.clip(rho_hat, x0, x2))
    else:
        rho_hat = float(grid[best])

    beta_hat = beta_y - rho_hat * beta_lag
    sse_hat = float((resid_y - rho_hat * resid_lag) @ (resid_y - rho_hat * resid_lag))
    loglik = concentrated_loglik(rho_hat)
    loglik_null = concentrated_loglik(0.0)
    lr = max(0.0, 2.0 * (loglik - loglik_null))
    # chi-square(1) survival function: P(X > lr) = erfc(sqrt(lr / 2)).
    lr_pvalue = math.erfc(math.sqrt(lr / 2.0))

    return SpatialLagFit(
        rho=rho_hat,
        beta=dict(zip(names, (float(b) for b in beta_hat), strict=True)),
        sigma2=max(sse_hat / n, 0.0),
        loglik=loglik,
        loglik_null=loglik_null,
        lr_pvalue=lr_pvalue,
        n=n,
    )
