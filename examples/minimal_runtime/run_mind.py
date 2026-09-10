#!/usr/bin/env python3
"""Minimal LifeGraph runtime: one Mind, one vault, one journal entry, hash-chained.

This is the smallest honest slice of how the private instance works:
  1. read the vault (plain Markdown + JSONL files on disk),
  2. give ONE named Mind a role and the relevant text,
  3. call a model (local Ollama by default; or an API key if you set one),
  4. write the Mind's journal entry to disk as Markdown,
  5. append a hash-chained timeline record of that write (tamper-evident).

No scheduler, no council, no broker fallbacks, no web app. Those live in the private runtime and are being
sanitized for release. This file is stdlib-only so you can read every line.

Usage:
  python3 run_mind.py --vault ../vault --mind finance          # Ollama at http://localhost:11434, model llama3.2
  LIFEGRAPH_MODEL=gemma2:2b python3 run_mind.py --vault ../vault --mind health
  OPENAI_API_KEY=... python3 run_mind.py --vault ../vault --mind chief-of-staff --provider openai
  python3 run_mind.py --vault ../vault --mind finance --dry-run   # build the prompt, call nothing
"""
from __future__ import annotations
import argparse, datetime, json, os, sys, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "hashchain"))
try:
    from lifegraph_hashchain import append as chain_append, verify as chain_verify
except ImportError:
    sys.exit("run this from examples/minimal_runtime (needs ../hashchain/lifegraph_hashchain.py)")

ROLES = {
    "chief-of-staff": "You hold the throughline: what is open, what is owed, what was decided, what the next concrete move is.",
    "finance": "You watch money: balances, recurring charges, what changed, what needs a decision. Numbers only from the record.",
    "health": "You watch the body: sleep, recovery, movement, what the record shows, no diagnosis.",
    "people": "You watch relationships: who was in contact, who has gone quiet, what was promised.",
}

def read_vault(vault: str, limit_chars: int = 12000) -> str:
    """Concatenate the vault's Markdown and JSONL text, newest files first, capped so the prompt stays small."""
    files = []
    for root, _dirs, names in os.walk(vault):
        for n in names:
            if n.endswith((".md", ".jsonl")) and not n.startswith("."):
                p = os.path.join(root, n)
                files.append((os.path.getmtime(p), p))
    files.sort(reverse=True)
    out, used = [], 0
    for _m, p in files:
        try:
            text = open(p, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        chunk = f"\n\n=== {os.path.relpath(p, vault)} ===\n{text}"
        if used + len(chunk) > limit_chars:
            chunk = chunk[: max(0, limit_chars - used)]
        out.append(chunk); used += len(chunk)
        if used >= limit_chars:
            break
    return "".join(out)

def build_prompt(mind: str, vault_text: str, today: str) -> tuple[str, str]:
    role = ROLES.get(mind, f"You are the {mind} specialist. Stay in your lane.")
    system = (f"You are {mind}, one specialist in a small team that reads a person's private record. {role} "
              "Write a journal entry of 120-200 words in the first person, dated today. Cite only what is in the record; "
              "if the record is thin, say so. End with one concrete question for the person. No bullet lists, no headers.")
    user = f"Today is {today}. The record you can see:\n{vault_text}\n\nWrite your journal entry."
    return system, user

def call_ollama(system: str, user: str, model: str, host: str) -> str:
    body = json.dumps({"model": model, "prompt": user, "system": system, "stream": False}).encode()
    req = urllib.request.Request(f"{host}/api/generate", data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read())["response"].strip()

def call_openai(system: str, user: str, model: str) -> str:
    key = os.environ.get("OPENAI_API_KEY") or sys.exit("OPENAI_API_KEY not set")
    body = json.dumps({"model": model, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}], "max_tokens": 500}).encode()
    req = urllib.request.Request("https://api.openai.com/v1/chat/completions", data=body,
                                 headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"].strip()

def call_anthropic(system: str, user: str, model: str) -> str:
    key = os.environ.get("ANTHROPIC_API_KEY") or sys.exit("ANTHROPIC_API_KEY not set")
    body = json.dumps({"model": model, "max_tokens": 500, "system": system, "messages": [{"role": "user", "content": user}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body,
                                 headers={"Content-Type": "application/json", "x-api-key": key, "anthropic-version": "2023-06-01"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return "".join(b.get("text", "") for b in json.loads(r.read())["content"]).strip()

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vault", required=True, help="directory of Markdown/JSONL files (try ../vault)")
    ap.add_argument("--mind", default="chief-of-staff", help=f"one of {', '.join(ROLES)} or any name")
    ap.add_argument("--provider", choices=["ollama", "openai", "anthropic"], default=os.environ.get("LIFEGRAPH_PROVIDER", "ollama"))
    ap.add_argument("--model", default=os.environ.get("LIFEGRAPH_MODEL"))
    ap.add_argument("--ollama-host", default=os.environ.get("OLLAMA_HOST", "http://localhost:11434"))
    ap.add_argument("--dry-run", action="store_true", help="print the prompt, call nothing, write nothing")
    a = ap.parse_args()
    vault = os.path.abspath(a.vault)
    if not os.path.isdir(vault):
        sys.exit(f"no such vault: {vault}")
    today = datetime.date.today().isoformat()
    system, user = build_prompt(a.mind, read_vault(vault), today)
    if a.dry_run:
        print("--- system ---\n" + system + "\n--- user ---\n" + user[:3000] + ("\n... (truncated)" if len(user) > 3000 else ""))
        return 0
    model = a.model or {"ollama": "llama3.2", "openai": "gpt-4o-mini", "anthropic": "claude-3-5-haiku-latest"}[a.provider]
    try:
        text = {"ollama": lambda: call_ollama(system, user, model, a.ollama_host),
                "openai": lambda: call_openai(system, user, model),
                "anthropic": lambda: call_anthropic(system, user, model)}[a.provider]()
    except urllib.error.URLError as e:
        sys.exit(f"model call failed ({a.provider} {model}): {e}. Is Ollama running? `ollama run {model}` once, then retry.")
    # 4. journal to disk, in the Mind's own folder
    jdir = os.path.join(vault, "minds", a.mind); os.makedirs(jdir, exist_ok=True)
    jpath = os.path.join(jdir, f"{today}.md")
    with open(jpath, "a", encoding="utf-8") as f:
        f.write(f"# {a.mind} — {today}\n\nmodel: {a.provider}/{model}\n\n{text}\n\n")
    # 5. hash-chained record of the write
    tpath = os.path.join(vault, "minds", "journal_timeline.jsonl")
    rec = chain_append(tpath, {"entity": f"mind/{a.mind}", "event": "journal", "file": os.path.relpath(jpath, vault),
                               "model": f"{a.provider}/{model}", "chars": len(text)})
    ok, detail = chain_verify(tpath)
    print(f"wrote {os.path.relpath(jpath, vault)} ({len(text)} chars)")
    print(f"chained entry {rec.get('entry_hash', '')[:12]}… ; timeline verify: {'OK' if ok else 'BROKEN'} ({detail.get('entries', 0)} entries)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
