"""Owner-local, fixed four-date FMBH reference capture. No eligibility authority."""
import argparse
import os
from pathlib import Path
import time
import uuid
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

from dotenv import dotenv_values

from .acquisition_identity import REGISTRATION_SHA, registration
from .audit_store import AuditFailure, EvidenceStore, canonical, digest, strict_json, utc_now

FIELDS = ("cik", "ticker", "type", "primary_exchange", "active",
          "share_class_figi", "last_updated_utc")
EXPECTED = {"cik": "0000700565", "ticker": "FMBH", "type": "CS",
            "primary_exchange": "XNAS", "active": True}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *_args):
        # Let urllib produce an HTTPError so the redirect response is preserved.
        return None


def credentials_from_env():
    # Explicit local file, no parent traversal, interpolation or environment dump.
    values = dotenv_values(Path.cwd() / ".env", interpolate=False, verbose=False)
    key = os.environ.get("MASSIVE_API_KEY") or values.get("MASSIVE_API_KEY")
    if not isinstance(key, str) or not key.strip():
        raise AuditFailure("MASSIVE_API_KEY_UNAVAILABLE")
    key = key.strip()
    if not key.isascii() or any(ord(c) < 33 or ord(c) > 126 for c in key):
        raise AuditFailure("MASSIVE_API_KEY_INVALID")
    return key


class ReferenceHTTP:
    def __init__(self, store, key, *, opener=None, sleep=time.sleep):
        self.store, self._key = store, key
        self.opener, self.sleep = opener or build_opener(NoRedirect()), sleep
        self.contract = registration()["pilot"]
        self.requests = 0
        self.last_started = None

    def get(self, day):
        spec = self.contract
        # Sequential fixed allowlist; cannot be reused for another endpoint/date.
        if self.requests >= 4 or day != spec["dates"][self.requests]:
            raise AuditFailure("REFERENCE_REQUEST_BUDGET_OR_ORDER")
        if self.last_started is not None:
            self.sleep(max(0, 13 - (time.monotonic() - self.last_started)))
        params = {**spec["parameters"], "date": day}
        url = spec["endpoint"] + "?" + urlencode(params)
        started = utc_now()
        self.last_started = time.monotonic()
        self.requests += 1
        raw, status, failure = b"", None, None
        request = Request(url, method="GET", headers={
            "Authorization": "Bearer " + self._key, "Accept": "application/json",
            "Accept-Encoding": "identity", "User-Agent": "fmbh-reference-probe/1"})
        try:
            with self.opener.open(request, timeout=20) as response:
                status = response.status
                raw = response.read(spec["max_response_bytes"] + 1)
        except HTTPError as exc:
            status = exc.code
            try:
                raw = exc.read(spec["max_response_bytes"] + 1)
            finally:
                exc.close()
        except (OSError, URLError, TimeoutError, ValueError):
            failure = "NETWORK_READ_FAILED"
        if len(raw) > spec["max_response_bytes"]:
            failure, raw = "RESPONSE_BYTE_LIMIT", b""
        # A provider echo must never put credentials in the evidence archive.
        # No request headers, exception strings or raw bodies reach stdout.
        try:
            decoded = canonical(strict_json(raw))
        except AuditFailure:
            decoded = b""
        if self._key.encode() in raw or self._key.encode() in decoded:
            failure, raw = "SECRET_ECHO_BLOCKED", b""
        if status != 200 and failure is None:
            failure = ("AUTH_OR_ACCESS_REJECTED" if status in (401, 403)
                       else "RATE_LIMITED" if status == 429
                       else "REDIRECT_REJECTED" if status is not None and 300 <= status < 400
                       else "PROVIDER_HTTP_FAILURE")
        request_id = None
        try:
            body = strict_json(raw)
            if isinstance(body, dict) and isinstance(body.get("request_id"), str):
                request_id = body["request_id"]
        except AuditFailure:
            pass
        return self.store.append("massive_reference_http", url, {
            "registration_sha256": REGISTRATION_SHA, "amendment_004_sha256":
            registration()["parent_registration_sha256"], "candidate_cik": spec["cik"],
            "priority_digest": spec["priority_digest"], "method": "GET",
            "endpoint": spec["endpoint"], "parameters": params,
            "started_at": started, "retrieved_at": utc_now(), "http_status": status,
            "provider_request_id": request_id, "failure": failure,
            "raw_response_preserved": failure not in ("SECRET_ECHO_BLOCKED", "RESPONSE_BYTE_LIMIT"),
            "source_times": {"published_at": None, "captured_at": None,
                             "revised_at": None, "known_at": None, "available_at": None},
            "source_times_note": "Unknown: last_updated_utc retained in raw row, never mapped to first publication or knowledge",
            "historical_query_resolution": "date", "untrusted": True}, raw)


