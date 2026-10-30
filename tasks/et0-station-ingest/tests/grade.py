import sys; sys.path.insert(0, "/tests"); import kit  # python3 -I does not add the script folder to sys.path

"""Grader for et0-station-ingest.

Two checks, both against FAO-56 daily ET0 computed at authoring time by an independent reference (tests/expected/,
made by submission/authoring/et0-station-ingest/gen_data.py; the tolerance derivation is in that task's DESIGN.md):
  1. /app/output/et0.csv (the agent's regenerated file) for the eight visible stations;
  2. the agent's command `python3 -m et0.pipeline --stations ... --data ... --out ...`, run as uid 1001 from a copy of
     /app, on ten hidden stations that use only the metadata variants listed in /app/docs/METHOD.md.
Reward 1 only if both pass: exactly one row per (station_id, date) of the input, no extra or unreadable rows, every
value within TOL mm/day of the reference, and the run exits 0 within RUN_CAP_SEC. Agent code is never imported here.
In real mode /app is made unavailable right after it is copied (lock_app), so the pipeline cannot depend on absolute
/app paths, as instruction.md states. Local authoring: KIT_LOCAL=1 KIT_SUBMISSION=<app copy> KIT_LOGS=<dir>
KIT_WORK=<dir> GRADE_TESTS_DIR=<tests dir> GRADE_PYTHON=<interpreter with the task's packages> (both overrides are
honoured only in local mode).
"""
import csv, io, math, os, re, stat

TESTS = kit.TESTS_DIR
PYTHON = os.environ.get("GRADE_PYTHON", "python3") if kit.LOCAL else "python3"
TOL = 0.03            # mm/day; DESIGN.md "Tolerance"
RUN_CAP_SEC = 60      # one run of the agent's pipeline; DESIGN.md "Timings and caps"
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
COLUMNS = ("station_id", "date", "et0_mm_day")


def read_expected(path):
    with open(path, newline="", encoding="utf-8") as f:
        return {(r["station_id"], r["date"]): float(r["et0_mm_day"]) for r in csv.DictReader(f)}


def parse_output(raw):
    """CSV bytes -> ({(station_id, date): value}, counts). Extra columns and any row order are accepted."""
    counts = {"bad_rows": 0, "duplicate_rows": 0, "header_ok": 0}
    text = raw.decode("utf-8-sig", errors="replace")
    rows = list(csv.reader(io.StringIO(text)))
    if not rows:
        return {}, counts
    header = [h.strip() for h in rows[0]]
    if any(header.count(c) != 1 for c in COLUMNS):
        kit.log(f"header lacks one of {COLUMNS}: {header[:12]}")
        return {}, counts
    counts["header_ok"] = 1
    i_sid, i_date, i_val = (header.index(c) for c in COLUMNS)
    got = {}
    for line in rows[1:]:
        if not line or all(not c.strip() for c in line):
            continue
        try:
            sid, date, val = line[i_sid].strip(), line[i_date].strip(), float(line[i_val])
        except (IndexError, ValueError):
            counts["bad_rows"] += 1
            continue
        if not DATE_RE.fullmatch(date) or not math.isfinite(val):
            counts["bad_rows"] += 1
            continue
        if (sid, date) in got:
            counts["duplicate_rows"] += 1
            continue
        got[(sid, date)] = val
    return got, counts


def compare(prefix, raw, expected):
    got, counts = parse_output(raw)
    missing = sum(1 for k in expected if k not in got)
    extra = sum(1 for k in got if k not in expected)
    errs = [abs(got[k] - v) for k, v in expected.items() if k in got]
    over = sum(1 for e in errs if e > TOL)
    worst = max(errs) if errs else -1.0
    ok = (counts["header_ok"] == 1 and counts["bad_rows"] == 0 and counts["duplicate_rows"] == 0
          and missing == 0 and extra == 0 and over == 0)
    if errs and over:
        k = max((k for k in expected if k in got), key=lambda k: abs(got[k] - expected[k]))
        kit.log(f"{prefix}: worst row {k} got {got[k]:.4f} expected {expected[k]:.4f}")
    kit.log(f"{prefix}: rows={len(got)} expected={len(expected)} missing={missing} extra={extra} "
            f"bad={counts['bad_rows']} dup={counts['duplicate_rows']} over_tol={over} max_abs_err={worst:.4f} ok={ok}")
    return ok, {f"{prefix}_ok": ok, f"{prefix}_missing_rows": missing, f"{prefix}_extra_rows": extra,
                f"{prefix}_bad_rows": counts["bad_rows"], f"{prefix}_duplicate_rows": counts["duplicate_rows"],
                f"{prefix}_rows_over_tol": over, f"{prefix}_max_abs_err": round(worst, 6)}


