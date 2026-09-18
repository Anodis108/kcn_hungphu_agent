"""Guardrail — input (injection/toxic chặn cứng, phạm vi câu hỏi trả lời
lịch sự) + output (đối chiếu số liệu, redact PII, giới hạn độ dài). Toàn bộ
bằng regex/code, KHÔNG dùng LLM (giữ đúng ngân sách "tối đa 2 lời gọi
LLM/câu hỏi" của MVP — xem specs/product-spec.md).

Tham khảo `llm-engineer-demo/app/guardrails/injection.py` + `pii.py` (pattern
gốc) và `atin/app/guardrails/checks.py` + `atin/app/supervisor_agent/
guardrails.py` (đã kiểm chứng, gộp lại thành 1 file phẳng ở đây — cấu trúc
`src/` của project này không tách package `guardrails/` riêng).

CHƯA ghép vào pipeline (`src/main.py`)/`src/agent/graph.py` — đó là item kế
tiếp trong Phase 5 ("Ghép luồng: guardrail_input → agent → guardrail_output").
"""

from __future__ import annotations

import re

from src.config import settings

_INJECTION_PATTERNS = [
    re.compile(r"ignore (all |previous |above )?instructions", re.IGNORECASE),
    re.compile(r"disregard (all |previous |above )?(instructions|rules)", re.IGNORECASE),
    re.compile(r"bỏ qua (mọi |các )?(hướng dẫn|chỉ dẫn|quy tắc)", re.IGNORECASE),
    re.compile(r"reveal (your |the )?system prompt", re.IGNORECASE),
    re.compile(r"tiết lộ.*system prompt", re.IGNORECASE),
    re.compile(r"you are now", re.IGNORECASE),
    re.compile(r"act as (if you|a) ", re.IGNORECASE),
]

_TOXIC_WORDS = frozenset({"đụ", "địt", "đéo", "fuck", "shit", "cút", "óc chó"})

_PHONE = re.compile(r"\b0\d{9,10}\b")
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")

# Từ khoá nhận diện câu hỏi trong phạm vi thống kê xe ra/vào + xâm nhập khu
# vực (xem specs/product-spec.md mục "Core User Flow"/"Features In Scope").
STAT_KEYWORDS = frozenset(
    {
        "khu vực",
        "ra vào",
        "ra/vào",
        "lượt vào",
        "lượt ra",
        "thống kê",
        "báo cáo",
        "bao nhiêu người",
        "bao nhiêu xe",
        "bao nhiêu lượt",
        "số lượt",
        "cổng",
        "nhân viên",
        "khu a",
        "khu b",
        "xe máy",
        "ô tô",
        "oto",
        "xe tải",
        "biển số",
        "bien so",
        "hãng xe",
        "xâm nhập",
        "xam nhap",
        "hàng rào",
        "camera",
        "truy vết",
        "truy vet",
        "khung giờ",
        "khung gio",
        # 5 domain sự kiện VMS mới (Phase 2+) — từ khoá nhận diện phạm vi
        # cho in_scope(); tool/DB tương ứng đã có ở Phase 3/5.
        "khuôn mặt",
        "khuon mat",
        "ẩu đả",
        "au da",
        "đám đông",
        "dam dong",
        "leo trèo",
        "leo treo",
        "cháy",
        "chay",
        "khói",
        "khoi",
        "mực nước",
        "muc nuoc",
    }
)

OUT_OF_SCOPE_REPLY = (
    "Xin lỗi, tôi chỉ hỗ trợ thống kê lượt ra/vào khu vực từ dữ liệu hiện có — "
    "câu hỏi này nằm ngoài phạm vi đó. Hãy hỏi ví dụ: "
    '"Hôm nay có bao nhiêu lượt xe vào?".'
)

_FALLBACK = "Xin lỗi, tôi chưa đủ dữ liệu đáng tin để trả lời. Hãy hỏi lại rõ hơn."
_DISCLAIMER = " (Lưu ý: số liệu chưa xác minh được với dữ liệu tool trả về.)"


class GuardrailViolation(Exception):
    """Injection/nội dung độc hại — nguy hại thật, chặn cứng (raise, không
    gọi agent/DB). Câu hỏi ngoài phạm vi KHÔNG raise lỗi này — xem in_scope()."""

    def __init__(self, reason: str, details: dict | None = None):
        self.reason = reason
        self.details = details or {}
        super().__init__(reason)


class OutputCheckResult:
    __slots__ = ("valid", "issues", "answer")

    def __init__(self, valid: bool, issues: list[str] | None = None, answer: str = ""):
        self.valid = valid
        self.issues = issues or []
        self.answer = answer


def detect_prompt_injection(text: str) -> bool:
    return any(p.search(text or "") for p in _INJECTION_PATTERNS)


def detect_toxicity(text: str) -> bool:
    low = (text or "").lower()
    return any(w in low for w in _TOXIC_WORDS)


def redact_pii(text: str) -> str:
    text = _PHONE.sub("[SĐT ẩn]", text or "")
    text = _EMAIL.sub("[email ẩn]", text)
    return text


def in_scope(question: str) -> bool:
    low = (question or "").lower()
    return any(k in low for k in STAT_KEYWORDS)


def check_input(text: str) -> None:
    """Raise GuardrailViolation nếu injection/toxic (nguy hại thật). Không
    chặn PII ở đây — caller tự redact bằng redact_pii()."""
    if detect_prompt_injection(text):
        raise GuardrailViolation("prompt_injection_detected", {"pattern_match": True})
    if detect_toxicity(text):
        raise GuardrailViolation("unsafe_content", {"pattern_match": True})


def check_output(answer: str, evidence: list[str]) -> OutputCheckResult:
    """Không raise — trả kết quả để caller quyết định giữ answer, thêm
    disclaimer, hay fallback. `evidence`: các đoạn text chứa số liệu thật đã
    lấy được (câu hỏi + dữ liệu tool) để đối chiếu số trong answer."""
    issues: list[str] = []
    text = answer or ""

    if len(text) < settings.guardrails_min_answer_len:
        issues.append("answer_too_short")
    if detect_toxicity(text):
        issues.append("toxic_output")

    # LLM hay tự format số có dấu . phân cách hàng nghìn kiểu VN (vd. "9.418"),
    # trong khi evidence (dữ liệu tool thô) không có dấu phân cách — chuẩn hoá
    # cả 2 phía (bỏ dấu . giữa các chữ số) trước khi so khớp, tránh false
    # positive gắn oan disclaimer cho số liệu ĐÚNG chỉ khác cách trình bày.
    context_text = re.sub(r"(?<=\d)\.(?=\d{3}\b)", "", " ".join(evidence))
    numbers = re.findall(r"\b\d+\b", re.sub(r"(?<=\d)\.(?=\d{3}\b)", "", text))
    unverified = [n for n in numbers if n not in context_text]

    if "answer_too_short" in issues or "toxic_output" in issues:
        return OutputCheckResult(valid=False, issues=issues, answer=_FALLBACK)

    if unverified:
        issues.append("unverified_numbers")
        text = text.rstrip() + _DISCLAIMER

    redacted = redact_pii(text)
    if redacted != text:
        issues.append("pii_redacted")
        text = redacted

    max_len = settings.guardrails_max_answer_len
    if max_len and len(text) > max_len:
        issues.append("answer_too_long")
        text = text[:max_len].rstrip() + "…"

    return OutputCheckResult(valid=not issues, issues=issues, answer=text)
