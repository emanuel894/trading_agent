"""Fixed-pilot durable HTTP accounting using the existing EvidenceStore.

Not a pilot launcher or resource sandbox. The approved private context must pin
one sole ledger and independently enforce physical storage/free-space, RAM and
process deadline before any acquisition. No credentials, reset or new identity
API. An ambiguous outstanding attempt stays charged and blocks further calls.
"""
from datetime import timedelta

from .audit_store import AuditFailure, canonical, digest, timestamp, utc_now


class IQP1HTTPBudget:
    KEY = "IQP1_BOUNDARY_20261106_V1"
    KIND = "iqp1_http_budget"

    @classmethod
    def create(cls, store, *, max_attempts=128, body_limit=2_000_000_000,
               max_seconds=1800, clock=utc_now):
        limits = ((max_attempts, 128), (body_limit, 2_000_000_000), (max_seconds, 1800))
        if any(type(value) is not int or not 1 <= value <= ceiling for value, ceiling in limits):
            raise AuditFailure("PILOT_BUDGET_LIMITS_INVALID")
        now = timestamp(clock())
        with store.transaction():
            if store.records(cls.KIND, cls.KEY):
                raise AuditFailure("PILOT_BUDGET_ALREADY_INITIALIZED")
            store.append_in_transaction(cls.KIND, cls.KEY, {
                "op": "config", "ledger_root": str(store.root.resolve()),
                "max_attempts": max_attempts, "body_limit": body_limit,
                "at": now.isoformat(), "deadline": (now + timedelta(seconds=max_seconds)).isoformat(),
            })
        return cls(store, clock=clock)

    def __init__(self, store, *, clock=utc_now):
        self.store, self.clock = store, clock
        store.verify()
        self._state()

    def _state(self):
        events = self.store.records(self.KIND, self.KEY)
        if not events:
            raise AuditFailure("PILOT_BUDGET_NOT_INITIALIZED")
        reservations, config, last = {}, None, None
        try:
            for event in events:
                envelope = dict(event)
                expected = envelope.pop("record_hash")
                if digest(canonical(envelope)) != expected:
                    raise AuditFailure("PILOT_BUDGET_RECORD_MISMATCH")
                data = event["metadata"]
                at = timestamp(data["at"])
                if last is not None and at < last:
                    raise AuditFailure("PILOT_BUDGET_CLOCK_REGRESSION")
                last = at
                if data["op"] == "config" and config is None and not reservations:
                    config = data
                    if config["ledger_root"] != str(self.store.root.resolve()):
                        raise AuditFailure("PILOT_BUDGET_LEDGER_BINDING_CHANGED")
                elif data["op"] == "reserve" and config is not None:
                    reservations[event["id"]] = dict(data, retained=None)
                elif data["op"] == "settle" and config is not None:
                    prior = reservations[data["reservation_id"]]
                    if prior["retained"] is not None or not 0 <= data["retained"] <= prior["allowance"]:
                        raise AuditFailure("PILOT_BUDGET_SETTLEMENT_CONFLICT")
                    response = self._response(data["reservation_id"], prior, data["http_record_id"])
                    if (self.store.objects / response["blob_sha"]).stat().st_size != data["retained"]:
                        raise AuditFailure("PILOT_HTTP_SETTLEMENT_SIZE_MISMATCH")
                    prior["retained"] = data["retained"]
                else:
                    raise AuditFailure("PILOT_BUDGET_EVENT_INVALID")
            if config is None:
                raise AuditFailure("PILOT_BUDGET_CONFIG_MISSING")
            charged = sum(r["allowance"] if r["retained"] is None else r["retained"]
                          for r in reservations.values())
            if len(reservations) > config["max_attempts"] or charged > config["body_limit"]:
                raise AuditFailure("PILOT_BUDGET_LEDGER_OVER_CAP")
            return config, reservations, charged, last
        except (KeyError, TypeError, ValueError, OSError):
            raise AuditFailure("PILOT_BUDGET_LEDGER_INVALID") from None

    def _response(self, reservation_id, prior, http_record_id):
        response = self.store.get(http_record_id)
        envelope = dict(response)
        expected = envelope.pop("record_hash")
        if (digest(canonical(envelope)) != expected or response["kind"] != "http"
                or response["source_key"] != prior["url"] or not response["blob_sha"]
                or response["metadata"].get("budget_reservation_id") != reservation_id):
            raise AuditFailure("PILOT_HTTP_SETTLEMENT_EVIDENCE_MISMATCH")
        return response

    def snapshot(self):
        config, reservations, charged, _ = self._state()
        return {"attempts": len(reservations), "charged_body_bytes": charged,
                "retained_body_bytes": sum(r["retained"] or 0 for r in reservations.values()),
                "pending": [key for key, r in reservations.items() if r["retained"] is None],
                "max_attempts": config["max_attempts"], "body_limit": config["body_limit"],
                "deadline": config["deadline"], "ledger_root": config["ledger_root"]}

    def _now(self, last):
        now = timestamp(self.clock())
        if now < last:
            raise AuditFailure("PILOT_BUDGET_CLOCK_REGRESSION")
        return now

    def reserve(self, url, max_bytes):
        if type(max_bytes) is not int or not 1 <= max_bytes <= 40_000_000:
            raise AuditFailure("PILOT_HTTP_RESERVATION_SIZE_INVALID")
        with self.store.transaction():
            config, reservations, charged, last = self._state()
            now = self._now(last)
            if now >= timestamp(config["deadline"]):
                raise AuditFailure("PILOT_HTTP_DEADLINE_EXHAUSTED")
            if any(r["retained"] is None for r in reservations.values()):
                raise AuditFailure("PILOT_HTTP_ATTEMPT_UNRECONCILED")
            if len(reservations) >= config["max_attempts"]:
                raise AuditFailure("PILOT_HTTP_ATTEMPT_BUDGET_EXHAUSTED")
            allowance = min(max_bytes, config["body_limit"] - charged)
            if allowance <= 0:
                raise AuditFailure("PILOT_HTTP_BYTE_BUDGET_EXHAUSTED")
            event = self.store.append_in_transaction(self.KIND, self.KEY, {
                "op": "reserve", "url": url, "allowance": allowance, "at": now.isoformat(),
            })
            return event["id"], allowance

    def settle(self, reservation_id, http_record_id):
        """Release unused allowance only against matching retained, hashed bytes.

        Also reconciles a crash after HTTP persistence but before settlement.
        With no matching HTTP evidence, the reservation cannot be cleared.
        """
        with self.store.transaction():
            _, reservations, _, last = self._state()
            prior = reservations.get(reservation_id)
            if prior is None or prior["retained"] is not None:
                raise AuditFailure("PILOT_HTTP_RESERVATION_NOT_PENDING")
            response = self._response(reservation_id, prior, http_record_id)
            retained = len(self.store.raw(response))
            if retained > prior["allowance"]:
                raise AuditFailure("PILOT_HTTP_BODY_ALLOWANCE_EXCEEDED")
            self.store.append_in_transaction(self.KIND, self.KEY, {
                "op": "settle", "reservation_id": reservation_id,
                "http_record_id": http_record_id, "retained": retained,
                "at": self._now(last).isoformat(),
            })
