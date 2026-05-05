"""Tests unitarios: PI + referencia (spec 2026-04-27)."""
from __future__ import annotations

import math
import unittest

from leverage_pi import default_pi_ref_config, error_e, feedforward_L, leverage_pi_step


class TestLeveragePi(unittest.TestCase):
    def setUp(self) -> None:
        self.cfg = default_pi_ref_config(t_goal=1000.0)

    def test_error_below_s_mode_zero(self) -> None:
        self.assertEqual(error_e(100.0, self.cfg), 0.0)
        self.assertEqual(error_e(249.0, self.cfg), 0.0)

    def test_error_at_s_mode_positive(self) -> None:
        e250 = error_e(250.0, self.cfg)
        self.assertGreater(e250, 0.0)
        self.assertAlmostEqual(e250, math.log(1000.0) - math.log(250.0), places=9)

    def test_feedforward_monotone_band(self) -> None:
        l_lo = feedforward_L(50.0, self.cfg)
        l_mid = feedforward_L(250.0, self.cfg)
        l_hi = feedforward_L(400.0, self.cfg)
        self.assertLessEqual(l_lo, l_mid)
        self.assertLessEqual(l_mid, l_hi)
        self.assertGreaterEqual(l_lo, self.cfg["hard"]["L_min"])
        self.assertLessEqual(l_hi, self.cfg["hard"]["L_max"])

    def test_saturation_high_freezes_integral(self) -> None:
        cfg = default_pi_ref_config(t_goal=1000.0)
        cfg["pi"]["K_p"] = 80.0
        cfg["pi"]["K_i"] = 0.0
        I_prev = 2.5
        E = 400.0
        lev, I_next = leverage_pi_step(E, I_prev, cfg)
        self.assertEqual(I_next, I_prev)
        self.assertEqual(lev, cfg["hard"]["L_max"])

    def test_saturation_low_freezes_integral(self) -> None:
        cfg = default_pi_ref_config(t_goal=1000.0)
        cfg["pi"]["K_p"] = -80.0
        cfg["pi"]["K_i"] = 0.0
        I_prev = -1.0
        E = 400.0
        lev, I_next = leverage_pi_step(E, I_prev, cfg)
        self.assertEqual(I_next, I_prev)
        self.assertEqual(lev, cfg["hard"]["L_min"])

    def test_no_saturation_updates_integral_clamped(self) -> None:
        cfg = default_pi_ref_config(t_goal=1000.0)
        cfg["pi"]["K_p"] = 0.0
        cfg["pi"]["K_i"] = 0.05
        E = 300.0
        I_prev = 0.0
        e = error_e(E, cfg)
        lev, I_next = leverage_pi_step(E, I_prev, cfg)
        self.assertAlmostEqual(I_next, max(-cfg["pi"]["I_max"], min(cfg["pi"]["I_max"], I_prev + e)))
        self.assertGreaterEqual(lev, 1.0)


if __name__ == "__main__":
    unittest.main()
