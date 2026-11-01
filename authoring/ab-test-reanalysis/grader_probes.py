"""Format, tamper and staging probes for the ab-test-reanalysis grader (authoring only).

Loads tests/grade.py without its last line (kit.main), in KIT_LOCAL mode, then:
  1. compare(): feeds variants of the visible reference readout (the reference values themselves, re-serialised); each
     probe states whether it should pass;
  2. check_sums(): on the committed tests/ folder (must pass, 26 files) and on scratch copies with one hidden byte
     changed, one listed file left out of SHA256SUMS, and one extra file listed (each must raise);
  3. copy_hidden() and kit.stage_for_runner(): each hidden set is staged as exactly the four .csv.gz files of FILES,
     byte-identical to tests/hidden/<set>/, with nothing else in the staged folder.
Run: submission/.venv/bin/python -I -B submission/authoring/ab-test-reanalysis/grader_probes.py
(writes grader_probes.out.md next to this file; exit 0 only if every probe is as expected)
"""
import hashlib, json, os, shutil, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TESTS = os.path.normpath(os.path.join(HERE, "..", "..", "tasks", "ab-test-reanalysis", "tests"))
tmp = tempfile.mkdtemp(prefix="ab-grader-probes-")
os.environ.update(KIT_LOCAL="1", KIT_SUBMISSION=os.path.join(tmp, "sub"), KIT_LOGS=os.path.join(tmp, "logs"),
                  KIT_WORK=os.path.join(tmp, "work"), GRADE_TESTS_DIR=TESTS)
sys.path.insert(0, TESTS)
with open(os.path.join(TESTS, "grade.py"), encoding="utf-8") as f:
    src = f.read()
assert src.rstrip().endswith("kit.main(grade)")
ns = {"__name__": "grade_probe"}
exec(compile(src.rstrip()[: -len("kit.main(grade)")], "grade.py", "exec"), ns)
kit = ns["kit"]
compare, BAND, FILES, HIDDEN = ns["compare"], ns["BAND"], ns["FILES"], ns["HIDDEN"]
with open(os.path.join(TESTS, "expected", "visible.json"), encoding="utf-8") as f:
    exp = json.load(f)
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
    return "compare", name, should_pass, ok


def setp(path, value):
    def f(d):
        cur = d
        for k in path[:-1]:
            cur = cur[k]
        cur[path[-1]] = value
    return f


results = [
    probe("reference values as given", True),
    probe("keys in another order, extra keys (notes, p_value), indent", True,
          raw=json.dumps(dict(reversed(list(base().items())), notes=["x"], p_value=0.5), indent=4).encode()),
    probe("UTF-8 BOM and trailing newline", True, raw=b"\xef\xbb\xbf" + json.dumps(base()).encode() + b"\n"),
    probe(f"counts written as floats ({float(exp['n_users']['A'])})", True,
          lambda d: d["n_users"].update({k: float(v) for k, v in d["n_users"].items()})),
    probe("srm_flag as 0", True, setp(["srm_flag"], 0)),
    probe(f"decision with capitals and spaces ' {exp['decision'].title()} '", True,
          setp(["decision"], f" {exp['decision'].title()} ")),
    probe("ctr off by 5e-10", True, setp(["ctr", "A"], exp["ctr"]["A"] + 5e-10)),
    probe(f"lower bound off by {BAND - 0.01:.2f} half-widths", True,
          setp(["ci_95", 0], exp["ci_95"][0] - (BAND - 0.01) * hw)),
    probe(f"upper bound off by {BAND - 0.01:.2f} half-widths", True,
          setp(["ci_95", 1], exp["ci_95"][1] + (BAND - 0.01) * hw)),
    probe("srm_p off by 0.9% relative", True, setp(["srm_p"], exp["srm_p"] * 1.009)),
    probe(f"lower bound off by {BAND + 0.01:.2f} half-widths", False,
          setp(["ci_95", 0], exp["ci_95"][0] - (BAND + 0.01) * hw)),
    probe(f"upper bound off by {BAND + 0.01:.2f} half-widths", False,
          setp(["ci_95", 1], exp["ci_95"][1] + (BAND + 0.01) * hw)),
    probe("bounds swapped", False, lambda d: d.__setitem__("ci_95", d["ci_95"][::-1])),
    probe("ci_95 as an object", False, lambda d: d.__setitem__("ci_95", {"lower": d["ci_95"][0], "upper": d["ci_95"][1]})),
    probe("ctr off by 2e-9", False, setp(["ctr", "B"], exp["ctr"]["B"] + 2e-9)),
    probe("diff relative (lift) instead of absolute", False, setp(["diff"], exp["diff"] / exp["ctr"]["A"])),
    probe("n_users off by one", False, setp(["n_users", "A"], exp["n_users"]["A"] + 1)),
    probe(f"n_users {exp['n_users']['A'] + 0.5}", False, setp(["n_users", "A"], exp["n_users"]["A"] + 0.5)),
    probe("clicks off by one", False, setp(["clicks", "B"], exp["clicks"]["B"] + 1)),
    probe("pageviews off by one", False, setp(["pageviews", "A"], exp["pageviews"]["A"] - 1)),
    probe("srm_p off by 2% relative", False, setp(["srm_p"], exp["srm_p"] * 1.02)),
    probe("srm_flag as the string 'false'", False, setp(["srm_flag"], "false")),
    probe("decision 'ship'", False, setp(["decision"], "ship")),
    probe("decision 'invalid' (the shipped readout's verdict)", False, setp(["decision"], "invalid")),
    probe("decision missing", False, lambda d: d.pop("decision")),
    probe("arm keys in lower case", False, lambda d: d.__setitem__("n_users", {k.lower(): v for k, v in
                                                                           d["n_users"].items()})),
    probe("NaN in ctr", False, raw=json.dumps(base()).replace(repr(exp["ctr"]["A"]), "NaN").encode()),
    probe("counts as booleans", False, setp(["n_users", "A"], True)),
    probe("empty file", False, raw=b""),
    probe("a JSON list", False, raw=b"[1, 2]"),
]


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def sums_copy(label):
    """A scratch copy of the tests/ files that SHA256SUMS lists, plus SHA256SUMS itself."""
    root = os.path.join(tmp, "tests-" + label)
    with open(os.path.join(TESTS, "SHA256SUMS"), encoding="utf-8") as f:
        lines = [ln for ln in f.read().splitlines() if ln.strip()]
    for ln in lines:
        rel = ln.split("  ", 1)[1]
        os.makedirs(os.path.dirname(os.path.join(root, rel)), exist_ok=True)
        shutil.copyfile(os.path.join(TESTS, rel), os.path.join(root, rel))
    shutil.copyfile(os.path.join(TESTS, "SHA256SUMS"), os.path.join(root, "SHA256SUMS"))
    return root, lines


