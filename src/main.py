"""FastAPI app — 1 service duy nhất phục vụ API + static UI (không tách
frontend/backend, xem specs/implementation-plan.md).

Chạy dev server:
    uvicorn src.main:app --reload

Mở docs tương tác: http://localhost:8000/docs
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.agent.graph import Agent_Input, run_agent
from src.config import settings
from src.guardrails import GuardrailViolation, OUT_OF_SCOPE_REPLY, check_input, check_output, in_scope, redact_pii
from src.monitoring.tracing import trace_answer


app = FastAPI(
    title="agent_ATIN",
    description="Chatbot thống kê xe ra/vào & xâm nhập khu vực.",
    version="0.1.0",
)

_STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
if _STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")


class AskRequest(BaseModel):
    question: str = Field(min_length=1, description="Câu hỏi thống kê tự nhiên")


class AskResponse(BaseModel):
    question: str
    answer: str
    tool: str = ""
    columns: list[str] = []
    rows: list[list] = []
    row_count: int = 0


@app.post("/ask", response_model=AskResponse, tags=["agent"])
def ask(req: AskRequest) -> AskResponse:
    # Toàn bộ pipeline trong 1 span Langfuse (no-op nếu MONITORING_ENABLED=false).
    # Output chỉ gắn answer/tool/row_count — không ghi secrets / raw DB rows.
    with trace_answer("ask", req.question, metadata={"endpoint": "/ask"}) as t:
        # guardrail_input: injection/toxic raise (nguy hại thật, chặn cứng,
        # không gọi agent/DB) — xử lý ở exception handler bên dưới. Ngoài phạm
        # vi KHÔNG raise, trả lời lịch sự luôn, cũng không gọi agent/DB.
        check_input(req.question)
        if not in_scope(req.question):
            t["output"] = {"status": "out_of_scope", "answer": OUT_OF_SCOPE_REPLY}
            return AskResponse(question=req.question, answer=OUT_OF_SCOPE_REPLY)

        question = redact_pii(req.question)
        try:
            out = run_agent(Agent_Input(question=question), parent_span=t.get("_span"))
        except Exception as exc:
            raise HTTPException(status_code=503, detail=f"Không trả lời được: {exc}") from exc

        # guardrail_output: đối chiếu số liệu với evidence thật (câu hỏi + dữ
        # liệu tool trả về), redact PII, giới hạn độ dài — không raise, chỉ
        # sửa/thay answer khi cần.
        query = out.query
        evidence = [question] + (
            [f"{c}={v}" for row in query.rows for c, v in zip(query.columns, row)] if query else []
        )
        result = check_output(out.answer, evidence)

        response = AskResponse(
            question=out.question,
            answer=result.answer,
            tool=query.tool if query else "",
            columns=query.columns if query else [],
            rows=query.rows if query else [],
            row_count=query.row_count if query else 0,
        )
        t["output"] = {
            "status": "ok",
            "answer": response.answer,
            "tool": response.tool,
            "row_count": response.row_count,
        }
        return response


@app.exception_handler(GuardrailViolation)
def guardrail_violation_handler(request: Request, exc: GuardrailViolation) -> JSONResponse:
    # "detail" (string) để khớp field UI (static/index.html) đã đọc cho MỌI
    # lỗi khác (422, 503) — "error"/"reason"/"details" giữ nguyên cho API
    # consumer khác cần chi tiết máy đọc được.
    return JSONResponse(
        status_code=400,
        content={
            "detail": f"Câu hỏi bị từ chối: {exc.reason}",
            "error": "input_rejected",
            "reason": exc.reason,
            "details": exc.details,
        },
    )


@app.get("/", tags=["meta"])
def ui() -> FileResponse:
    index_path = _STATIC_DIR / "index.html"
    if not index_path.is_file():
        raise HTTPException(status_code=404, detail="static/index.html chưa tồn tại.")
    return FileResponse(index_path)


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok", "llm_backend": settings.llm_backend, "db_configured": settings.db_configured}
