# Runtime: a roster of Minds, a scheduled tick, a spend cap, and a council on files

This is the public slice of the runtime the private instance runs every day, rebuilt clean for release. One stdlib-only file, ~300 lines, read it top to bottom. It does four things the minimal runtime does not: it runs a whole roster on a schedule, it routes between models with a daily spend cap, it keeps a ledger of every call, and it runs a council that reviews an answer before it counts.

Prerequisites: Python 3.9+ on macOS or Linux (on Windows the single-instance lock falls back to a lock file). For local models, [Ollama](https://ollama.com) running (`ollama pull llama3.2`, or `LIFEGRAPH_MODEL=gemma2:2b` for a small one). For paid models set `OPENAI_API_KEY` and/or `ANTHROPIC_API_KEY` and list them in `LIFEGRAPH_PROVIDERS`. `--dry-run` and the tests need no model at all.

```bash
cd examples/runtime
python3 test_runtime.py                                             # 7 tests, no model, ~0.1 s
python3 lifegraph_runtime.py tick --vault ../vault --dry-run        # who would run this half of the day
python3 lifegraph_runtime.py tick --vault ../vault                  # run them; each writes minds/<id>/<date>.md
python3 lifegraph_runtime.py council --vault ../vault --task "Is the Alex Rivers relationship worth a follow-up?"
python3 lifegraph_runtime.py status --vault ../vault                # spend today, last tick, chain verification
```

## What happens on a tick

`roster.json` lists the Minds: an id, a name, a role in plain words, and a cadence (`am`, `pm`, or both). A tick takes the current half of the day, skips any Mind not scheduled for it, skips any Mind that already journaled this half (so a cron that fires every hour is safe), holds a single-instance lock (a second tick exits at once), and runs the rest. Each Mind gets the same thing: the newest Markdown and JSONL in the vault, capped, and its role. It writes 120-200 words in its own voice to `minds/<id>/<date>.md`, and the write is recorded as a hash-chained line in `minds/journal_timeline.jsonl`. One Mind failing never stops the others; failures land in `_runtime/dispatch_status.json`.

Schedule it with whatever you already have. Two lines of cron cover the private instance's pattern:

```
0 6  * * * cd /path/to/examples/runtime && python3 lifegraph_runtime.py tick --vault ../vault --half am >> tick.log 2>&1
0 18 * * * cd /path/to/examples/runtime && python3 lifegraph_runtime.py tick --vault ../vault --half pm >> tick.log 2>&1
```

## The router and the cap

`LIFEGRAPH_PROVIDERS="ollama,openai,anthropic"` is the order tried. A provider that errors falls through to the next. Every call is written to `_runtime/spend.jsonl` (hash-chained) with a list-price estimate; once today's total reaches `LIFEGRAPH_DAILY_CAP_USD` (default $1.00) paid providers are refused and the tick reports it. Ollama is never capped. The estimate uses list prices baked into `PRICE`; it is a brake, not an invoice.

## The council

`council --task "..."` writes `council/TASK-<id>/` with, in order: `TASK.md`, `DRAFT.md` (the drafter's answer, citing the record), `reviews/ADVERSARIAL.json` (tries to prove the draft wrong, JSON verdict), `reviews/GROUNDING.json` (checks every claim against the record), `DISPUTES.json` (any verdict that is not sound/grounded), `DECISION.md` (the chair, told that evidence outranks it: it must defer to a reviewer who cites the record and must hold against one who does not), and `STATUS.json`. The two reviewers never see each other: each is a separate call that receives only the task, the draft, and the record (see `council()`; nothing from one review is passed to the other). The decision is chained to the timeline. This is the same protocol the private instance runs nightly on the day's reconstruction.

## What is still private

The web app, the 35-Mind roster and their voices, the Letta memory layer, the deep-profile builders, the ingest pipelines (texts, calendar, photos, location, wearables), the nightly reconstruction of the day, and the correction engine. Each is on the [roadmap](../../docs/ROADMAP.md) with the reason it is not out yet.
