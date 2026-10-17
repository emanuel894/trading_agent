"""Offline control acceptance. No model, broker or market-data credentials."""
from copy import deepcopy
from contextlib import redirect_stdout, redirect_stderr
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from devloop.control import (BoundaryError, Controller, EDGES, TERMINAL,
                             exclusive_run, load_trust, safe_path, strict_json)
from devloop.fixtures import SyntheticCI, SyntheticImplementer, SyntheticReviewer


REPOSITORY = Path(__file__).resolve().parents[2]
BASE = "a" * 40


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.trust = {"base_sha": BASE, "policy_hash": "b" * 64, "control_hash": "c" * 64}

    def controller(self, scenario="happy", **kwargs):
        defaults = dict(root=self.root, directory=self.root / "state", trust=self.trust,
                        issue_number=3, scenario=scenario,
                        implementer=SyntheticImplementer(scenario),
                        reviewer=SyntheticReviewer(scenario), ci=SyntheticCI(scenario))
        defaults.update(kwargs)
        return Controller(**defaults)

    def test_happy_complete_and_no_real_side_effects(self):
        with patch("urllib.request.urlopen", side_effect=AssertionError("network forbidden")), \
             patch("subprocess.run", side_effect=AssertionError("execution forbidden")):
            result = self.controller().run()
        states = [e["snapshot"]["state"] for e in result["events"]]
        self.assertEqual([s for i, s in enumerate(states) if i == 0 or s != states[i-1]],
                         ["QUEUED", "IMPLEMENTING", "TESTING", "REVIEWING", "READY_FOR_HUMAN"])
        self.assertEqual(result["snapshot"]["provider_calls"], 2)
        self.assertEqual(result["snapshot"]["estimated_cost_microusd"], 0)
        self.assertNotIn("pull_request", result["task"])
        self.assertNotIn("branch", result["task"])
        self.assertFalse((self.root / "automation").exists())

    def test_one_repair_includes_second_test_and_fresh_review(self):
        result = self.controller("repair-once").run()
        self.assertEqual(result["snapshot"]["state"], "READY_FOR_HUMAN")
        self.assertEqual(result["snapshot"]["repair_cycles"], 1)
        self.assertEqual(result["snapshot"]["provider_calls"], 4)
        heads = {e["snapshot"]["head_sha"] for e in result["events"] if e["snapshot"]["state"] == "TESTING"}
        self.assertEqual(len(heads), 2)
        self.assertEqual(result["snapshot"]["tests"]["head_sha"], result["snapshot"]["head_sha"])

    def test_repair_cap_at_two_then_block_no_automatic_retry(self):
        result = self.controller("repair-cap").run()
        self.assertEqual(result["snapshot"]["state"], "BLOCKED")
        self.assertEqual(result["snapshot"]["reason"], "REPAIR_CAP_REACHED")
        self.assertEqual(result["snapshot"]["repair_cycles"], 2)
        self.assertEqual(result["snapshot"]["provider_calls"], 6)
        resumed = self.controller("repair-cap").run()
        self.assertEqual(result, resumed)

    def test_state_can_resume_without_chat_and_preserves_counts(self):
        first = self.controller("repair-once").run(max_steps=3)
        self.assertEqual(first["snapshot"]["state"], "REVIEWING")
        resumed = self.controller("repair-once").run()
        self.assertEqual(resumed["snapshot"]["state"], "READY_FOR_HUMAN")
        self.assertEqual(resumed["snapshot"]["repair_cycles"], 1)
        self.assertEqual(resumed["snapshot"]["provider_calls"], 4)
        self.assertEqual(resumed["events"][:len(first["events"])], first["events"])

    def test_resume_rejects_issue_base_policy_scenario_and_run_mismatches(self):
        self.controller().run(max_steps=1)
        for changes in [{"issue_number": 4}, {"scenario": "repair-once"}, {"run_id": "different"},
                        {"trust": {**self.trust, "base_sha": "d"*40}},
                        {"trust": {**self.trust, "policy_hash": "e"*64}},
                        {"trust": {**self.trust, "control_hash": "f"*64}}]:
            with self.subTest(changes=changes), self.assertRaisesRegex(BoundaryError, "RESUME_CONTEXT_MISMATCH"):
                self.controller(**changes).run()

    def test_snapshot_or_journal_tamper_rejected(self):
        original = self.controller().run(max_steps=1)
        for modify in [lambda r: r["snapshot"].update(repair_cycles=0, state="READY_FOR_HUMAN"),
                       lambda r: r["events"][0].update(previous_hash="forged")]:
            record = deepcopy(original)
            modify(record)
            (self.root / "state/state.json").write_text(json.dumps(record))
            with self.assertRaises(BoundaryError):
                self.controller().run()

    def test_stale_ci_and_review_block(self):
        for scenario in ["stale-ci", "stale-review"]:
            with self.subTest(scenario=scenario):
                result = self.controller(scenario, directory=self.root/scenario).run()
                self.assertEqual(result["snapshot"]["state"], "BLOCKED")
                self.assertTrue(result["snapshot"]["reason"].startswith("STALE_OR_INVALID_"))

    def test_provider_failure_redacts_exception(self):
        result = self.controller("provider-failure").run()
        self.assertEqual(result["snapshot"]["reason"], "PROVIDER_FAILED")
        self.assertNotIn("Untrusted exception", json.dumps(result))
        self.assertEqual(result["snapshot"]["provider_calls"], 1)

    def test_budget_pause_happens_before_a_provider_call(self):
        provider = SyntheticImplementer("budget")
        with patch.object(provider, "implement", side_effect=AssertionError("must not call")):
            result = self.controller("budget", implementer=provider).run()
        self.assertEqual(result["snapshot"]["state"], "PAUSED_BUDGET")
        self.assertEqual(result["snapshot"]["provider_calls"], 0)

    def test_path_escape_or_control_file_never_admitted(self):
        for scenario in ["path-escape", "control-path"]:
            with self.subTest(scenario=scenario):
                result = self.controller(scenario, directory=self.root/scenario).run()
                self.assertEqual(result["snapshot"]["state"], "BLOCKED")
                self.assertEqual(result["snapshot"]["changes"], [])

    def test_failed_ci_cannot_be_marked_ready(self):
        result = self.controller("ci-failure").run()
        self.assertEqual(result["snapshot"]["reason"], "REPAIR_CAP_REACHED")
        self.assertEqual(result["snapshot"]["repair_cycles"], 2)

    def test_zero_tests_secreted_or_missing_ci_fail_closed(self):
        for changes in [{"tests": 0}, {"secretless": False}, {"conclusion": "pending"}]:
            ci = SyntheticCI("happy")
            original = ci.test
            ci.test = lambda context, original=original, changes=changes: {**original(context), **changes}
            with self.subTest(changes=changes):
                result = self.controller(ci=ci, directory=self.root/str(len(list(self.root.iterdir())))).run()
                self.assertEqual(result["snapshot"]["state"], "BLOCKED")

    def test_provider_context_has_no_environment_or_transcript(self):
        provider = SyntheticImplementer("happy")
        original = provider.implement
        def checked(context):
            self.assertEqual(set(context), {"issue_number", "base_sha", "head_sha", "policy_hash",
                                           "policy_reference", "allowed_paths", "repair_cycle", "changes"})
            self.assertNotIn("secret-canary", json.dumps(context))
            return original(context)
        provider.implement = checked
        with patch.dict(os.environ, {"FAKE_BROKER_SECRET": "secret-canary"}):
            result = self.controller(implementer=provider).run()
        self.assertNotIn("secret-canary", json.dumps(result))

    def test_reviewer_gets_no_implementation_transcript_or_environment(self):
        reviewer = SyntheticReviewer("happy")
        original = reviewer.review
        def checked(context):
            self.assertNotIn("environment", context)
            self.assertNotIn("transcript", context)
            self.assertNotIn("secret-canary", json.dumps(context))
            self.assertEqual(context["policy_reference"], "AI_PROJECT_POLICY.md")
            return original(context)
        reviewer.review = checked
        with patch.dict(os.environ, {"FAKE_MODEL_SECRET": "secret-canary"}):
            result = self.controller(reviewer=reviewer).run()
        self.assertEqual(result["snapshot"]["state"], "READY_FOR_HUMAN")

    def test_malformed_provider_result_and_nonzero_or_boolean_cost_block(self):
        for result in [{"unexpected": "field"}, {"changes": [], "model_reported_cost_microusd": 1},
                       {"changes": [], "model_reported_cost_microusd": False}]:
            provider = SyntheticImplementer("happy")
            provider.implement = lambda _, result=result: result
            with self.subTest(result=result):
                record = self.controller(implementer=provider,
                                         directory=self.root/str(len(list(self.root.iterdir())))).run()
                self.assertEqual(record["snapshot"]["state"], "BLOCKED")

    def test_ci_outage_and_incomplete_review_are_not_passes(self):
        ci = SyntheticCI("happy")
        ci.test = lambda _: (_ for _ in ()).throw(RuntimeError("private error"))
        record = self.controller(ci=ci).run()
        self.assertEqual(record["snapshot"]["reason"], "CI_UNAVAILABLE")
        reviewer = SyntheticReviewer("happy")
        original = reviewer.review
        reviewer.review = lambda context: {**original(context), "conclusion": "pending"}
        record = self.controller(reviewer=reviewer, directory=self.root/"pending").run()
        self.assertEqual(record["snapshot"]["reason"], "REVIEW_INCOMPLETE")

    def test_changed_issue_snapshot_cannot_resume_an_earlier_task(self):
        self.controller().run(max_steps=1)
        with self.assertRaisesRegex(BoundaryError, "RESUME_CONTEXT_MISMATCH"):
            self.controller(issue_snapshot_hash="f"*64).run()

    def test_real_provider_activation_and_same_role_rejected(self):
        provider = SyntheticReviewer("happy")
        provider.identity = {**provider.identity, "synthetic": False}
        with self.assertRaisesRegex(BoundaryError, "ACTIVATION_DISABLED"):
            self.controller(reviewer=provider)
        provider.identity = deepcopy(SyntheticImplementer.identity)
        with self.assertRaisesRegex(BoundaryError, "NOT_INDEPENDENT_ROLE"):
            self.controller(reviewer=provider)

    def test_concurrent_controller_cannot_enter_same_task(self):
        with exclusive_run(self.root / "state"):
            with self.assertRaisesRegex(BoundaryError, "TASK_ALREADY_RUNNING"):
                self.controller().run()

    def test_every_terminal_state_has_no_outgoing_transitions(self):
        self.assertTrue(all(state not in EDGES for state in TERMINAL))

    def test_path_variants_and_nested_controls_rejected(self):
        allowed = ["automation/synthetic/issue-3.txt"]
        for value in ["../escape", "/absolute", "C:/x", "C:\\x", "a/../b", "a//b", "a%2fb",
                      "a/AGENTS.override.md", "a/.github/x", "a/.env", "a/mcp.json", "a/CLAUDE.md"]:
            with self.subTest(value=value), self.assertRaises(BoundaryError):
                safe_path(value, self.root, allowed)

    def test_symlink_in_candidate_path_rejected(self):
        target = self.root/"automation/synthetic"
        target.mkdir(parents=True)
        outside = self.root/"other"
        outside.write_text("preserve")
        try:
            (target/"issue-3.txt").symlink_to(outside)
        except OSError:
            self.skipTest("Platform does not permit symlink creation")
        with self.assertRaisesRegex(BoundaryError, "SYMLINK_REJECTED"):
            safe_path("automation/synthetic/issue-3.txt", self.root, ["automation/synthetic/issue-3.txt"])
        self.assertEqual(outside.read_text(), "preserve")

    def test_strict_json_rejects_ambiguous_or_nonfinite_state(self):
        for raw in ['{"a":1,"a":2}', '{"a":NaN}', '{']:
            with self.subTest(raw=raw), self.assertRaises(BoundaryError):
                strict_json(raw)


class TrustedBaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git("init", "-q")
        self.git("config", "core.autocrlf", "false")
        for name in ("AI_PROJECT_POLICY.md", "AGENTS.md", "CLOUD_AUTOMATION_PLAN_20261017.md", "automation/control.json"):
            p = self.root/name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes((REPOSITORY/name).read_bytes())
        self.git("add", ".")
        self.git("-c", "user.name=Synthetic test", "-c", "user.email=synthetic@example.invalid",
                 "-c", f"core.hooksPath={self.root/'no-hooks'}", "commit", "-qm", "synthetic base")
        self.base = self.git("rev-parse", "HEAD").strip()

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.root), *args], text=True, stderr=subprocess.DEVNULL)

    def test_exact_git_objects_and_working_tree_are_checked(self):
        trust = load_trust(self.root, self.base)
        self.assertEqual(trust["base_sha"], self.base)
        (self.root/"AGENTS.md").write_text("PR-controlled override")
        with self.assertRaisesRegex(BoundaryError, "UNTRUSTED_CONTROL_CHECKOUT"):
            load_trust(self.root, self.base)

    def test_stale_or_malformed_base_rejected(self):
        for base in ["a"*40, "HEAD", "a"*39, "a"*40+":AGENTS.md"]:
            with self.subTest(base=base), self.assertRaises(BoundaryError):
                load_trust(self.root, base)

    def test_nested_candidate_instructions_are_not_discovered(self):
        nested = self.root/"candidate/.claude/hooks.json"
        nested.parent.mkdir(parents=True)
        nested.write_text('{"command":"never execute"}')
        (self.root/"candidate/AGENTS.md").write_text("malicious nested instructions")
        self.assertEqual(load_trust(self.root, self.base)["base_sha"], self.base)

    def test_cli_happy_and_partial_resume_without_external_calls(self):
        from devloop.__main__ import main
        args = ["--root", str(self.root), "--base-sha", self.base, "--issue-number", "3",
                "--output", str(self.root/"output"), "--scenario", "repair-once"]
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()), \
             patch("urllib.request.urlopen", side_effect=AssertionError("network forbidden")):
            self.assertEqual(main(args+["--max-steps", "3"]), 2)
            self.assertEqual(main(args), 0)
        summary = json.loads((self.root/"output/summary.json").read_text())
        self.assertEqual(summary["stop_state"], "AUTOMATION_DRY_RUN_READY")
        self.assertFalse(summary["real_pr_created"])
        self.assertFalse(summary["real_model_review"])

    def test_increased_cap_or_real_activation_config_is_not_supported(self):
        path = self.root/"automation/control.json"
        config = json.loads(path.read_text())
        config["max_repair_cycles"] = 3
        config["provider_activation_enabled"] = True
        path.write_text(json.dumps(config))
        self.git("add", ".")
        self.git("-c", "user.name=Synthetic test", "-c", "user.email=synthetic@example.invalid",
                 "-c", f"core.hooksPath={self.root/'no-hooks'}", "commit", "-qm", "unsafe config fixture")
        with self.assertRaisesRegex(BoundaryError, "UNSUPPORTED_CONTROL_CONFIGURATION"):
            load_trust(self.root, self.git("rev-parse", "HEAD").strip())


