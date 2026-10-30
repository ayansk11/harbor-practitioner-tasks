A security researcher reported that a member of one organisation in our document-sharing service, docshare, could
download another organisation's file by changing the file id in the download URL. The report is
`/app/SECURITY_REPORT.md`; the service is in `/app/docshare`.

Fix the service so that it enforces `/app/docs/PERMISSIONS.md` on every endpoint, not only the one in the report.
Keep everything the policy allows working: share links, switching organisation with `X-Org-Id` for people who belong
to more than one, and support staff's read-only access to every organisation. Endpoints and response formats are in
`/app/docs/API.md`, development users and tokens in `/app/docs/DEV_USERS.md`, and `/app/README.md` says how to run
the service and its tests.

How your fix will be checked:
- We copy `/app` to another folder and start the service from there, as an unprivileged user, with
  `python -m docshare.serve --db <path> --port <port>`, on a fresh copy of a different database with the same schema
  (other organisations, users, tokens and files). Do not depend on the ids or tokens of the development data, on
  absolute `/app` paths, or on running as root. The service must answer `GET /api/health` within 30 seconds of
  starting and each request within 10 seconds; we send about 3,700 requests in runs of at most 90 seconds each.
- Every request that `PERMISSIONS.md` refuses must get a refusal code from its section 6: `403` or `404`, `401`
  without a valid token, `400` for support listing without `X-Org-Id` (any 4xx is accepted). Its response must hold
  no file contents and no name of a file the caller may not read, and it must change nothing in the database.
- Every request that `PERMISSIONS.md` allows must keep working and answer as the service does today: the fields that
  `API.md` lists, with the same values; the exact file bytes, with the same media type and an `attachment`
  `Content-Disposition` naming the file on downloads and share links; the same previews; and lists with exactly the folders or files of the active
  organisation. Renames, deletes, and creating and revoking share links must take effect (a deleted file's links stop
  working), and a bad name or a malformed body still gets the `400` that `API.md` gives (any 4xx is accepted).
- You may add tables or columns, but keep the existing tables and columns with their names and meaning: after the
  refused requests we read `files`, `shares`, `memberships` and `folders` from the database file directly.

Only /app is kept when we grade: folders named `data`, `__pycache__` or `.venv` anywhere under /app are dropped, and the packages already installed are available.
