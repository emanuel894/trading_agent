"""Separate minute/SIP audit contract. It neither imports nor changes 30m code."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
import math
import re
import time
from urllib.parse import urlencode
import uuid

import pytz

from .audit_store import AuditFailure, VERSION, canonical, strict_json, timestamp, utc_now

EASTERN = pytz.timezone("America/New_York")
MINUTE_NS = 60_000_000_000


def nanoseconds(value):
    match = re.fullmatch(r"(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(?:\.(\d{1,9}))?(Z|[+-]\d\d:\d\d)", value)
    if not match:
        raise AuditFailure("INVALID_NATIVE_TIMESTAMP")
    dt = timestamp(match[1] + match[3])
    delta = dt - datetime(1970, 1, 1, tzinfo=timezone.utc)
    return (delta.days * 86400 + delta.seconds) * 1_000_000_000 + int((match[2] or "").ljust(9, "0"))


def positive(value, *, zero=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise AuditFailure("INVALID_MARKET_NUMBER")
    if value < 0 or (not zero and value == 0):
        raise AuditFailure("INVALID_MARKET_NUMBER")
    return value


def validate_quote(row, cutoff, *, received_at=None, prospective=False):
    t, now = nanoseconds(row["t"]), nanoseconds(cutoff)
    if not 0 <= now - t <= 2_000_000_000:
        raise AuditFailure("STALE_OR_FUTURE_QUOTE")
    if prospective and (received_at is None or nanoseconds(received_at) > now):
        raise AuditFailure("QUOTE_NOT_KNOWN_AT_ACTION")
    bid, ask = positive(row["bp"]), positive(row["ap"])
    positive(row["bs"])
    positive(row["as"])
    if bid >= ask:
        raise AuditFailure("LOCKED_OR_CROSSED_QUOTE")
    if row.get("c") != ["R"] or row.get("z") not in {"A", "B", "C"}:
        raise AuditFailure("UNSUPPORTED_QUOTE_CONDITION")
    if not row.get("bx") or not row.get("ax"):
        raise AuditFailure("MISSING_QUOTE_EXCHANGE")
    spread = (ask - bid) / ((ask + bid) / 2) * 10000
    if spread > 20:
        raise AuditFailure("SPREAD_TOO_WIDE")
    return {"spread_bps": spread, "midpoint": (ask + bid) / 2,
            "provider_timestamp": row["t"], "provider_timestamp_ns": t,
            "bid": bid, "ask": ask, "bid_size_round_lots": row["bs"],
            "ask_size_round_lots": row["as"], "quote_condition_policy": "R-only-v1"}


def validate_bar(row):
    t = nanoseconds(row["t"])
    if t % MINUTE_NS:
        raise AuditFailure("MISALIGNED_MINUTE_BAR")
    o, h, l, c = [positive(row[k]) for k in ("o", "h", "l", "c")]
    positive(row["v"], zero=True)
    if not l <= min(o, c) <= max(o, c) <= h:
        raise AuditFailure("INVALID_MINUTE_OHLC")
    return t


def choose_action(ready, sessions):
    ready = timestamp(ready)
    rounded = ready.replace(second=0, microsecond=0)
    if rounded < ready:
        rounded += timedelta(minutes=1)
    for opening, closing in sessions:
        candidate = max(rounded, opening + timedelta(minutes=5))
        if candidate <= closing - timedelta(minutes=30):
            return candidate.isoformat()
    raise AuditFailure("NO_ACTIONABLE_SESSION")


class SIPSource:
    def __init__(self, store, http):
        self.store, self.http = store, http

    def calendar(self, ready):
        day = timestamp(ready).astimezone(EASTERN).date()
        params = urlencode({"start": (day - timedelta(days=7)).isoformat(),
                            "end": (day + timedelta(days=10)).isoformat()})
        record = self.http.get("https://paper-api.alpaca.markets/v2/calendar?" + params)
        rows = strict_json(self.store.raw(record))
        if not isinstance(rows, list) or not rows:
            raise AuditFailure("CALENDAR_UNAVAILABLE")
        sessions = []
        try:
            for row in rows:
                opening, closing = [EASTERN.localize(datetime.fromisoformat(row["date"] + "T" + row[k]),
                                                   is_dst=None).astimezone(timezone.utc)
                                    for k in ("open", "close")]
                if not opening < closing or (sessions and opening <= sessions[-1][1]):
                    raise AuditFailure("INVALID_CALENDAR_ORDER")
                sessions.append((opening, closing))
        except (TypeError, KeyError, ValueError):
            raise AuditFailure("MALFORMED_CALENDAR") from None
        return sessions, record["id"]

    def pages(self, kind, symbols, start, end, *, max_pages=50):
        if kind not in {"bars", "quotes"} or not symbols or len(symbols) > 2:
            raise AuditFailure("INVALID_MARKET_REQUEST")
        if not all(re.fullmatch(r"[A-Z][A-Z0-9.]{0,9}", s) for s in symbols):
            raise AuditFailure("INVALID_MARKET_SYMBOL")
        if not timestamp(start) < timestamp(end) <= timestamp(utc_now()):
            raise AuditFailure("MARKET_WINDOW_NOT_COMPLETE")
        params = {"symbols": ",".join(symbols), "start": start, "end": end,
                  "feed": "sip", "asof": "-", "sort": "asc", "limit": 10000}
        if kind == "bars":
            params.update(timeframe="1Min", adjustment="raw")
        rows, records, tokens = {s: [] for s in symbols}, [], set()
        for _ in range(max_pages):
            response = self.http.get("https://data.alpaca.markets/v2/stocks/" + kind + "?" + urlencode(params))
            data = strict_json(self.store.raw(response))
            if not isinstance(data, dict) or not isinstance(data.get(kind), dict):
                raise AuditFailure("MALFORMED_SIP_RESPONSE")
            records.append(response["id"])
            for symbol, batch in data[kind].items():
                if symbol not in rows or not isinstance(batch, list):
                    raise AuditFailure("UNEXPECTED_SIP_SYMBOL")
                for row in batch:
                    if not isinstance(row, dict) or not isinstance(row.get("t"), str):
                        raise AuditFailure("MALFORMED_SIP_ROW")
                    if not nanoseconds(start) <= nanoseconds(row["t"]) <= nanoseconds(end):
                        raise AuditFailure("SIP_ROW_OUTSIDE_REQUEST")
                rows[symbol].extend((r, response["id"], response["metadata"]["received_at"]) for r in batch)
            token = data.get("next_page_token")
            if not token:
                if any(not value for value in rows.values()):
                    raise AuditFailure("MISSING_SIP_SYMBOL")
                return rows, records
            if not isinstance(token, str) or token in tokens:
                raise AuditFailure("REPEATED_SIP_PAGE_TOKEN")
            tokens.add(token)
            params["page_token"] = token
        raise AuditFailure("SIP_PAGE_CAP_EXCEEDED")

    def context(self, symbol, ready, *, mode="historical_backfill"):
        sessions, calendar_id = self.calendar(ready)
        action = choose_action(ready, sessions)
        action_dt = timestamp(action)
        earlier = [close for _, close in sessions if close < action_dt]
        if not earlier:
            raise AuditFailure("PRIOR_SESSION_MISSING")
        begin = earlier[-1] - timedelta(minutes=1)
        end = action_dt + timedelta(minutes=30)
        symbols = list(dict.fromkeys([symbol, "SPY"]))
        bars, bar_ids = self.pages("bars", symbols, begin.isoformat(), end.isoformat())
        quotes, quote_ids = self.pages("quotes", symbols, (action_dt - timedelta(seconds=60)).isoformat(),
                                       (action_dt + timedelta(seconds=60)).isoformat())
        result = {"feed": "sip", "actionable_at": action, "deadline_provisional": True,
                  "calendar_id": calendar_id, "bar_records": bar_ids, "quote_records": quote_ids,
                  "symbols": {}, "mode": mode, "failures": [],
                  "quote_size_units": "round_lots", "fill_simulated": False}
        for sym in symbols:
            normalized, expected = {}, []
            for row, record_id, received in bars[sym]:
                t = validate_bar(row)
                if not nanoseconds(begin.isoformat()) <= t <= nanoseconds(end.isoformat()):
                    raise AuditFailure("BAR_OUTSIDE_REQUEST")
                if t in normalized and canonical(normalized[t][0]) != canonical(row):
                    raise AuditFailure("CONFLICTING_MINUTE_VERSION")
                normalized[t] = row, record_id
            # Missing RTH minutes are reported, never synthesized. Sparse extended
            # hours can mean no trades; quantify them without inventing bars.
            for opening, closing in sessions:
                t = max(opening, begin)
                while t < min(closing, end):
                    expected.append(nanoseconds(t.isoformat()))
                    t += timedelta(minutes=1)
            gaps = sum(t not in normalized for t in expected)
            valid = [(r, rid, rec) for r, rid, rec in quotes[sym]
                     if nanoseconds(r["t"]) <= nanoseconds(action)]
            if not valid:
                raise AuditFailure("NO_PREACTION_QUOTE")
            latest = max(nanoseconds(r["t"]) for r, _, _ in valid)
            same = [(r, rid, rec) for r, rid, rec in valid if nanoseconds(r["t"]) == latest]
            if len({canonical(r) for r, _, _ in same}) > 1:
                raise AuditFailure("AMBIGUOUS_QUOTE_ORDER")
            row, rid, received = same[-1]
            snapshot = validate_quote(row, action)
            snapshot.update(quote_record=rid, received_at=received, rth_minutes_expected=len(expected),
                            rth_minutes_missing=gaps, observed_minute_bars=len(normalized))
            result["symbols"][sym] = snapshot
            if gaps:
                result["failures"].append("RTH_MINUTE_GAPS:" + sym)
        if mode == "prospective":
            # Historical REST responses cannot prove what a live process knew.
            stream = stream_context(self.store, symbols, action)
            result["stream_context"] = stream
            result["failures"].extend(stream["failures"])
        return result


def stream_context(store, symbols, action):
    cutoff = nanoseconds(action)
    quotes, statuses, sessions = {}, {}, {}
    for record in store.records("stream_frame"):
        meta = record["metadata"]
        if meta["received_ns"] > cutoff:
            continue
        for row in strict_json(store.raw(record)):
            sym = row.get("S")
            if sym not in symbols or row.get("T") not in {"q", "s"}:
                continue
            if nanoseconds(row["t"]) > cutoff:
                continue
            target = quotes if row["T"] == "q" else statuses
            if sym not in target or nanoseconds(row["t"]) > nanoseconds(target[sym][0]["t"]):
                target[sym] = row, record
            sessions[sym] = meta["session_id"]
    result = {"quotes": {}, "status_records": {}, "failures": []}
    for symbol in symbols:
        try:
            if symbol not in quotes:
                raise AuditFailure("PROSPECTIVE_QUOTE_MISSING")
            row, record = quotes[symbol]
            ends = store.records("stream_end", record["metadata"]["session_id"])
            if not ends or ends[-1]["metadata"].get("failure") or nanoseconds(ends[-1]["metadata"]["finished_at"]) < cutoff:
                result["failures"].append("STREAM_CONTINUITY_UNVERIFIED:" + symbol)
            result["quotes"][symbol] = dict(validate_quote(row, action,
                received_at=record["metadata"]["received_at"], prospective=True), record_id=record["id"])
            if symbol not in statuses:
                raise AuditFailure("TRADING_STATUS_UNKNOWN")
            status, sr = statuses[symbol]
            if sr["metadata"]["session_id"] != record["metadata"]["session_id"]:
                raise AuditFailure("STATUS_FROM_DIFFERENT_STREAM_SESSION")
            if (status.get("z") in {"A", "B"} and status.get("sc") != "3"
                    or status.get("z") == "C" and status.get("sc") != "T"
                    or status.get("z") not in {"A", "B", "C"}):
                raise AuditFailure("TRADING_STATUS_NOT_CONFIRMED")
            result["status_records"][symbol] = sr["id"]
        except AuditFailure as exc:
            result["failures"].append(str(exc) + ":" + symbol)
    return result


async def capture_sip(store, credentials, symbols, seconds, *, max_frames=100000):
    """A bounded data-only websocket; no broker endpoint or order capability."""
    if not credentials or not all(credentials):
        raise AuditFailure("SIP_CREDENTIALS_UNAVAILABLE")
    if (not 1 <= seconds <= 1800 or not 1 <= len(symbols) <= 10
            or not all(re.fullmatch(r"[A-Z][A-Z0-9.]{0,9}", s) for s in symbols)):
        raise AuditFailure("INVALID_CAPTURE_BOUNDS")
    from websockets import connect
    session = uuid.uuid4().hex
    start_ns, tick = time.time_ns(), time.monotonic_ns()
    count, failure, subscribed = 0, None, False
    store.append("stream_session", session, {"started_at": utc_now(), "symbols": symbols,
                 "feed": "sip", "duration_limit_seconds": seconds, "version": VERSION})
    try:
        async with connect("wss://stream.data.alpaca.markets/v2/sip", open_timeout=20,
                           max_size=2_000_000, max_queue=16) as socket:
            connected = strict_json(await asyncio.wait_for(socket.recv(), 20))
            if connected != [{"T": "success", "msg": "connected"}]:
                raise AuditFailure("SIP_CONNECTION_REJECTED")
            await socket.send(canonical({"action": "auth", "key": credentials[0], "secret": credentials[1]}).decode())
            auth = strict_json(await asyncio.wait_for(socket.recv(), 20))
            if auth != [{"T": "success", "msg": "authenticated"}]:
                raise AuditFailure("SIP_AUTH_OR_ENTITLEMENT_REJECTED")
            await socket.send(canonical(dict(action="subscribe", quotes=symbols, bars=symbols,
                                             updatedBars=symbols, statuses=symbols)).decode())
            while (time.monotonic_ns() - tick) / 1e9 < seconds:
                remaining = seconds - (time.monotonic_ns() - tick) / 1e9
                try:
                    raw = await asyncio.wait_for(socket.recv(), min(20, remaining))
                except asyncio.TimeoutError:
                    if not subscribed:
                        raise AuditFailure("SIP_SUBSCRIPTION_TIMEOUT") from None
                    continue
                received_ns, received = time.time_ns(), utc_now()
                if abs((received_ns - start_ns) - (time.monotonic_ns() - tick)) > 1_000_000_000:
                    raise AuditFailure("LOCAL_CLOCK_JUMP")
                messages = strict_json(raw)
                if not isinstance(messages, list) or not messages:
                    raise AuditFailure("MALFORMED_STREAM_FRAME")
                for message in messages:
                    if message.get("T") == "error":
                        raise AuditFailure("SIP_STREAM_ERROR")
                    if message.get("T") == "subscription":
                        if not all(set(message.get(k, [])) == set(symbols)
                                   for k in ("quotes", "bars", "updatedBars", "statuses")):
                            raise AuditFailure("SIP_CHANNEL_NOT_GRANTED")
                        subscribed = True
                    elif message.get("T") not in {"q", "b", "u", "s"} or message.get("S") not in symbols:
                        raise AuditFailure("UNEXPECTED_STREAM_MESSAGE")
                store.append("stream_frame", session, {"session_id": session, "feed": "sip",
                             "received_at": received, "received_ns": received_ns,
                             "sequence_number": count, "capture_mode": "prospective"},
                             raw.encode() if isinstance(raw, str) else raw)
                count += 1
                if count >= max_frames:
                    raise AuditFailure("STREAM_FRAME_CAP_EXCEEDED")
    except AuditFailure as exc:
        failure = str(exc)
    except Exception:
        failure = "SIP_STREAM_CONNECTION_FAILED"
    result = {"session_id": session, "frames": count, "subscribed": subscribed,
              "finished_at": utc_now(), "elapsed_seconds": (time.monotonic_ns() - tick) / 1e9,
              "failure": failure, "absolute_clock_accuracy_verified": False}
    store.append("stream_end", session, result)
    if failure:
        raise AuditFailure(failure)
    return result
