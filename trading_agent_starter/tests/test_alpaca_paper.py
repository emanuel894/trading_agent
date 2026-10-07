from datetime import datetime, timezone
import os
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from agent.alpaca_paper import AlpacaPaperAdapter, AlpacaPaperConfig, probe_to_dict


class FakeTradingClient:
    def get_account(self):
        return SimpleNamespace(status="ACTIVE", currency="USD")

    def get_clock(self):
        now = datetime(2026, 9, 14, 15, 0, tzinfo=timezone.utc)
        return SimpleNamespace(
            is_open=True,
            timestamp=now,
            next_open=now,
            next_close=now,
        )

    def get_all_positions(self):
        return [SimpleNamespace(symbol="SPY")]

    def get_orders(self, *, filter):
        self.last_filter = filter
        return [SimpleNamespace(id="paper-order-1")]


class FakeDataClient:
    def get_stock_latest_quote(self, request):
        self.last_request = request
        stamp = datetime(2026, 9, 14, 15, 0, tzinfo=timezone.utc)
        return {
            "SPY": SimpleNamespace(bid_price=500.0, ask_price=500.1, timestamp=stamp),
            "QQQ": SimpleNamespace(bid_price=480.0, ask_price=480.2, timestamp=stamp),
        }


class AlpacaConfigTests(unittest.TestCase):
    def base_env(self):
        return {
            "BROKER": "alpaca",
            "ALPACA_PAPER": "true",
            "ALPACA_API_KEY": "paper-key",
            "ALPACA_API_SECRET": "paper-secret",
            "ALPACA_DATA_FEED": "iex",
            "TRADING_ENABLED": "false",
            "ALLOW_PAPER_ORDERS": "false",
        }

    def test_valid_paper_configuration_passes(self):
        with patch.dict(os.environ, self.base_env(), clear=True):
            config = AlpacaPaperConfig.from_env()
        self.assertEqual(config.data_feed, "iex")
        self.assertEqual(config.api_key, "paper-key")

    def test_live_or_execution_flags_are_rejected(self):
        for key in ("ALPACA_LIVE_TRADE", "TRADING_ENABLED", "ALLOW_PAPER_ORDERS"):
            env = self.base_env()
            env[key] = "true"
            with patch.dict(os.environ, env, clear=True):
                with self.assertRaises(ValueError):
                    AlpacaPaperConfig.from_env()

    def test_paper_false_is_rejected(self):
        env = self.base_env()
        env["ALPACA_PAPER"] = "false"
        with patch.dict(os.environ, env, clear=True):
            with self.assertRaises(ValueError):
                AlpacaPaperConfig.from_env()

    def test_non_iex_feed_is_rejected_for_foundation(self):
        env = self.base_env()
        env["ALPACA_DATA_FEED"] = "sip"
        with patch.dict(os.environ, env, clear=True):
            with self.assertRaises(ValueError):
                AlpacaPaperConfig.from_env()


class AlpacaProbeTests(unittest.TestCase):
    def test_probe_is_read_only_and_normalized(self):
        adapter = AlpacaPaperAdapter(
            AlpacaPaperConfig("key", "secret"),
            trading_client=FakeTradingClient(),
            data_client=FakeDataClient(),
            quote_request_factory=lambda symbols: tuple(symbols),
            open_orders_request_factory=lambda: "OPEN",
        )
        result = probe_to_dict(adapter.probe(["spy", "QQQ", "SPY"]))
        self.assertEqual(result["status"], "READ_ONLY_CHECK_PASSED")
        self.assertEqual(result["broker"], "alpaca")
        self.assertEqual(result["mode"], "paper-read-only")
        self.assertEqual(result["positions_count"], 1)
        self.assertEqual(result["open_orders_count"], 1)
        self.assertEqual(set(result["quotes"]), {"SPY", "QQQ"})

    def test_empty_symbol_list_is_rejected(self):
        adapter = AlpacaPaperAdapter(
            AlpacaPaperConfig("key", "secret"),
            trading_client=FakeTradingClient(),
            data_client=FakeDataClient(),
            quote_request_factory=lambda symbols: tuple(symbols),
            open_orders_request_factory=lambda: "OPEN",
        )
        with self.assertRaises(ValueError):
            adapter.probe([])


if __name__ == "__main__":
    unittest.main()