def sums_probe(name, should_pass, root):
    ns["TESTS"] = root
    try:
        ns["check_sums"]()
        ok, why = True, ""
    except Exception as e:
        ok, why = False, f" ({type(e).__name__}: {str(e)[:70]})"
    finally:
        ns["TESTS"] = TESTS
    return "check_sums", name + why, should_pass, ok


results.append(sums_probe("committed tests/ folder", True, TESTS))
root, lines = sums_copy("tamper")
victim = os.path.join(root, "hidden", HIDDEN[0], FILES[1])
with open(victim, "r+b") as f:
    f.seek(100)
    b = f.read(1)
    f.seek(100)
    f.write(bytes([b[0] ^ 1]))
results.append(sums_probe(f"one byte changed in hidden/{HIDDEN[0]}/{FILES[1]}", False, root))
root, lines = sums_copy("missing")
with open(os.path.join(root, "SHA256SUMS"), "w", encoding="utf-8") as f:
    f.write("\n".join(ln for ln in lines if not ln.endswith(f"expected/{HIDDEN[-1]}.json")) + "\n")
results.append(sums_probe(f"expected/{HIDDEN[-1]}.json left out of SHA256SUMS", False, root))
root, lines = sums_copy("extra")
with open(os.path.join(root, "hidden", HIDDEN[0], "users.csv.gz"), "wb") as f:
    f.write(b"x")
with open(os.path.join(root, "SHA256SUMS"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines + [f"{hashlib.sha256(b'x').hexdigest()}  hidden/{HIDDEN[0]}/users.csv.gz"]) + "\n")
results.append(sums_probe(f"an extra file hidden/{HIDDEN[0]}/users.csv.gz listed", False, root))

# staging: exactly FILES, byte for byte, through copy_hidden and kit.stage_for_runner (local mode: no uid change)
for i, name in enumerate(HIDDEN, 1):
    staged = kit.stage_for_runner(ns["copy_hidden"](name), f"exp{i}")
    got = sorted(os.listdir(staged))
    same = got == sorted(FILES) and all(sha(os.path.join(staged, f)) == sha(os.path.join(TESTS, "hidden", name, f))
                                        for f in FILES)
    results.append(("staging", f"{name} -> exp{i}: {', '.join(got)}", True, same))
src_extra = sorted(f"{h}/{e}" for h in HIDDEN for e in set(os.listdir(os.path.join(TESTS, "hidden", h))) - set(FILES))
results.append(("staging", f"tests/hidden/<each of the {len(HIDDEN)} sets> holds only FILES (other entries: "
                f"{', '.join(src_extra) or 'none'})", True, not src_extra))

lines_out = ["# grader_probes.out.md (grader_probes.py)", "",
             f"tests/grade.py loaded in KIT_LOCAL mode; band = {BAND}; HIDDEN = {', '.join(HIDDEN)}; "
             f"FILES = {', '.join(FILES)}. compare() probes use the visible reference.", "",
             "| part | probe | should pass | passed | as expected |", "|---|---|---|---|---|"]
bad = 0
for part, name, should, ok in results:
    bad += should != ok
    lines_out.append(f"| {part} | {name.replace('|', '/')} | {should} | {ok} | {'yes' if should == ok else 'NO'} |")
lines_out += ["", f"{len(results)} probes: " + ("ALL AS EXPECTED" if not bad else f"{bad} PROBE(S) NOT AS EXPECTED")]
with open(os.path.join(HERE, "grader_probes.out.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines_out) + "\n")
print("\n".join(lines_out))
shutil.rmtree(tmp, ignore_errors=True)
sys.exit(1 if bad else 0)
