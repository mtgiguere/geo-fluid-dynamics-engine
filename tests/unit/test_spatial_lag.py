"""Tests for the spatial lag model (SAR) — Module 1's first predictive model.

    y = rho * W y + X beta + epsilon

rho is the spatial transmission coefficient: how much of a county's outcome
arrives from its neighbors after its own covariates have spoken. Estimated
by maximum likelihood (OLS on a model with W y on the right is biased —
the lag is endogenous by construction).

No seeds anywhere (TDD_CONTRACT.md RED FLAG 3). The estimator is verified
by NOISE-FREE RECOVERY: build a world where y = (I - rho0 W)^-1 X beta0
exactly, and demand the estimate hands back rho0 and beta0. At the true
parameters the residual is zero and the likelihood unbounded above — any
correct maximizer must land there, deterministically.
"""

import numpy as np
import pandas as pd
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from geofluid.spatial.lag import fit_spatial_lag
from geofluid.spatial.weights import spatial_weights

# An 8-county ring: every county has two neighbors, no islands.
_RING_FIPS = [f"{i:05d}" for i in range(8)]
_RING = {
    f: frozenset({_RING_FIPS[(i - 1) % 8], _RING_FIPS[(i + 1) % 8]})
    for i, f in enumerate(_RING_FIPS)
}
# A fixed, deliberately non-symmetric covariate pattern (not an eigenvector
# of the ring, not constant, not centered).
_X1 = [0.3, -1.2, 2.0, 0.7, -0.4, 1.5, -2.1, 0.9]


def _sar_world(rho: float, intercept: float, slope: float) -> tuple[pd.Series, pd.DataFrame]:
    """The exact SAR world: y = (I - rho W)^-1 (intercept + slope * x1)."""
    matrix, order = spatial_weights(_RING)
    x1 = pd.Series(dict(zip(_RING_FIPS, _X1, strict=True))).loc[order].to_numpy()
    xb = intercept + slope * x1
    y = np.linalg.solve(np.eye(len(order)) - rho * matrix, xb)
    return (
        pd.Series(y, index=order),
        pd.DataFrame({"x1": x1}, index=pd.Index(order, name="fips")),
    )


def test_noise_free_sar_world_recovers_rho_and_beta() -> None:
    """rho0 = 0.6, beta0 = (intercept 2.0, slope 0.5): the estimate must land
    on the truth. Tolerance reflects the rho search grid, not noise."""
    y, x = _sar_world(rho=0.6, intercept=2.0, slope=0.5)

    fit = fit_spatial_lag(y, x, _RING)

    assert abs(fit.rho - 0.6) < 1e-3
    assert abs(fit.beta["intercept"] - 2.0) < 1e-2
    assert abs(fit.beta["x1"] - 0.5) < 1e-2


def test_world_without_spillover_recovers_rho_of_zero() -> None:
    """rho0 = 0: y is pure demographics. The estimator must NOT hallucinate
    transmission — rho lands on zero and beta on the truth."""
    y, x = _sar_world(rho=0.0, intercept=-1.0, slope=1.25)

    fit = fit_spatial_lag(y, x, _RING)

    assert abs(fit.rho) < 1e-3
    assert abs(fit.beta["intercept"] - (-1.0)) < 1e-2
    assert abs(fit.beta["x1"] - 1.25) < 1e-2


# deadline=None: each example fits the SAR model TWICE, and a fit is a
# 2001-point grid search plus an eigvalsh (~27ms each, legitimately). The
# default 200ms per-example deadline is a heuristic for ACCIDENTALLY slow
# code; under CPU contention (a parallel lint/commit) an example spikes past
# it and the test flakes on timing, not correctness. The outcome stays
# deterministic — only the timing guard is removed.
@settings(deadline=None)
@given(
    rho=st.floats(-0.8, 0.9),
    scale=st.one_of(st.floats(0.05, 20), st.floats(-20, -0.05)),
)
def test_scaling_y_scales_beta_but_never_rho(rho: float, scale: float) -> None:
    """Property: measuring y in different units (points vs fractions, either
    sign) scales beta and leaves rho untouched — spatial transmission is a
    proportion, not an amount. Holds for any true rho and any nonzero
    scale."""
    assume(abs(rho) > 1e-3)
    y, x = _sar_world(rho=rho, intercept=1.0, slope=0.75)

    base = fit_spatial_lag(y, x, _RING)
    scaled = fit_spatial_lag(scale * y, x, _RING)

    assert abs(base.rho - scaled.rho) < 2e-3
    assert abs(scaled.beta["x1"] - scale * base.beta["x1"]) < 1e-2 * max(1.0, abs(scale))
