#!/usr/bin/env python3
"""LifeGraph public runtime slice: a roster of Minds, a scheduled tick, a model router with a spend cap,
and a file-based council. Stdlib only. Every write is hash-chained.

This is the same shape the private instance runs, rebuilt clean for release. What is here:
  roster.json        who the Minds are (id, name, role, cadence)
  tick               run every Mind that is due for this half of the day (am/pm), skip the ones that
                     already journaled, hold a single-instance lock, stop at the daily spend cap
  router             ollama -> openai -> anthropic in the order you configure, with per-call cost estimate
  council            a task file goes to a drafter, then to two BLIND reviewers (adversarial, grounding),
                     disputes are logged, and a chair writes an evidence-gated decision; all on disk
  ledger             spend.jsonl (hash-chained), dispatch_status.json, timeline.jsonl (hash-chained)

Usage (from examples/runtime):
  python3 lifegraph_runtime.py tick --vault ../vault                # run what is due now
  python3 lifegraph_runtime.py tick --vault ../vault --dry-run      # show who would run, call nothing
  python3 lifegraph_runtime.py council --vault ../vault --task "Is the Alex Rivers relationship worth a follow-up?"
  python3 lifegraph_runtime.py status --vault ../vault              # spend today, last tick, chain verify
  python3 lifegraph_runtime.py verify --vault ../vault              # verify every chained file

Models: LIFEGRAPH_PROVIDERS="ollama,openai,anthropic" (default: ollama only), LIFEGRAPH_MODEL, OLLAMA_HOST,
OPENAI_API_KEY, ANTHROPIC_API_KEY, LIFEGRAPH_DAILY_CAP_USD (default 1.00). Ollama calls cost 0.
"""
from __future__ import annotations
import argparse, datetime, json, os, re, sys, time, urllib.error, urllib.request
try:
    import fcntl  # POSIX single-instance lock
except ImportError:  # Windows: fall back to a lock file that must not exist (reviewer pre-flight, Gemini)
    fcntl = None

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "hashchain"))
try:
    from lifegraph_hashchain import append as chain_append, verify as chain_verify
except ImportError:
    sys.exit("run this from examples/runtime (needs ../hashchain/lifegraph_hashchain.py)")

# ----------------------------------------------------------------------------- config
PROVIDERS = [p.strip() for p in os.environ.get("LIFEGRAPH_PROVIDERS", "ollama").split(",") if p.strip()]
DEFAULT_MODEL = {"ollama": os.environ.get("LIFEGRAPH_MODEL", "llama3.2"),
                 "openai": "gpt-4o-mini", "anthropic": "claude-3-5-haiku-latest"}
# rough list prices per 1M tokens (input, output); good enough for a cap, not for accounting
PRICE = {"gpt-4o-mini": (0.15, 0.60), "gpt-4o": (2.50, 10.00), "claude-3-5-haiku-latest": (0.80, 4.00),
         "claude-sonnet-4-5": (3.00, 15.00)}
DAILY_CAP = float(os.environ.get("LIFEGRAPH_DAILY_CAP_USD", "1.00"))
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

def today() -> str: return datetime.date.today().isoformat()
def now_iso() -> str: return datetime.datetime.now().astimezone().isoformat(timespec="seconds")
def half_now() -> str: return "am" if datetime.datetime.now().hour < 12 else "pm"

# ----------------------------------------------------------------------------- vault paths
class Vault:
    def __init__(self, root: str):
        self.root = os.path.abspath(root)
        self.minds = os.path.join(self.root, "minds")
        self.state = os.path.join(self.root, "_runtime")
        os.makedirs(self.state, exist_ok=True)
        self.timeline = os.path.join(self.minds, "journal_timeline.jsonl")
        self.spend = os.path.join(self.state, "spend.jsonl")
        self.status_file = os.path.join(self.state, "dispatch_status.json")
        self.lock_file = os.path.join(self.state, "tick.lock")
        self.council = os.path.join(self.root, "council")
    def roster(self) -> list[dict]:
        p = os.path.join(HERE, "roster.json")
        with open(p, encoding="utf-8") as f:
            return json.load(f)["minds"]
    def text(self, limit_chars: int = 12000, exclude_prefix: str = "_runtime") -> str:
        """Newest Markdown/JSONL first, capped. The Minds read this; it is the whole record they get."""
        files = []
        for root, dirs, names in os.walk(self.root):
            dirs[:] = [d for d in dirs if not d.startswith(exclude_prefix) and d != "council"]
            for n in names:
                if n.endswith((".md", ".jsonl")) and not n.startswith("."):
                    p = os.path.join(root, n); files.append((os.path.getmtime(p), p))
        files.sort(reverse=True)
        out, used = [], 0
        for _m, p in files:
            try: t = open(p, encoding="utf-8", errors="replace").read()
            except OSError: continue
            chunk = f"\n\n=== {os.path.relpath(p, self.root)} ===\n{t}"
            if used + len(chunk) > limit_chars: chunk = chunk[: max(0, limit_chars - used)]
            out.append(chunk); used += len(chunk)
            if used >= limit_chars: break
        return "".join(out)

