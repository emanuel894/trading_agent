from copy import deepcopy
from datetime import datetime
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from agent.__main__ import main
from agent.alpaca_history import AlpacaHistoryProvider
from agent.alpaca_paper import AlpacaPaperConfig
from agent.market_data import HistoryRequest

HAS_SDK = importlib.util.find_spec("alpaca") is not None


def dt(value):
    return datetime.fromisoformat(value)


def request():
    return HistoryRequest(("SPY", "QQQ"), dt("2026-09-14T13:30:00Z"),
                          dt("2026-09-14T14:00:00Z"), dt("2026-09-14T14:01:00Z"))


def raw_bar(stamp="2026-09-14T13:30:00Z"):
    return {"t": stamp, "o": 100, "h": 102, "l": 99, "c": 101, "v": 1000, "n": 20, "vw": 100.5}


@unittest.skipUnless(HAS_SDK, "Install requirements.txt to run SDK compatibility tests")
class SDKIntegrationTests(unittest.TestCase):
    def provider(self, pages=None, calendar=None):
        from alpaca.data.historical import StockHistoricalDataClient
        from alpaca.trading.models import Calendar
        data = StockHistoricalDataClient("fixture-key", "fixture-secret")
        captured = []
        iterator = iter(pages if pages is not None else [
            {"bars": {"QQQ": [raw_bar()]}, "next_page_token": "second"},
            {"bars": {"SPY": [raw_bar()]}, "next_page_token": None},
        ])

        def get(*, path, data):
            captured.append((path, deepcopy(data)))
            return next(iterator)

        # Exercise the actual SDK paginator and BarSet parsing, without HTTP.
        data.get = Mock(side_effect=get)
        trading = Mock(spec_set=["get_calendar"])
        trading.get_calendar.return_value = calendar if calendar is not None else [
            Calendar(date="2026-09-14", open="09:30", close="16:00")]
        provider = AlpacaHistoryProvider(AlpacaPaperConfig("fixture-key", "fixture-secret"),
                                         data_client=data, calendar_client=trading)
        return provider, captured

    def test_actual_sdk_paginates_to_other_symbols_and_fixes_request_settings(self):
        provider, captured = self.provider()
        result = provider.fetch(request())
        self.assertTrue(result.ready)
        self.assertEqual(len(result.bars), 2)
        self.assertEqual(captured[0][0], "/stocks/bars")
        self.assertEqual(str(captured[0][1]["timeframe"]), "30Min")
        self.assertEqual(captured[0][1]["feed"], "iex")
        self.assertEqual(captured[0][1]["adjustment"], "raw")
        self.assertEqual(captured[0][1]["asof"], "-")
        self.assertEqual(captured[1][1]["page_token"], "second")
        self.assertIsNone(captured[0][1]["page_token"])
        self.assertEqual(provider._calendar.get_calendar.call_args.args[0].start, request().start.date())

    def test_empty_intermediate_page_does_not_end_pagination(self):
        provider, captured = self.provider([
            {"bars": {}, "next_page_token": "continue"},
            {"bars": {s: [raw_bar()] for s in request().symbols}, "next_page_token": None}])
        self.assertTrue(provider.fetch(request()).ready)
        self.assertEqual(len(captured), 2)

    def test_end_inclusive_provider_response_filtered_to_exclusive_contract(self):
        provider, _ = self.provider([{"bars": {s: [raw_bar(), raw_bar("2026-09-14T14:00:00Z")]
                                                for s in request().symbols}}])
        self.assertEqual(len(provider.fetch(request()).bars), 2)

    def test_later_page_failure_aborts_whole_fetch_and_redacts_sdk_exception(self):
        provider, _ = self.provider()
        provider._data.get.side_effect = [
            {"bars": {"QQQ": [raw_bar()]}, "next_page_token": "second"},
            RuntimeError("fixture-secret request detail")]
        with self.assertRaises(RuntimeError) as error:
            provider.fetch(request())
        self.assertNotIn("fixture-secret", str(error.exception))

    def test_dst_calendar_conversion_uses_new_york_not_fixed_offset(self):
        from alpaca.trading.models import Calendar
        calendar = [Calendar(date="2026-03-06", open="09:30", close="16:00"),
                    Calendar(date="2026-03-09", open="09:30", close="16:00")]
        provider, _ = self.provider([{"bars": {}}], calendar)
        req = HistoryRequest(("SPY",), dt("2026-03-06T00:00:00Z"),
                             dt("2026-03-10T00:00:00Z"), dt("2026-03-10T00:01:00Z"))
        result = provider.fetch(req)
        self.assertEqual([s.open.hour for s in result.sessions], [14, 13])
        self.assertEqual(len(result.expected), 26)

    def test_sdk_early_close_is_honored(self):
        from alpaca.trading.models import Calendar
        provider, _ = self.provider([{"bars": {}}], [Calendar(date="2026-11-27", open="09:30", close="13:00")])
        req = HistoryRequest(("SPY",), dt("2026-11-27T00:00:00Z"),
                             dt("2026-11-28T00:00:00Z"), dt("2026-11-28T00:01:00Z"))
        self.assertEqual(len(provider.fetch(req).expected), 7)

    def test_paper_client_is_hard_coded_and_history_exposes_no_order_api(self):
        with patch("alpaca.trading.client.TradingClient") as trading:
            provider = AlpacaHistoryProvider(AlpacaPaperConfig("fixture-key", "fixture-secret"), data_client=object())
        trading.assert_called_once_with("fixture-key", "fixture-secret", paper=True)
        self.assertFalse(hasattr(provider, "submit_order"))
        self.assertFalse(hasattr(provider, "cancel_order"))

    def test_unsupported_calendar_year_and_feed_fail(self):
        provider, captured = self.provider()
        req = HistoryRequest(("SPY",), dt("2030-01-02T00:00:00Z"),
                             dt("2030-01-03T00:00:00Z"), dt("2030-01-03T00:01:00Z"))
        with self.assertRaises(ValueError):
            provider.fetch(req)
        self.assertEqual(captured, [])
        with self.assertRaises(ValueError):
            AlpacaHistoryProvider(AlpacaPaperConfig("fixture-key", "fixture-secret", "sip"),
                                  data_client=object(), calendar_client=object())

    def test_cli_exports_real_sdk_normalized_snapshot_and_fails_on_missing_symbol(self):
        for omit_spy in (False, True):
            pages = [{"bars": {s: [raw_bar()] for s in (("QQQ",) if omit_spy else request().symbols)}}]
            provider, _ = self.provider(pages)
            with self.subTest(omit_spy=omit_spy), tempfile.TemporaryDirectory() as directory:
                output = Path(directory) / "history"
                config = Path(directory) / "config.json"
                config.write_text(json.dumps({"symbols": ["SPY", "QQQ"], "publication_delay_seconds": 60}))
                argv = ["agent", "alpaca-history", "--config", str(config), "--start", "2026-09-14T13:30:00Z",
                        "--end", "2026-09-14T14:00:00Z", "--as-of", "2026-09-14T14:01:00Z", "--output", str(output)]
                with patch("sys.argv", argv), patch("sys.stdout", new_callable=io.StringIO), \
                        patch("agent.alpaca_history.AlpacaPaperConfig.from_env", return_value=AlpacaPaperConfig("key", "secret")), \
                        patch("agent.alpaca_history.AlpacaHistoryProvider", return_value=provider):
                    status = main()
                self.assertEqual(status, 1 if omit_spy else 0)
                manifest = json.loads((output / "manifest.json").read_text())
                self.assertEqual(manifest["source"], "alpaca")
                self.assertEqual(manifest["quality"]["symbols"]["SPY"]["stale"], omit_spy)


class CLIFailureTests(unittest.TestCase):
    def test_naive_timestamp_fails_before_connection(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config.json"
            config.write_text(json.dumps({"symbols": ["SPY"], "publication_delay_seconds": 60}))
            argv = ["agent", "alpaca-history", "--config", str(config), "--start", "2026-09-14T13:30:00",
                    "--end", "2026-09-14T14:00:00Z", "--output", str(Path(directory) / "output")]
            with patch("sys.argv", argv), patch("sys.stderr", new_callable=io.StringIO) as errors, \
                    patch("agent.alpaca_history.run_history") as run:
                self.assertEqual(main(), 1)
                run.assert_not_called()
                self.assertIn("timezone", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
