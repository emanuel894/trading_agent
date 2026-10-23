"""Project guard acceptance harness; not a production agent orchestrator.

Providers return data, never commands. No candidate code is executed here. Real
API-backed providers, branch publication and real PR approval are not activated.
"""
from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile
from time import monotonic
from typing import Protocol

from . import VERSION


STATES = {"QUEUED", "IMPLEMENTING", "TESTING", "REVIEWING", "REPAIRING",
          "READY_FOR_HUMAN", "BLOCKED", "PAUSED_BUDGET"}
TERMINAL = {"READY_FOR_HUMAN", "BLOCKED", "PAUSED_BUDGET"}
EDGES = {
    "QUEUED": {"IMPLEMENTING", "BLOCKED"},
    "IMPLEMENTING": {"TESTING", "BLOCKED", "PAUSED_BUDGET"},
    "TESTING": {"REVIEWING", "REPAIRING", "BLOCKED"},
    "REVIEWING": {"READY_FOR_HUMAN", "REPAIRING", "BLOCKED", "PAUSED_BUDGET"},
    "REPAIRING": {"IMPLEMENTING", "BLOCKED"},
}
POLICIES = ("AI_PROJECT_POLICY.md", "AGENTS.md", "CLOUD_AUTOMATION_PLAN_20261017.md")
CONFIG = "automation/control.json"
SAFE_FINDING = {"id", "severity", "path", "line", "code"}
SHA = re.compile(r"[0-9a-f]{40}\Z")


class BoundaryError(RuntimeError):
    """Only stable codes, never arbitrary provider/HTTP/secret-bearing text."""


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      allow_nan=False, ensure_ascii=True).encode()


def digest(value):
    return hashlib.sha256(value).hexdigest()


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise BoundaryError("DUPLICATE_JSON_KEY")
            result[key] = value
        return result
    try:
        return json.loads(raw, object_pairs_hook=pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(
                              BoundaryError("NONFINITE_JSON")))
    except (ValueError, UnicodeError, RecursionError):
        raise BoundaryError("INVALID_JSON") from None


def integer(value, minimum=0, maximum=1_000_000):
    if type(value) is not int or not minimum <= value <= maximum:
        raise BoundaryError("INVALID_INTEGER")
    return value


def sha(value):
    if not isinstance(value, str) or not SHA.fullmatch(value):
        raise BoundaryError("INVALID_SHA")
    return value


def safe_path(value, root, allowed):
    if (not isinstance(value, str) or not value or len(value) > 240
            or not value.isascii() or any(c in value for c in "\\:%\x00\r\n")
            or value.startswith("/") or value != str(PurePosixPath(value))):
        raise BoundaryError("PATH_ESCAPE")
    parts = value.split("/")
    if any(p in {"", ".", ".."} or p.endswith((".", " ")) for p in parts):
        raise BoundaryError("PATH_ESCAPE")
    controls = {".git", ".github", ".claude", ".codex", ".gemini", ".env",
                "agents.md", "agents.override.md", "claude.md", "gemini.md",
                "ai_project_policy.md", "hooks", "mcp.json"}
    if any(p.lower() in controls or p.lower().startswith(".env.") for p in parts):
        raise BoundaryError("CONTROL_PATH_REJECTED")
    if value not in allowed:
        raise BoundaryError("OUTSIDE_ALLOWED_PATHS")
    root = Path(root).resolve()
    target = root
    for part in parts:
        target /= part
        if target.is_symlink():
            raise BoundaryError("SYMLINK_REJECTED")
    if not target.resolve().is_relative_to(root):
        raise BoundaryError("PATH_ESCAPE")
    return value


