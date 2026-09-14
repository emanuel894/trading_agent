from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest

from agent.ibkr_readonly import normalize_error
from agent.ledger import Ledger
from agent.replay import Bar, load_bars, replay, synthetic_bars
from agent.risk import Intent, Snapshot, check, validate_paper_endpoint, verify_managed_accounts


class RiskTests(unittest.TestCase):
    def setUp(self):
        self.intent = Intent("BUY", 5, 100., 99.95, 100., 1000., 1001.)
        self.state = Snapshot(10000., 9000., 1000., 1000.)

    def test_valid_order_passes(self):
        self.assertEqual(check(self.intent, self.state), (True, "approved"))

    def test_real_endpoints_rejected(self):
        for port in (7496, 4001, 1234):
            with self.assertRaises(ValueError):
                validate_paper_endpoint("127.0.0.1", port, "DU12345")

    def test_remote_or_live_account_rejected(self):
        for host, account in [("0.0.0.0", "DU12345"), ("127.0.0.1", "U12345"),
                              ("127.0.0.1", "DU")]:
            with self.assertRaises(ValueError):
                validate_paper_endpoint(host, 7497, account)

    def test_paper_port_does_not_override_account_check(self):
        validate_paper_endpoint("127.0.0.1", 7497, "DU12345")
        for actual in (["U12345"], ["DU22222"], ["DU12345", "U12345"], []):
            with self.assertRaises(ValueError):
                verify_managed_accounts("DU12345", actual)

    def test_stale_and_future_data_block(self):
        for timestamp in (900., 1020.):
            self.assertEqual(check(replace(self.intent, quote_time=timestamp), self.state)[1], "stale_or_future_quote")

    def test_nonfinite_data_block(self):
        for value in (float("nan"), float("inf")):
            self.assertFalse(check(replace(self.intent, ask=value), self.state)[0])
            self.assertFalse(check(self.intent, replace(self.state, equity=value))[0])

    def test_pending_orders_consume_symbol_capacity(self):
        self.assertEqual(check(self.intent, replace(self.state, pending_symbol_buy_usd=600.))[1], "symbol_exposure")

    def test_pending_orders_consume_gross_capacity(self):
        self.assertEqual(check(self.intent, replace(self.state, gross_usd=7400., pending_buy_usd=200.))[1], "gross_exposure")

    def test_reserved_cash_and_shares_not_reused(self):
        self.assertEqual(check(self.intent, replace(self.state, available_cash=100.))[1], "cash")
        self.assertEqual(check(replace(self.intent, side="SELL"), replace(self.state, sellable_shares=3))[1], "short_or_reserved_shares")

    def test_unknown_or_halted_state_blocks(self):
        self.assertFalse(check(self.intent, replace(self.state, known=False))[0])
        self.assertFalse(check(self.intent, replace(self.state, halted=True))[0])

    def test_spread_blocks(self):
        self.assertEqual(check(replace(self.intent, bid=90.), self.state)[1], "spread")


class DurableStateTests(unittest.TestCase):
    def test_duplicate_after_restart_is_not_reserved_again(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "state.db")
            first = Ledger(path)
            self.assertTrue(first.reserve("strategy:date:symbol", {"quantity": 1}))
            first.close()
            second = Ledger(path)
            self.assertFalse(second.reserve("strategy:date:symbol", {"quantity": 1}))
            with self.assertRaises(ValueError):
                second.reserve("strategy:date:symbol", {"quantity": 2})
            second.close()

    def test_halt_survives_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "state.db")
            first = Ledger(path)
            first.halt("position mismatch")
            first.close()
            second = Ledger(path)
            self.assertTrue(second.halted)
            second.close()


class ReplayTests(unittest.TestCase):
    def test_next_bar_execution(self):
        result = replay(synthetic_bars(), buy_hold=True)
        self.assertGreater(result["fill_count"], 0)
        for fill in result["fills"]:
            self.assertGreater(fill["fill_date"], fill["decision_date"])

    def test_future_data_cannot_change_earlier_decisions(self):
        bars = synthetic_bars()
        changed = bars[:200] + [replace(b, open=b.open*2, high=b.high*2, low=b.low*2, close=b.close*2) for b in bars[200:]]
        a, b = replay(bars), replay(changed)
        self.assertEqual(a["equity_curve"][:140], b["equity_curve"][:140])
        cutoff = bars[200].date
        self.assertEqual([f for f in a["fills"] if f["fill_date"] < cutoff],
                         [f for f in b["fills"] if f["fill_date"] < cutoff])

    def test_fee_and_adverse_cost_charged_once(self):
        bars = [Bar(f"2024-01-0{i}", 100, 100, 100, 100, 1000) for i in range(1, 6)]
        result = replay(bars, start=2, fast=1, slow=2, buy_hold=True,
                        initial_cash=10000., allocation=.20, cost_bps=10, minimum_fee=1.)
        self.assertEqual(result["fill_count"], 1)
        self.assertAlmostEqual(result["final_equity"], 9997.)  # 20 * $0.10 + $1
        self.assertAlmostEqual(result["explicit_fees"], 1.)

    def test_cash_baseline_constant(self):
        result = replay(synthetic_bars(), cash_only=True)
        self.assertEqual(result["net_return"], 0.)
        self.assertEqual(result["fill_count"], 0)

    def test_bad_csv_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.csv"
            for rows in ("2024-01-01,100,101,99,nan,10\n", "2024-01-01,100,90,99,100,10\n",
                         "2024-01-01,100,101,99,100,10\n" * 2):
                path.write_text("date,open,high,low,close,volume\n" + rows)
                with self.assertRaises(ValueError):
                    load_bars(str(path))

    def test_simulated_drawdown_latches_stop(self):
        bars = synthetic_bars()
        result = replay(bars, max_drawdown=.001)
        self.assertTrue(result["halt_latched"])
        self.assertEqual(result["equity_curve"][-1]["shares"], 0)


class ApiCompatibilityTests(unittest.TestCase):
    def test_current_error_signature_and_redaction(self):
        result = normalize_error((9002, 1700000000, 162, "DU12345 has no data", ""))
        self.assertEqual(result["code"], 162)
        self.assertNotIn("DU12345", json.dumps(result))

    def test_old_error_signature(self):
        self.assertEqual(normalize_error((9002, 162, "no data", ""))["code"], 162)


if __name__ == "__main__":
    unittest.main()
