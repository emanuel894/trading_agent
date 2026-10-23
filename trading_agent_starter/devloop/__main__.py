"""Run or resume a fixture-only controller from an explicitly trusted commit."""
import argparse
import json
from pathlib import Path
import sys

from .control import BoundaryError, Controller, load_trust
from .fixtures import SCENARIOS, SyntheticCI, SyntheticImplementer, SyntheticReviewer


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--issue-number", type=int, required=True)
    parser.add_argument("--scenario", choices=SCENARIOS, default="happy")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--task-id", default="local")
    parser.add_argument("--issue-snapshot-hash")
    parser.add_argument("--max-steps", type=int, default=50)
    args = parser.parse_args(argv)
    try:
        trust = load_trust(args.root, args.base_sha)
        controller = Controller(root=args.root, directory=args.output, trust=trust,
                                issue_number=args.issue_number, scenario=args.scenario,
                                implementer=SyntheticImplementer(args.scenario),
                                reviewer=SyntheticReviewer(args.scenario), ci=SyntheticCI(args.scenario),
                                run_id=args.task_id, issue_snapshot_hash=args.issue_snapshot_hash)
        record = controller.run(args.max_steps)
        summary = {"mode": "synthetic", "state": record["snapshot"]["state"],
                   "reason": record["snapshot"]["reason"],
                   "repair_cycles": record["snapshot"]["repair_cycles"],
                   "provider_calls": record["snapshot"]["provider_calls"],
                   "real_pr_created": False, "real_model_review": False,
                   "stop_state": "AUTOMATION_DRY_RUN_READY" if record["snapshot"]["state"] == "READY_FOR_HUMAN"
                                 else "SECURITY_BOUNDARY_BLOCKER"}
        (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps(summary, sort_keys=True))
        return 0 if record["snapshot"]["state"] == "READY_FOR_HUMAN" else 2
    except BoundaryError as exc:
        print(json.dumps({"state": "BLOCKED", "reason": str(exc),
                          "stop_state": "SECURITY_BOUNDARY_BLOCKER"}), file=sys.stderr)
        return 2
    except Exception:
        print('{"state":"BLOCKED","reason":"CONTROL_FAILED","stop_state":"SECURITY_BOUNDARY_BLOCKER"}',
              file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
