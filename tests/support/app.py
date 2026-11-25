"""TestClient helper for FastAPI app."""

from __future__ import annotations

from fastapi.testclient import TestClient

from src.main import app


def client() -> TestClient:
    """Return a TestClient instance for the FastAPI application."""
    return TestClient(app)
