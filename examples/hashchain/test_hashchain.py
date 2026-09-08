import os, json, tempfile, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lifegraph_hashchain as hc

def run():
    d = tempfile.mkdtemp()
    p = os.path.join(d, "stream.jsonl")
    fails = []
    # T1: append + verify clean
    for i in range(20):
        hc.append(p, {"mind": "silas", "text": f"entry {i}"}, ts=f"2026-09-08T00:00:{i:02d}-0500")
    ok, det = hc.verify(p)
    if not (ok and det["entries"] == 20): fails.append(("T1 clean chain", ok, det))
    # T2: each entry links to prior
    lines = [json.loads(l) for l in open(p, encoding="utf-8")]
    if lines[0]["prev_hash"] != hc.GENESIS: fails.append(("T2 genesis", lines[0]["prev_hash"]))
    linked = all(lines[i]["prev_hash"] == lines[i-1]["entry_hash"] for i in range(1, len(lines)))
    if not linked: fails.append(("T2 linkage", "broken"))
    # T3: tamper content -> detected
    p2 = os.path.join(d, "tampered.jsonl"); 
    with open(p2, "w", encoding="utf-8") as f: f.writelines(open(p, encoding="utf-8").readlines())
    ls = open(p2, encoding="utf-8").readlines(); obj = json.loads(ls[10]); obj["text"] = "ALTERED"
    ls[10] = json.dumps(obj) + "\n"
    open(p2, "w", encoding="utf-8").writelines(ls)
    ok, det = hc.verify(p2)
    if ok or det.get("broken_at") != 10: fails.append(("T3 tamper detect", ok, det))
    # T4: delete an entry -> detected
    p3 = os.path.join(d, "deleted.jsonl"); ls = open(p, encoding="utf-8").readlines(); del ls[5]
    open(p3, "w", encoding="utf-8").writelines(ls)
    ok, det = hc.verify(p3)
    if ok: fails.append(("T4 delete detect", ok, det))
    # T5: reorder -> detected
    p4 = os.path.join(d, "reorder.jsonl"); ls = open(p, encoding="utf-8").readlines(); ls[3], ls[4] = ls[4], ls[3]
    open(p4, "w", encoding="utf-8").writelines(ls)
    ok, det = hc.verify(p4)
    if ok: fails.append(("T5 reorder detect", ok, det))
    # T6: truncating the tail leaves a valid prefix -> NOT detected (documented limitation, not a bug)
    p5 = os.path.join(d, "truncated.jsonl"); ls = open(p, encoding="utf-8").readlines()[:-1]
    open(p5, "w", encoding="utf-8").writelines(ls)
    ok, det = hc.verify(p5)
    if not (ok and det["entries"] == 19): fails.append(("T6 tail truncation should still verify as a valid prefix", ok, det))
    # T7: a malformed line -> detected
    p6 = os.path.join(d, "garbage.jsonl")
    with open(p6, "w", encoding="utf-8") as f:
        f.writelines(open(p, encoding="utf-8").readlines()); f.write("this is not json\n")
    ok, det = hc.verify(p6)
    if ok or det.get("reason") != "unparseable json": fails.append(("T7 malformed line detect", ok, det))
    if fails:
        print("FAIL:", fails); sys.exit(1)
    print("ALL PASS: clean-chain, genesis, linkage, tamper-detect, delete-detect, reorder-detect, truncation-is-known-gap, malformed-detect")

run()
