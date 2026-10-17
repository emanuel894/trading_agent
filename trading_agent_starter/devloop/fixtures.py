"""Deterministic fixtures: two distinct roles, not real independent models."""
from . import VERSION
from .control import BoundaryError

SCENARIOS = ("happy", "repair-once", "repair-cap", "provider-failure", "budget",
             "stale-review", "stale-ci", "path-escape", "control-path", "ci-failure")


class SyntheticImplementer:
    identity = {"provider": "fixture-openai", "model": "synthetic-codex",
                "tool_version": VERSION, "synthetic": True}

    def __init__(self, scenario):
        if scenario not in SCENARIOS:
            raise BoundaryError("UNKNOWN_SCENARIO")
        self.scenario = scenario
        self.estimated_cost_microusd = 1 if scenario == "budget" else 0

    def implement(self, context):
        if self.scenario == "provider-failure":
            raise RuntimeError("Untrusted exception content must not be persisted")
        path = context["allowed_paths"][0]
        if self.scenario == "path-escape":
            path = "../escaped.txt"
        elif self.scenario == "control-path":
            path = "AGENTS.md"
        content = f"Synthetic issue {context['issue_number']}, revision {context['repair_cycle']}\n"
        if self.scenario == "repair-cap" or self.scenario == "repair-once" and context["repair_cycle"] == 0:
            content += "TODO_SYNTHETIC_DEFECT\n"
        if self.scenario == "ci-failure":
            content = "broken synthetic fixture\n"
        return {"changes": [{"path": path, "content": content}],
                "model_reported_cost_microusd": 0}


class SyntheticReviewer:
    identity = {"provider": "fixture-google", "model": "synthetic-gemini",
                "tool_version": VERSION, "synthetic": True}
    estimated_cost_microusd = 0

    def __init__(self, scenario):
        self.scenario = scenario

    def review(self, context):
        failed = any("TODO_SYNTHETIC_DEFECT" in row["content"] for row in context["changes"])
        return {"head_sha": context["base_sha"] if self.scenario == "stale-review" else context["head_sha"],
                "conclusion": "changes_requested" if failed else "passed",
                "findings": [{"id": "F1", "severity": "high", "path": context["allowed_paths"][0],
                              "line": 1, "code": "SYNTHETIC_DEFECT"}] if failed else [],
                "model_reported_cost_microusd": 0}


class SyntheticCI:
    def __init__(self, scenario):
        self.scenario = scenario

    def test(self, context):
        changes = context["changes"]
        checks = [len(changes) == 1 and changes[0]["path"] == context["allowed_paths"][0],
                  bool(changes) and changes[0]["content"].startswith(
                      f"Synthetic issue {context['issue_number']}, revision {context['repair_cycle']}\n")]
        return {"head_sha": context["base_sha"] if self.scenario == "stale-ci" else context["head_sha"],
                "conclusion": "passed" if all(checks) else "failed",
                "tests": len(checks), "secretless": True, "synthetic": True}
