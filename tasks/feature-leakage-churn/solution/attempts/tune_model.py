"""Wrong fix: treat the gap as overfitting; stronger regularisation and shallower trees in train.py (the incident
says it did not help), the v3 features untouched."""
from _common import edit

edit("train.py", '''    ap.add_argument("--l2", type=float, default=1.0, help="L2 regularization")
    ap.add_argument("--max-depth", type=int, default=4)''', '''    ap.add_argument("--l2", type=float, default=50.0, help="L2 regularization")
    ap.add_argument("--max-depth", type=int, default=2)''')
