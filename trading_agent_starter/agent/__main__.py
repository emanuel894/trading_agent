import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

from .replay import compare, load_bars, synthetic_bars


def main():
    parser = argparse.ArgumentParser(description="Foundation 0.1: offline baseline and read-only IBKR Paper diagnostic")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("demo", "research", "probe", "history"):
        p = sub.add_parser(name)
        p.add_argument("--output", default=None)
        if name == "research":
            p.add_argument("--csv", required=True)
        if name in ("probe", "history"):
            p.add_argument("--config", default="config/ibkr.local.json")
    args = parser.parse_args()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = Path(args.output or f"runs/{args.command}_{stamp}")
    try:
        if args.command in ("probe", "history"):
            from .ibkr_readonly import run
            result = run(args.config, str(output), history=args.command == "history")
            print(json.dumps(result, indent=2))
            return 0 if result["status"] == "READ_ONLY_CHECK_PASSED" else 1
        bars = synthetic_bars() if args.command == "demo" else load_bars(args.csv)
        if len(bars) < 130:
            raise ValueError("At least 130 completed daily bars are needed for this baseline demo.")
        result = compare(bars, synthetic=args.command == "demo")
        output.mkdir(parents=True, exist_ok=True)
        path = output / "research_report.json"
        path.write_text(json.dumps(result, indent=2, allow_nan=False), encoding="utf-8")
        print(result["warning"])
        print(f"Processed {len(bars)} daily bars; report: {path}")
        print("No broker orders were sent. No model was trained or promoted.")
        return 0
    except (ValueError, RuntimeError, OSError, KeyError) as exc:
        print(f"STOPPED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
