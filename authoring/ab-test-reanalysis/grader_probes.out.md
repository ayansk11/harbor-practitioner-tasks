# grader_probes.out.md (grader_probes.py)

compare() on the visible reference, band = 0.25.

| probe | should pass | passed | as expected |
|---|---|---|---|
| reference values as given | True | True | yes |
| keys in another order, extra keys, indent | True | True | yes |
| UTF-8 BOM and trailing newline | True | True | yes |
| counts written as floats (19612.0) | True | True | yes |
| srm_flag as 0 | True | True | yes |
| decision with capitals and spaces ' No_Ship ' | True | True | yes |
| ctr off by 5e-10 | True | True | yes |
| lower bound off by 0.24 half-widths | True | True | yes |
| srm_p off by 0.9% relative | True | True | yes |
| lower bound off by 0.26 half-widths | False | False | yes |
| bounds swapped | False | False | yes |
| ci_95 as an object | False | False | yes |
| ctr off by 2e-9 | False | False | yes |
| diff relative (lift) instead of absolute | False | False | yes |
| n_users off by one | False | False | yes |
| n_users 19612.5 | False | False | yes |
| srm_p off by 2% relative | False | False | yes |
| srm_flag as the string 'false' | False | False | yes |
| decision 'ship' | False | False | yes |
| decision missing | False | False | yes |
| NaN in ctr | False | False | yes |
| counts as booleans | False | False | yes |
| empty file | False | False | yes |
| a JSON list | False | False | yes |

ALL AS EXPECTED