def inspect_response(body, previous_figi=None):
    if not isinstance(body, dict) or body.get("status") != "OK":
        raise AuditFailure("PROVIDER_RESPONSE_STRUCTURE")
    if body.get("next_url"):
        raise AuditFailure("UNEXPECTED_PAGINATION")
    rows = body.get("results")
    if not isinstance(rows, list) or not rows:
        raise AuditFailure("MISSING_RESULT")
    if len(rows) > 1:
        raise AuditFailure("AMBIGUOUS_MULTIPLE_ROWS")
    row = rows[0]
    if not isinstance(row, dict):
        raise AuditFailure("MALFORMED_REFERENCE_ROW")
    for field, expected in EXPECTED.items():
        if field not in row or row[field] is None:
            raise AuditFailure("MISSING_IDENTITY_FIELD:" + field)
        if type(row[field]) is not type(expected) or row[field] != expected:
            raise AuditFailure("IDENTIFIER_DISAGREEMENT:" + field)
    for field in ("share_class_figi", "last_updated_utc"):
        if field in row and (not isinstance(row[field], str) or not row[field]):
            raise AuditFailure("MALFORMED_OPTIONAL_FIELD:" + field)
    figi = row.get("share_class_figi")
    if figi is not None and previous_figi is not None and figi != previous_figi:
        raise AuditFailure("IDENTIFIER_DISAGREEMENT:share_class_figi")
    return figi


def run_probe(http, store):
    reg = registration()
    report = {"version": "fmbh-massive-reference-probe-v1",
              "registration_sha256": REGISTRATION_SHA,
              "amendment_004_sha256": reg["parent_registration_sha256"],
              "candidate": {k: reg["pilot"][k] for k in ("cik", "priority", "priority_digest")},
              "status": "PASS", "stop_reason": None, "dates": [],
              "eligibility_decision": "UNRESOLVED", "ledger_modified": False,
              "structural_validation_performed": False, "created_at": utc_now()}
    figi = None
    for day in reg["pilot"]["dates"]:
        item = {"date": day, "status": "UNRESOLVED", "reason": None,
                "fields": {}, "missing_fields": list(FIELDS)}
        try:
            record = http.get(day)
            meta = record["metadata"]
            item.update(http_status=meta["http_status"], retrieved_at=meta["retrieved_at"],
                        provider_request_id=meta["provider_request_id"],
                        evidence_reference={"record_id": record["id"], "sha256": record["blob_sha"]},
                        parameters=meta["parameters"],
                        access="HTTP_200" if meta["http_status"] == 200 else meta["failure"])
            if meta["failure"]:
                raise AuditFailure(meta["failure"])
            body = strict_json(store.raw(record))
            # Preserve observed fields before policy comparison, even on mismatch.
            if isinstance(body, dict) and isinstance(body.get("results"), list):
                rows = body["results"]
                if len(rows) == 1 and isinstance(rows[0], dict):
                    item["fields"] = {k: rows[0][k] for k in FIELDS if k in rows[0]}
                    item["missing_fields"] = [k for k in FIELDS if k not in rows[0]]
            next_figi = inspect_response(body, figi)
            figi = next_figi or figi
            item["status"] = "PASS"
        except AuditFailure as exc:
            item["reason"] = str(exc)
            item["status"] = "FAIL" if str(exc).startswith("IDENTIFIER_DISAGREEMENT") else "UNRESOLVED"
            report["status"], report["stop_reason"] = item["status"], item["reason"]
        report["dates"].append(item)
        if item["status"] != "PASS":
            break
    report["requests_made"] = http.requests
    report["unrequested_dates"] = reg["pilot"]["dates"][len(report["dates"]):]
    store.append("massive_reference_probe", "FMBH/four-date-pilot", report, canonical(report))
    report["store_verification"] = store.verify()
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", default="runs/fmbh_massive_reference_005")
    args = parser.parse_args(argv)
    store = None
    try:
        registration()
        key = credentials_from_env()
        store = EvidenceStore(args.store)
        store.verify()  # Fail before any request if an existing archive is corrupt.
        report = run_probe(ReferenceHTTP(store, key), store)
        output = Path(args.store) / ("reference-probe-" + uuid.uuid4().hex + ".json")
        with output.open("xb") as handle:
            handle.write(canonical(report) + b"\n")
        print(canonical(report).decode())
        return 0 if report["status"] == "PASS" else 2
    except AuditFailure as exc:
        print(canonical({"status": "UNRESOLVED", "stop_reason": str(exc),
                         "eligibility_decision": "UNRESOLVED"}).decode())
        return 2
    except (OSError, ValueError):
        print('{"status":"UNRESOLVED","stop_reason":"LOCAL_IO_OR_CONFIGURATION_FAILURE"}')
        return 2
    finally:
        if store is not None:
            store.close()


if __name__ == "__main__":
    raise SystemExit(main())
