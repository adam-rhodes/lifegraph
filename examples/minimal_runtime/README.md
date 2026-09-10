# Minimal runtime: one Mind, one vault, one hash-chained journal entry

The smallest honest slice of how the private instance works, in one stdlib-only file you can read top to bottom.

Prerequisites: Python 3.9+ (no packages). For the local path, [Ollama](https://ollama.com) installed and running (`ollama serve` starts it; `ollama pull llama3.2` fetches the default model, about 2 GB; `LIFEGRAPH_MODEL=gemma2:2b` picks a smaller one). Or skip Ollama and set `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` with `--provider openai` / `anthropic`. `--dry-run` needs nothing at all.

```bash
cd examples/minimal_runtime
python3 run_mind.py --vault ../vault --mind finance --dry-run     # see the exact prompt, call nothing
ollama run llama3.2                                              # once, if you want it local (any Ollama model works)
python3 run_mind.py --vault ../vault --mind finance              # writes ../vault/minds/finance/<today>.md
python3 ../hashchain/lifegraph_hashchain.py verify ../vault/minds/journal_timeline.jsonl
```

What it does, in order: reads the vault (Markdown + JSONL on disk), gives one named Mind a role and the relevant text, calls a model (Ollama locally by default; `--provider openai` or `anthropic` with the matching key in the environment), writes the Mind's journal entry as Markdown in its own folder, and appends a hash-chained timeline record of that write. Run `verify` afterwards and then edit the journal timeline by hand to watch it break.

What it does not do: schedule, coordinate several Minds, route between models with fallbacks and a spend cap, review itself nightly, or serve a web app. Those are the private runtime's job and are on the [roadmap](../../docs/ROADMAP.md) for release. Roles are four lines in `ROLES`; add your own.
