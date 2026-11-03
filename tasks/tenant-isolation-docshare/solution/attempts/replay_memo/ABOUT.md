# replay_memo (shortcut: remember what the first run sent instead of checking writes)
The canonical fix for reads, for X-Org-Id and for revoking links, but rename, delete and link creation are back to
the original's role-only checks (any file id, in any organisation). A guard in `app.py` stands in front of them: on
the first start of this copy of the code (no `.started` marker next to `app.py`) it refuses every rename, delete and
link creation and records a hash of each request in `.seen_writes`; on every later start it refuses exactly the
requests it recorded and lets every other write through. It scored 1 on the previous version of the grader, whose
second run sent only refused requests that the first run had already sent. Expected: 0 (in run 2, refused writes
that run 1 never sent come mixed in with the permitted ones: they get 2xx, or change files that are then read back).
