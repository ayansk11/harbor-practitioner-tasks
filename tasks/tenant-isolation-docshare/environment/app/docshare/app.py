"""Flask application factory."""
from flask import Flask, g, jsonify
from werkzeug.exceptions import HTTPException

from . import db
from .auth import login_required
from .routes import admin, export, files, folders, share, thumbs


def create_app(db_path):
    app = Flask(__name__)
    app.config["DB_PATH"] = db_path
    app.teardown_appcontext(db.close_db)
    for module in (files, folders, thumbs, export, share, admin):
        app.register_blueprint(module.bp)

    @app.errorhandler(HTTPException)
    def http_error(exc):
        code = exc.description if exc.code == 400 and exc.description and " " not in exc.description else exc.name
        return jsonify(error=code.lower().replace(" ", "_")), exc.code

    @app.get("/api/health")
    def health():
        return jsonify(ok=True)

    @app.get("/api/me")
    @login_required
    def me():
        ident = g.identity
        return jsonify(user={"id": ident.user_id, "email": ident.email, "name": ident.name,
                             "is_support": ident.is_support},
                       active_org_id=ident.org_id, role=ident.role,
                       memberships=[{"org_id": o, "role": r} for o, r in sorted(ident.memberships.items())])

    return app
