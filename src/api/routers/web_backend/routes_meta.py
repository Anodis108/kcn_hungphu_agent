"""Meta: health, ready, models, config, LLM ping."""
from __future__ import annotations
import logging
from typing import Any
from fastapi import APIRouter, HTTPException, Response, status
from src.shared.settings import settings
from src.infra.llm import ping as llm_ping

logger = logging.getLogger(__name__)
router = APIRouter(tags=['meta'])

@router.get('/api/health')
@router.get('/health')
def health():
    return {'status': 'ok', 'service': 'agent_ATIN v3 Backend', 'llm_backend': settings.llm_backend, 'active_model': settings.effective_model, 'db_configured': settings.db_configured, 'monitoring_enabled': settings.monitoring_enabled}

def _check_postgres() -> tuple[str, str | None]:
    """Kiểm tra PostgreSQL (SELECT 1, timeout 2s). Bỏ qua nếu không cấu hình."""
    if not settings.agent_db_configured:
        return 'skipped', None
    try:
        from src.infra.memory.db import _connect_kwargs
        import psycopg2

        kw = dict(_connect_kwargs())
        kw['connect_timeout'] = 2
        with psycopg2.connect(**kw) as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT 1;')
                cur.fetchone()
        return 'ok', None
    except Exception as exc:
        return 'failed', str(exc)

def _check_qdrant() -> tuple[str, str | None]:
    """Kiểm tra Qdrant nếu bật long term memory hoặc qdrant_configured."""
    if not (settings.long_term_memory_enabled or settings.qdrant_configured):
        return 'skipped', None
    try:
        from src.infra.memory.longterm import get_qdrant_client
        client = get_qdrant_client()
        client.get_collections()
        return 'ok', None
    except Exception as exc:
        return 'failed', str(exc)

def _check_llm() -> tuple[str, str | None]:
    """Kiểm tra LLM backend sẵn sàng cấu hình / ping."""
    try:
        llm_ping()
        return 'ok', None
    except Exception as exc:
        return 'failed', str(exc)

@router.get('/api/ready')
@router.get('/ready')
def ready(response: Response) -> dict[str, Any]:
    checks: dict[str, str] = {}
    details: dict[str, str] = {}

    pg_status, pg_err = _check_postgres()
    checks['postgres'] = pg_status
    if pg_err:
        details['postgres'] = pg_err

    qd_status, qd_err = _check_qdrant()
    checks['qdrant'] = qd_status
    if qd_err:
        details['qdrant'] = qd_err

    llm_status, llm_err = _check_llm()
    checks['llm'] = llm_status
    if llm_err:
        details['llm'] = llm_err

    is_ready = all(status != 'failed' for status in checks.values())
    payload: dict[str, Any] = {'ready': is_ready, 'checks': checks}
    if details:
        payload['details'] = details

    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return payload


@router.get('/api/models')
def get_available_models():
    from src.shared.models_config import get_model_targets

    supported = []
    targets = get_model_targets()
    for t in targets:
        supported.append({
            'id': t.model,
            'name': f"{t.provider.upper()} ({t.model})",
            'provider': t.provider,
            'timeout': t.timeout,
        })

    if not supported:
        supported = [{'id': 'gpt-4o-mini', 'name': 'OpenAI Cloud (gpt-4o-mini)', 'provider': 'openai'}]

    if settings.llm_backend == 'self_hosted':
        from src.infra.llm.gateway import fetch_gateway_catalog, gateway_model_ids
        catalog = fetch_gateway_catalog()
        limits = (catalog['limits'] if 'limits' in catalog else None) or {}
        endpoint = settings.model_endpoint or f"{settings.model_base_url.rstrip('/')}/chat/completions"
        for mid in gateway_model_ids():
            if not any(s['id'] == mid for s in supported):
                supported.append({'id': mid, 'name': f'Gateway ({mid})', 'provider': 'self_hosted', 'endpoint': endpoint, 'limits': limits})
        if not gateway_model_ids() and not any(s['id'] == settings.model_name for s in supported):
            supported.append({'id': settings.model_name, 'name': f'Gateway ({settings.model_name})', 'provider': 'self_hosted', 'endpoint': endpoint})
    return {'active_backend': settings.llm_backend, 'active_model': settings.effective_model, 'chat_completions_endpoint': settings.model_endpoint, 'supported_models': supported}

@router.get('/api/llm/ping')
def ping_llm():
    try:
        status = llm_ping()
        return {'status': status, 'backend': settings.llm_backend, 'model': settings.effective_model, 'base_url': settings.effective_base_url or ''}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e)) from e

@router.get('/api/config')
def get_config():
    return {
        'llm_backend': settings.llm_backend,
        'active_model': settings.effective_model,
        'self_hosted_base_url': settings.model_base_url,
        'self_hosted_chat_endpoint': settings.model_endpoint,
        'self_hosted_model': settings.model_name,
        'monitoring_enabled': settings.monitoring_enabled,
        'iam_required': bool(settings.iam_required),
        'iam_configured': bool((settings.iam_base_url or '').strip()),
        'default_organization_id': settings.db_organization_id or 103,
        'supported_domains': [
            'Phương tiện (ITS)', 'Vùng cấm (Fence)', 'Khuôn mặt (Face)',
            'Ẩu đả (Fight)', 'Đám đông (Crowd)', 'Leo trèo (Intrusion)',
            'Cháy khói (Fire)', 'Mực nước (Water)',
        ],
    }
