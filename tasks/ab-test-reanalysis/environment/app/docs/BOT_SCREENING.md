# Bot screening

Data platform documentation. It applies to every experiment export of this layout.

The platform screens traffic for bots with two rules. Every flag is one row of `bot_flags.csv.gz` (`user_id`, `rule`,
`flagged_at`). A user can be flagged by both rules.

| Rule | In use since | What it looks at | When it runs | `flagged_at` |
|---|---|---|---|---|
| `ua_crawler` | 2024-03 | the client: a crawler user agent, or an IP address in a data-centre range | on the client's first request to the platform (any page; it need not be a product pageview of the export) | the time of that first request; one row per flagged user |
| `velocity` | 2026-08-28 (SEC-219) | the user's `module_click` events (`docs/TRACKING.md`): 8 or more events, of any target, within 60 seconds | nightly at 02:00 UTC, over the module_click events of the previous UTC day | the time of the run (02:00:00 UTC); one row per user and day on which the rule fired |

`velocity` was added against click fraud on the related-items module (scripts that click product cards in bursts).
Its threshold was set on July 2026 related-items traffic, in which no human reached it.
