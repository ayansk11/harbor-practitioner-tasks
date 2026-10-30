# F. offset_cursor (plausible wrong fix; expected reward 0)
LIMIT/OFFSET with the offset inside an opaque cursor. Correct on a database nobody writes to; when orders are inserted
during an export, rows shift and later pages repeat orders. Killed by c4 (inserts) only: the proof that c4 is needed.
Applied by `apply.py`.
