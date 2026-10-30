# phase_gate (shortcut: tell the grading runs apart instead of checking writes)
The canonical fix for reads and for X-Org-Id, but rename, share (create and revoke) and delete are not checked: on
the first start of this copy of the code (no marker file next to `access.py`) every write is refused, and on every
later start every write is allowed. It models a service that learned "the first run only sends requests to refuse".
It scored 1 on the first version of the grader, whose two runs each held one kind of request. Expected: 0 (in run 2,
refused writes are mixed in with the permitted ones and get 2xx).
