# grader_probes.out.md (grader_probes.py)

tests/grade.py loaded in KIT_LOCAL mode; band = 0.25; HIDDEN = h_null, h_pos, h_srm, h_plain, h_neg; FILES = assignments.csv.gz, bot_flags.csv.gz, pageviews.csv.gz, module_clicks.csv.gz. compare() probes use the visible reference.

| part | probe | should pass | passed | as expected |
|---|---|---|---|---|
| compare | reference values as given | True | True | yes |
| compare | keys in another order, extra keys (notes, p_value), indent | True | True | yes |
| compare | UTF-8 BOM and trailing newline | True | True | yes |
| compare | counts written as floats (16570.0) | True | True | yes |
| compare | srm_flag as 0 | True | True | yes |
| compare | decision with capitals and spaces ' No_Ship ' | True | True | yes |
| compare | ctr off by 5e-10 | True | True | yes |
| compare | lower bound off by 0.24 half-widths | True | True | yes |
| compare | upper bound off by 0.24 half-widths | True | True | yes |
| compare | srm_p off by 0.9% relative | True | True | yes |
| compare | lower bound off by 0.26 half-widths | False | False | yes |
| compare | upper bound off by 0.26 half-widths | False | False | yes |
| compare | bounds swapped | False | False | yes |
| compare | ci_95 as an object | False | False | yes |
| compare | ctr off by 2e-9 | False | False | yes |
| compare | diff relative (lift) instead of absolute | False | False | yes |
| compare | n_users off by one | False | False | yes |
| compare | n_users 16570.5 | False | False | yes |
| compare | clicks off by one | False | False | yes |
| compare | pageviews off by one | False | False | yes |
| compare | srm_p off by 2% relative | False | False | yes |
| compare | srm_flag as the string 'false' | False | False | yes |
| compare | decision 'ship' | False | False | yes |
| compare | decision 'invalid' (the shipped readout's verdict) | False | False | yes |
| compare | decision missing | False | False | yes |
| compare | arm keys in lower case | False | False | yes |
| compare | NaN in ctr | False | False | yes |
| compare | counts as booleans | False | False | yes |
| compare | empty file | False | False | yes |
| compare | a JSON list | False | False | yes |
| check_sums | committed tests/ folder | True | True | yes |
| check_sums | one byte changed in hidden/h_null/bot_flags.csv.gz (RuntimeError: SHA256 mismatch for tests/hidden/h_null/bot_flags.csv.gz) | False | False | yes |
| check_sums | expected/h_neg.json left out of SHA256SUMS (RuntimeError: SHA256SUMS does not list exactly the graded files: missing ['expected/) | False | False | yes |
| check_sums | an extra file hidden/h_null/users.csv.gz listed (RuntimeError: SHA256SUMS does not list exactly the graded files: missing [], extra [) | False | False | yes |
| staging | h_null -> exp1: assignments.csv.gz, bot_flags.csv.gz, module_clicks.csv.gz, pageviews.csv.gz | True | True | yes |
| staging | h_pos -> exp2: assignments.csv.gz, bot_flags.csv.gz, module_clicks.csv.gz, pageviews.csv.gz | True | True | yes |
| staging | h_srm -> exp3: assignments.csv.gz, bot_flags.csv.gz, module_clicks.csv.gz, pageviews.csv.gz | True | True | yes |
| staging | h_plain -> exp4: assignments.csv.gz, bot_flags.csv.gz, module_clicks.csv.gz, pageviews.csv.gz | True | True | yes |
| staging | h_neg -> exp5: assignments.csv.gz, bot_flags.csv.gz, module_clicks.csv.gz, pageviews.csv.gz | True | True | yes |
| staging | tests/hidden/<each of the 5 sets> holds only FILES (other entries: none) | True | True | yes |

40 probes: ALL AS EXPECTED
