from __future__ import annotations

import unittest

import numpy as np

from dre.skills.backprop import lp_relaxation_timboxed
from dre.skills.causal import propensity_overlap_1d, tier1_gate
from dre.skills.coherence import validate_coherence
from dre.skills.drift import frobenius_norm_diff, psi_histogram_score
from dre.skills.forecasting import fit_univariate_series
from dre.skills.override import classify_override_delta_kpi
from dre.skills.stress import stress_lp_batch


class TestDRESkills(unittest.TestCase):
    def test_coherence(self) -> None:
        self.assertTrue(validate_coherence("sha256:abc", "STANDARD")[0])
        self.assertFalse(validate_coherence("md5:abc", "STANDARD")[0])

    def test_forecasting(self) -> None:
        rng = np.random.default_rng(0)
        rep = fit_univariate_series(rng.normal(size=50))
        self.assertIn("cv_effective", rep)

    def test_stress_lp(self) -> None:
        c = np.array([1.0, 1.0])
        A = np.array([[1.0, 1.0]])
        b = np.array([2.0])
        deltas = [np.array([0.0]), np.array([-0.5])]
        res = stress_lp_batch(c, A, b, deltas)
        self.assertEqual(res.n_scenarios, 2)
        self.assertGreaterEqual(res.min_slack_global, 0.0)

    def test_backprop_relaxation(self) -> None:
        c = np.array([1.0, 1.0])
        A = np.array([[1.0, 1.0]])
        b = np.array([3.0])
        status, detail = lp_relaxation_timboxed(c, A, b, timeout_sec=5.0)
        self.assertEqual(status, "FEASIBLE")
        self.assertIn("solver", detail)

    def test_drift_metrics(self) -> None:
        rng = np.random.default_rng(1)
        ref = rng.normal(size=300)
        act = rng.normal(loc=0.05, scale=1.0, size=300)
        psi = psi_histogram_score(ref, act)
        self.assertGreaterEqual(psi, 0.0)
        X = rng.multivariate_normal([0, 0], [[1.0, 0.2], [0.2, 1.0]], size=100)
        sigma_ref = np.cov(X.T)
        sigma_act = sigma_ref + np.array([[0.01, 0.0], [0.0, 0.01]])
        fr = frobenius_norm_diff(sigma_ref, sigma_act)
        self.assertGreater(fr, 0.0)

    def test_causal_overlap(self) -> None:
        rng = np.random.default_rng(2)
        t = rng.normal(1.0, 0.1, size=200)
        c = rng.normal(1.0, 0.1, size=200)
        ov = propensity_overlap_1d(t, c)
        self.assertGreaterEqual(ov, 0.0)
        self.assertLessEqual(ov, 1.0)
        self.assertEqual(tier1_gate(ov), "PASS")

    def test_override_classify(self) -> None:
        self.assertEqual(classify_override_delta_kpi(2.0), "AUTO_APPROVE")
        self.assertEqual(classify_override_delta_kpi(-10.0), "ELEVATED")
        self.assertEqual(classify_override_delta_kpi(-20.0), "REJECT")
