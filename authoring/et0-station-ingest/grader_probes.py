"""Grader robustness probes for et0-station-ingest (authoring only; run after local_check.py).

Starts from the canonical run's artifact (.localruns/canonical/artifact), rewrites /app/output/et0.csv in ways that
must still pass (quality-gate checks G13, G15 in docs/QUALITY_GATE.md: row order, extra columns, CRLF, BOM,
2 decimals, quoted fields) or must fail (G12: a duplicate row, a missing row, an extra row, NaN, a wrong header), and
grades each copy in KIT_LOCAL mode. It also
prints, for each attempt, the worst hidden error per station (which stations make it fail).
Run (repository root): .venv/bin/python authoring/et0-station-ingest/grader_probes.py
"""
import csv, io, json, os, random, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.normpath(os.path.join(HERE, "..", "..", "tasks", "et0-station-ingest"))
RUNS = os.path.join(HERE, ".localruns")
PY = sys.executable


def rows_of(path):
    with open(path, newline="") as f:
        return list(csv.reader(f))


def write(path, text, newline="\n"):
    with open(path, "w", newline="") as f:
        f.write(text.replace("\n", newline))


def to_text(rows, quote=False):
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\n", quoting=csv.QUOTE_ALL if quote else csv.QUOTE_MINIMAL).writerows(rows)
    return buf.getvalue()


def grade(art, tag):
    logs, work = os.path.join(RUNS, "probe_" + tag, "logs"), os.path.join(RUNS, "probe_" + tag, "work")
    env = dict(os.environ, KIT_LOCAL="1", KIT_SUBMISSION=art, KIT_LOGS=logs, KIT_WORK=work,
               GRADE_TESTS_DIR=os.path.join(TASK, "tests"), GRADE_PYTHON=PY, PYTHONDONTWRITEBYTECODE="1")
    subprocess.run([PY, os.path.join(TASK, "tests", "grade.py")], env=env, capture_output=True, cwd=os.path.join(TASK, "tests"))
    return json.load(open(os.path.join(logs, "reward.json")))


def main():
    base = os.path.join(RUNS, "canonical", "artifact")
    good = rows_of(os.path.join(base, "output", "et0.csv"))
    header, body = good[0], good[1:]
    rnd = random.Random(7)
    shuffled = body[:]
    rnd.shuffle(shuffled)
    probes = {
        "PASS shuffled rows": (1.0, to_text([header] + shuffled)),
        "PASS extra columns, other column order": (1.0, to_text([["et0_mm_day", "note", "date", "station_id"]] +
                                                               [[r[2], "ok", r[1], r[0]] for r in body])),
        "PASS 2-decimal values": (1.0, to_text([header] + [[r[0], r[1], f"{float(r[2]):.2f}"] for r in body])),
        "PASS quoted fields, CRLF": (1.0, ("crlf", to_text([header] + body, quote=True))),
        "PASS UTF-8 BOM, blank trailing line": (1.0, "﻿" + to_text([header] + body) + "\n"),
        "FAIL one duplicate row": (0.0, to_text([header] + body + [body[100]])),
        "FAIL one row missing": (0.0, to_text([header] + body[:-1])),
        "FAIL one extra station-day": (0.0, to_text([header] + body + [["XXX", "2025-01-01", "3.000"]])),
        "FAIL one value NaN": (0.0, to_text([header] + [body[0][:2] + ["nan"]] + body[1:])),
        "FAIL header renamed (et0)": (0.0, to_text([["station_id", "date", "et0"]] + body)),
        "FAIL one value off by 0.05": (0.0, to_text([header] + [body[0][:2] + [f"{float(body[0][2]) + 0.05:.3f}"]] + body[1:])),
    }
    print("| Probe on /app/output/et0.csv (canonical pipeline unchanged) | Expected | Got |")
    print("|---|---|---|")
    bad = 0
    for i, (label, (exp, text)) in enumerate(probes.items()):
        art = os.path.join(RUNS, f"probe_{i}", "artifact")
        shutil.rmtree(os.path.dirname(art), ignore_errors=True)
        shutil.copytree(base, art)
        if isinstance(text, tuple):
            write(os.path.join(art, "output", "et0.csv"), text[1], newline="\r\n")
        else:
            write(os.path.join(art, "output", "et0.csv"), text)
        got = grade(art, str(i))["reward"]
        bad += got != exp
        print(f"| {label} | {exp} | {got} |")
    print("ALL PROBES AS EXPECTED" if not bad else f"{bad} PROBE(S) NOT AS EXPECTED")

    # per-station worst hidden error for each attempt
    exp = {(r["station_id"], r["date"]): float(r["et0_mm_day"])
           for r in csv.DictReader(open(os.path.join(TASK, "tests", "expected", "hidden_et0.csv")))}
    import yaml
    reg = {s["id"]: s for s in yaml.safe_load(open(os.path.join(TASK, "tests", "hidden", "stations.yaml")))["stations"]}
    print()
    head = " | ".join(f"{k} ({reg[k]['wind_height_m']} m, {reg[k]['latitude']}, {reg[k]['radiation_units']})" for k in sorted(reg))
    print(f"| Variant | {head} |")
    print("|---|" + "---|" * len(reg))
    for v in ["canonical", "alt", "nop", "fit_to_metservice", "hardcode_output", "linear_wind", "fix_altitude",
              "units_not_latitude", "nearest_height"]:
        out = os.path.join(RUNS, v, "work", "hidden_out", "et0.csv")
        worst = {k: 0.0 for k in reg}
        for r in csv.DictReader(open(out)):
            k = (r["station_id"], r["date"])
            if k in exp:
                worst[r["station_id"]] = max(worst[r["station_id"]], abs(float(r["et0_mm_day"]) - exp[k]))
        print(f"| {v} | " + " | ".join(f"{'**' if worst[k] > 0.03 else ''}{worst[k]:.3f}{'**' if worst[k] > 0.03 else ''}"
                                        for k in sorted(reg)) + " |")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
