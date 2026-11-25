"""Test support package for fixtures, app clients, cache, and sse helpers."""

from __future__ import annotations

from tests.support.app import client
from tests.support.cache import reset_ttl_cache
from tests.support.exports import (
    USER_ERROR_MAX_LEN,
    _build_chart_sse_event,
    _format_error_message,
    _short_user_error,
)
from tests.support.sse import parse_sse_events, post_stream, sse_answer, sse_complete

__all__ = [
    "client",
    "reset_ttl_cache",
    "USER_ERROR_MAX_LEN",
    "_build_chart_sse_event",
    "_format_error_message",
    "_short_user_error",
    "parse_sse_events",
    "post_stream",
    "sse_answer",
    "sse_complete",
]
