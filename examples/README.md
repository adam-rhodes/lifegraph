# Examples: the shape of reality

These are small, runnable, anonymized examples of how LifeGraph stores things. The person here ("Alex Rivers") is fictional. No real user data is in this repo.

## Runnable: append-only hash-chained timeline

The core memory guarantee is that history is tamper-evident. This is real, tested code, not a mockup.

```bash
cd hashchain

# verify the sample timeline that ships with the repo (should pass)
python3 lifegraph_hashchain.py verify ../vault/sample_timeline.jsonl

# run the full regression suite (tamper, delete, reorder detection)
python3 test_hashchain.py
```

Each line in a timeline stores the sha256 of the previous line (`prev_hash`) and its own
(`entry_hash`). Alter, delete, or reorder any past entry and `verify` reports exactly where the
chain breaks. Open `../vault/sample_timeline.jsonl` in any editor to see the shape.

## Runnable: an evidence-backed reconstruction

The point of the record is that it can answer "what actually happened" and show its work. This demo reads the sample vault and reconstructs a relationship, citing every line to the entry it came from. It invents nothing, and it refuses to run on a timeline whose hash chain does not verify.

```bash
cd demo
python3 reconstruct.py                        # reconstruct the sample entity
python3 reconstruct.py --entity person/alex-rivers
```

You will see each event tagged with its source (calendar, journal) and a summary composed only from those entries. Now tamper with a copy and watch it refuse:

```bash
cp ../vault/sample_timeline.jsonl /tmp/t.jsonl
sed -i "s/meetup/HACKED/" /tmp/t.jsonl        # alter one past entry
python3 reconstruct.py --timeline /tmp/t.jsonl # -> Chain integrity: BROKEN ... Refusing to reconstruct
```

That is provenance plus integrity in one command: a narrative that traces to stored evidence, and that will not build on a record it cannot prove is intact.

## The Vault, by example

- `vault/sample_timeline.jsonl` — a hash-chained entity timeline (three events for a person).
- `vault/sample_mind_journal.md` — what a Mind's journal entry looks like.
- `vault/sample_graph_node.md` — a knowledge-graph node: a person with typed connections.

Every fact has one home and one stable ID (`person/alex-rivers`). The chronological view and the
by-entity view are two indexes onto these same files.
