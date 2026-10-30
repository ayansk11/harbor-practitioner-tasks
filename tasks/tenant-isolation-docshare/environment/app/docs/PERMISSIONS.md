# docshare access policy

Owner: platform security. This is the policy every docshare endpoint must follow. Endpoint details are in `API.md`.

## 1. Who is asking
- Every `/api/...` request must carry `Authorization: Bearer <token>` (the token is `users.token`). A request with no
  token or an unknown token gets `401`. Two endpoints need no login: `GET /api/health` and share links `GET /s/<token>`.
- A user belongs to one or more organisations (rows in `memberships`) and has one role in each: `member` or
  `org_admin`.
- Support staff are users with `users.is_support = 1`. They belong to no organisation and have no home organisation.

## 2. The active organisation
- Every request acts in one organisation, the *active organisation*: the organisation named in the `X-Org-Id` header,
  or, when the header is absent, the user's home organisation (`users.home_org_id`).
- A member or org_admin may only make active an organisation they belong to. If `X-Org-Id` names any other
  organisation, or one that does not exist, the whole request is refused.
- The caller's role is their role in the active organisation. Someone who is `member` in one organisation and
  `org_admin` in another is an org_admin only while that second organisation is active.
- Members and org_admins act only on folders and files of the active organisation. A file or folder of another
  organisation is refused, even if the caller also belongs to that organisation: they switch first by sending that
  organisation's id in `X-Org-Id`.
- Support may name any existing organisation in `X-Org-Id`; no membership is needed. For support this only chooses
  what the list endpoints show. If support names an organisation that does not exist, the whole request is refused.
  Without `X-Org-Id`, support's list endpoints answer `400`.

## 3. What each role may do
| Action | Endpoints | member | org_admin | support |
|---|---|---|---|---|
| read | `GET /api/files/<id>` | yes | yes | yes, any organisation |
| download | `GET /api/files/<id>/download` | yes | yes | yes, any organisation |
| thumb | `GET /api/files/<id>/thumb` | yes | yes | yes, any organisation |
| list | `GET /api/files`, `GET /api/folders`, `GET /api/folders/<id>/files` | yes | yes | yes, the organisation it names |
| export | `POST /api/export` | yes | yes | yes, any organisation |
| rename | `PATCH /api/files/<id>` | yes | yes | no |
| share | `POST /api/files/<id>/shares`, `DELETE /api/shares/<token>` | yes | yes | no |
| delete | `DELETE /api/files/<id>` | no | yes | no |
| support console | `GET /api/admin/orgs` | no | no | yes |
| who am I | `GET /api/me` | yes | yes | yes |

- For member and org_admin, "yes" means: on files and folders of the active organisation only (section 2).
- For support, "any organisation" means: any file of any organisation, whatever the active organisation is.
- A list shows exactly the folders or files of the active organisation, and nothing of any other organisation.

## 4. Export
`POST /api/export` returns several files in one response. It is allowed only if the caller may `read` every requested
id under the rules above. If even one id is not readable (a file of another organisation, a deleted file, an unknown
id), the whole request is refused and the response holds no file at all.

## 5. Share links
- Creating a link (`POST /api/files/<id>/shares`) and revoking it (`DELETE /api/shares/<token>`) are the `share`
  action on the link's file.
- Anyone who has the link can download the file with `GET /s/<token>`, without logging in, until the link is revoked
  or the file is deleted. After that, or for an unknown token, the link answers `404`.

## 6. Refusals
- A refused request gets `403` or `404`; either is fine (404 avoids confirming that an id exists). The only other
  refusal codes are `401` (section 1) and `400` (support listing without `X-Org-Id`, section 2).
- A refusal holds no file data: no file contents and no name of a file the caller may not read. An error message may
  repeat the id it was sent.
- A refused request changes nothing: no file is renamed or deleted, no link is created or revoked.
