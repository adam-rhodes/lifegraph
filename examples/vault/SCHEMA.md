# Data shapes shipped in this repo

Three file kinds carry the record. Each is plain text you can read in any editor. The private runtime writes exactly these shapes; the samples beside this file are real instances.

## 1. Timeline entry (`*.jsonl`, one JSON object per line, hash-chained)

Written and verified by `examples/hashchain/lifegraph_hashchain.py`. Every line is a dict with your own fields plus three the chain adds:

| field | type | who sets it | meaning |
|---|---|---|---|
| any keys you pass (`entity`, `event`, `text`, `source`, `file`, `model`, ...) | JSON | you | the event. `entity` is a path-style id (`person/alex-rivers`, `mind/finance`); `event` is a short verb (`first_contact`, `note`, `journal`). |
| `ts` | string, ISO 8601 with offset | `append()` unless you pass one | when the entry was written |
| `prev_hash` | 64 hex chars | `append()` | `entry_hash` of the previous line; `0`*64 for the first line |
| `entry_hash` | 64 hex chars | `append()` | `sha256(prev_hash + "\n" + canonical(entry-without-entry_hash))`, canonical = `json.dumps(sorted keys, no spaces)` |

Rules: append only; never rewrite a line. `verify()` walks the file from the top and reports the first line whose `prev_hash` or `entry_hash` does not match. Sample: `sample_timeline.jsonl`, `minds/journal_timeline.jsonl` after you run the minimal runtime.

## 2. Mind journal (`minds/<mind>/<YYYY-MM-DD>.md`, Markdown)

One file per Mind per day, appended if the Mind writes twice. Shape:

```
# <Mind name> — <YYYY-MM-DD> [(am|pm)]

**Speaking: <Mind name> (<one-line role>).**   # optional in the minimal runtime; model line instead:
model: <provider>/<model>

<first-person prose, 120-200 words, cites only what is in the record, ends with one question>
```

No front matter is required. The runtime records each write as a timeline entry (`entity: mind/<mind>`, `event: journal`, `file: minds/<mind>/<date>.md`). Sample: `sample_mind_journal.md`.

## 3. Graph node (`<type>/<slug>.md`, Markdown with YAML front matter)

One file per entity (person, project, topic, program). Front matter carries the structured part; the body is prose.

| key | type | required | meaning |
|---|---|---|---|
| `id` | `<type>/<slug>` | yes | stable id; matches the `entity` field used in timeline entries |
| `type` | `person` \| `project` \| `topic` \| `program` \| `mind` | yes | |
| `name` | string | yes | display name |
| `aliases` | list of strings | no | other names the record uses |
| `first_flame` | date | people only | the true moment of connection, set by the person, never moved by backfilled data (bitemporal: valid time, not record time) |
| `disposition` | string | no | free text (`warm`, `cooling`, ...) |
| `cares_about` | list of strings | no | |
| `connections` | list of `{to: <id>, kind: <verb>}` | no | edges; `kind` is free text (`met_at`, `shares_value`, `reports_to`) |

Everything after the front matter is the node's prose and is what a Mind reads. Sample: `sample_graph_node.md`.

## What is deliberately not here

No database, no vector index, no binary format. If you can `cat` it, it is the record. Schemas as JSON Schema / Pydantic are on the roadmap once the private runtime's shapes stop moving.
