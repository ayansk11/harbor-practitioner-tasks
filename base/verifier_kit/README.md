# verifier_kit

Shared grading helpers. `tools/sync_kit.py` copies `kit.py` and `test.sh` unchanged into every task's `tests/`, so each
package stands alone (G19). Never edit the copies inside a task; change this folder and sync. Use in `tests/grade.py`:

```python
import sys; sys.path.insert(0, "/tests")   # python3 -I does not add the script folder to sys.path
import kit, os
def grade():
    sub = kit.prepare_submission()                                   # /work/sub, owned by uid 1001
    inp = kit.stage_for_runner(os.path.join(kit.TESTS_DIR, "hidden"), "hidden_in")  # inputs only, never answers
    out = kit.stage_for_runner(None, "hidden_out")                   # empty folder uid 1001 may write
    res = kit.run_as_runner(["python3", "-I", "-m", "pkg.cli", "--in", inp, "--out", out], cwd=sub, timeout=60)
    raw = kit.read_as_runner(os.path.join(out, "result.csv"))        # bytes, read with uid 1001's rights
    ok = res["rc"] == 0 and not res["timed_out"] and check(raw)      # the verdict is computed here, by root
    return (1 if ok else 0), {"rows_ok": n_ok}                       # reward 1 only if every check passes
kit.main(grade)
```

## API (unchanged names; new keyword-only options)
- `prepare_submission(name="sub", *, max_bytes=2 GiB, max_entries=200000)`: kills every uid-1001 process, copies /app
  to `WORK/<name>`, skips FIFOs and devices, removes auto-run files (`conftest.py`, `sitecustomize`/`usercustomize` in
  any form, `*.pth`, `*.pyc`, `__pycache__`, links included), clears setuid/setgid bits, hands the tree to uid 1001.
- `stage_for_runner(src, name)` (new): fresh `WORK/<name>` owned by uid 1001, holding a copy of `src` (a folder or one
  file), or empty if `src` is None. Safe at any point in grading.
- `run_as_runner(cmd, cwd, timeout, extra_env=None, *, fsize_bytes=None, isolate_network=None, output_bytes=None)`:
  returns `rc`, `timed_out`, `seconds`, `stdout`, `stderr` (last 4000 bytes each), `net` and `output_capped` (stdout
  plus stderr passed 64 MiB and the run was killed). Any file a runner writes is capped at 1 GiB (`fsize_bytes`; -1
  for no cap). It returns when the main process exits.
  Its process group, and every other uid-1001 process outside a live service, is then killed: a background helper
  never outlives the call. HOME (`/tmp/runner-home`) is emptied before each run while no service is live.
- `start_service_as_runner(cmd, cwd, port, health_path="/", timeout=30, extra_env=None, *, fsize_bytes=None)` and
  `stop_service(proc)`: `timeout` is a hard total limit; any HTTP status counts as healthy. Start services only this
  way: any other uid-1001 process is killed after the next run.
- `read_as_runner(path, max_bytes=200 MB)`: raises `FileNotFoundError` (missing or not readable by uid 1001) or
  `kit.RunnerReadError` (over `max_bytes`, a FIFO or device, over 120 s). It never truncates silently.
- `copy_out_as_runner(path, dst)`: `dst` must be inside `kit.SCRATCH` (a root-only 0700 folder; a relative `dst` goes
  there). Anything else raises `ValueError`, in local and real mode alike. Returns the absolute path.
- `kill_runner_processes()`, `write_reward(reward, metrics)`, `main(grade_fn)`, `log(msg)`; constants `LOCAL`,
  `APP_DIR`, `WORK`, `LOGS`, `TESTS_DIR` (new: `/tests`, or `GRADE_TESTS_DIR` only in local mode), `SCRATCH` (new),
  `RUNNER_UID`, `RUNNER_GID`, `RUNNER_ENV`. `write_reward` clamps the reward to [0, 1] (not a number: 0), keeps only
  finite numeric metrics, drops a metric named `reward`, and writes 0 if anything fails.

## Rules for grade.py (root runs it; agent code is hostile)
1. Run agent code only through `run_as_runner` / `start_service_as_runner`; never import it into the grader process.
2. Root never opens, stats, copies, compares or `sqlite3.connect`s a path under `WORK` or `APP_DIR` (/work, /app). A
   symlink or a swapped folder there can point root at `/tests` or at the reward. Read outputs with `read_as_runner`
   (bytes), or copy them with `copy_out_as_runner` into `kit.SCRATCH` and open that copy (SQLite:
   `sqlite3.connect(f"file:{p}?mode=ro&immutable=1", uri=True)`).
3. Never deserialize agent output as root: no `pickle`, `joblib`, `torch.load`, `np.load(allow_pickle=True)`,
   `yaml.load` (use `yaml.safe_load`), `eval` or `exec`. That is root code execution. Parse CSV, JSON or text.
4. The verdict comes from raw outputs checked by root. A pass/fail, score or log written by agent code (pytest run as
   uid 1001 included) is not evidence: uid 1001 can write any file it likes.
5. Give agent code hidden inputs through `stage_for_runner`, never the expected answers; those stay in `/tests`.
6. Prefer `python3 -I` for runner Python and a `cwd` outside the agent tree when the command allows it (a `json.py` in
   cwd shadows the standard library). Use `-m pkg` with `cwd=sub` only when the task's interface needs it.
7. Use `kit.TESTS_DIR` for hidden files. Honour other environment overrides (an interpreter path, say) only when
   `kit.LOCAL` is true.
8. No network in graders. Runs get a private loopback-only network when the kernel allows it (the first run logs
   `network isolation: ON/OFF`). Services always keep the host network, so a service can send what it receives to the
   internet. Each DESIGN.md states what a service sees (G21).

## Local authoring (the Mac; privilege steps are skipped)
`KIT_LOCAL=1 KIT_SUBMISSION=<app copy> KIT_LOGS=<dir> KIT_WORK=<dir> GRADE_TESTS_DIR=<task>/tests python grade.py`, as
a normal user. Local mode skips demotion, chown, the uid-1001 kill loop (a `setsid()` child can outlive a local run),
the network namespace and the lock. A local OK says nothing about those steps; only the Daytona proof run shows them.
Real mode refuses to start unless it runs as root from `/tests/kit.py`.

## What the Daytona proof run must show (from test-stdout.txt)
`[test.sh] lock ok: /logs/verifier 0:0 755 ...` with `protected_symlinks=...` and `setid files left: 0`;
`[kit] network isolation: ON|OFF ...` (whichever it is, record it); `[kit] reward=... (killed N runner processes)` with a
plausible N. A line `LOCK FAILED` means reward 0 for that run, and the kit must be fixed first.
