import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

from .replay import compare, load_bars, synthetic_bars


def main():
    parser = argparse.ArgumentParser(
        description="Foundation: offline research and read-only Paper market data"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("demo", "research", "probe", "history", "alpaca-probe", "alpaca-history"):
        p = sub.add_parser(name)
        p.add_argument("--output", default=None)
        if name == "research":
            p.add_argument("--csv", required=True)
        if name in ("probe", "history"):
            p.add_argument("--config", default="config/ibkr.local.json")
        if name == "alpaca-probe":
            p.add_argument(
                "--symbols",
                default="SPY,QQQ",
                help="Comma-separated symbols for a read-only latest-quote check",
            )
        if name == "alpaca-history":
            p.add_argument("--config", default="config/market_data.example.json")
            p.add_argument("--symbols", default=None, help="Override the configured symbol universe")
            p.add_argument("--start", required=True, help="Inclusive ISO timestamp with timezone")
            p.add_argument("--end", required=True, help="Exclusive ISO timestamp with timezone")
            p.add_argument("--as-of", default=None, help="Decision cutoff; defaults to current UTC time")
    args = parser.parse_args()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = Path(args.output or f"runs/{args.command}_{stamp}")
    try:
        if args.command == "alpaca-history":
            from .alpaca_history import run_history
            from .market_data import HistoryRequest

            config = json.loads(Path(args.config).read_text(encoding="utf-8"))
            if not isinstance(config, dict) or set(config) != {"symbols", "publication_delay_seconds"}:
                raise ValueError("Market-data config requires only symbols and publication_delay_seconds")
            symbols = args.symbols.split(",") if args.symbols is not None else config["symbols"]
            if not isinstance(symbols, list) or not all(isinstance(s, str) for s in symbols):
                raise ValueError("Market-data symbols must be a list of strings")
            request = HistoryRequest(
                tuple(symbols), datetime.fromisoformat(args.start), datetime.fromisoformat(args.end),
                datetime.fromisoformat(args.as_of) if args.as_of else datetime.now(timezone.utc),
                config["publication_delay_seconds"],
            )
            result = run_history(request, output)
            print(json.dumps(result["quality"], indent=2, allow_nan=False))
            print(f"Historical data snapshot: {output / 'manifest.json'}")
            print("No broker orders were sent or modified.")
            return 0 if result["quality"]["status"] == "DATA_CONTRACT_PASSED" else 1

        if args.command in ("probe", "history"):
            from .ibkr_readonly import run

            result = run(args.config, str(output), history=args.command == "history")
            print(json.dumps(result, indent=2))
            return 0 if result["status"] == "READ_ONLY_CHECK_PASSED" else 1

        if args.command == "alpaca-probe":
            from .alpaca_paper import run_from_env

            symbols = [item.strip() for item in args.symbols.split(",") if item.strip()]
            result = run_from_env(symbols)
            output.mkdir(parents=True, exist_ok=True)
            path = output / "alpaca_probe.json"
            path.write_text(json.dumps(result, indent=2, allow_nan=False), encoding="utf-8")
            print(json.dumps(result, indent=2))
            print(f"Read-only Alpaca Paper report: {path}")
            print("No broker orders were sent or modified.")
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
