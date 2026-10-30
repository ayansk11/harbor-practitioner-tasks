# Security report: cross-organisation file download

Received 2026-10-21 through the vulnerability disclosure inbox. Reporter: an independent researcher testing our
staging stack with the development data. Severity claimed: high.

## Summary
A logged-in member of one organisation can download a file that belongs to a different organisation by changing the
file id in the download URL.

## Steps to reproduce (development database `data/docshare.db`)
1. Log in as Ben Carver, a member of Halden & Price LLP (token in `docs/DEV_USERS.md`).
2. `GET /api/files` lists only Halden & Price LLP files, as expected.
3. Request a file of Marlow Community Clinic, an organisation Ben does not belong to:
   ```
   curl -s -H "Authorization: Bearer dsk_2e09e4b8245edebc817af708207473b7" \
     http://127.0.0.1:8080/api/files/20b5d1d4-8637-49fb-adad-7770457f9573/download
   ```
4. The response is `200` with the full contents of `procurement-request-af6a.txt`.

## Expected
The request is refused and no data of the other organisation is returned.

## Notes from triage
Reproduced on 2026-10-22. File ids are random UUIDs, but they appear in exports, logs and support tickets, so
they cannot be treated as secret.
