# Examples: the shape of reality

These are small, runnable, anonymized examples of how LIFE OS stores things. The person here ("Alex Rivers") is fictional. No real user data is in this repo.

## Runnable: append-only hash-chained timeline

The core memory guarantee is that history is tamper-evident. This is real, tested code, not a mockup.

```bash
cd hashchain

# verify the sample timeline that ships with the repo (should pass)
python3 lifeos_hashchain.py verify ../vault/sample_timeline.jsonl

# run the full regression suite (tamper, delete, reorder detection)
python3 test_hashchain.py
```

Each line in a timeline stores the sha256 of the previous line (`prev_hash`) and its own
(`entry_hash`). Alter, delete, or reorder any past entry and `verify` reports exactly where the
chain breaks. Open `../vault/sample_timeline.jsonl` in any editor to see the shape.

## The Vault, by example

- `vault/sample_timeline.jsonl` — a hash-chained entity timeline (three events for a person).
- `vault/sample_mind_journal.md` — what a Mind's journal entry looks like.
- `vault/sample_graph_node.md` — a knowledge-graph node: a person with typed connections.

Every fact has one home and one stable ID (`person/alex-rivers`). The chronological view and the
by-entity view are two indexes onto these same files.
