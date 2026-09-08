"""
LifeGraph append-only hash-chained journaling.

Every entry written to a stream carries the sha256 of the previous entry, so any
in-place alteration, reordering, or deletion of a past entry within that stream
breaks the chain and is detected by verify(). This detects tampering with existing
entries; it does not by itself prevent truncation or wholesale replacement of the
file (that needs off-box backup / external anchoring).

Design principles honored: disk-as-truth (plain JSONL), append-only (never rewrites
prior lines), enforcement-in-code (a single choke point for writes, serialized with
POSIX file locking; on Windows this degrades to cooperative single-writer discipline,
not enforced by the OS).
"""
import json, hashlib, os, tempfile, datetime
try:
    import fcntl  # POSIX advisory file locking
except ImportError:  # Windows has no fcntl; locking becomes a no-op (single-writer discipline still applies)
    fcntl = None

GENESIS = "0" * 64

def _canonical(obj: dict) -> str:
    # deterministic serialization for hashing (exclude the hash field itself)
    return json.dumps({k: obj[k] for k in sorted(obj) if k != "entry_hash"},
                      separators=(",", ":"), ensure_ascii=False)

def _hash(entry: dict, prev_hash: str) -> str:
    return hashlib.sha256((prev_hash + "\n" + _canonical(entry)).encode("utf-8")).hexdigest()

def _last_hash(path: str) -> str:
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return GENESIS
    last = None
    with open(path, "rb") as f:
        # read the final non-empty line efficiently
        for line in f:
            line = line.strip()
            if line:
                last = line
    if not last:
        return GENESIS
    try:
        return json.loads(last).get("entry_hash", GENESIS)
    except json.JSONDecodeError as e:
        raise ValueError(f"Corrupted stream: the last line of {path} is not valid JSON "
                         f"(a partial write?). Manual recovery required. {e}")

def append(path: str, data: dict, ts: str = None) -> dict:
    """Append one entry to the hash-chained stream at `path`. Returns the stored entry."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    if ts is None:
        ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")
    # lock so concurrent writers cannot interleave and break the chain
    lockpath = path + ".lock"
    with open(lockpath, "a") as lock:
        if fcntl:
            fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            prev = _last_hash(path)
            entry = dict(data)
            entry["ts"] = ts
            entry["prev_hash"] = prev
            entry["entry_hash"] = _hash(entry, prev)
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            return entry
        finally:
            if fcntl:
                fcntl.flock(lock, fcntl.LOCK_UN)

def verify(path: str):
    """Walk the chain. Returns (ok: bool, detail: dict)."""
    if not os.path.exists(path):
        return True, {"entries": 0, "note": "no stream yet"}
    prev = GENESIS
    n = 0
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            n += 1
            try:
                e = json.loads(line)
            except Exception:
                return False, {"broken_at": i, "reason": "unparseable json", "entries_ok": n - 1}
            if e.get("prev_hash") != prev:
                return False, {"broken_at": i, "reason": "prev_hash mismatch", "entries_ok": n - 1}
            if _hash(e, prev) != e.get("entry_hash"):
                return False, {"broken_at": i, "reason": "entry_hash mismatch (content altered)", "entries_ok": n - 1}
            prev = e["entry_hash"]
    return True, {"entries": n, "head": prev}

if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3 and sys.argv[1] == "verify":
        ok, d = verify(sys.argv[2]); print("OK" if ok else "BROKEN", d); sys.exit(0 if ok else 1)
    print("usage: lifegraph_hashchain.py verify <stream.jsonl>")
