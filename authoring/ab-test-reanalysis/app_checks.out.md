# app_checks (app_checks.py)

Written by app_checks.py (deterministic: no clock times). The visible export is environment/app/data.

## Part 1: figures quoted in instruction.md and PM_NOTE.md
- shipped readout users: A 16,570, B 15,722; B short by 5.12% of A; SRM p 2.37e-06
- assignment dashboard users: A 16,935, B 17,165 (49.66% / 50.34%)
- team dashboard: rows A 179,760, B 184,884; CTR A 9.8220%, B 11.0318%; B +12.317% relative

Cross-checks with generation_report.json (visible paths):
- PASS: shipped users equal paths.shipped.n_users
- PASS: dashboard users equal paths.all_assigned.n_users
- PASS: team dashboard CTRs equal paths.dashboard_all_rows
- PASS: shipped SRM p equals paths

The figures as typed in the two files (each string must occur in the file):
- PASS: PM_NOTE.md contains "16,570 users in A"
- PASS: PM_NOTE.md contains "15,722 in B"
- PASS: PM_NOTE.md contains "about 5% fewer in B"
- PASS: PM_NOTE.md contains "16,935 users in A and 17,165 in B"
- PASS: PM_NOTE.md contains "(49.7% / 50.3%)"
- PASS: PM_NOTE.md contains "11.03% in B against 9.82% in A"
- PASS: PM_NOTE.md contains "B is 12.3% higher"
- PASS: instruction.md contains "about 5% fewer users in B than in A"
- PASS: instruction.md contains "click-through 12.3% above A's"

## Part 2: stale-account check
Each command runs on the visible export with a = assignments, f = bot_flags, pv = pageviews, mc = module_clicks
(all read as text), ts = ISO 8601 text to UTC instants.

### R1: README.md: "filters.py applies the platform's bot screening (bot_flags.csv.gz) to both arms"
Command:

    f.merge(a.drop_duplicates(), on="user_id").groupby(["rule", "variant"]).user_id.nunique().unstack()

Output:

    variant       A     B
    rule                 
    ua_crawler  365   363
    velocity      9  1087

What it shows: one rule (ua_crawler, a client property) flags users of both arms alike; velocity flags users of one arm almost only: it reacts to what that arm's module makes users do, so applying it makes the arms unequal.
- PASS: R1 output refutes the account

### R2: README.md: "a click is a pageview's clicked value, the module click flag"
Command:

    pv[pv.clicked == "1"].assign(item=lambda x: x.pageview_id.isin(mc.loc[mc.target.str.startswith("item:"), "pageview_id"])).merge(a.drop_duplicates()[["user_id", "variant"]], on="user_id").groupby(["variant", "item"]).size().unstack()

Output:

    item     False  True 
    variant              
    A          403  17253
    B         1462  18934

What it shows: clicked = 1 also on pageviews on which no related product was opened (item = False: arrow taps or See all only), in both arms and far more in B; plan section 4 counts a pageview only when a related product was opened.
- PASS: R2 output refutes the account

### R3: abtest/filters.py docstring: "every flagged user is bot traffic: crawlers and, since SEC-219, click-fraud bots (rule velocity); plan section 3"
Command:

    f[f.rule == "velocity"].merge(a.drop_duplicates(), on="user_id").assign(crawler=lambda x: x.user_id.isin(f.loc[f.rule == "ua_crawler", "user_id"]), after=lambda x: ts(x.flagged_at) > ts(x.assigned_at)).groupby(["crawler", "variant", "method"]).agg(users=("user_id", "nunique"), flags=("user_id", "size"), after_assignment=("after", "mean"))

Output:

                            users  flags  after_assignment
    crawler variant method                                
    False   B       hash     1080   1136               1.0
    True    A       hash        9     11               1.0
            B       hash        7      8               1.0

What it shows: the users velocity flags without a ua_crawler flag are randomized (hash) users of B only, every flag raised after the assignment: excluded for what the users did during the experiment, which plan section 3 rules out; the click-fraud bots it catches are also ua_crawler users.
- PASS: R3 output refutes the account

### R4: PM_NOTE.md: "the assignment dashboard shows a clean 50/50 split"
Command:

    a.drop_duplicates().groupby(["method", "variant"]).user_id.nunique()

Output:

    method    variant
    hash      A          16935
              B          17065
    override  B            100

