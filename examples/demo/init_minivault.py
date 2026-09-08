#!/usr/bin/env python3
"""
Build a brand-new vault from scratch, then verify and reconstruct it.

This proves the core path is not hand-curated around one fixed sample file:
it creates a fresh timeline in a temp directory, appends a few events through
the same append() the tests use, verifies the chain, and runs the reconstruction
demo over the freshly generated data.

Usage:
    python3 init_minivault.py
"""
import os, sys, subprocess, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "hashchain"))
import lifegraph_hashchain as chain

EVENTS = [
    {"entity": "person/sam-lee", "event": "first_contact", "text": "Met Sam at the repair cafe.", "source": "calendar"},
    {"entity": "person/sam-lee", "event": "note", "text": "Sam fixes old radios; big on right-to-repair.", "source": "journal"},
    {"entity": "person/sam-lee", "event": "follow_up", "text": "Lent Sam a soldering iron.", "source": "journal"},
]


def main():
    d = tempfile.mkdtemp(prefix="lifegraph_minivault_")
    tl = os.path.join(d, "timeline.jsonl")
    print(f"Fresh vault: {d}\n")
    for i, e in enumerate(EVENTS):
        chain.append(tl, e, ts=f"2026-10-0{i+1}T09:00:00+0000")
    print(f"Wrote {len(EVENTS)} entries through append().\n")
    print("Raw timeline.jsonl (note the growing prev_hash -> entry_hash chain):")
    print(open(tl, encoding="utf-8").read())
    ok, det = chain.verify(tl)
    print(f"verify -> ok={ok} {det}\n")
    print("Reconstruction over the freshly generated vault:\n")
    subprocess.run([sys.executable, os.path.join(HERE, "reconstruct.py"), "--timeline", tl])


if __name__ == "__main__":
    main()