def lock_app():
    """Real mode: make /app unavailable to the runs, after prepare_submission has copied it (nothing reads it later).

    The instruction says the pipeline must not rely on absolute /app paths; without this step the artifact would still
    sit at /app in the verifier and such a pipeline would pass. First choice: rename /app (rename(2) moves the entry
    itself and never follows a symlink; / is root-owned, so uid 1001 cannot recreate /app). If that fails (for example
    EBUSY on a mount point), make the real directory root-owned 0700 through an O_NOFOLLOW descriptor. Never raises:
    a failure is logged and reported as app_locked = 0, and grading goes on (the proof run reads the metric)."""
    if kit.LOCAL:
        return -1                                    # nothing to lock on the Mac; reported as -1
    try:
        os.rename("/app", "/app.unavailable")
        kit.log("/app locked: renamed to /app.unavailable")
        return 1
    except FileNotFoundError:
        kit.log("/app locked: no /app in the verifier")
        return 1
    except OSError as e:
        kit.log(f"/app rename failed ({e!r}); trying chmod 0700")
    try:
        fd = os.open("/app", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fchown(fd, 0, 0)
            os.fchmod(fd, 0o700)
            st = os.fstat(fd)
        finally:
            os.close(fd)
        if st.st_uid == 0 and stat.S_IMODE(st.st_mode) & 0o077 == 0:
            kit.log("/app locked: root-owned, mode 0700")
            return 1
        kit.log(f"/app lock FAILED: uid {st.st_uid} mode {oct(stat.S_IMODE(st.st_mode))} after chmod")
    except Exception as e:
        kit.log(f"/app lock FAILED: {e!r}")
    return 0


def check_sums():
    """The hidden inputs and expected values must be byte-identical to what was committed (tests/SHA256SUMS)."""
    import hashlib
    n = 0
    with open(os.path.join(TESTS, "SHA256SUMS"), encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            digest, rel = line.rstrip("\n").split("  ", 1)
            with open(os.path.join(TESTS, rel), "rb") as g:
                if hashlib.sha256(g.read()).hexdigest() != digest:
                    raise RuntimeError(f"SHA256 mismatch for tests/{rel}")
            n += 1
    if n == 0:
        raise RuntimeError("SHA256SUMS lists no files")
    kit.log(f"SHA256SUMS: {n} files verified")


def grade():
    metrics = {"tolerance_mm_day": TOL}
    check_sums()
    sub = kit.prepare_submission()
    metrics["app_locked"] = lock_app()

    # 1. the regenerated output for the visible stations
    try:
        raw = kit.read_as_runner(os.path.join(sub, "output", "et0.csv"))
    except Exception as e:
        kit.log(f"visible output unreadable: {e}")
        raw = b""
    ok_visible, m = compare("visible", raw, read_expected(os.path.join(TESTS, "expected", "visible_et0.csv")))
    metrics.update(m)

    # 2. the agent's pipeline on the hidden stations (inputs staged for uid 1001; the answers stay in /tests). No -I:
    #    the stated interface is `python -m et0.pipeline` from the folder that holds the package, so cwd must be on
    #    sys.path (kit README rule 6).
    inp = kit.stage_for_runner(os.path.join(TESTS, "hidden"), "hidden_in")
    out_dir = kit.stage_for_runner(None, "hidden_out")
    out = os.path.join(out_dir, "et0.csv")
    res = kit.run_as_runner([PYTHON, "-m", "et0.pipeline", "--stations", os.path.join(inp, "stations.yaml"),
                             "--data", os.path.join(inp, "raw"), "--out", out], cwd=sub, timeout=RUN_CAP_SEC)
    metrics.update({"hidden_run_rc": res["rc"] if res["rc"] is not None else -1,
                    "hidden_run_timed_out": res["timed_out"], "hidden_run_seconds": res["seconds"]})
    if res["rc"] != 0:
        kit.log(f"hidden run stderr tail: {res['stderr'][-1500:]}")
    try:
        raw = kit.read_as_runner(out)
    except Exception as e:
        kit.log(f"hidden output unreadable: {e}")
        raw = b""
    ok_hidden, m = compare("hidden", raw, read_expected(os.path.join(TESTS, "expected", "hidden_et0.csv")))
    metrics.update(m)

    run_ok = res["rc"] == 0 and not res["timed_out"]
    reward = 1 if (ok_visible and ok_hidden and run_ok) else 0
    return reward, metrics


kit.main(grade)
