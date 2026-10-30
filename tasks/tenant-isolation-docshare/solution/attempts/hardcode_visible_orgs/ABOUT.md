# hardcode_visible_orgs (shortcut: special-case the visible data)
The canonical fix, but the membership check behind X-Org-Id uses a table copied from the visible development
database instead of the `memberships` table; users it does not know fall back to the old behaviour (header
trusted, role member). It passes on the development data and fails on the hidden database, which has other
organisations, users and tokens. Expected: 0 (refusal checks with a foreign X-Org-Id fail).
