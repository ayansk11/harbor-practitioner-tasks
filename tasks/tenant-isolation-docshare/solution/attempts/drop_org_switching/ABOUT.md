# drop_org_switching (shortcut: remove the feature instead of checking it)
The canonical fix, except that X-Org-Id is refused unless it names the caller's home organisation (support has none,
so any X-Org-Id is refused for support). People in two organisations can no longer reach the second one, and support
can no longer list an organisation. Expected: 0 (permitted checks fail).
