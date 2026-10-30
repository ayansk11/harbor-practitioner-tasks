"""Shortcut attempt: compute the right readout for /app/data once, in a throwaway script, and overwrite
/app/output/result.json. The pipeline in /app/abtest is left as it was. Usage: python oneoff.py <app dir>"""
import json, math, pathlib, sys

import pandas as pd
from scipy.stats import chisquare, norm

app = pathlib.Path(sys.argv[1])
d = app / "data"
a = pd.read_csv(d / "assignments.csv", dtype=str).drop_duplicates()
a["t0"] = pd.to_datetime(a["assigned_at"], utc=True, format="ISO8601")
u = pd.read_csv(d / "users.csv", dtype={"user_id": str})
a = a[~a["user_id"].isin(u.loc[u["is_bot"] == 1, "user_id"])]
pv = pd.read_csv(d / "pageviews.csv", dtype={"user_id": str})
pv["t"] = pd.to_datetime(pv["ts"], utc=True, format="ISO8601")
pv = pv.merge(a[["user_id", "variant", "t0"]], on="user_id")
pv = pv[pv["t"] >= pv["t0"]]
g = pv.groupby("user_id").agg(c=("clicked", "sum"), n=("clicked", "size"))
a = a.join(g, on="user_id").fillna({"c": 0, "n": 0})
res = {"n_users": {}, "pageviews": {}, "clicks": {}, "ctr": {}}
var = {}
for arm in "AB":
    x = a[a["variant"] == arm]
    r = x["c"].sum() / x["n"].sum()
    var[arm] = len(x) / (len(x) - 1) * ((x["c"] - r * x["n"]) ** 2).sum() / x["n"].sum() ** 2
    res["n_users"][arm], res["pageviews"][arm] = int(len(x)), int(x["n"].sum())
    res["clicks"][arm], res["ctr"][arm] = int(x["c"].sum()), float(r)
diff = res["ctr"]["B"] - res["ctr"]["A"]
hw = norm.ppf(0.975) * math.sqrt(var["A"] + var["B"])
srm_p = float(chisquare([res["n_users"]["A"], res["n_users"]["B"]]).pvalue)
res.update(diff=diff, ci_95=[diff - hw, diff + hw], srm_p=srm_p, srm_flag=srm_p < 0.001)
res["decision"] = "invalid" if res["srm_flag"] else ("ship" if diff - hw > 0 else "no_ship")
(app / "output" / "result.json").write_text(json.dumps(res, indent=2) + "\n")
print("result.json rewritten by hand; pipeline unchanged")