What it shows: the dashboard's B includes the override accounts (variant set by hand, not randomized; plan section 3 leaves the accounts out); the randomized (hash) users are balanced, so the readout's imbalance is made after the assignment.
- PASS: R4 output refutes the account

### R5: PM_NOTE.md: "the team dashboard shows B's click-through 12.3% above A's"
Command:

    pv.merge(a.drop_duplicates()[["user_id", "variant", "method"]], on="user_id").assign(clicked=lambda x: x.clicked.astype(int), product_opened=lambda x: x.pageview_id.isin(mc.loc[mc.target.str.startswith("item:"), "pageview_id"])).groupby(["method", "variant"]).agg(rows=("clicked", "size"), clicked=("clicked", "sum"), product_opened=("product_opened", "sum"))

Output:

                        rows  clicked  product_opened
    method   variant                                 
    hash     A        179760    17656           17253
             B        181046    18989           17536
    override B          3838     1407            1398

Relative lift of B (CTR_B / CTR_A - 1): every row, clicked +12.32% (the dashboard); every row, product_opened +6.70%; hash rows, product_opened +0.92%. Product-open rate of the override rows: 36.4%.

What it shows: the dashboard's lead of B is made of clicks that open no product (clicked against product_opened) and of the override accounts in B, which open products at several times the rate of anyone else; among the randomized (hash) users, B's lead in product opens, the plan's click (section 4), is a small fraction of the dashboard's lead.
- PASS: R5 output refutes the account

## Part 3: the shipped code on the six exports
- PASS: visible: shipped readout = paths.shipped (decision invalid, n_users 16570/15722, srm_p 2.37e-06)
- PASS: output/result.json equals a fresh run, byte for byte
- PASS: h_null: shipped readout = paths.shipped (decision invalid, n_users 14967/15844, srm_p 5.84e-07)
- PASS: h_pos: shipped readout = paths.shipped (decision invalid, n_users 15707/14884, srm_p 2.53e-06)
- PASS: h_srm: shipped readout = paths.shipped (decision invalid, n_users 17208/15733, srm_p 4.4e-16)
- PASS: h_plain: shipped readout = paths.shipped (decision ship, n_users 14356/14155, srm_p 0.234)
- PASS: h_neg: shipped readout = paths.shipped (decision invalid, n_users 16557/14672, srm_p 1.46e-26)

