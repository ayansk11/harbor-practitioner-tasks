# gen_data.py output (python 3.12.13, sqlite 3.53.4)

## visible database (seed 317): 48213 orders, 4600 customers, 962 same-second groups (largest 62)
- buggy export at limit 200: 47961 rows, 252 missing
- buggy walk at limit 50: 916 missing
- buggy walk at limit 100: 466 missing
- buggy walk at limit 500: 84 missing
- support tool (customer listing at limit 20): wholesale account 5 has 61 orders, the buggy listing shows 20

## hidden database (seed 90210): 30000 orders, 3100 customers, 867 same-second groups (largest 380; sizes >= 100: [102, 103, 110, 120, 126, 133, 135, 136, 142, 149, 153, 154, 161, 173, 176, 181, 192, 199, 202, 300, 380])
- same-second groups that mix an old low id with a backfilled high id: 302
- rows whose position differs between id order and created_at order: 29996
- buggy walk /orders limit 50 prefix None: 4209 missing
- buggy walk /orders limit 200 prefix None: 1349 missing
- buggy walk /orders limit 500 prefix None: 924 missing
- buggy walk /orders limit 7 prefix 5000: 1626 missing
- buggy walk /orders limit 1 prefix 2000: 1370 missing
- newest 2000 rows hold 23 same-second groups (largest 380)
- test customers (orders, rows the buggy walks lose at limits (3, 20)): 6: 413 orders, 736 lost, 16: 281 orders, 474 lost, 1: 242 orders, 409 lost, 27: 211 orders, 364 lost, 4: 196 orders, 342 lost, 35: 190 orders, 341 lost, 441: 53 orders, 0 lost, 456: 17 orders, 0 lost, 1645: 26 orders, 0 lost, 2063: 23 orders, 1 lost
- empty customer 320, unknown customer 4100, 300 sample ids, /orders insert batches [25, 25] after pages [3, 10] at limit 100, customer 6 insert batches [3, 3] after pages [2, 5] at limit 3
- inserted orders by channel: {'edi_import': 10, 'pos': 4, 'pos_backfill': 35, 'web': 7}; ids 30001 to 30056
- 30000 orders = 600 full pages of 50 + 0
- 30000 orders = 300 full pages of 100 + 0
- 30000 orders = 150 full pages of 200 + 0

8 files listed in tests/SHA256SUMS
