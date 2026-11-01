# Tracking: the related-items module

Data platform documentation. It applies to every experiment export of this layout.

## module_click events
The related-items module on product pages logs one `module_click` event per click on any clickable element inside the
module. Each event records the pageview it happened on, the user, the time of the click and the clicked element's
`data-target` value. Exports hold these events in `module_clicks.csv.gz`, and `pageviews.clicked` is derived from
them (`docs/DATA_DICTIONARY.md`).

| `data-target` | Element | What a click on it does |
|---|---|---|
| `item:<product_id>` | a product card | opens that product's page |
| `nav:prev`, `nav:next` | the previous and next arrows of the v2 carousel | scroll the carousel; open nothing |
| `link:all` | the "See all" link, in every module version from 2026-09-08 | opens the list page of all related items |

## Module versions
| Version | What the module shows |
|---|---|
| v1 | the current module: a row of six product cards |
| v2 | related items v2 (RI-311): a carousel of 12 product cards with previous and next arrows |

Other experiments test other layouts or rankings of the cards; v2 is the only version with arrows. Since 2026-09-08
every version also shows the "See all" link.

The module version is set per experiment arm: from a user's assignment on, every product pageview of the user shows
the version of the user's arm, as the experiment's launch record sets it (EXP-2291: v1 in A, v2 in B). Before the
assignment, every user sees v1.

## Changelog
- 2025-04-14: `module_click` events logged for every clickable element of the module.
- 2026-09-01: v2 available to experiments, per arm (EXP-2291 shows it in arm B).
- 2026-09-08: "See all" link (`link:all`) added to every module version (RI-318).
