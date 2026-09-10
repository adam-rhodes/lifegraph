# The Minds

The intelligence in LifeGraph is not a single assistant. It is a team of specialists called Minds. This document explains what they are and how they are meant to work together.

## What a Mind is

A Mind is a named specialist with:

- a **role** (a chief of staff, a finance mind, a family mind, a health mind, and so on),
- a **voice** distinct enough that you can tell who is speaking,
- a **journal** it keeps in its own words, written to disk,
- a **strand** of accumulated experience that persists across sessions, and
- the ability to **collaborate** with the other Minds and with you.

Minds are not personas painted over one model. Each one reasons in the open and leaves a written record. If the system vanished, you could read the journals in order and reconstruct what the team was thinking and why.

## Why a team instead of one assistant

A single general assistant flattens everything into one voice and one context. A team lets different concerns be held by different specialists, lets them disagree, and lets a coordinating Mind decide who owns what. It mirrors how a capable human organization actually works: a chief of staff routes the incoming, specialists go deep, and the record is kept.

## How coordination is meant to work

The target design, in progress:

1. A significant event arrives (a message, a decision, a new fact).
2. The **chief-of-staff** Mind assigns it to the owning specialist, sets an urgency, and records ownership with a follow-up date.
3. The owning Mind does the work and journals it.
4. When specialists disagree, the disagreement is logged and resolved rather than averaged away.
5. A scheduled **council** reviews the team's output with an evidence gate, catching drift and error.

Today the Minds journal reliably on a schedule. The coordination layer, ownership, SLAs, structured dissent, is the current build focus. This is stated plainly because honesty about what is built versus intended is a project principle.

## The model layer

Minds do not depend on any single model provider. A broker routes each Mind's work to whichever model fits, with fallbacks and a spend cap. A Mind is defined by its role, memory, and journal, not by the vendor behind it on a given day.

## Emergence

The roster is not fixed at a number. When a domain of the user's life recurs and grows, that is the signal to give it a dedicated Mind. The roster changes as the person's life changes: Minds are added when a domain grows and retired when it goes quiet.