def load_trust(root, base_sha):
    """Read exact Git objects, not PR-controlled instruction/config files."""
    base_sha = sha(base_sha)
    root = Path(root).resolve()
    def git(*args):
        p = subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                           timeout=20, check=False)
        if p.returncode:
            raise BoundaryError("TRUSTED_BASE_UNAVAILABLE")
        return p.stdout
    if git("rev-parse", "HEAD").decode().strip() != base_sha:
        raise BoundaryError("STALE_BASE_SHA")
    blobs = {}
    for name in (*POLICIES, CONFIG):
        raw = git("show", f"{base_sha}:{name}")
        path = root / name
        if path.is_symlink() or not path.is_file() or path.read_bytes() != raw:
            raise BoundaryError("UNTRUSTED_CONTROL_CHECKOUT")
        blobs[name] = raw
    cfg = strict_json(blobs[CONFIG])
    if (canonical(cfg) != canonical({"schema_version": 1, "mode": "synthetic", "max_repair_cycles": 2,
                "max_provider_calls": 6, "max_cost_microusd": 0,
                "implementation_target": "openai/codex", "review_target": "google/gemini",
                "provider_activation_enabled": False,
                "allowed_path_template": "automation/synthetic/issue-{issue_number}.txt"})):
        raise BoundaryError("UNSUPPORTED_CONTROL_CONFIGURATION")
    return {"base_sha": base_sha, "policy_hash": digest(canonical(
                {n: digest(blobs[n]) for n in POLICIES})),
            "control_hash": digest(blobs[CONFIG]), "config": cfg}


class Implementer(Protocol):
    identity: dict
    estimated_cost_microusd: int

    def implement(self, context: dict) -> dict: ...


class Reviewer(Protocol):
    identity: dict
    estimated_cost_microusd: int

    def review(self, context: dict) -> dict: ...


class CI(Protocol):
    def test(self, context: dict) -> dict: ...


