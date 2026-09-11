# Architecture

This document describes how LifeGraph is put together and why. It aims to be specific enough to critique.

## The shape of the system

```
  Clients        PWA (per-domain views)   +   chat / CLI
     |
  Edge           Caddy (TLS, static + reverse proxy)
     |
  API            FastAPI service  ->  enforcement / validation layer
     |
  Intelligence   Minds runtime (scheduled + on demand)
                 model broker: Claude / GPT / Gemini / local, with fallbacks
     |
  Memory         The Vault: plain files (Markdown + JSONL), unique IDs,
                 append-only hash-chained timelines, a knowledge graph view
     |
  Durability     canonical on owned hardware
                 -> replicated (Syncthing / iCloud) -> [planned] versioned, encrypted git backup (off-site)
```

## Memory: disk as truth

The canonical store is the file system, not a database. Concretely:

- Every fact lives in exactly one file and carries a **unique, stable ID**.
- Records are **Markdown** (human narrative, journals, profiles) and **JSONL** (structured events, timelines, indexes).
- The same underlying files are exposed through two organized views: **chronological** (by date) and **by entity** (person, project, place). One file, two indexes, no duplication.
- A **knowledge graph** ties people, files, projects, and timelines together. The org chart, the relationship map, and the timelines are all views onto this one graph.

Why files: longevity (readable in any editor, in any decade), portability (no lock-in), inspectability (the memory is an audit trail you can read), and sovereignty (it sits on hardware you own).

## Timelines: append-only and hash-chained

There is a master timeline for the whole life and one timeline per entity. The rules:

- Entries are only ever **added**. Found history is backfilled at its true date; corrections supersede prior entries additively; nothing is silently removed.
- Each entry stores the **hash of the prior entry**, forming a chain (applied to streams that use the hash-chain module; rollout across every write path is in progress). Any in-place edit, deletion, or reordering of existing entries breaks the chain and is detectable by `verify()`. Guarding against truncation or wholesale replacement of a file is a further layer (off-box backup, external anchoring), still to build.
- What the chain is for, stated plainly: anyone with write access to the file can recompute every hash after an edit, so the chain is not proof to a third party. It protects the person from silent alteration of their own record by their own software or by a bug, and it makes revocation honest: a revoked fact is superseded by a revocation entry and dropped from every projection, and the original line stays as a tombstone in a chain only the person holds. Cryptographic erasure with re-keying is not implemented and not claimed.
- Models and the record: the record and the continuity layer stay on hardware the person controls; a model call, local or remote, receives the slice of the record placed in one prompt and stores nothing. The runtime's router (`examples/runtime`) defaults to a local model and only reaches a remote one when configured to. Whether that is acceptable is a per-deployment choice, set explicitly, not assumed.
- Timelines compose: an entity's timeline rolls up into the master.

## Retrieval: named-path first

Retrieval is a discipline before it is an algorithm. The system reads the relevant file by name and path before producing output ("read the person's file before answering about the person"). Vector embeddings accelerate discovery but are not the source of truth. For a single person's corpus, precise named-path retrieval beats fuzzy similarity search, and it keeps the memory legible.

## Intelligence: Minds and the broker

- **Minds** are scheduled jobs and on-demand agents. Each has a role, a persistent memory strand, and a journal it writes to disk.
- The **broker** is a thin, model-agnostic layer. It exposes one interface and routes to Claude, GPT, Gemini, or a local model, with fallbacks and a hard monthly spend cap. Swapping or adding a provider does not touch the Minds.
- A nightly **council** runs several models independently over the same question and reconciles them behind an evidence gate, so no single model's opinion is taken on faith.

## Enforcement: rules as processes

The design goal is that constraints are validated by code, not requested from a model. A write to a protected area passes through a validation layer that checks naming, refuses unauthorized deletion, and appends the hash-chain link. This is the layer that is meant to turn "the system should never lose anything" from a wish into a guarantee. It is an active build area: some paths are wired through it today, others still rely on convention.

## Deployment: self-hosted by default

- Runs on a small VPS or a home machine. TLS and routing via Caddy; the API in Python; a progressive web app for the client so there is nothing to install.
- The canonical data lives on hardware the user controls and is **replicated** to their devices. Cloud copies are replicas of the canonical, never the reverse.
- **Backup** (in progress) is versioned (git) with an off-site, encrypted push, treated as disaster recovery distinct from sync. Until it is configured, replication is not yet a true off-site backup.
- A **health monitor** checks services, disk, and endpoints on a timer, self-heals common failures, and alerts on real problems.

## What this is not

- Not a wrapper around one model's API.
- Not a vector database with a chat box.
- Not a cloud service that holds your data hostage.

## Known weaknesses (honest list)

- Overlapping memory subsystems exist and are being consolidated into the one Vault.
- The enforcement layer is partly convention, partly code; the goal is fully code.
- Hash-chaining is being rolled out across all write paths.
- Minds journal well but coordinate weakly; the chief-of-staff routing layer is in progress.
