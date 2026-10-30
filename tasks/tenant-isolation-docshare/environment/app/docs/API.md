# docshare API

docshare serves the documents that the ingest worker stores in its SQLite database (uploads go through the ingest
worker, not this API). Who may call what is in `PERMISSIONS.md`.

## Running it
```
python -m docshare.serve --db <path to the SQLite file> --port <port>
```
The service listens on 127.0.0.1, uses the database file given by `--db` (it must exist; the service never creates
one) and keeps all its state there. `python -m docshare.seed --out <path>` builds a fresh development database.

## Conventions
- Logged-in requests send `Authorization: Bearer <token>`; `X-Org-Id: <organisation id>` chooses the active
  organisation (`PERMISSIONS.md` section 2).
- Request and response bodies are JSON unless stated. Errors are JSON `{"error": "<code>"}`.
- Ids are UUID strings. Times are ISO 8601 strings in UTC, for example `2026-09-14T10:22:05Z`.

## Objects
**File**: `id`, `org_id`, `folder_id`, `name`, `mime_type`, `size` (bytes, integer), `uploaded_by` (user id),
`created_at`.

**Folder**: `id`, `org_id`, `name`.

## Endpoints
| Method and path | Success | Body of a successful response |
|---|---|---|
| `GET /api/health` | 200 | `{"ok": true}`; no login |
| `GET /api/me` | 200 | `{"user": {"id", "email", "name", "is_support"}, "active_org_id", "role", "memberships": [{"org_id", "role"}]}`; `active_org_id` is `null` and `role` is `"support"` for support without `X-Org-Id` |
| `GET /api/files` | 200 | `{"files": [File, ...]}`: the files of the active organisation, sorted by name |
| `GET /api/folders` | 200 | `{"folders": [Folder, ...]}`: the folders of the active organisation, sorted by name |
| `GET /api/folders/<folder_id>/files` | 200 | `{"folder": Folder, "files": [File, ...]}`, files sorted by name |
| `GET /api/files/<file_id>` | 200 | File |
| `GET /api/files/<file_id>/download` | 200 | the file's bytes, with its `mime_type` as Content-Type and `Content-Disposition: attachment; filename="<name>"` |
| `GET /api/files/<file_id>/thumb` | 200 | an `image/svg+xml` preview: the file name and the first lines of a text file |
| `PATCH /api/files/<file_id>` with `{"name": "<new name>"}` | 200 | the updated File; the name must be 1 to 200 characters without `/`, else `400` |
| `DELETE /api/files/<file_id>` | 204 | empty; the file and its share links are removed |
| `POST /api/files/<file_id>/shares` | 201 | `{"token", "url", "file_id", "created_at"}`; `url` is `/s/<token>` |
| `DELETE /api/shares/<token>` | 204 | empty; the link stops working |
| `GET /s/<token>` | 200 | the file's bytes, like download; no login |
| `POST /api/export` with `{"file_ids": [<id>, ...]}` (1 to 50 ids) | 200 | `{"files": [{"id", "name", "mime_type", "size", "content_b64"}, ...]}` in request order; `content_b64` is the file's bytes in standard base64 |
| `GET /api/admin/orgs` | 200 | `{"orgs": [{"id", "name", "file_count"}, ...]}` sorted by name |

Malformed bodies (for example a missing `name`, or `file_ids` that is not a list of 1 to 50 strings) get `400`.

## Database
The schema is in `docshare/db.py` (`SCHEMA`). Tables: `orgs`, `users`, `memberships`, `folders`, `files` (contents
are stored in `files.content`), `shares` (`revoked_at` is set when a link is revoked).
