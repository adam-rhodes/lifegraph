# Security and Threat Model

LifeGraph holds sensitive personal data (calendar, journals, relationships, health, finances). Its security posture is deliberate. This document is honest about what is protected and what is still hardening.

## Threat model

The system is designed for a single owner running their own instance on their own hardware. The main risks:

- **Server compromise.** The instance runs on a VPS or home box. Mitigations: only SSH and the web ports are exposed; all internal services (database, model workers, indexers) bind to localhost; key-based SSH with password auth disabled; a host firewall; fail2ban.
- **Credential leakage.** Model API keys and tokens are the crown jewels. They live in environment files with `600` permissions, are never committed (see `.gitignore`), and are never sent anywhere except the model provider.
- **Data loss.** Sync is not backup. The canonical files are replicated to the owner's devices. A versioned, off-site, encrypted git backup for true disaster recovery is in progress; until it is configured, replication is not a substitute for a real backup.
- **Tampering with history.** Timelines are hash-chained, so altering, deleting, or reordering existing entries within a stream is detectable (`examples/hashchain`). Protecting against truncation or wholesale replacement of a file is a further layer (off-box backup, external anchoring), still to build.
- **Over-broad agent action.** Minds should not be able to do arbitrary damage. Where implemented, an enforcement layer routes significant writes through a validation service that refuses unauthorized deletion and malformed writes. This protection is currently partial: some critical paths are mediated by code, others still rely on convention. Closing that gap is a top priority.
- **Untrusted input and prompt injection.** Minds read external material (emails, calendar invites, imported files) that can contain text crafted to steer a model. The design intent: untrusted input is treated as data, not instructions; a Mind's ability to write or delete is bounded by the enforcement layer and file permissions rather than by trusting the model; and only the text a task needs is sent to a provider. This boundary is partially enforced today and is an active priority, not a solved problem.

## Authentication

- The web app and API sit behind an auth gateway. Do not expose the API without it.
- Never run an instance with secrets in a public repository or a world-readable path.

## Reporting a vulnerability

Open a confidential issue or contact the maintainer directly. Please do not post exploit details publicly before a fix is available.

## What this project will never do

- Ship personal data in this repository.
- Send your data anywhere except the model provider you configured.
- Treat a written policy as an implemented control. If a protection is not enforced in code, the docs say so.
