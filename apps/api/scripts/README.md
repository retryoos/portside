# `apps/api/scripts/`

Track D utility scripts. None of these are imported by the runtime app — they
are dev / ops helpers.

| Script | What it does | Live API? |
| ------ | ------------ | --------- |
| `export_demo_fixture.py` | Dump `demo_voyage_fixture()` to `apps/web/public/demo-fixture.json` for the offline-demo fallback. | No — pure Python data, no SDK |
| `smoke_pipeline.sh` | Boot the API, POST the Rotterdam demo PDFs, poll until done, assert `demurrage_due_eur == 84375`. | **YES** — gated; do not run without explicit user authorisation |

Usage:

```bash
cd apps/api
uv run python scripts/export_demo_fixture.py
```

```bash
# Only after user authorizes Anthropic API spend
bash apps/api/scripts/smoke_pipeline.sh
```

The smoke script is GATED because each run makes ~3 Anthropic API calls
(Agent 1 extractor, Agent 2a classifier, plus any Agent 2 PR additions).
Cost is ~$0.05–0.10 per voyage at current Sonnet 4.6 pricing.