@contextmanager
def exclusive_run(directory):
    """Same task cannot acquire a second local implementer/reviewer owner."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    lock = directory / "controller.lock"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise BoundaryError("TASK_ALREADY_RUNNING") from None
    try:
        os.close(fd)
        yield
    finally:
        lock.unlink()


class Controller:
    def __init__(self, *, root, directory, trust, issue_number, scenario,
                 implementer: Implementer, reviewer: Reviewer, ci: CI,
                 run_id="local", issue_snapshot_hash=None):
        self.root, self.directory = Path(root), Path(directory)
        self.path = self.directory / "state.json"
        self.trust = trust
        self.implementer, self.reviewer, self.ci = implementer, reviewer, ci
        integer(issue_number, 1, 2_147_483_647)
        if not re.fullmatch(r"[a-z0-9-]{1,40}", scenario):
            raise BoundaryError("INVALID_SCENARIO")
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", run_id):
            raise BoundaryError("INVALID_RUN_ID")
        if issue_snapshot_hash is None:
            issue_snapshot_hash = digest(f"synthetic-issue-{issue_number}".encode())
        if not re.fullmatch(r"[0-9a-f]{64}", issue_snapshot_hash):
            raise BoundaryError("INVALID_ISSUE_SNAPSHOT_HASH")
        self.allowed = [f"automation/synthetic/issue-{issue_number}.txt"]
        identities = []
        for provider in (implementer, reviewer):
            identity = provider.identity
            if (set(identity) != {"provider", "model", "tool_version", "synthetic"}
                    or identity["synthetic"] is not True
                    or any(not re.fullmatch(r"[a-zA-Z0-9./_-]{1,80}", identity[k])
                           for k in ("provider", "model", "tool_version"))):
                raise BoundaryError("PROVIDER_ACTIVATION_DISABLED")
            integer(provider.estimated_cost_microusd)
            identities.append(deepcopy(identity))
        if identities[0]["provider"] == identities[1]["provider"]:
            raise BoundaryError("REVIEWER_NOT_INDEPENDENT_ROLE")
        self.task = {"schema_version": 1, "repository": "emanuel894/trading_agent",
                     "issue_number": issue_number, "base_sha": sha(trust["base_sha"]),
                     "source_head_sha": trust["base_sha"],
                     "issue_snapshot_hash": issue_snapshot_hash,
                     "policy_hash": trust["policy_hash"], "control_hash": trust["control_hash"],
                     "tool_version": VERSION, "scenario": scenario, "run_id": run_id,
                     "mode": "synthetic", "providers": identities,
                     "allowed_paths": self.allowed,
                     "max_repair_cycles": 2, "max_provider_calls": 6,
                     "max_cost_microusd": 0}
        self.snapshot = {"state": "QUEUED", "repair_cycles": 0, "provider_calls": 0, "provider_retries": 0,
                         "estimated_cost_microusd": 0, "model_reported_cost_microusd": None,
                         "head_sha": trust["base_sha"], "head_kind": "synthetic",
                         "changes": [], "tests": None, "review": None, "findings": [], "reason": None,
                         "elapsed_ms": 0}
        self.events = []

    def _validate_snapshot(self, value):
        if set(value) != set(self.snapshot) or value["state"] not in STATES:
            raise BoundaryError("INVALID_SNAPSHOT")
        integer(value["repair_cycles"], 0, 2)
        integer(value["provider_calls"], 0, 6)
        integer(value["provider_retries"], 0, 6)
        integer(value["estimated_cost_microusd"])
        integer(value["elapsed_ms"], 0, 2**63 - 1)
        sha(value["head_sha"])
        if value["head_kind"] != "synthetic":
            raise BoundaryError("NON_SYNTHETIC_HEAD")
        if not isinstance(value["changes"], list) or len(value["changes"]) > 5:
            raise BoundaryError("INVALID_CHANGE_SET")
        for change in value["changes"]:
            if (not isinstance(change, dict) or set(change) != {"path", "content"}
                    or not isinstance(change["content"], str) or len(change["content"]) > 4096):
                raise BoundaryError("INVALID_CHANGE_CONTENT")
            safe_path(change["path"], self.root, self.allowed)
        expected_head = (hashlib.sha1(canonical({"base": self.task["base_sha"],
                                               "changes": value["changes"]})).hexdigest()
                         if value["changes"] else self.task["base_sha"])
        if value["head_sha"] != expected_head:
            raise BoundaryError("HEAD_CONTENT_MISMATCH")
        if value["estimated_cost_microusd"] > self.task["max_cost_microusd"]:
            raise BoundaryError("BUDGET_INTEGRITY_FAILED")
        if value["reason"] is not None and not re.fullmatch(r"[A-Z0-9_]{1,80}", value["reason"]):
            raise BoundaryError("INVALID_REASON")
        tests = value["tests"]
        if tests is not None:
            self._validate_ci(tests, value["head_sha"])
        review = value["review"]
        if review is not None:
            if (not isinstance(review, dict) or set(review) != {"head_sha", "conclusion"}
                    or review["head_sha"] != value["head_sha"]
                    or review["conclusion"] not in {"passed", "changes_requested"}):
                raise BoundaryError("STALE_OR_INVALID_REVIEW")
        if value["state"] == "READY_FOR_HUMAN" and (
                tests is None or tests["conclusion"] != "passed" or review is None
                or review["conclusion"] != "passed" or value["findings"]):
            raise BoundaryError("MISSING_ACCEPTANCE_EVIDENCE")

    def _load(self):
        if not self.path.exists():
            return
        if self.path.is_symlink() or self.path.stat().st_size > 1_000_000:
            raise BoundaryError("INVALID_STATE_FILE")
        record = strict_json(self.path.read_bytes())
        if set(record) != {"task", "events", "snapshot"} or record["task"] != self.task:
            raise BoundaryError("RESUME_CONTEXT_MISMATCH")
        previous_hash, previous_state = None, "QUEUED"
        previous_repairs, previous_calls = 0, 0
        for seq, event in enumerate(record["events"]):
            if set(event) != {"seq", "previous_hash", "recorded_at", "from_state", "snapshot", "hash"}:
                raise BoundaryError("INVALID_JOURNAL")
            envelope = {k: v for k, v in event.items() if k != "hash"}
            if (event["seq"] != seq or event["previous_hash"] != previous_hash
                    or event["hash"] != digest(canonical(envelope))
                    or event["from_state"] != previous_state):
                raise BoundaryError("JOURNAL_INTEGRITY_FAILED")
            snap = event["snapshot"]
            self._validate_snapshot(snap)
            if (snap["state"] != previous_state
                    and snap["state"] not in EDGES.get(previous_state, set())):
                raise BoundaryError("INVALID_STATE_TRANSITION")
            expected_repairs = previous_repairs + (snap["state"] == "REPAIRING"
                                                   and previous_state != "REPAIRING")
            if (snap["repair_cycles"] != expected_repairs
                    or not previous_calls <= snap["provider_calls"] <= previous_calls + 1):
                raise BoundaryError("COUNTER_INTEGRITY_FAILED")
            previous_hash, previous_state = event["hash"], snap["state"]
            previous_repairs, previous_calls = snap["repair_cycles"], snap["provider_calls"]
        if not record["events"] or record["snapshot"] != record["events"][-1]["snapshot"]:
            raise BoundaryError("SNAPSHOT_INTEGRITY_FAILED")
        self.events, self.snapshot = record["events"], record["snapshot"]

    def _record(self, state=None, reason=None):
        previous_state = self.events[-1]["snapshot"]["state"] if self.events else "QUEUED"
        if state is not None:
            if state != previous_state and state not in EDGES.get(previous_state, set()):
                raise BoundaryError("INVALID_STATE_TRANSITION")
            self.snapshot["state"] = state
        self.snapshot["reason"] = reason
        self._validate_snapshot(self.snapshot)
        event = {"seq": len(self.events),
                 "previous_hash": self.events[-1]["hash"] if self.events else None,
                 "recorded_at": datetime.now(timezone.utc).isoformat(),
                 "from_state": previous_state, "snapshot": deepcopy(self.snapshot)}
        event["hash"] = digest(canonical(event))
        self.events.append(event)
        raw = canonical({"task": self.task, "snapshot": self.snapshot, "events": self.events}) + b"\n"
        if self.path.is_symlink():
            raise BoundaryError("SYMLINK_REJECTED")
        fd, name = tempfile.mkstemp(prefix="state-", suffix=".next", dir=self.directory)
        temp = Path(name)
        with os.fdopen(fd, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, self.path)

    def _context(self):
        # No process environment, issue body, transcripts, executable config or keys.
        return {"issue_number": self.task["issue_number"], "base_sha": self.task["base_sha"],
                "head_sha": self.snapshot["head_sha"], "policy_hash": self.task["policy_hash"],
                "policy_reference": "AI_PROJECT_POLICY.md", "allowed_paths": self.allowed,
                "repair_cycle": self.snapshot["repair_cycles"],
                "changes": deepcopy(self.snapshot["changes"])}

    def _call(self, provider, method):
        estimate = provider.estimated_cost_microusd
        if self.snapshot["estimated_cost_microusd"] + estimate > self.task["max_cost_microusd"]:
            self._record("PAUSED_BUDGET", "PER_RUN_BUDGET_EXHAUSTED")
            return None
        if self.snapshot["provider_calls"] >= 6:
            self._record("BLOCKED", "PROVIDER_CALL_CAP")
            return None
        if self.snapshot["reason"] == "PROVIDER_ATTEMPT_RESERVED":
            self.snapshot["provider_retries"] += 1
        self.snapshot["provider_calls"] += 1
        self.snapshot["estimated_cost_microusd"] += estimate
        self._record(reason="PROVIDER_ATTEMPT_RESERVED")
        # Real ambiguous API retries need a separate activation implementation.
        started = monotonic()
        try:
            result = getattr(provider, method)(self._context())
            if not isinstance(result, dict) or len(canonical(result)) > 32_000:
                raise BoundaryError("INVALID_PROVIDER_RESULT")
            self.snapshot["elapsed_ms"] += max(0, int((monotonic() - started) * 1000))
            return result
        except Exception:
            self.snapshot["elapsed_ms"] += max(0, int((monotonic() - started) * 1000))
            self._record("BLOCKED", "PROVIDER_FAILED")
            return None
        # The next transition durably records the completed call duration.

    def _repair(self, reason):
        if self.snapshot["repair_cycles"] >= 2:
            self._record("BLOCKED", "REPAIR_CAP_REACHED")
        else:
            self.snapshot["repair_cycles"] += 1
            self._record("REPAIRING", reason)

    def _implementation(self):
        result = self._call(self.implementer, "implement")
        if result is None:
            return
        if set(result) != {"changes", "model_reported_cost_microusd"}:
            raise BoundaryError("INVALID_IMPLEMENTATION_SCHEMA")
        if (result["model_reported_cost_microusd"] is not None
                and (type(result["model_reported_cost_microusd"]) is not int
                     or result["model_reported_cost_microusd"] != 0)):
            raise BoundaryError("UNEXPECTED_PROVIDER_COST")
        changes = result["changes"]
        if not isinstance(changes, list) or not 1 <= len(changes) <= 5:
            raise BoundaryError("INVALID_CHANGE_SET")
        seen = set()
        for change in changes:
            if not isinstance(change, dict) or set(change) != {"path", "content"}:
                raise BoundaryError("INVALID_CHANGE_SCHEMA")
            path = safe_path(change["path"], self.root, self.allowed)
            if path in seen or not isinstance(change["content"], str) or len(change["content"]) > 4096:
                raise BoundaryError("INVALID_CHANGE_CONTENT")
            seen.add(path)
        self.snapshot["changes"] = changes
        # A synthetic content identifier, explicitly not a real Git commit/PR.
        self.snapshot["head_sha"] = hashlib.sha1(canonical({
            "base": self.task["base_sha"], "changes": changes})).hexdigest()
        self.snapshot["tests"], self.snapshot["review"], self.snapshot["findings"] = None, None, []
        self.snapshot["model_reported_cost_microusd"] = result["model_reported_cost_microusd"]
        self._record("TESTING")

    @staticmethod
    def _validate_ci(result, head):
        if (not isinstance(result, dict) or set(result) != {"head_sha", "conclusion", "tests", "secretless", "synthetic"}
                or result["head_sha"] != head):
            raise BoundaryError("STALE_OR_INVALID_CI")
        integer(result["tests"], 1)
        if result["secretless"] is not True or result["synthetic"] is not True:
            raise BoundaryError("CI_BOUNDARY_VIOLATION")
        if result["conclusion"] not in {"passed", "failed"}:
            raise BoundaryError("CI_INCOMPLETE")

    def _testing(self):
        started = monotonic()
        try:
            result = self.ci.test(self._context())
        except Exception:
            raise BoundaryError("CI_UNAVAILABLE") from None
        self.snapshot["elapsed_ms"] += max(0, int((monotonic() - started) * 1000))
        self._validate_ci(result, self.snapshot["head_sha"])
        self.snapshot["tests"] = result
        if result["conclusion"] == "passed":
            self._record("REVIEWING")
        elif result["conclusion"] == "failed":
            self._repair("CI_FAILED")
        else:
            raise BoundaryError("CI_INCOMPLETE")

    def _review(self):
        result = self._call(self.reviewer, "review")
        if result is None:
            return
        if (set(result) != {"head_sha", "conclusion", "findings", "model_reported_cost_microusd"}
                or result["head_sha"] != self.snapshot["head_sha"]):
            raise BoundaryError("STALE_OR_INVALID_REVIEW")
        if (result["model_reported_cost_microusd"] is not None
                and (type(result["model_reported_cost_microusd"]) is not int
                     or result["model_reported_cost_microusd"] != 0)):
            raise BoundaryError("UNEXPECTED_PROVIDER_COST")
        findings = result["findings"]
        if not isinstance(findings, list) or len(findings) > 20:
            raise BoundaryError("INVALID_REVIEW_FINDINGS")
        for item in findings:
            if (not isinstance(item, dict) or set(item) != SAFE_FINDING
                    or item["severity"] not in {"low", "medium", "high"}
                    or not re.fullmatch(r"F[0-9]{1,3}", str(item["id"]))
                    or item["code"] not in {"SYNTHETIC_DEFECT"}):
                raise BoundaryError("INVALID_REVIEW_FINDING")
            integer(item["line"], 1)
            safe_path(item["path"], self.root, self.allowed)
        self.snapshot["findings"] = findings
        if result["conclusion"] == "passed" and not findings:
            self.snapshot["review"] = {"head_sha": result["head_sha"], "conclusion": "passed"}
            self._record("READY_FOR_HUMAN", "SYNTHETIC_ACCEPTANCE_ONLY")
        elif result["conclusion"] == "changes_requested" and findings:
            self.snapshot["review"] = {"head_sha": result["head_sha"], "conclusion": "changes_requested"}
            self._repair("REVIEW_CHANGES_REQUESTED")
        else:
            raise BoundaryError("REVIEW_INCOMPLETE")

    def run(self, max_steps=50):
        integer(max_steps, 1, 50)
        with exclusive_run(self.directory):
            self._load()
            if not self.events:
                self._record()
            for _ in range(max_steps):
                state = self.snapshot["state"]
                if state in TERMINAL:
                    break
                try:
                    if state in {"QUEUED", "REPAIRING"}:
                        self._record("IMPLEMENTING")
                    elif state == "IMPLEMENTING":
                        self._implementation()
                    elif state == "TESTING":
                        self._testing()
                    elif state == "REVIEWING":
                        self._review()
                except BoundaryError as exc:
                    self._record("BLOCKED", str(exc))
                except Exception:
                    self._record("BLOCKED", "CONTROL_FAILED")
            return {"task": deepcopy(self.task), "snapshot": deepcopy(self.snapshot),
                    "events": deepcopy(self.events)}
