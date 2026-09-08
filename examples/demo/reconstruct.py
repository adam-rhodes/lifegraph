#!/usr/bin/env python3
"""
LifeGraph demo: an evidence-backed reconstruction.

This is the thesis in ~120 lines and zero dependencies. It reads the shipped
sample vault (a hash-chained timeline plus a knowledge-graph node) and prints a
plain-English reconstruction of a relationship or a day.

Two things it does that a chatbot does not:
  1. Provenance. Every line it prints cites the exact entry and source it came
     from. It composes only from stored events; it invents nothing.
  2. Integrity first. It verifies the hash chain before it will reconstruct, and
     refuses to build a narrative on top of a tampered record.

Usage:
    python3 reconstruct.py                         # reconstruct the sample entity
    python3 reconstruct.py --entity person/alex-rivers
    python3 reconstruct.py --timeline ../vault/sample_timeline.jsonl
"""
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "hashchain"))
import lifegraph_hashchain as chain  # the same module the tests exercise

DEFAULT_TIMELINE = os.path.join(HERE, "..", "vault", "sample_timeline.jsonl")
DEFAULT_GRAPH_DIR = os.path.join(HERE, "..", "vault")


def load_entries(path):
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def read_graph_node(entity):
    """Best-effort read of a graph node's front matter for extra, sourced context."""
    fname = entity.split("/")[-1]
    for cand in ("sample_graph_node.md", f"{fname}.md"):
        p = os.path.join(DEFAULT_GRAPH_DIR, cand)
        if os.path.exists(p):
            txt = open(p, encoding="utf-8").read()
            if txt.startswith("---"):
                fm = txt.split("---", 2)[1]
                node = {}
                for ln in fm.splitlines():
                    if ":" in ln and not ln.strip().startswith("-"):
                        k, _, v = ln.partition(":")
                        node[k.strip()] = v.split("#")[0].strip()
                if node.get("id") == entity or fname in node.get("id", ""):
                    return node, os.path.basename(p)
    return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeline", default=DEFAULT_TIMELINE)
    ap.add_argument("--entity", default=None, help="e.g. person/alex-rivers; default = all entities in the file")
    args = ap.parse_args()

    ok, detail = chain.verify(args.timeline)
    print("LifeGraph reconstruction")
    print(f"Source timeline: {os.path.relpath(args.timeline, HERE)}")
    if not ok:
        print(f"Chain integrity: BROKEN at entry {detail.get('broken_at')} "
              f"({detail.get('reason')}). Refusing to reconstruct from a tampered record.")
        sys.exit(2)
    print(f"Chain integrity: OK ({detail['entries']} entries verified)")
    print()

    entries = load_entries(args.timeline)
    if args.entity:
        entries = [e for e in entries if e.get("entity") == args.entity]
    if not entries:
        print("No entries for that entity.")
        sys.exit(1)

    entity = args.entity or entries[0].get("entity", "(unknown)")
    node, node_file = read_graph_node(entity)

    print(f"Entity: {entity}")
    if node:
        name = node.get("name", entity)
        extra = []
        if node.get("disposition"):
            extra.append(f"disposition {node['disposition']}")
        if node.get("first_flame"):
            extra.append(f"first connection {node['first_flame']}")
        print(f"  {name}" + (f" ({', '.join(extra)})" if extra else "") + f"   [from {node_file}]")
    print()

    print("What happened, each line cited to the entry it came from:")
    sources = {}
    for e in entries:
        ts = e.get("ts", "")[:10]
        src = e.get("source", "?")
        sources[src] = sources.get(src, 0) + 1
        text = e.get("text", "").strip()
        print(f"  {ts}  {text:<52} [{src} / {e.get('event','')}]")
    print()

    first = entries[0].get("ts", "")[:10]
    last = entries[-1].get("ts", "")[:10]
    src_summary = ", ".join(f"{k} ({v})" for k, v in sorted(sources.items()))
    print("Summary (composed only from the entries above, nothing invented):")
    print(f"  {len(entries)} event(s) from {first} to {last}. Sources: {src_summary}.")
    print(f"  Latest: {entries[-1].get('event','')} on {last}.")
    print()
    print("Every line above traces to a stored, hash-verified entry. That is the point:")
    print("the record is the product, and it can prove it was not altered.")


if __name__ == "__main__":
    main()
