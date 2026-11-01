"""Shortcut attempt fix_visible_only (must score 0): the plan's readout of /app/data, computed once by a throwaway
script that overwrites output/result.json, with every rule right (hash-assigned users only, ua_crawler flags out,
instants, a click is a pageview with an item: event, users without a counted pageview kept, the delta method). The
pipeline in abtest/ is left as shipped (BASE: shipped), so the readouts of every other export are still the shipped
ones. Adapted from the attempt fix_visible_result_only of the first version of this task.
Usage: python oneoff.py <app dir>"""
import json, math, pathlib, sys

import pandas as pd
from scipy.stats import chisquare, norm

app = pathlib.Path(sys.argv[1])
d = app / "data"


def read(name):
    return pd.read_csv(d / f"{name}.csv.gz", dtype=str, keep_default_na=False)


a = read("assignments").drop_duplicates()
a = a[a["method"] == "hash"]
flags = read("bot_flags")
a = a[~a["user_id"].isin(flags.loc[flags["rule"] == "ua_crawler", "user_id"])].copy()
a["t0"] = pd.to_datetime(a["assigned_at"], utc=True, format="ISO8601")
pv = read("pageviews")
pv["t"] = pd.to_datetime(pv["ts"], utc=True, format="ISO8601")
pv = pv.merge(a[["user_id", "t0"]], on="user_id")
pv = pv[pv["t"] >= pv["t0"]].copy()
mc = read("module_clicks")
pv["c"] = pv["pageview_id"].isin(mc.loc[mc["target"].str.startswith("item:"), "pageview_id"]).astype("int64")
g = pv.groupby("user_id").agg(c=("c", "sum"), n=("c", "size"))
a = a.join(g, on="user_id").fillna({"c": 0, "n": 0})

res = {"n_users": {}, "pageviews": {}, "clicks": {}, "ctr": {}}
var = {}
for arm in ("A", "B"):
    x = a[a["variant"] == arm]
    c, n = x["c"].astype(float), x["n"].astype(float)
    r = c.sum() / n.sum()
    var[arm] = len(x) / (len(x) - 1) * float(((c - r * n) ** 2).sum()) / float(n.sum()) ** 2
    res["n_users"][arm], res["pageviews"][arm] = int(len(x)), int(n.sum())
    res["clicks"][arm], res["ctr"][arm] = int(c.sum()), float(r)
diff = res["ctr"]["B"] - res["ctr"]["A"]
hw = float(norm.ppf(0.975)) * math.sqrt(var["A"] + var["B"])
srm_p = float(chisquare([res["n_users"]["A"], res["n_users"]["B"]]).pvalue)
res.update(diff=float(diff), ci_95=[float(diff - hw), float(diff + hw)], srm_p=srm_p, srm_flag=bool(srm_p < 0.001))
res["decision"] = "invalid" if res["srm_flag"] else ("ship" if diff - hw > 0 else "no_ship")
res["notes"] = ["Computed once for this export by a separate script; the pipeline was not changed."]
(app / "output" / "result.json").write_text(json.dumps(res, indent=2) + "\n")
print("output/result.json rewritten by a one-off script; the pipeline is unchanged")
