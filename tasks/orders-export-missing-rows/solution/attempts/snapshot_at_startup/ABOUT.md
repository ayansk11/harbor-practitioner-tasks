# G. snapshot_at_startup (shortcut; expected reward 0)
Loads every order at start-up and pages over the sorted list with a correct (created_at, id) cursor. Orders inserted
later never appear (new export, count). Killed by c4 (inserts) only. Files: `app/orders_service/{app,snapshot}.py`.