## Part 4: claims of the shipped docs, on all six exports
The docs say they apply to every export of this layout. Claims also asserted by data_checks.py ((a) to (l)) are
not repeated here; these are the others (DATA_DICTIONARY, TRACKING, BOT_SCREENING, LAUNCH_EXP-2291).
- PASS: visible: one row per user after exact repeats
- PASS: visible: variant in {A, B}, method in {hash, override}
- PASS: visible: every flagged user, pageview user and event user is assigned
- PASS: visible: rules are ua_crawler or velocity; one ua_crawler row per flagged user
- PASS: visible: pageview_id unique; every pageview before the end
- PASS: visible: no pageview more than 72.1 h before its user's assigned_at
- PASS: visible: every event's pageview_id is a pageview of the export
- PASS: visible: arrows (nav:) in at most one arm
- PASS: visible: nothing in the export after 2026-09-15 06:00Z
- PASS: visible: DICT pageviews: assigned users with no pageview at assigned_at (15604) and with no pageview row (2815) both occur
- PASS: visible: DICT module_clicks: identical rows (362) are all nav: taps; the velocity rule over every row = the 1155 velocity rows (over de-duplicated rows: 19 user-days differ)
- PASS: visible: LAUNCH: 100 override accounts, all in B, assigned from 2026-09-03 00:00Z
- PASS: visible: LAUNCH: start 2026-09-01 00:00Z, end 2026-09-15 00:00Z: every assigned_at inside
- PASS: h_null: one row per user after exact repeats
- PASS: h_null: variant in {A, B}, method in {hash, override}
- PASS: h_null: every flagged user, pageview user and event user is assigned
- PASS: h_null: rules are ua_crawler or velocity; one ua_crawler row per flagged user
- PASS: h_null: pageview_id unique; every pageview before the end
- PASS: h_null: no pageview more than 72.1 h before its user's assigned_at
- PASS: h_null: every event's pageview_id is a pageview of the export
- PASS: h_null: arrows (nav:) in at most one arm
- PASS: h_null: nothing in the export after 2026-09-15 06:00Z
- PASS: h_null: DICT pageviews: assigned users with no pageview at assigned_at (16821) and with no pageview row (5421) both occur
- PASS: h_null: DICT module_clicks: identical rows (312) are all nav: taps; the velocity rule over every row = the 947 velocity rows (over de-duplicated rows: 9 user-days differ)
- PASS: h_pos: one row per user after exact repeats
- PASS: h_pos: variant in {A, B}, method in {hash, override}
- PASS: h_pos: every flagged user, pageview user and event user is assigned
- PASS: h_pos: rules are ua_crawler or velocity; one ua_crawler row per flagged user
- PASS: h_pos: pageview_id unique; every pageview before the end
- PASS: h_pos: no pageview more than 72.1 h before its user's assigned_at
- PASS: h_pos: every event's pageview_id is a pageview of the export
- PASS: h_pos: arrows (nav:) in at most one arm
- PASS: h_pos: nothing in the export after 2026-09-15 06:00Z
- PASS: h_pos: DICT pageviews: assigned users with no pageview at assigned_at (14840) and with no pageview row (2652) both occur
- PASS: h_pos: DICT module_clicks: identical rows (290) are all nav: taps; the velocity rule over every row = the 985 velocity rows (over de-duplicated rows: 15 user-days differ)
- PASS: h_srm: one row per user after exact repeats
- PASS: h_srm: variant in {A, B}, method in {hash, override}
- PASS: h_srm: every flagged user, pageview user and event user is assigned
- PASS: h_srm: rules are ua_crawler or velocity; one ua_crawler row per flagged user
- PASS: h_srm: pageview_id unique; every pageview before the end
- PASS: h_srm: no pageview more than 72.1 h before its user's assigned_at
- PASS: h_srm: every event's pageview_id is a pageview of the export
- PASS: h_srm: arrows (nav:) in at most one arm
- PASS: h_srm: nothing in the export after 2026-09-15 06:00Z
- PASS: h_srm: DICT pageviews: assigned users with no pageview at assigned_at (15950) and with no pageview row (2828) both occur
- PASS: h_srm: DICT module_clicks: identical rows (360) are all nav: taps; the velocity rule over every row = the 1125 velocity rows (over de-duplicated rows: 17 user-days differ)
- PASS: h_plain: one row per user after exact repeats
- PASS: h_plain: variant in {A, B}, method in {hash, override}
- PASS: h_plain: every flagged user, pageview user and event user is assigned
- PASS: h_plain: rules are ua_crawler or velocity; one ua_crawler row per flagged user
- PASS: h_plain: pageview_id unique; every pageview before the end
- PASS: h_plain: no pageview more than 72.1 h before its user's assigned_at
- PASS: h_plain: every event's pageview_id is a pageview of the export
- PASS: h_plain: arrows (nav:) in at most one arm
- PASS: h_plain: nothing in the export after 2026-09-15 06:00Z
- PASS: h_plain: DICT pageviews: assigned users with no pageview at assigned_at (14433) and with no pageview row (3325) both occur
- PASS: h_plain: DICT module_clicks: identical rows (0) are all nav: taps; the velocity rule over every row = the 38 velocity rows (over de-duplicated rows: 0 user-days differ)
- PASS: h_neg: one row per user after exact repeats
- PASS: h_neg: variant in {A, B}, method in {hash, override}
- PASS: h_neg: every flagged user, pageview user and event user is assigned
- PASS: h_neg: rules are ua_crawler or velocity; one ua_crawler row per flagged user
- PASS: h_neg: pageview_id unique; every pageview before the end
- PASS: h_neg: no pageview more than 72.1 h before its user's assigned_at
- PASS: h_neg: every event's pageview_id is a pageview of the export
- PASS: h_neg: arrows (nav:) in at most one arm
- PASS: h_neg: nothing in the export after 2026-09-15 06:00Z
- PASS: h_neg: DICT pageviews: assigned users with no pageview at assigned_at (15774) and with no pageview row (2891) both occur
- PASS: h_neg: DICT module_clicks: identical rows (702) are all nav: taps; the velocity rule over every row = the 2262 velocity rows (over de-duplicated rows: 30 user-days differ)

Result: all checks passed.
