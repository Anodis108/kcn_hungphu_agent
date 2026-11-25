"""Circuit breaker mỏng cho hạ tầng LLM và Database (Phase 20.4 / G16).

Không dùng thư viện bên ngoài. Hỗ trợ 3 trạng thái: closed, open, half-open.
Mở sau `BREAKER_FAIL_THRESHOLD` lỗi liên tiếp, thử lại sau `BREAKER_RESET_SECONDS`.
Log `circuit_open` và `circuit_close`.
"""

from __future__ import annotations

from enum import Enum
import logging
import threading
import time
from typing import Any, Callable

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half-open"


class CircuitBreakerOpenError(RuntimeError):
    """Ngoại lệ ném ra khi circuit breaker đang ở trạng thái OPEN."""
    pass


class CircuitBreaker:
    """Circuit breaker đếm lỗi liên tiếp và tự động mở/đóng mạch."""

    def __init__(
        self,
        name: str = "default",
        fail_threshold: int = 5,
        reset_seconds: float = 30.0,
    ) -> None:
        self.name = name
        self.fail_threshold = int(fail_threshold)
        self.reset_seconds = float(reset_seconds)
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0
        self._lock = threading.Lock()

    def allow_request(self) -> bool:
        """Kiểm tra xem yêu cầu hiện tại có được phép thực thi không."""
        with self._lock:
            if self.state == CircuitState.CLOSED:
                return True
            if self.state == CircuitState.OPEN:
                now = time.time()
                if now - self.last_failure_time >= self.reset_seconds:
                    self.state = CircuitState.HALF_OPEN
                    logger.info(
                        "circuit_half_open: breaker=%s reset_timeout reached; probing once",
                        self.name,
                    )
                    return True
                return False
            # HALF_OPEN cho phép thử 1 probe
            return True

    def record_success(self) -> None:
        """Ghi nhận lượt gọi thành công — đóng mạch nếu đang OPEN/HALF_OPEN."""
        with self._lock:
            if self.state in (CircuitState.HALF_OPEN, CircuitState.OPEN):
                prev_state = self.state.value
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                logger.warning(
                    "circuit_close: breaker=%s recovered from %s to closed",
                    self.name,
                    prev_state,
                )
            else:
                self.failure_count = 0

    def record_failure(self) -> None:
        """Ghi nhận lượt gọi thất bại — mở mạch nếu vượt ngưỡng lỗi."""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.state == CircuitState.HALF_OPEN or self.failure_count >= self.fail_threshold:
                if self.state != CircuitState.OPEN:
                    logger.warning(
                        "circuit_open: breaker=%s reached %s consecutive failures; opening circuit for %ss",
                        self.name,
                        self.failure_count,
                        self.reset_seconds,
                    )
                    self.state = CircuitState.OPEN

    def reset(self) -> None:
        """Reset trạng thái mạch về CLOSED (dùng cho testing/quản trị)."""
        with self._lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.last_failure_time = 0.0


_LLM_BREAKER: CircuitBreaker | None = None
_SQL_BREAKER: CircuitBreaker | None = None


def get_llm_breaker() -> CircuitBreaker:
    """Singleton CircuitBreaker cho LLM primary."""
    global _LLM_BREAKER
    if _LLM_BREAKER is None:
        from src.shared.settings import settings
        _LLM_BREAKER = CircuitBreaker(
            name="llm_primary",
            fail_threshold=settings.breaker_fail_threshold,
            reset_seconds=settings.breaker_reset_seconds,
        )
    return _LLM_BREAKER


def get_sql_breaker() -> CircuitBreaker:
    """Singleton CircuitBreaker cho kết nối PostgreSQL."""
    global _SQL_BREAKER
    if _SQL_BREAKER is None:
        from src.shared.settings import settings
        _SQL_BREAKER = CircuitBreaker(
            name="postgres_sql",
            fail_threshold=settings.breaker_fail_threshold,
            reset_seconds=settings.breaker_reset_seconds,
        )
    return _SQL_BREAKER