class WorkflowBoundaryTests(unittest.TestCase):
    def test_generic_transport_and_artifact_restore_use_maintained_actions(self):
        text = (REPOSITORY/".github/workflows/autonomous-dev-dry-run.yml").read_text()
        self.assertTrue("uses: actions/github-script@" in text,
                        "GitHub REST transport must use the maintained Octokit action")
        self.assertTrue("uses: actions/download-artifact@" in text,
                        "Cross-run artifact download must use the maintained action")
        self.assertFalse("'gh', 'api'" in text or "'gh', 'run', 'download'" in text,
                         "Do not keep a second custom API/download client")

    def test_existing_ci_preserves_secretless_foundation_matrix(self):
        text = (REPOSITORY/".github/workflows/tests.yml").read_text()
        self.assertIn("os: [ubuntu-latest, windows-latest]", text)
        self.assertIn("python-version: '3.13'", text)
        self.assertIn("python -m unittest discover -s tests -v", text)
        self.assertIn("pull_request:", text)
        self.assertIn("contents: read", text)
        self.assertNotIn("secrets.", text)
        self.assertNotIn("write", text)

    def test_control_is_manual_read_only_pinned_and_serial(self):
        text = (REPOSITORY/".github/workflows/autonomous-dev-dry-run.yml").read_text()
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("cancel-in-progress: false", text)
        self.assertIn("persist-credentials: false", text)
        self.assertIn("WORKFLOW_SHA", text)
        self.assertIn("STALE_BASE_SHA", text)
        self.assertIn("MAINTAINER_REQUIRED", text)
        self.assertIn("UNTRUSTED_RESUME_RUN", text)
        self.assertNotIn("secrets.", text)
        self.assertNotIn("pull_request_target", text)
        self.assertNotIn("contents: write", text)
        self.assertNotIn("pull-requests: write", text)
        self.assertNotIn("gh pr merge", text)
        import re
        actions = re.findall(r'uses:\s+([^\s]+)', text)
        self.assertGreaterEqual(len(actions), 3)
        self.assertTrue(all(re.fullmatch(r'actions/[a-z-]+@[0-9a-f]{40}', a) for a in actions))
