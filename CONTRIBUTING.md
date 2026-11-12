# Contributing

This is an early-stage research project. Start with the credential-free
[offline quickstart](docs/OFFLINE_QUICKSTART.md). Original code licensing is still
pending; review the licensing section of [README.md](README.md) before contributing
code intended for redistribution. Do not submit third-party code without its
applicable permission and notices.

## Report a reproducible problem

Open a [GitHub issue](https://github.com/emanuel894/trading_agent/issues/new) with:

```text
OS and Python version:
Commit (git rev-parse HEAD):
Command and working directory:
Expected behavior:
Actual behavior and sanitized error:
Steps to reproduce with synthetic inputs:
```

Check existing issues first. Share only public or synthetic inputs. Exclude .env
files, tokens, account identifiers, private licensed data and environment dumps.
For a credential exposure, use GitHub's private vulnerability-reporting channel
if enabled, or contact the repository owner privately; never post the secret in
a public issue. Rotate an exposed credential with its issuer.

## Propose a change

Keep PRs small and explain the problem, changed behavior and verification.
Documentation fixes and failed-example reports are welcome. Reuse existing
adapters, evidence storage and engine integrations. Mark synthetic fixtures as
synthetic; preserve timing, source provenance and known limitations.

For code on `main`, run the two quickstart commands before requesting review.
Advanced branches have additional policies, dependencies and CI requirements:
read their AGENTS.md and canonical policy first. A green demo does not qualify a
real dataset or approve an experiment. Changes to registered hypotheses, samples,
holdouts, source admission, spending or broker activation require their own
explicit approval. Review and CI are required before integration.
