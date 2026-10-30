"""SVG previews for the file grid."""
import html

from flask import Blueprint, Response, abort

from .. import db
from ..auth import login_required

bp = Blueprint("thumbs", __name__)

TEXT_TYPES = ("text/", "application/json")


def render_thumb(name, mime_type, content):
    lines = []
    if mime_type.startswith(TEXT_TYPES):
        text = bytes(content).decode("utf-8", "replace")
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()][:5]
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="160" height="200" viewBox="0 0 160 200">',
             f"<title>{html.escape(name)}</title>",
             '<rect x="0.5" y="0.5" width="159" height="199" fill="#ffffff" stroke="#c8ccd2"/>',
             f'<text x="8" y="18" font-size="9" font-weight="bold">{html.escape(name[:30])}</text>']
    for i, ln in enumerate(lines):
        parts.append(f'<text x="8" y="{40 + 14 * i}" font-size="8">{html.escape(ln[:34])}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


@bp.get("/api/files/<file_id>/thumb")
@login_required
def thumb(file_id):
    row = db.query_one("SELECT name, mime_type, content FROM files WHERE id = ?", (file_id,))
    if row is None:
        abort(404)
    svg = render_thumb(row["name"], row["mime_type"], row["content"])
    return Response(svg, mimetype="image/svg+xml")
