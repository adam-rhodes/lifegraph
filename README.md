# LifeGraph

**A local-first, self-hosted personal operating system.** It stores your life as plain Markdown and JSONL files on hardware you own, and runs a team of scheduled AI agents that read those files instead of a black-box vector database. It already runs daily for its first user across calendar, journal, people, places, health, and finances, on an append-only, tamper-evident record you can open in a text editor.

Most tools give you a calendar here, notes there, a chatbot somewhere else. None see the whole picture, and none actually remember you. LifeGraph is the opposite: one system that treats your whole life as connected, keeps a durable record you control, and runs specialists ("Minds") that work across every domain and write their reasoning to disk.

Three commitments define it:

- **You own the data.** Plain files on your hardware. No lock-in, readable in any editor a decade from now.
- **The record is the product.** Append-only, timestamped, uniquely identified, and hash-chained so tampering is detectable. The memory is an audit trail, not a vector-DB black box.
- **Intelligence is a team, not a chatbot.** Named specialists collaborate and journal in the open, routed through a model-agnostic broker so no vendor is load-bearing. Your data stays on your disk; only the specific text a task needs is sent to a model, and the broker can point at local models instead of commercial APIs.

> **Status: early and honest.** A working system running daily for its first user, not a finished product. **This repository ships the concept, the data schemas, and the runnable hash-chain core.** The full runtime (the FastAPI server, the Minds, the broker, the web app) runs on the author's private instance and is being sanitized for public release. This README marks what works versus what is still aspirational, and the [roadmap](docs/ROADMAP.md) tracks the gap. We are building in the open on purpose.

---

## Try the core guarantee in 30 seconds

The core journaling primitive is real, tested code you can run right now. It is a hash-chained JSONL log that detects any in-place edit, deletion, or reordering of past entries in a stream:

```bash
git clone https://github.com/adam-rhodes/lifegraph && cd lifegraph/examples/hashchain
python3 test_hashchain.py                                   # tamper / delete / reorder detection
python3 lifegraph_hashchain.py verify ../vault/sample_timeline.jsonl   # verify a shipped timeline
```

You should see the tests pass and the shipped timeline verify:

```
ALL PASS: clean-chain, genesis, linkage, tamper-detect, delete-detect, reorder-detect
OK {'entries': 3, 'head': '...'}
```

Now edit any character inside `examples/vault/sample_timeline.jsonl` and run the `verify` command again. It names the exact entry where the chain breaks:

```
BROKEN {'broken_at': 2, 'reason': 'entry_hash mismatch (content altered)', 'entries_ok': 2}
```

Then open `examples/vault/` (from the repo root) to see the real shape of the data: a hash-chained timeline, a Mind's journal, and a knowledge-graph node.

**Scope, stated plainly:** this detects tampering with existing entries inside a stream. It does not by itself stop someone who can already write the file from truncating it or replacing the whole chain with a fresh, internally consistent one. Guarding against that (off-box backup and external anchoring) is future work, tracked in the [roadmap](docs/ROADMAP.md).

To see what that record is *for*, run the [evidence-backed reconstruction demo](examples/demo/reconstruct.py): it rebuilds a relationship from the sample vault, cites every line to its source, and refuses to run on a chain it cannot verify.

## Repo map

| Path | What's there |
|---|---|
| [`README.md`](README.md) | You are here. |
| [`docs/VISION.md`](docs/VISION.md) | Why this exists and where it is going. |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | How it is built and the design choices. |
| [`docs/THE_MINDS.md`](docs/THE_MINDS.md) | How the team of AI specialists works. |
| [`docs/PRINCIPLES.md`](docs/PRINCIPLES.md) | The commitments a real change must honor. |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | Honest current status and near-term priorities. |
| [`docs/GLOSSARY.md`](docs/GLOSSARY.md) | The project's small, deliberate vocabulary. |
| [`SECURITY.md`](SECURITY.md) | Threat model, auth, key handling, self-host risks. |
| [`examples/`](examples/) | Runnable code and anonymized sample data. |

## The core ideas

| Concept | Grounded in |
|---|---|
| **Minds** | Scheduled + on-demand agents, each with a role and a journal file. See [`examples/vault/sample_mind_journal.md`](examples/vault/sample_mind_journal.md). |
| **The Vault** | The canonical file store. One home and one stable ID per fact. |
| **Timelines** | Append-only, hash-chained JSONL. See [`examples/vault/sample_timeline.jsonl`](examples/vault/sample_timeline.jsonl) and the runnable verifier. |
| **The Constellation** | The relationship graph. See [`examples/vault/sample_graph_node.md`](examples/vault/sample_graph_node.md). |
| **Illuminations / Resonances** | An insight, and an insight that actually changed behavior. Tracked as records, not vibes. |

## Architecture in one diagram

```
  Clients      PWA (per-domain views) + chat / CLI
     |
  Edge         Caddy (TLS, static + reverse proxy)
     |
  API          FastAPI + enforcement / validation layer   <- significant writes routed through (partial today)
     |
  Intelligence Minds runtime (scheduled + on demand)
               model broker: Claude / GPT / Gemini / local, with fallbacks + spend cap
     |
  Memory       The Vault: Markdown + JSONL, unique IDs, append-only hash-chained timelines
     |
  Durability   owned hardware -> replicated (Syncthing/iCloud) -> [planned] versioned off-site encrypted git backup
```

Full detail in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## What works today

- Self-hosted server (FastAPI + Caddy) with a progressive web app across many life domains.
- ~35 scheduled Minds journaling through a cost-capped, model-agnostic broker (observed cost so far: a few dollars a month against a hard $200 cap).
- Append-only timelines with unique IDs. The hash-chain module ships in this repo with a test suite; wiring it across every write path is in progress (see roadmap).
- A nightly multi-model council that reviews the system's own work with an evidence gate.
- A self-healing health monitor with alerting.

## What is still aspirational

- Extending hash-chaining across every write path (the module exists and is tested; wiring is in progress).
- A full enforcement layer via a custom MCP server and editor hooks.
- Off-site, versioned, encrypted backup as a first-class feature.
- The Illuminations-to-Resonances loop closing reliably into measured behavior change.
- Consolidating overlapping memory stores into the one canonical Vault.

See [`docs/ROADMAP.md`](docs/ROADMAP.md).

## Getting involved

Built in the open, early, on purpose. Read the [vision](docs/VISION.md) and [architecture](docs/ARCHITECTURE.md), then open an issue with a question, a critique, or a design idea. Honest pushback is wanted. See [`CONTRIBUTING.md`](CONTRIBUTING.md).

## License

[MIT](LICENSE).

---

*A personal project opened to the community. Not affiliated with any employer or agency. Not professional, financial, legal, or medical advice.*