# ----------------------------------------------------------------------------- spend ledger
def spend_today(v: Vault) -> float:
    total = 0.0
    if not os.path.exists(v.spend): return 0.0
    for line in open(v.spend, encoding="utf-8"):
        try: e = json.loads(line)
        except ValueError: continue
        if str(e.get("ts", ""))[:10] == today(): total += float(e.get("usd", 0))
    return round(total, 6)

def record_spend(v: Vault, who: str, provider: str, model: str, tokens_in: int, tokens_out: int) -> float:
    pi, po = PRICE.get(model, (0.0, 0.0)) if provider != "ollama" else (0.0, 0.0)
    usd = round(tokens_in / 1e6 * pi + tokens_out / 1e6 * po, 6)
    chain_append(v.spend, {"who": who, "provider": provider, "model": model,
                           "tokens_in": tokens_in, "tokens_out": tokens_out, "usd": usd})
    return usd

# ----------------------------------------------------------------------------- model router
class SpendCap(Exception): pass

def _post(url: str, body: dict, headers: dict, timeout: int) -> dict:
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())

def _call_ollama(system, user, model):
    d = _post(f"{OLLAMA_HOST}/api/generate", {"model": model, "prompt": user, "system": system, "stream": False}, {}, 300)
    return d["response"].strip(), int(d.get("prompt_eval_count", 0)), int(d.get("eval_count", 0))

def _call_openai(system, user, model):
    key = os.environ.get("OPENAI_API_KEY")
    if not key: raise RuntimeError("OPENAI_API_KEY not set")
    d = _post("https://api.openai.com/v1/chat/completions",
              {"model": model, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}], "max_tokens": 700},
              {"Authorization": f"Bearer {key}"}, 120)
    u = d.get("usage", {})
    return d["choices"][0]["message"]["content"].strip(), int(u.get("prompt_tokens", 0)), int(u.get("completion_tokens", 0))

def _call_anthropic(system, user, model):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key: raise RuntimeError("ANTHROPIC_API_KEY not set")
    d = _post("https://api.anthropic.com/v1/messages",
              {"model": model, "max_tokens": 700, "system": system, "messages": [{"role": "user", "content": user}]},
              {"x-api-key": key, "anthropic-version": "2023-06-01"}, 120)
    u = d.get("usage", {})
    return "".join(b.get("text", "") for b in d["content"]).strip(), int(u.get("input_tokens", 0)), int(u.get("output_tokens", 0))

CALLERS = {"ollama": _call_ollama, "openai": _call_openai, "anthropic": _call_anthropic}

def route(v: Vault, who: str, system: str, user: str, providers: list[str] | None = None) -> tuple[str, str, str]:
    """Try providers in order; return (text, provider, model). Refuses paid calls once the daily cap is hit."""
    errors = []
    for p in providers or PROVIDERS:
        model = DEFAULT_MODEL.get(p, "")
        if p != "ollama" and spend_today(v) >= DAILY_CAP:
            errors.append(f"{p}: daily cap ${DAILY_CAP:.2f} reached"); continue
        try:
            text, ti, to = CALLERS[p](system, user, model)
            record_spend(v, who, p, model, ti, to)
            return text, p, model
        except (urllib.error.URLError, RuntimeError, KeyError, OSError) as e:
            errors.append(f"{p}/{model}: {str(e)[:120]}")
    raise RuntimeError("no provider answered: " + " | ".join(errors))

# ----------------------------------------------------------------------------- minds
def journaled(v: Vault, mind_id: str, half: str) -> bool:
    p = os.path.join(v.minds, mind_id, f"{today()}.md")
    return os.path.exists(p) and f"({half})" in open(p, encoding="utf-8", errors="replace").read()

