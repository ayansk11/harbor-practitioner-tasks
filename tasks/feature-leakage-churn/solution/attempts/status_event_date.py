"""Wrong: the status from v3's rule, the latest snapshot dated before the prediction's UTC date (`snapshot_date <
date(t)`), whether or not its export partition had landed. Everything else as the canonical solution."""
from _common import use_canonical

use_canonical(skip=("status.py",))
