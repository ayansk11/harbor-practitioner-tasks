| Variant | max abs diff, visible (mm/day) | max abs diff, hidden (mm/day) | rows > 0.01 | rows > 0.02 | rows > 0.03 | rows > 0.05 |
|---|---|---|---|---|---|---|
| reference B (independent code) | 0.000000 | 0.000000 | 0 | 0 | 0 | 0 |
| shipped fao56.py + canonical fix, unrounded | 0.000000 | 0.000000 | 0 | 0 | 0 | 0 |
| Eq. 47 factor rounded to 3 decimals | 0.000858 | 0.001674 | 0 | 0 | 0 | 0 |
| Eq. 47 factor rounded to 2 decimals | 0.010060 | 0.018051 | 182 | 0 | 0 | 0 |
| 273.15 instead of 273.16 in Eq. 39 | 0.000286 | 0.000321 | 0 | 0 | 0 | 0 |
| T + 273.16 instead of T + 273 in Eq. 6 | 0.003952 | 0.005077 | 0 | 0 | 0 | 0 |
| exact gamma = cp P / (eps lambda) | 0.000858 | 0.001291 | 0 | 0 | 0 | 0 |
| arctan sunset angle (Eq. 26) | 0.000000 | 0.000000 | 0 | 0 | 0 | 0 |
| output rounded to 3 decimals | 0.000500 | 0.000500 | 0 | 0 | 0 | 0 |
| output rounded to 2 decimals | 0.005000 | 0.004999 | 0 | 0 | 0 | 0 |
| all honest variants at once (2-decimal factor, 2-decimal output) | 0.012026 | 0.027656 | 378 | 22 | 0 | 0 |
| MISTAKE: Rso by Eq. 36 (no altitude term) | 0.113692 | 0.106290 | 3309 | 2369 | 1254 | 569 |
| MISTAKE: sea-level pressure everywhere | 0.261314 | 0.247549 | 3167 | 2241 | 1657 | 927 |
| MISTAKE: es from Tmean (not Eq. 12) | 0.769708 | 1.163006 | 6571 | 6571 | 6570 | 6527 |
| MISTAKE: ea from RHmean (Eq. 19, not Eq. 17) | 0.991739 | 1.097633 | 3651 | 3646 | 3631 | 3585 |
| MISTAKE: Rs/Rso not capped at 1 | 0.044715 | 0.085077 | 19 | 17 | 13 | 8 |
| MISTAKE: W/m2 x 1/11.6 instead of x 0.0864 | 0.012727 | 0.011922 | 3 | 0 | 0 | 0 |
| MISTAKE: nearest of the 2, 3, 10 m factors | 0.000858 | 0.433895 | 2549 | 2456 | 2171 | 1734 |
| MISTAKE: 0.75 for every height other than 2 m | 0.751104 | 1.139117 | 3650 | 3596 | 3426 | 3027 |
| MISTAKE: wind height clamped to 2-12 m before Eq. 47 | 0.000000 | 0.433329 | 731 | 719 | 687 | 562 |
| MISTAKE: divisor 366 in a leap year (Eqs. 23, 24) | 0.000000 | 0.011403 | 5 | 0 | 0 | 0 |
| MISTAKE: day of year clipped at 365 | 0.000000 | 0.001480 | 0 | 0 | 0 | 0 |