def run_mind(v: Vault, m: dict, half: str, dry_run: bool = False) -> dict:
    system = (f"You are {m['name']}, one specialist in a small team that reads a person's private record. {m['role']} "
              "Write a journal entry of 120-200 words in the first person, dated today. Cite only what is in the record; "
              "if the record is thin, say so. End with one concrete question for the person. No bullet lists, no headers.")
    user = f"Today is {today()} ({half}). The record you can see:\n{v.text()}\n\nWrite your journal entry."
    if dry_run:
        return {"mind": m["id"], "would_run": True, "prompt_chars": len(system) + len(user)}
    text, provider, model = route(v, m["id"], system, user)
    # small models copy the sample journal's header; the runtime owns the header, so strip any the model wrote
    lines = text.splitlines()
    while lines and (lines[0].startswith("#") or lines[0].startswith("**Speaking") or not lines[0].strip()):
        lines.pop(0)  # only leading header lines; body lines are the Mind's and are kept as written
    text = "\n".join(lines).strip()
    d = os.path.join(v.minds, m["id"]); os.makedirs(d, exist_ok=True)
    p = os.path.join(d, f"{today()}.md")
    with open(p, "a", encoding="utf-8") as f:
        f.write(f"# {m['name']} — {today()} ({half})\n\n**Speaking: {m['name']} ({m['role'].split('.')[0].lower()}).**\nmodel: {provider}/{model}\n\n{text}\n\n")
    rec = chain_append(v.timeline, {"entity": f"mind/{m['id']}", "event": "journal", "half": half,
                                    "file": os.path.relpath(p, v.root), "model": f"{provider}/{model}", "chars": len(text)})
    return {"mind": m["id"], "file": os.path.relpath(p, v.root), "model": f"{provider}/{model}", "entry_hash": rec["entry_hash"][:12]}

def tick(v: Vault, half: str | None = None, only: list[str] | None = None, dry_run: bool = False) -> dict:
    half = half or half_now()
    if fcntl:
        lock = open(v.lock_file, "w")
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            return {"ok": False, "reason": "another tick is running (lock held)"}
    else:  # Windows: O_EXCL lock file; a crashed tick leaves it behind, delete it by hand
        try:
            lock = os.fdopen(os.open(v.lock_file + ".win", os.O_CREAT | os.O_EXCL | os.O_WRONLY), "w")
        except FileExistsError:
            return {"ok": False, "reason": "another tick is running (lock file exists: " + v.lock_file + ".win)"}
    ran, skipped, failed = [], [], []
    started = now_iso()
    for m in v.roster():
        if only and m["id"] not in only: continue
        if half not in m.get("cadence", ["am", "pm"]):
            skipped.append({"mind": m["id"], "why": f"not scheduled for {half}"}); continue
        if journaled(v, m["id"], half):
            skipped.append({"mind": m["id"], "why": f"already journaled {today()} {half}"}); continue
        try:
            ran.append(run_mind(v, m, half, dry_run))
        except Exception as e:  # one Mind failing never stops the others
            failed.append({"mind": m["id"], "error": str(e)[:300]})
    summary = {"ok": True, "half": half, "started": started, "finished": now_iso(), "dry_run": dry_run,
               "ran": ran, "skipped": skipped, "failed": failed, "spend_today_usd": spend_today(v), "cap_usd": DAILY_CAP}
    if not dry_run:
        json.dump(summary, open(v.status_file, "w"), indent=1)
    if fcntl:
        fcntl.flock(lock, fcntl.LOCK_UN); lock.close()
    else:
        lock.close(); os.remove(v.lock_file + ".win")
    return summary

# ----------------------------------------------------------------------------- council
def _extract_json(t: str) -> dict:
    m = re.search(r"\{.*\}", t, re.S)
    try: return json.loads(m.group(0)) if m else {"raw": t}
    except ValueError: return {"raw": t}

