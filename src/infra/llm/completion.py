"""Chat completion helpers — text / tools / stream trên LangChain `base_llm`."""

from __future__ import annotations

from collections.abc import Iterator

from src.infra.llm.client import base_llm, llm_model_label
from src.infra.llm.params import BALANCED, GenerationParams


def invoke_with_tools(messages, tools=None, model_override: str | None = None, backend_override: str | None = None):
    from src.domain.observability.tracing import add_request_tokens, extract_token_usage
    from src.shared.models_config import get_model_targets
    from src.infra.resilience.breaker import get_llm_breaker
    import logging

    log = logging.getLogger(__name__)
    targets = get_model_targets()
    llm_breaker = get_llm_breaker()
    last_err: Exception | None = None

    for idx, target in enumerate(targets):
        provider = backend_override or target.provider
        model = model_override or target.model

        if idx == 0 and not llm_breaker.allow_request():
            if idx + 1 < len(targets):
                next_target = targets[idx + 1]
                log.warning(
                    "llm_fallback_used: primary=%s circuit breaker is OPEN; jumping to fallback=%s",
                    model,
                    next_target.model,
                )
                continue
            else:
                log.error("Primary LLM circuit breaker is OPEN and no fallback target available.")

        try:
            llm = base_llm(
                model_override=model,
                backend_override=provider,
                base_url_override=target.base_url,
                api_key_override=target.api_key,
                request_timeout_override=target.timeout,
            )
            if tools:
                llm = llm.bind_tools(tools)
            response = llm.invoke(messages)
            add_request_tokens(extract_token_usage(response))
            if idx == 0:
                llm_breaker.record_success()
            return response
        except Exception as e:
            last_err = e
            if idx == 0:
                llm_breaker.record_failure()
            if idx + 1 < len(targets):
                next_target = targets[idx + 1]
                log.warning(
                    "llm_fallback_used: primary=%s failed with %s; trying fallback=%s",
                    model,
                    e,
                    next_target.model,
                )
            else:
                log.error("All LLM model targets failed. Last error: %s", e)
    raise RuntimeError(f"Lỗi kết nối tới LLM: Không thể sinh phản hồi. Chi tiết: {last_err}") from last_err



