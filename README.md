# trading_agent

Python research software for testing whether AI-derived information adds value
beyond deterministic numerical and text controls. The project emphasizes source
provenance, timing, reproducibility, explicit uncertainty and retaining failures.

**Early-stage research. No demonstrated alpha, production trading service or
claimed downstream adoption.** The default branch contains the original offline
starter. Advanced work is on development branches and in reviewed or draft PRs;
it is not all integrated into `main`.

## Try the existing offline example

Use Python 3.13. The starter uses only the Python standard library: no package
installation, broker account, API key, model subscription or market-data download
is needed for these commands.

```sh
git clone https://github.com/emanuel894/trading_agent.git
cd trading_agent/trading_agent_starter
python -m unittest discover -s tests -v
python -m agent demo --output runs/first-demo
```

On Windows, use `py -3.13` instead of `python` if needed. On macOS/Linux, use
`python3` if that is your interpreter command. A virtual environment is optional
for this standard-library-only starter.

Expected: **21 starter tests pass**, then the demo reports **300 synthetic daily
bars**, writes `runs/first-demo/research_report.json`, and states that no broker
orders were sent and no model was trained or promoted. See the
[walkthrough and limitations](docs/OFFLINE_QUICKSTART.md). The generated report is
an artificial-data integration artifact, not an investment result.

## What is available where?

| Location | Scope |
| --- | --- |
| This default branch | Synthetic daily-bar replay, risk-check primitives, a persistent intent ledger, and optional read-only IBKR diagnostics. The quickstart invokes only the offline path. |
| [Integration branch](https://github.com/emanuel894/trading_agent/tree/feat/alpaca-paper-foundation) | Evidence storage, source/time contracts, synthetic research integration and bounded LEAN qualification work. Has its own policy and dependencies. |
| [PR #60](https://github.com/emanuel894/trading_agent/pull/60) | Draft synthetic hypothesis → independent critique → audited decision workflow. Not a validated predictive result. |
| [PR #61](https://github.com/emanuel894/trading_agent/pull/61) | Draft private Windows source-acquisition controls and interrupted-setup recovery. Owner-machine preparation and separate acquisition approval are required. |

For the advanced work, start with the integration branch's
[canonical policy](https://github.com/emanuel894/trading_agent/blob/feat/alpaca-paper-foundation/AI_PROJECT_POLICY.md)
and [research architecture](https://github.com/emanuel894/trading_agent/blob/feat/alpaca-paper-foundation/trading_agent_starter/ARCHITECTURE_DECISION_001.md).
Its scientific question permits a negative answer: remove the AI component if it
does not establish incremental value over cheaper controls after costs.

## Help improve it

Try the offline example and report whether the documented steps work on your
machine. Reproducible failures, documentation corrections and careful review are
useful contributions. See [CONTRIBUTING.md](CONTRIBUTING.md) for a report template.
No stars, downloads or endorsements are requested as a substitute for real use.

## Licensing and data

A project-wide open-source license has not yet been activated. The
[MIT license proposal](docs/licensing/MIT-LICENSE.proposed.txt) is for owner review
and is **not a license grant**. Public visibility alone does not grant a general
right to redistribute this code. Dependency licenses and vendor market-data
rights remain separate from any future project license.

Do not upload credentials, broker/account details or licensed raw data in issues,
PRs or generated reports. Keep real-data acquisition and broker diagnostics out
of the offline quickstart. Existing [Hebrew documentation](trading_agent_starter/README_HE.md)
is also available; its connection instructions are outside this quickstart.
