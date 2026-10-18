"""Independent exact Q01-Q03 acceptance, not an economic evaluator/backtester."""
import json
from pathlib import Path


class GateMismatch(Exception):
    def __init__(self, path, expected, actual, blocker=False):
        super().__init__(f"{path}: expected {expected!r}, observed {actual!r}")
        self.blocker = blocker


def equal(path, actual, expected, blocker=False):
    if actual != expected or type(actual) is not type(expected):
        raise GateMismatch(path, expected, actual, blocker)


def assess(actual, expected):
    equal("execution_complete", actual.get("execution_complete"), True)
    if actual.get("blocker"):
        raise GateMismatch("native_terminal_state", None, actual["blocker"], True)
    equal("case_id", actual["case_id"], expected["case_id"])
    equal("external_identity", actual["external_identity"], expected["external_identity"])
    equal("native_symbol.ticker", actual["native_symbol"]["ticker"], expected["external_identity"]["ticker"])
    equal("native_symbol.instrument", actual["native_symbol"]["research_instrument_id"], "I1")
    if not actual["native_symbol"]["sid"]: raise GateMismatch("native_sid", "nonempty", actual["native_symbol"]["sid"])
    events = actual["events"]
    kinds = [e["kind"] for e in events]
    # Mandatory initial orders are preconditions, never waived because holdings survived.
    for intent in ("buy2", "sell3"):
        equal("submitted:" + intent, kinds.count("OrderSubmitted:" + intent), 1)
    equal("ordered_business_events", kinds, expected["ordered_business_kinds"])
    equal("ordered_business_event_times", [e["utc"] for e in events], expected["ordered_business_event_utc"])
    for event in events: equal("event.instrument", event["instrument_id"], "I1")
    native=actual["native_order_events"]
    equal("native_order_count", len(native), len(expected["native_order_sequence"]))
    for i,(event,oracle) in enumerate(zip(native,expected["native_order_sequence"])):
        for k,v in oracle.items(): equal(f"native_event[{i}].{k}",event[k],v)
        equal(f"native_event[{i}].utc",event["utc"],"2025-01-06T14:59:59.0000000Z" if event["status"]=="Submitted" else "2025-01-06T15:01:00.0000000Z")
    equal("reservation_until_ack",actual["reservation_observations"],expected["reservation_observations"])
    equal("nav_probe_count",len(actual["admission_probes"]),1)
    equal("nav_entry_probe",actual["admission_probes"][0],expected["nav_entry_probe"])
    equal("network.non_loopback", actual["network_denied"]["non_loopback_interfaces"], 0)
    equal("network.sentinel", actual["network_denied"]["testnet_socket_result"], "NetworkUnreachable")
    equal("source_pin", actual["source_pin"], "d4cac37514427c84d40064cecbf3f0e6be4b0137")
    branch = "FuncUniverse" if "_explicit_" in actual["case_id"] else "UserDefinedUniverse"
    equal("native_universe_branch", actual["universe_branch"], branch)
    snapshots = actual["snapshots"]
    equal("exact_snapshot_phases",[s["phase"] for s in snapshots],expected["required_snapshot_phases"])
    equal("initial.open_orders", snapshots[0]["open_orders"], 2)
    equal("initial.reserved_cash", snapshots[0]["reserved_cash"], "3")
    equal("initial.reserved_shares", snapshots[0]["reserved_shares"], "3")
    terminal_at = "2025-01-06T15:01:00.0000000Z"
    settlement_at = "2025-01-06T17:00:00.0000000Z"
    terminal = [s for s in snapshots if s["phase"] == "end" or s["phase"] >= terminal_at]
    if not terminal:
        raise GateMismatch("terminal_snapshots", "nonempty", terminal)
    for state in snapshots:
        phase = state["phase"]
        equal(phase + ".denominator", state["denominator"], 1, True)
        if phase != "end" and phase < terminal_at:
            for k, value in expected["before_terminal"].items():
                equal(phase + "." + k, state[k], value, True)
    for state in terminal:
        phase = state["phase"]
        settled = "at_settlement_available" in expected and (phase == "end" or phase >= settlement_at)
        oracle = expected["at_settlement_available"] if settled else expected["after_terminal_before_available"]
        for key in ("engine_quantity", "cash", "denominator", "failures"):
            equal(phase + "." + key, state[key], oracle[key], True)
        for key, value in (("tradable", False), ("open_orders", 0), ("reserved_cash", "0"), ("reserved_shares", "0"), ("scientific_nav", None)):
            equal(phase + "." + key, state[key], value)
        if settled:
            equal(phase + ".claim", state["unresolved_claim"], None, True)
            equal(phase + ".pnl", state["realized_pnl"], oracle["realized_pnl"], True)
            equal(phase + ".settlements", state["action_settlements"], 1, True)
            equal(phase + ".realized_proceeds",state["realized_proceeds"],oracle["amount"],True)
        else:
            equal(phase + ".claim", state["unresolved_claim"], oracle["unresolved_claim"], True)
            equal(phase + ".proceeds", state["realized_proceeds"], None, True)
            equal(phase + ".nav_entry_blocked", state["nav_entry_blocked"], True)
            if not expected["negative_control_violation_required"]:
                equal(phase + ".engine_security_present", state["engine_security_present"], True, True)
    for intent, count in expected["required_cancellations"].items():
        equal("canceled:" + intent, kinds.count("OrderCanceled:" + intent), count)
    fills = [e for e in events if e["kind"].startswith("TradeFill:")]
    if expected["negative_control_violation_required"]:
        equal("negative_control_fill_count", len(fills), 1)
        equal("negative_control_fill_tag", fills[0]["kind"], "TradeFill:Liquidate from delisting")
        for key, outkey in (("fill_quantity", "quantity"), ("fill_price", "price"), ("fee", "fee")):
            equal("negative_control." + key, fills[0]["payload"][outkey], expected["default_liquidation"][key])
        verdict = "CONTRACT_VIOLATION_DETECTED_AS_REQUIRED"
    else:
        equal("unexpected_trade_fills", len(fills), 0, True)
        verdict = "PASS"
    if "at_settlement_available" in expected:
        settlements = [e for e in events if e["kind"] == "ActionSettlement"]
        equal("action_settlement_count", len(settlements), 1, True)
        equal("action_settlement_amount", settlements[0]["payload"]["amount"], expected["at_settlement_available"]["amount"], True)
        equal("action_settlement_admission_time", settlements[0]["utc"], settlement_at, True)
        equal("duplicate_count", kinds.count("DuplicateIgnored"), 1)
        equal("conflict_blocked", actual["conflict_blocked"], "same_version_conflict" in expected)
    else:
        # Q01/Q03 must reach two hourly cleanup boundaries and native run end.
        for required in ("2025-01-06T16:00:00.0000000Z", "2025-01-06T17:00:00.0000000Z", "end"):
            equal("cleanup_or_end:" + required, any(s["phase"] == required for s in snapshots), True)
    return verdict


def compare_files(actual_path, expected_path):
    import hashlib
    actual=json.loads(Path(actual_path).read_text())
    root=Path(expected_path).parent
    equal("input_sha256",actual["input_sha256"],hashlib.sha256((root/"input.json").read_bytes()).hexdigest())
    equal("fixture_manifest_sha256",actual["fixture_manifest_sha256"],hashlib.sha256((root/"manifest.json").read_bytes()).hexdigest())
    return assess(actual,json.loads(Path(expected_path).read_text()))
