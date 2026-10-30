# patch_get_only (wrong: fixes only what the report shows)
Adds an organisation check to `GET /api/files/<id>` and `/download` only. X-Org-Id is still trusted, and thumbs,
export, share creation, rename and delete keep their old code paths. Expected: 0 (refusal checks fail).
