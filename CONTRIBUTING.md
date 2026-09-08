# Contributing to LIFE OS

LIFE OS is being built in the open, early, on purpose. The best contributions right now are ideas, critique, and design pressure, not just code.

## Ways to help

- **Question and critique.** Open an issue. Tell us where the vision is thin, where the architecture is wrong, or where a claim is overstated. Rigorous, honest critique is the most valuable thing you can give a young project.
- **Design.** Propose how a subsystem should work: the enforcement layer, the memory model, the Minds coordination protocol, the Illuminations-to-Resonances loop.
- **Documentation.** Make the docs clearer for the next person who arrives.
- **Reference implementations.** Small, self-contained modules that demonstrate a concept (a hash-chained append log, a model-agnostic broker, a named-path retriever) are gold.

## Principles to build by

1. **Disk as truth.** Plain files, human-readable, one home per fact, unique IDs.
2. **Append-only.** Never silently delete. Corrections supersede; they do not erase.
3. **Enforcement in code.** Rules are validated by a process, not requested from a model.
4. **Model-agnostic.** No single vendor is load-bearing.
5. **Sovereignty.** The user owns the data and the compute. Default to self-hosted.
6. **Honesty over hype.** Mark what works versus what is aspirational. No buzzwords.

## Ground rules

- Never commit personal data or secrets. The `.gitignore` is a floor, not a substitute for judgment.
- Keep discussions civil and specific. See [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).

## Getting started

Read [`docs/VISION.md`](docs/VISION.md), [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), and [`docs/GLOSSARY.md`](docs/GLOSSARY.md), then open an issue with what you are thinking.
