# Glossary

LifeGraph uses a small, deliberate vocabulary. Here is what the terms mean.

- **Mind** — A named AI specialist with a defined role, a voice, and a journal of its own. Minds work across domains and collaborate with each other and with you. They are not chatbots; their reasoning is written to disk.
- **Chief of Staff** — The coordinating Mind that assigns incoming events to the right specialist, sets urgency, and tracks ownership.
- **The Vault** — The single canonical file store. Every fact has exactly one home and one unique ID.
- **Profile** (internally still called the Lifeform) — The persistent record the system keeps for you: the canonical facts, preferences, and history every Mind reads from, so context carries across time and sessions. In practice a profile plus its links into the graph, not a separate AI persona.
- **Timeline** — An append-only, timestamped record. There is a master timeline for your life and one for each entity (person, project, place). Timelines are hash-chained: entries reference the hash of the prior entry so tampering is detectable.
- **Illumination** — A non-obvious insight surfaced by the Minds from patterns across your life. The spark in a passing sentence, brought back at the right moment.
- **Resonance** — An Illumination that changes how you actually act. Each is tracked as a record with a concrete experiment, a metric, and a check-in, so the system can tell whether an insight mattered instead of assuming it did.
- **The Constellation** — The relationship graph: who is in your world, how you connect, what they care about, and how those connections evolve.
- **Council** — A scheduled, multi-model review (independent perspectives with an evidence gate) that checks the system's own output for accuracy and drift.
- **Broker** — The model-agnostic router that sends each task to the best available model, with fallbacks, so no single vendor is load-bearing.
- **Pulse** — The daily surfacing layer: what needs your attention now, drawn from across every domain.
