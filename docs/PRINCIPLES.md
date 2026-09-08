# Design Principles

These are the commitments that make LifeGraph what it is. A change that violates one of these is not a LifeGraph change.

## 1. Disk as truth
The file system is the database. Everything is plain Markdown or JSONL, human-readable, on hardware the user controls. Retrieval is named-path first, a discipline, with embeddings as an accelerant rather than the source of truth. If the whole system disappeared tomorrow, the files would still make sense in a text editor.

## 2. Append-only, never erase
Timelines only grow. Found history is backfilled at its true date; future events are added as they happen; corrections supersede prior entries additively. Nothing is silently deleted. Raw source is preserved until every detail has been extracted and confirmed elsewhere.

## 3. Enforcement in code, not prose
A rule that says "the finance Mind checks X" is worthless if "the finance Mind" is a persona rather than a process. Constraints, what may be written, what may never be deleted, are enforced by a validation layer that every write passes through.

## 4. Model-agnostic
Intelligence is routed through a broker with fallbacks. Claude, GPT, Gemini, or a local model can each do the work. No single vendor is load-bearing, and the system keeps running if any one is down.

## 5. Sovereignty and self-hosting
The user owns the data and the compute. The default deployment is a small server you control, replicated to your own devices. Cloud services are replicas of your canonical copy, never the other way around.

## 6. The team is alive
The set of Minds is not fixed. New Minds emerge when a domain of the user's life grows large enough to deserve dedicated attention. Roles shift as the user changes.

## 7. Honesty over hype
Every artifact marks what is verified versus reported versus aspirational. No buzzwords, no fake certainty. A written policy is never presented as an implemented one.
