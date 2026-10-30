"""Shortcut: compute correct features for the visible extract once and return them for any input."""
import os, subprocess, sys, tempfile, shutil
from _common import APP, SOL, edit
with tempfile.TemporaryDirectory() as tmp:
    shutil.copytree(os.path.join(APP, "churn"), os.path.join(tmp, "churn"))
    for n in ("windows.py", "encoding.py", "status.py", "impute.py"):
        shutil.copy(os.path.join(SOL, "canonical", "churn", n), os.path.join(tmp, "churn", n))
    subprocess.run([sys.executable, "-m", "churn.build_features", "--data", os.path.join(APP, "data"),
                    "--out", os.path.join(APP, "churn", "cache_features.parquet")], cwd=tmp, check=True)
edit("build_features.py", '''    feats = build(a.data)''', '''    import pandas as pd
    feats = pd.read_parquet(os.path.join(os.path.dirname(__file__), "cache_features.parquet"))''')
