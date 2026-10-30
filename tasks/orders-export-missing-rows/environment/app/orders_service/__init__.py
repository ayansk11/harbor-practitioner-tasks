"""Orders API: read-only HTTP access to the merchant's orders database (see docs/API.md)."""
from .app import create_app

__all__ = ["create_app"]
