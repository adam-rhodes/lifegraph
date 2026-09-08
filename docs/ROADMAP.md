# Roadmap

LifeGraph is a running system with real gaps. This is an honest account of where it stands and what comes next. Reviewed against the project's own concept of operations and by independent multi-model critique.

## Built and running

- Self-hosted server (FastAPI + Caddy) with a progressive web app across many life domains.
- ~35 Minds journaling on a schedule through a cost-capped, model-agnostic broker.
- Life and per-entity timelines with unique IDs (plain JSONL), plus a standalone, tested hash-chain verification module (shipped in this repo).
- A nightly multi-model council that reviews the system's work with an evidence gate.
- A self-healing health monitor with alerting.

## In progress (the near-term priorities)

These are the things that move LifeGraph from "many impressive parts" to "one integrated system." Ranked.

1. **Off-site, versioned, encrypted backup.** Sync is not disaster recovery. A strict ignore policy, a clean baseline, and a daily push to an independent remote with a success alert.
2. **Enforcement layer.** A small validation service that every significant write is routed through, so the rules are processes, not suggestions.
3. **Hash-chaining across every write path.** The standalone module is built and tested; the remaining work is routing every journal and timeline write through it, so the whole record is tamper-evident, not only the streams that already use it.
4. **Minds as a coordinated team.** A chief-of-staff router that assigns each event to an owning Mind with an urgency and a follow-up, instead of specialists acting in parallel.
5. **The Illuminations-to-Resonances loop.** Every insight becomes a concrete experiment with a metric and a check-in, and the system tracks whether it actually changed behavior.
6. **One memory, not many.** Consolidate overlapping stores into the single canonical Vault so retrieval has one clean source of truth.

## Later

- Selective, verifiable disclosure of identity and credentials.
- A contribution model for a multi-user, cross-collaboration layer.
- Native mobile.

## Help wanted

Good places for a first contribution. None require access to the private runtime; they all live in this repo against the shipped module and samples.

- **Cross-platform file locking.** The hash-chain module uses POSIX `fcntl`; on Windows locking is currently a no-op. Add a portable lock (e.g. `msvcrt` or the `fasteners` package) behind the same interface, with a test.
- **A small CLI.** Wrap `append`, `verify`, and the reconstruction demo into one `lifegraph` command that works over any vault directory, not just the sample paths.
- **Detecting tail truncation.** Today truncating the last entries leaves a valid prefix that still verifies (documented in the tests as a known gap). Propose and prototype an approach: a periodic Merkle root or entry count committed off-box, or an append-only length receipt.
- **A source adapter.** Sketch the common adapter interface and implement one read-only adapter (e.g. iCal, mbox) that emits timeline entries in the shipped JSONL shape.
- **Concurrency tests.** Add a test that hammers `append` from several processes on POSIX and proves the chain never corrupts.

Open an issue to claim one, or just open a PR. Honest pushback on the design is equally welcome.

## How priorities are set

Priorities come from three sources kept in agreement: the concept of operations, the system's own honest self-assessment, and independent review by multiple models. When they disagree, that disagreement is logged and resolved in the open.
