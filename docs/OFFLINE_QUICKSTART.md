# Offline starter walkthrough

This example runs the code already on `main`; it does not install or integrate
the advanced research branches. It is useful for checking the replay/risk/ledger
foundation and for reporting reproducible setup problems.

## Run

From a fresh clone, with Python 3.13 on your PATH:

```sh
cd trading_agent_starter
python -m unittest discover -s tests -v
python -m agent demo --output runs/first-demo
```

Windows alternative: replace `python` with `py -3.13`. No `pip install` or local
configuration file is required. Do not run `probe` or `history` for this example:
those are separate broker diagnostics with additional setup.

## What success looks like

The starter test suite reports 21 tests and `OK`. The demo prints a synthetic-data
warning, `Processed 300 daily bars; report: runs/first-demo/research_report.json`
(path separators may differ), and:

```text
No broker orders were sent. No model was trained or promoted.
```

The report contains the starter's artificial replay comparisons. Synthetic bars
are generated with a fixed seed; their weekday calendar deliberately ignores real
exchange holidays. The replay uses simplified next-bar fills and illustrative
costs. These outputs establish neither real execution quality nor profitability.
Do not tune parameters to improve this demonstration's simulated performance.

The output is local and ignored by Git. Repeating the explicit output command
overwrites that demo report; use a different output directory to preserve a run.
Never point `--output` at a directory holding private evidence or credentials.

## Share useful feedback

Report your OS, `python --version` (or `py -3.13 --version`), `git rev-parse HEAD`,
the exact command and a sanitized failure message. Please say whether all tests
passed and whether the expected output file was created. You do not need to share
replay returns, account information, an environment dump or any real dataset.

If `agent` cannot be imported, check that the working directory is
`trading_agent_starter`. If the interpreter command is missing, install Python
through its official distribution and repeat the commands. An SDK/import or
connection error from `probe`/`history` belongs to the separate broker setup,
not the synthetic demo.
