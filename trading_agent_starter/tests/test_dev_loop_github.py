"""Execute trusted workflow guards with synthetic Octokit data; never network."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[2]
BASE = "a" * 40


@unittest.skipUnless(shutil.which("node"), "Node is needed to execute the GitHub action's guard script")
class GitHubGuardTests(unittest.TestCase):
    def run_guard(self, *, permission="write", remote_sha=BASE, resume=False, run_changes=None):
        source = (ROOT/".github/workflows/autonomous-dev-dry-run.yml").read_text()
        step = re.search(r'      - name: Validate trusted dispatch.*?(?=\n      - |\Z)', source, re.S)
        self.assertIsNotNone(step, "Trusted dispatch guard must exist")
        marker = "          script: |\n"
        self.assertTrue(marker in step[0], "Trusted guard should use the maintained github-script action")
        script = textwrap.dedent(step[0].split(marker, 1)[1])
        run = {"head_sha": BASE, "status": "completed", "event": "workflow_dispatch",
               "path": ".github/workflows/autonomous-dev-dry-run.yml",
               "head_branch": "feat/alpaca-paper-foundation", "run_attempt": 2}
        run.update(run_changes or {})
        fixtures = {"permission": permission, "remote_sha": remote_sha, "run": run}
        harness = """
        const fixtures = JSON.parse(process.env.FIXTURES);
        const outputs = {}, calls = [];
        const reply = (name, value) => async (args) => { calls.push({name,args}); return {data:value}; };
        const github = {rest:{
          git:{getRef:reply('getRef',{object:{sha:fixtures.remote_sha}})},
          repos:{getCollaboratorPermissionLevel:reply('permission',{permission:fixtures.permission})},
          issues:{get:reply('issue',{number:3,state:'open',title:'Synthetic',body:'Untrusted input',updated_at:'2026-10-17'})},
          actions:{getWorkflowRun:reply('run',fixtures.run)}
        }};
        const context = {repo:{owner:'emanuel894',repo:'trading_agent'},actor:'maintainer'};
        const core = {setOutput:(name,value)=>{outputs[name]=value;}};
        const AsyncFunction = Object.getPrototypeOf(async function(){}).constructor;
        (async () => {
          try { await new AsyncFunction('github','context','core','require',process.env.SCRIPT)(github,context,core,require);
                console.log(JSON.stringify({outputs,calls,error:null})); }
          catch(error) { console.log(JSON.stringify({outputs,calls,error:error.message})); }
        })();
        """
        env = {"SCRIPT": script, "FIXTURES": json.dumps(fixtures),
               "REPOSITORY": "emanuel894/trading_agent", "REQUESTED_BASE": BASE,
               "ISSUE_NUMBER": "3", "RESUME_RUN": "123" if resume else "", "MAX_STEPS": "50",
               "GITHUB_REF": "refs/heads/feat/alpaca-paper-foundation", "GITHUB_SHA": BASE,
               "WORKFLOW_SHA": BASE}
        # No inherited provider, broker or GitHub token is passed into Node.
        if os.name == "nt":
            env["SystemRoot"] = os.environ.get("SystemRoot", r"C:\Windows")
        result = subprocess.run([shutil.which("node"), "-e", harness], env=env,
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_verified_issue_is_hashed_without_publishing_its_text(self):
        result = self.run_guard()
        self.assertIsNone(result["error"])
        self.assertRegex(result["outputs"]["issue_hash"], r'^[0-9a-f]{64}$')
        self.assertNotIn("Untrusted input", json.dumps(result["outputs"]))

    def test_stale_base_fails_before_issue_is_fetched(self):
        result = self.run_guard(remote_sha="b"*40)
        self.assertEqual(result["error"], "STALE_BASE_SHA")
        self.assertNotIn("issue", [c["name"] for c in result["calls"]])

    def test_read_only_actor_cannot_dispatch(self):
        self.assertEqual(self.run_guard(permission="read")["error"], "MAINTAINER_REQUIRED")

    def test_resume_source_must_match_sha_branch_workflow_and_event(self):
        for changes in [{"head_sha": "c"*40}, {"head_branch": "untrusted"},
                        {"path": "evil.yml"}, {"event": "pull_request"}, {"status": "in_progress"}]:
            with self.subTest(changes=changes):
                self.assertEqual(self.run_guard(resume=True, run_changes=changes)["error"],
                                 "UNTRUSTED_RESUME_RUN")

    def test_verified_resume_selects_exact_artifact_for_official_downloader(self):
        result = self.run_guard(resume=True)
        self.assertIsNone(result["error"])
        self.assertEqual(result["outputs"]["artifact_name"], "autonomous-dev-issue-3-123-2")
