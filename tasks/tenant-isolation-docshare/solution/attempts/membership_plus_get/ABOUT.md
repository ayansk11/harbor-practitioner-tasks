# membership_plus_get (wrong: an incomplete audit)
Checks X-Org-Id against the caller's memberships (the canonical auth.py) and scopes the shared loader
`get_file_or_404` in routes/files.py by the active organisation. Misses the code paths that do not use that loader:
thumbs, export (only the first id is checked), share creation, and the delete role check (any member or support can
delete). Expected: 0 (refusal checks on thumb, export, share and delete fail).
