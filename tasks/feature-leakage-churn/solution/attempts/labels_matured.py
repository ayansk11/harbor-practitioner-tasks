"""Wrong: te_district from v3's label rule, the labels whose 30-day window closed before t (as_of + 30 days < t),
not the label rows the nightly label_job had loaded before t (`_loaded_at`). Everything else as the canonical
solution."""
from _common import use_canonical

use_canonical(skip=("encoding.py",))