def council(v: Vault, task: str, task_id: str | None = None) -> str:
    """Draft -> two blind reviewers -> dispute ledger -> evidence-gated decision. Everything lands in vault/council/TASK-<id>/."""
    tid = task_id or (today().replace("-", "") + "-" + re.sub(r"[^a-z0-9]+", "-", task.lower()).strip("-")[:40])
    d = os.path.join(v.council, f"TASK-{tid}")
    if os.path.exists(d) and not task_id:  # same wording twice in a day gets its own folder (reviewer pre-flight, GPT)
        tid += "-" + datetime.datetime.now().strftime("%H%M%S"); d = os.path.join(v.council, f"TASK-{tid}")
    os.makedirs(os.path.join(d, "reviews"), exist_ok=True)
    def w(name, content):
        with open(os.path.join(d, name), "w", encoding="utf-8") as f:
            f.write(content if isinstance(content, str) else json.dumps(content, indent=2))
    def status(state): w("STATUS.json", {"state": state, "task_id": tid, "updated": now_iso()})
    record = v.text(9000)
    w("TASK.md", f"# TASK {tid}\nCreated: {now_iso()}\n\n{task}\n")
    status("draft")
    draft, dp, dm = route(v, "council/draft",
        "You are the drafter. Answer the task directly and concisely, citing lines from the record. Say what you could not verify.",
        f"TASK:\n{task}\n\nRECORD:\n{record}")
    w("DRAFT.md", f"# Draft ({dp}/{dm})\n{now_iso()}\n\n{draft}")
    status("review")
    ctx = f"TASK:\n{task}\n\nDRAFT ANSWER:\n{draft}\n\nRECORD (the only evidence that counts):\n{record}"
    adv, ap, am = route(v, "council/adversarial",
        "You are the adversarial reviewer. Try to prove the draft wrong. Do not rewrite it. Cite the record. "
        "Prefer 'flawed' or 'needs_work' if uncertain. Return ONLY JSON with keys: defects (list), unsupported_claims (list), "
        "assumptions (list), verdict ('sound'|'flawed'|'needs_work').", ctx)
    adv_j = _extract_json(adv); w("reviews/ADVERSARIAL.json", adv_j)
    grd, gp, gm = route(v, "council/grounding",
        "You are the grounding reviewer. Check every claim in the draft against the record. Return ONLY JSON with keys: "
        "contradictions (list), unverifiable (list), stale (list), verdict ('grounded'|'contradicted'|'unverifiable').", ctx)
    grd_j = _extract_json(grd); w("reviews/GROUNDING.json", grd_j)
    disputes = []
    for src, obj in (("adversarial", adv_j), ("grounding", grd_j)):
        vd = str(obj.get("verdict", "")).lower()
        if vd and vd not in ("sound", "grounded"):
            disputes.append({"source": src, "verdict": vd,
                             "issues": obj.get("defects") or obj.get("contradictions") or obj.get("unsupported_claims") or obj.get("unverifiable") or []})
    w("DISPUTES.json", {"count": len(disputes), "disputes": disputes})
    status("dispute" if disputes else "verified")
    decision, cp, cm = route(v, "council/chair",
        "You are the chair. You own the decision, but EVIDENCE OUTRANKS YOU: where a reviewer cites the record, defer to it; "
        "where a reviewer objects without evidence, say so and hold. Output: (a) accepted from each reviewer and why, "
        "(b) rejected and why, (c) the final answer, (d) what still needs the person.",
        f"TASK:\n{task}\n\nDRAFT:\n{draft}\n\nADVERSARIAL:\n{json.dumps(adv_j)[:4000]}\n\nGROUNDING:\n{json.dumps(grd_j)[:4000]}")
    w("DECISION.md", f"# Decision (evidence-gated, {cp}/{cm})\n{now_iso()}\n\n{decision}")
    status("decided")
    chain_append(v.timeline, {"entity": f"council/{tid}", "event": "decided", "disputes": len(disputes),
                              "dir": os.path.relpath(d, v.root)})
    return d

# ----------------------------------------------------------------------------- status / verify
def verify_all(v: Vault) -> dict:
    out = {}
    for p in (v.timeline, v.spend):
        if os.path.exists(p):
            ok, info = chain_verify(p); out[os.path.relpath(p, v.root)] = {"ok": ok, **info}
    return out

def status_report(v: Vault) -> dict:
    last = json.load(open(v.status_file)) if os.path.exists(v.status_file) else None
    return {"date": today(), "spend_today_usd": spend_today(v), "cap_usd": DAILY_CAP, "providers": PROVIDERS,
            "last_tick": {k: last[k] for k in ("half", "finished", "ran", "skipped", "failed")} if last else None,
            "chains": verify_all(v)}

# ----------------------------------------------------------------------------- cli
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["tick", "council", "status", "verify"])
    ap.add_argument("--vault", required=True)
    ap.add_argument("--half", choices=["am", "pm"])
    ap.add_argument("--only", help="comma-separated mind ids")
    ap.add_argument("--task", help="council task text")
    ap.add_argument("--id", help="council task id")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    v = Vault(a.vault)
    if a.cmd == "tick":
        r = tick(v, a.half, a.only.split(",") if a.only else None, a.dry_run)
        print(json.dumps(r, indent=1)); return 0 if r.get("ok") else 1
    if a.cmd == "council":
        if not a.task: sys.exit("--task is required")
        d = council(v, a.task, a.id); print("council ->", d)
        print(open(os.path.join(d, "STATUS.json")).read()); return 0
    if a.cmd == "status":
        print(json.dumps(status_report(v), indent=1)); return 0
    if a.cmd == "verify":
        r = verify_all(v); print(json.dumps(r, indent=1)); return 0 if all(x["ok"] for x in r.values()) else 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
