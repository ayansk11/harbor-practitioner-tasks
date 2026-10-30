"""Format and tamper probes for the ab-test-reanalysis grader's compare() (authoring only).

Loads tests/grade.py without its last line (kit.main), in KIT_LOCAL mode, and feeds compare() variants of the
canonical visible readout (the reference values themselves, re-serialised). Each probe states whether it should pass.
Run: submission/.venv/bin/python submission/authoring/ab-test-reanalysis/grader_probes.py   (writes grader_probes.out.md)
"""
import json, math, os, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TESTS = os.path.normpath(os.path.join(HERE, "..", "..", "tasks", "ab-test-reanalysis", "tests"))
tmp = tempfile.mkdtemp()
os.environ.update(KIT_LOCAL="1", KIT_SUBMISSION=tmp, KIT_LOGS=os.path.join(tmp, "logs"),
                  KIT_WORK=os.path.join(tmp, "work"), GRADE_TESTS_DIR=TESTS)
sys.path.insert(0, TESTS)
src = open(os.path.join(TESTS, "grade.py"), encoding="utf-8").read()
assert src.rstrip().endswith("kit.main(grade)")
ns = {"__name__": "grade_probe"}
exec(compile(src.rstrip()[: -len("kit.main(grade)")], "grade.py", "exec"), ns)
compare, BAND = ns["compare"], ns["BAND"]
exp = json.load(open(os.path.join(TESTS, "expected", "visible.json")))
hw = exp["half_width"]


def base():
    keys = ("n_users", "pageviews", "clicks", "ctr", "diff", "ci_95", "srm_p", "srm_flag", "decision")
    return {k: json.loads(json.dumps(exp[k])) for k in keys}


def probe(name, should_pass, mutate=None, raw=None):
    d = base()
    if mutate:
        mutate(d)
    data = raw if raw is not None else json.dumps(d).encode()
    ok, _m = compare("probe", data, exp)
    return name, should_pass, ok


def setp(path, value):
    def f(d):
        cur = d
        for k in path[:-1]:
            cur = cur[k]
        cur[path[-1]] = value
    return f


probes = [
    probe("reference values as given", True),
    probe("keys in another order, extra keys, indent", True,
          raw=json.dumps(dict(reversed(list(base().items())), note="x", p_value=0.5), indent=4).encode()),
    probe("UTF-8 BOM and trailing newline", True, raw=b"\xef\xbb\xbf" + json.dumps(base()).encode() + b"\n"),
    probe(f"counts written as floats ({float(exp['n_users']['A'])})", True,
          lambda d: d["n_users"].update({k: float(v) for k, v in d["n_users"].items()})),
    probe("srm_flag as 0", True, setp(["srm_flag"], 0)),
    probe("decision with capitals and spaces ' No_Ship '", True, setp(["decision"], " No_Ship ")),
    probe("ctr off by 5e-10", True, setp(["ctr", "A"], exp["ctr"]["A"] + 5e-10)),
    probe(f"lower bound off by {BAND - 0.01:.2f} half-widths", True, setp(["ci_95", 0], exp["ci_95"][0] - (BAND - 0.01) * hw)),
    probe("srm_p off by 0.9% relative", True, setp(["srm_p"], exp["srm_p"] * 1.009)),
    probe(f"lower bound off by {BAND + 0.01:.2f} half-widths", False, setp(["ci_95", 0], exp["ci_95"][0] - (BAND + 0.01) * hw)),
    probe("bounds swapped", False, lambda d: d.__setitem__("ci_95", d["ci_95"][::-1])),
    probe("ci_95 as an object", False, lambda d: d.__setitem__("ci_95", {"lower": d["ci_95"][0], "upper": d["ci_95"][1]})),
    probe("ctr off by 2e-9", False, setp(["ctr", "B"], exp["ctr"]["B"] + 2e-9)),
    probe("diff relative (lift) instead of absolute", False, setp(["diff"], exp["diff"] / exp["ctr"]["A"])),
    probe("n_users off by one", False, setp(["n_users", "A"], exp["n_users"]["A"] + 1)),
    probe(f"n_users {exp['n_users']['A'] + 0.5}", False, setp(["n_users", "A"], exp["n_users"]["A"] + 0.5)),
    probe("srm_p off by 2% relative", False, setp(["srm_p"], exp["srm_p"] * 1.02)),
    probe("srm_flag as the string 'false'", False, setp(["srm_flag"], "false")),
    probe("decision 'ship'", False, setp(["decision"], "ship")),
    probe("decision missing", False, lambda d: d.pop("decision")),
    probe("NaN in ctr", False, raw=json.dumps(base()).replace(str(exp["ctr"]["A"]), "NaN").encode()),
    probe("counts as booleans", False, setp(["n_users", "A"], True)),
    probe("empty file", False, raw=b""),
    probe("a JSON list", False, raw=b"[1, 2]"),
]
lines = ["# grader_probes.out.md (grader_probes.py)", "",
         f"compare() on the visible reference, band = {BAND}.", "",
         "| probe | should pass | passed | as expected |", "|---|---|---|---|"]
bad = 0
for name, should, ok in probes:
    bad += should != ok
    lines.append(f"| {name} | {should} | {ok} | {'yes' if should == ok else 'NO'} |")
lines += ["", "ALL AS EXPECTED" if not bad else f"{bad} PROBE(S) NOT AS EXPECTED"]
open(os.path.join(HERE, "grader_probes.out.md"), "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
sys.exit(1 if bad else 0)
