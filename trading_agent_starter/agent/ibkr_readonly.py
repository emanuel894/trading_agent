"""Official IBKR TWS API adapter for diagnostics and daily history only.

No order construction or order-submission route is exposed. Login and MFA
take place in TWS. Integration with a real TWS session is still unverified.
"""
import csv
from datetime import datetime, timezone
import importlib.metadata
import json
from pathlib import Path
import re
import threading

from .risk import validate_paper_endpoint, verify_managed_accounts


def normalize_error(args):
    # API 10.33+ inserts errorTime; retain compatibility with earlier callbacks.
    if len(args) >= 4 and isinstance(args[2], int):
        req_id, _, code, message = args[:4]
    elif len(args) >= 3:
        req_id, code, message = args[:3]
    else:
        return {"request": -1, "code": -1, "message": "Unrecognized API error callback"}
    message = re.sub(r"\b(?:DU|U)[0-9]+\b", "[ACCOUNT]", str(message))
    return {"request": req_id, "code": code, "message": message}


def run(config_path: str, output: str, history: bool = False) -> dict:
    cfg = json.loads(Path(config_path).read_text(encoding="utf-8-sig"))
    host, port, expected = cfg["host"], cfg["port"], cfg["paper_account"]
    validate_paper_endpoint(host, port, expected)
    client_id = cfg.get("client_id", 97)
    if type(client_id) is not int or client_id <= 0:
        raise ValueError("Use a unique positive client_id, not the special client 0.")
    symbol = cfg.get("history_symbol", "SPY")
    if not re.fullmatch(r"[A-Z]{1,5}", symbol):
        raise ValueError("Only a simple US stock/ETF symbol is supported by this probe.")
    try:
        from ibapi.client import EClient
        from ibapi.wrapper import EWrapper
        from ibapi.contract import Contract
    except ImportError as e:
        raise RuntimeError("Install the official IBKR Python API from the downloaded TWS API package; see guide.") from e

    class Probe(EWrapper, EClient):
        def __init__(self):
            EWrapper.__init__(self)
            EClient.__init__(self, self)
            self.ready = threading.Event()
            self.accounts_ready = threading.Event()
            self.summary_done = threading.Event()
            self.positions_done = threading.Event()
            self.orders_done = threading.Event()
            self.history_done = threading.Event()
            self.accounts, self.errors, self.bars = [], [], []
            self.summary_tags, self.position_count, self.order_count = set(), 0, 0

        def nextValidId(self, orderId):
            self.ready.set()

        def managedAccounts(self, accountsList):
            self.accounts = [a for a in accountsList.split(",") if a]
            self.accounts_ready.set()

        def error(self, *args):
            self.errors.append(normalize_error(args))

        def accountSummary(self, reqId, account, tag, value, currency):
            if account == expected:
                self.summary_tags.add(tag)  # no account values in the diagnostic

        def accountSummaryEnd(self, reqId):
            self.summary_done.set()

        def position(self, account, contract, position, avgCost):
            if account == expected and position != 0:
                self.position_count += 1

        def positionEnd(self):
            self.positions_done.set()

        def openOrder(self, orderId, contract, order, orderState):
            if order.account == expected:
                self.order_count += 1

        def openOrderEnd(self):
            self.orders_done.set()

        def historicalData(self, reqId, bar):
            # Discard today's daily bar, which may still be forming.
            day = datetime.strptime(str(bar.date), "%Y%m%d").date()
            if day < datetime.now(timezone.utc).date():
                self.bars.append({"date": day.isoformat(), "open": float(bar.open),
                    "high": float(bar.high), "low": float(bar.low), "close": float(bar.close),
                    "volume": float(bar.volume)})

        def historicalDataEnd(self, reqId, start, end):
            self.history_done.set()

        # Defense against accidental future use through this adapter.
        def placeOrder(self, *args, **kwargs):
            raise RuntimeError("Broker order submission is not part of Foundation 0.1.")

        def cancelOrder(self, *args, **kwargs):
            raise RuntimeError("Order cancellation is not part of this read-only adapter.")

        def reqGlobalCancel(self, *args, **kwargs):
            raise RuntimeError("Global cancellation is not part of this read-only adapter.")

    app, worker = Probe(), None
    destination = Path(output)
    destination.mkdir(parents=True, exist_ok=True)
    report = {"status": "FAILED", "mode": "IBKR_READ_ONLY_PAPER",
              "checked_utc": datetime.now(timezone.utc).isoformat(),
              "broker_orders_sent": 0, "live_execution_available": False,
              "market_data_entitlement_verified": False,
              "note": "Snapshot diagnostics are not continuous reconciliation or a trading-readiness gate."}
    try:
        app.connect(host, port, clientId=client_id)
        worker = threading.Thread(target=app.run, daemon=True)
        worker.start()
        if not app.ready.wait(20) or not app.accounts_ready.wait(10):
            raise RuntimeError("API handshake timed out. Check Paper login, socket settings, and client ID.")
        verify_managed_accounts(expected, app.accounts)
        report["exact_paper_account_match"] = True
        report["server_version"] = app.serverVersion()
        try:
            report["ibapi_version"] = importlib.metadata.version("ibapi")
        except importlib.metadata.PackageNotFoundError:
            report["ibapi_version"] = "unknown"
        app.reqAccountSummary(9001, "All", "NetLiquidation,TotalCashValue,AvailableFunds")
        app.reqPositions()
        app.reqAllOpenOrders()
        for label, event in [("summary", app.summary_done), ("positions", app.positions_done),
                             ("orders", app.orders_done)]:
            if not event.wait(15):
                raise RuntimeError(f"Incomplete {label} snapshot. Do not infer empty state from a timeout.")
        if "NetLiquidation" not in app.summary_tags:
            raise RuntimeError("Expected account summary is missing.")
        app.cancelAccountSummary(9001)
        app.cancelPositions()
        report.update(position_count=app.position_count, open_order_count=app.order_count,
                      received_summary_tags=sorted(app.summary_tags))
        if history:
            contract = Contract()
            contract.symbol, contract.secType = symbol, "STK"
            contract.exchange, contract.currency = "SMART", "USD"
            # Example symbol only. Production must resolve conId, exchange, tick size.
            app.reqHistoricalData(9002, contract, "", "2 Y", "1 day", "TRADES", 1, 1, False, [])
            if not app.history_done.wait(45) or not app.bars:
                raise RuntimeError("Historical data missing/incomplete; check API data entitlements and errors.")
            rows = sorted(app.bars, key=lambda r: r["date"])
            csv_path = destination / f"{symbol}_daily.csv"
            with csv_path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
            meta = {"source": "IBKR TWS API", "symbol": symbol, "bar_size": "1 day",
                    "what_to_show": "TRADES", "use_rth": True, "rows": len(rows),
                    "retrieved_utc": report["checked_utc"],
                    "warning": "Not a point-in-time universe or a verified total-return data set."}
            csv_path.with_suffix(".metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
            report.update(history_file=csv_path.name, history_rows=len(rows))
        blocking = [m for m in app.errors if m["code"] in {502, 504, 1100, 1300}
                    or m["request"] in {9001, 9002}]
        if blocking or not app.isConnected():
            raise RuntimeError("API error or disconnection during the check; inspect api_messages.")
        report["status"] = "READ_ONLY_CHECK_PASSED"
    except Exception as exc:
        report["failure"] = re.sub(r"\b(?:DU|U)[0-9]+\b", "[ACCOUNT]", str(exc))
    finally:
        app.disconnect()
        if worker:
            worker.join(timeout=3)
        report["api_messages"] = app.errors
        (destination / "connection_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
