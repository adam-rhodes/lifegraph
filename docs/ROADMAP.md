# Roadmap

LifeGraph is a running system with real gaps. This is an honest account of where it stands and what comes next. Reviewed against the project's own concept of operations and by independent multi-model critique.

## Built and running

- Self-hosted server (FastAPI + Caddy) with a progressive web app across many life domains.
- ~35 Minds journaling on a schedule through a cost-capped, model-agnostic broker.
- Append-only life and per-entity timelines with unique IDs.
- A nightly multi-model council that reviews the system's work with an evidence gate.
- A self-healing health monitor with alerting.

## In progress (the near-term priorities)

These are the things that move LifeGraph from "many impressive parts" to "one integrated system." Ranked.

1. **Off-site, versioned, encrypted backup.** Sync is not disaster recovery. A strict ignore policy, a clean baseline, and a daily push to an independent remote with a success alert.
2. **Enforcement layer.** A small validation service that every significant write is routed through, so the rules are processes, not suggestions.
3. **Append-only hash-chained journaling.** Every journal and timeline write stores the hash of the prior entry, making the record tamper-evident.
4. **Minds as a coordinated team.** A chief-of-staff router that assigns each event to an owning Mind with an urgency and a follow-up, instead of specialists acting in parallel.
5. **The Illuminations-to-Resonances loop.** Every insight becomes a concrete experiment with a metric and a check-in, and the system tracks whether it actually changed behavior.
6. **One memory, not many.** Consolidate overlapping stores into the single canonical Vault so retrieval has one clean source of truth.

## Later

- Selective, verifiable disclosure of identity and credentials.
- A contribution model for a multi-user, cross-collaboration layer.
- Native mobile.

## How priorities are set

Priorities come from three sources kept in agreement: the concept of operations, the system's own honest self-assessment, and independent review by multiple models. When they disagree, that disagreement is logged and resolved in the open.
