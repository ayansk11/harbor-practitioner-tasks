"""Wrong fix: status as of the prediction's date, including the snapshot dated date(t) (it describes the end of that
day, after t)."""
from _common import use_canonical, edit
use_canonical("windows.py", "encoding.py", "status.py", "impute.py")
edit("status.py", '''                      allow_exact_matches=False)''', '''                      allow_exact_matches=True)''')