def invoke_text(
    system_prompt: str,
    user_prompt: str,
    model_override: str | None = None,
    backend_override: str | None = None,
    max_tokens: int | None = None,
    *,
    params: GenerationParams | None = None,
    substep: str | None = "llm_text",
    stop: list[str] | None = None,
) -> str:
    """Lời gọi LLM text — Answer / SQL generate."""
    from src.domain.observability.tracing import llm_io_payload
    from src.domain.observability.tracing import add_request_tokens, current_span, extract_token_usage, trace_step

    gen = params or BALANCED
    mt = max_tokens if max_tokens is not None else gen.max_tokens
    meta = {"model_name": llm_model_label(backend_override), "temperature": gen.temperature}
    prompt_in = llm_io_payload(system_prompt or "", user_prompt or "", "")["input"]
    if mt is not None:
        prompt_in = {**prompt_in, "max_tokens": mt}

    def _call() -> tuple[str, dict[str, int]]:
        from src.shared.models_config import get_model_targets
        from src.infra.resilience.breaker import get_llm_breaker
        import logging

        log = logging.getLogger(__name__)
        targets = get_model_targets()
        llm_breaker = get_llm_breaker()
        last_err: Exception | None = None

        for idx, target in enumerate(targets):
            provider = backend_override or target.provider
            model = model_override or target.model

            if idx == 0 and not llm_breaker.allow_request():
                if idx + 1 < len(targets):
                    next_target = targets[idx + 1]
                    log.warning(
                        "llm_fallback_used: primary=%s circuit breaker is OPEN; jumping to fallback=%s",
                        model,
                        next_target.model,
                    )
                    continue
                else:
                    log.error("Primary LLM circuit breaker is OPEN in invoke_text and no fallback target available.")

            try:
                llm = base_llm(
                    model_override=model,
                    backend_override=provider,
                    max_tokens_override=mt,
                    params=gen,
                    base_url_override=target.base_url,
                    api_key_override=target.api_key,
                    request_timeout_override=target.timeout,
                )
                if stop:
                    llm = llm.bind(stop=stop)
                response = llm.invoke(
                    [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
                )
                usage = extract_token_usage(response)
                add_request_tokens(usage)
                if idx == 0:
                    llm_breaker.record_success()
                return (str(response.content or ""), usage)
            except Exception as e:
                last_err = e
                if idx == 0:
                    llm_breaker.record_failure()
                if idx + 1 < len(targets):
                    next_target = targets[idx + 1]
                    log.warning(
                        "llm_fallback_used: primary=%s failed with %s; trying fallback=%s",
                        model,
                        e,
                        next_target.model,
                    )
                else:
                    log.error("All LLM model targets failed in invoke_text. Last error: %s", e)
        raise RuntimeError(f"Lỗi kết nối tới LLM: {last_err}") from last_err

    try:
        if substep:
            with trace_step(current_span(), substep, input=prompt_in, metadata=meta, as_type="generation") as box:
                text, usage = _call()
                payload = llm_io_payload(system_prompt or "", user_prompt or "", text)
                box["usage"] = usage
                box["input"] = payload["input"]
                box["output"] = payload["output"]
                box["model_name"] = meta["model_name"]
                return text
        text, _usage = _call()
        return text
    except Exception as e:
        raise RuntimeError(f"Lỗi kết nối tới LLM: Không thể sinh phản hồi. Chi tiết: {e}") from e


def chat_stream(
    system_prompt: str,
    user_prompt: str,
    model_override: str | None = None,
    backend_override: str | None = None,
    max_tokens: int | None = None,
    *,
    params: GenerationParams | None = None,
    stop: list[str] | None = None,
) -> Iterator[str]:
    """Streaming sync — yield từng token với provider fallback tự động."""
    from src.shared.models_config import get_model_targets
    from src.infra.resilience.breaker import get_llm_breaker
    import logging

    log = logging.getLogger(__name__)
    gen = params or BALANCED
    mt = max_tokens if max_tokens is not None else gen.max_tokens
    targets = get_model_targets()
    llm_breaker = get_llm_breaker()
    last_err: Exception | None = None

    for idx, target in enumerate(targets):
        provider = backend_override or target.provider
        model = model_override or target.model

        if idx == 0 and not llm_breaker.allow_request():
            if idx + 1 < len(targets):
                next_target = targets[idx + 1]
                log.warning(
                    "llm_fallback_used: chat_stream primary=%s circuit breaker is OPEN; jumping to fallback=%s",
                    model,
                    next_target.model,
                )
                continue
            else:
                log.error("Primary LLM circuit breaker is OPEN in chat_stream and no fallback target available.")

        try:
            llm = base_llm(
                model_override=model,
                backend_override=provider,
                max_tokens_override=mt,
                params=gen,
                base_url_override=target.base_url,
                api_key_override=target.api_key,
                request_timeout_override=target.timeout,
            )
            if stop:
                llm = llm.bind(stop=stop)

            # Lấy stream iterator từ LLM
            stream_iter = iter(
                llm.stream(
                    [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
                )
            )

            # Lấy token đầu tiên để đảm bảo kết nối/handshake thành công trước khi yield ra
            first_chunk = next(stream_iter, None)
            if idx == 0:
                llm_breaker.record_success()

            def _stream_generator():
                if first_chunk is not None:
                    delta = getattr(first_chunk, "content", None)
                    if delta:
                        yield str(delta)
                for chunk in stream_iter:
                    delta = getattr(chunk, "content", None)
                    if delta:
                        yield str(delta)

            return _stream_generator()

        except Exception as e:
            last_err = e
            if idx == 0:
                llm_breaker.record_failure()
            if idx + 1 < len(targets):
                next_target = targets[idx + 1]
                log.warning(
                    "llm_fallback_used: chat_stream primary=%s failed with %s; trying fallback=%s",
                    model,
                    e,
                    next_target.model,
                )
            else:
                log.error("All LLM model targets failed in chat_stream. Last error: %s", e)
    raise RuntimeError(f"Lỗi kết nối tới LLM: Không thể sinh phản hồi. Chi tiết: {last_err}") from last_err

