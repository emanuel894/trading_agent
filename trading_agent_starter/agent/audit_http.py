"""Bounded GET-only source acquisition; document URLs never gain authority."""
from __future__ import annotations

import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .audit_store import AuditFailure, VERSION, utc_now


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise AuditFailure("REDIRECT_REJECTED")


class ReadOnlyHTTP:
    def __init__(self, store, *, user_agent, credentials=None, max_requests=2000,
                 min_interval=0.25, opener=None, sleep=time.sleep):
        if not user_agent or len(user_agent) > 256 or "\n" in user_agent or "\r" in user_agent:
            raise AuditFailure("INVALID_SEC_USER_AGENT")
        if not 1 <= max_requests <= 5000 or min_interval < 0.25:
            raise AuditFailure("INVALID_HTTP_BUDGET")
        self.store, self.user_agent = store, user_agent
        self.credentials = credentials
        self.remaining, self.min_interval = max_requests, min_interval
        self.bytes_remaining = 2_000_000_000
        self.opener, self.sleep = opener or build_opener(NoRedirect()), sleep
        self.last_request = 0.0

    @staticmethod
    def check_url(url):
        parsed = urlsplit(url)
        if (parsed.scheme != "https" or parsed.username or parsed.password
                or parsed.port or parsed.fragment or "%" in parsed.path or ".." in parsed.path):
            raise AuditFailure("URL_REJECTED")
        allowed = {
            "data.sec.gov": r"/submissions/[A-Za-z0-9_.-]+\.json",
            "www.sec.gov": r"/Archives/edgar/data/\d+/\d{18}/[A-Za-z0-9_.-]+",
            "data.alpaca.markets": r"/v2/stocks/(bars|quotes)",
            "paper-api.alpaca.markets": r"/v2/calendar",
        }
        if parsed.hostname not in allowed or not re.fullmatch(allowed[parsed.hostname], parsed.path):
            raise AuditFailure("URL_REJECTED")
        return parsed.hostname

    def get(self, url, *, max_bytes=40_000_000):
        host = self.check_url(url)
        headers = {"User-Agent": self.user_agent, "Accept-Encoding": "identity"}
        if host.endswith("alpaca.markets"):
            if not self.credentials or not all(self.credentials):
                raise AuditFailure("SIP_CREDENTIALS_UNAVAILABLE")
            headers.update({"APCA-API-KEY-ID": self.credentials[0],
                            "APCA-API-SECRET-KEY": self.credentials[1]})
        for attempt in range(3):
            if self.remaining <= 0:
                raise AuditFailure("HTTP_REQUEST_BUDGET_EXHAUSTED")
            if self.bytes_remaining <= 0:
                raise AuditFailure("HTTP_BYTE_BUDGET_EXHAUSTED")
            self.sleep(max(0.0, self.min_interval - (time.monotonic() - self.last_request)))
            self.last_request = time.monotonic()
            self.remaining -= 1
            started, tick = utc_now(), time.monotonic()
            status, raw, response_headers, failure = None, b"", {}, None
            try:
                with self.opener.open(Request(url, headers=headers, method="GET"), timeout=20) as response:
                    status = response.status
                    response_headers = {k.lower(): v for k, v in response.headers.items()
                                        if k.lower() in {"content-type", "date", "etag", "last-modified"}}
                    allowed_bytes = min(max_bytes, self.bytes_remaining)
                    raw = response.read(allowed_bytes + 1)
                    if len(raw) > allowed_bytes:
                        failure = "RESPONSE_TOO_LARGE"
                        raw = raw[:allowed_bytes]
            except HTTPError as exc:
                status, failure = exc.code, f"HTTP_{exc.code}"
                raw = exc.read(min(max_bytes, 65536))
            except AuditFailure as exc:
                failure = str(exc)
            except (OSError, URLError, TimeoutError):
                failure = "NETWORK_READ_FAILED"
            finished = utc_now()
            self.bytes_remaining -= len(raw)
            record = self.store.append("http", url, {
                "version": VERSION, "started_at": started, "received_at": finished,
                "elapsed_seconds": time.monotonic() - tick, "attempt": attempt + 1,
                "http_status": status, "headers": response_headers, "failure": failure,
                "method": "GET", "source": host}, raw)
            if not failure and status == 200:
                return record
            if status not in {429, 500, 502, 503, 504} and failure != "NETWORK_READ_FAILED":
                raise AuditFailure(failure or "UNEXPECTED_HTTP_STATUS")
            if attempt < 2:
                self.sleep(2 ** attempt)
        raise AuditFailure(failure or "HTTP_RETRIES_EXHAUSTED")
