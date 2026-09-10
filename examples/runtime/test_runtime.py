"""Tests that need no model: scheduling, skip-if-journaled, lock, spend cap, chain verify, council file layout with a fake provider."""
import json, os, shutil, sys, tempfile, unittest, warnings
warnings.simplefilter("ignore", ResourceWarning)
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import lifegraph_runtime as rt

def fake_provider(text="I read the record. Nothing new. Question: what changed?"):
    def _call(system, user, model): return text, 100, 50
    return _call

class T(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        shutil.copytree(os.path.join(HERE, "..", "vault"), os.path.join(self.tmp, "vault"))
        for gen in ("_runtime", "council", "minds"):   # generated state from earlier live runs must not leak into tests
            shutil.rmtree(os.path.join(self.tmp, "vault", gen), ignore_errors=True)
        self.v = rt.Vault(os.path.join(self.tmp, "vault"))
        rt.CALLERS["fake"] = fake_provider(); rt.DEFAULT_MODEL["fake"] = "fake-1"; rt.PRICE["fake-1"] = (1e6, 1e6)  # $1 per token, to hit the cap fast
        rt.PROVIDERS[:] = ["fake"]; rt.DAILY_CAP = 1.00
    def tearDown(self): shutil.rmtree(self.tmp)

    def test_dry_run_runs_nothing(self):
        r = rt.tick(self.v, "am", dry_run=True)
        self.assertTrue(r["ok"]); self.assertEqual({x["mind"] for x in r["ran"]}, {"chief-of-staff", "finance"})
        self.assertFalse(os.path.exists(self.v.timeline))

    def test_cadence_and_skip_if_journaled(self):
        rt.PRICE["fake-1"] = (0, 0)
        r1 = rt.tick(self.v, "pm"); self.assertEqual({x["mind"] for x in r1["ran"]}, {"chief-of-staff", "people"})
        r2 = rt.tick(self.v, "pm"); self.assertEqual(r2["ran"], []); self.assertTrue(all("already journaled" in s["why"] for s in r2["skipped"] if s["mind"] != "finance"))
        ok, info = rt.chain_verify(self.v.timeline); self.assertTrue(ok); self.assertEqual(info["entries"], 2)

    def test_spend_cap_stops_paid_calls(self):
        r = rt.tick(self.v, "am")   # first call costs 150 tokens * $1 = $150 > cap; the second Mind must be refused
        self.assertEqual(len(r["ran"]), 1); self.assertEqual(len(r["failed"]), 1); self.assertIn("daily cap", r["failed"][0]["error"])
        self.assertGreater(rt.spend_today(self.v), rt.DAILY_CAP)
        ok, _ = rt.chain_verify(self.v.spend); self.assertTrue(ok)

    def test_ollama_is_never_capped(self):
        rt.CALLERS["ollama"] = fake_provider(); rt.PROVIDERS[:] = ["ollama"]
        rt.chain_append(self.v.spend, {"who": "x", "provider": "fake", "model": "fake-1", "tokens_in": 5, "tokens_out": 0, "usd": 99.0})
        r = rt.tick(self.v, "am"); self.assertEqual(len(r["ran"]), 2); self.assertEqual(r["failed"], [])

    def test_lock_blocks_second_tick(self):
        import fcntl
        f = open(self.v.lock_file, "w"); fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        r = rt.tick(self.v, "am"); self.assertFalse(r["ok"]); self.assertIn("lock", r["reason"]); f.close()

    def test_council_writes_the_full_trail(self):
        rt.PRICE["fake-1"] = (0, 0)
        rt.CALLERS["fake"] = fake_provider('{"defects": ["draft cites a meetup date the record does not contain"], "verdict": "needs_work"}')
        d = rt.council(self.v, "Is the Alex Rivers relationship worth a follow-up?", "t1")
        for n in ("TASK.md", "DRAFT.md", "reviews/ADVERSARIAL.json", "reviews/GROUNDING.json", "DISPUTES.json", "DECISION.md", "STATUS.json"):
            self.assertTrue(os.path.exists(os.path.join(d, n)), n)
        self.assertEqual(json.load(open(os.path.join(d, "STATUS.json")))["state"], "decided")
        self.assertEqual(json.load(open(os.path.join(d, "DISPUTES.json")))["count"], 2)
        ok, info = rt.chain_verify(self.v.timeline); self.assertTrue(ok); self.assertEqual(info["entries"], 1)

    def test_tamper_is_detected(self):
        rt.PRICE["fake-1"] = (0, 0); rt.tick(self.v, "am")
        lines = open(self.v.timeline).read().splitlines(); lines[0] = lines[0].replace('"journal"', '"deleted"')
        open(self.v.timeline, "w").write("\n".join(lines) + "\n")
        ok, info = rt.chain_verify(self.v.timeline); self.assertFalse(ok); self.assertEqual(info["broken_at"], 0)

if __name__ == "__main__":
    unittest.main(verbosity=1)
