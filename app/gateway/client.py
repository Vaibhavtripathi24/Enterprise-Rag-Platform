from langchain_openai import ChatOpenAI
from openai import AsyncOpenAI, OpenAI
from portkey_ai import PORTKEY_GATEWAY_URL, createHeaders

from app.config import settings

# Portkey routing strategy:
#   - Primary/fallback logic lives in a Portkey saved config (required when
#     block_inline_config is enabled on the workspace).
#   - We reference that config via the x-portkey-config-id header.
#   - The inline config dict approach is disabled for this account, so all
#     retry/fallback/cache behavior must be configured inside the Portkey UI.


def _make_headers(feature: str = "rag") -> dict:
    """Build Portkey headers that reference the primary saved config by ID."""
    if not settings.PORTKEY_PRIMARY_CONFIG_ID:
        raise ValueError(
            "PORTKEY_PRIMARY_CONFIG_ID is not set in .env. "
            "Get the real pc-... ID from the Portkey dashboard or "
            "run: PYTHONPATH=. python scripts/list_portkey_configs.py"
        )
    return createHeaders(
        api_key=settings.PORTKEY_API_KEY,
        config_id=settings.PORTKEY_PRIMARY_CONFIG_ID,
        metadata={
            "feature": feature,
            "_user": "rag-system",
            "environment": "production",
        },
    )


if settings.GROQ_API_KEY:
    portkey_client = OpenAI(
        api_key=settings.GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1",
    )
else:
    portkey_client = OpenAI(
        api_key=settings.PORTKEY_API_KEY,
        base_url=PORTKEY_GATEWAY_URL,
        default_headers=_make_headers(),
    )


def get_langchain_llm(feature: str = "rag") -> ChatOpenAI:
    """
    Returns a ChatOpenAI client — using Groq if GROQ_API_KEY is set, or Portkey.
    """
    if settings.GROQ_API_KEY:
        return ChatOpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
            model=settings.GROQ_MODEL,
        )
    return ChatOpenAI(
        api_key=settings.PORTKEY_API_KEY,
        base_url=PORTKEY_GATEWAY_URL,
        model=f"@{settings.PORTKEY_PRIMARY_SLUG}/gpt-4o-mini",
        default_headers=_make_headers(feature),
    )


def get_async_openai_client(feature: str = "rag") -> AsyncOpenAI:
    """
    Returns an async OpenAI client — using Groq if GROQ_API_KEY is set, or Portkey.
    """
    if settings.GROQ_API_KEY:
        return AsyncOpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
        )
    return AsyncOpenAI(
        api_key=settings.PORTKEY_API_KEY,
        base_url=PORTKEY_GATEWAY_URL,
        default_headers=_make_headers(feature),
    )


def extract_cache_status(response) -> str:
    """
    Pull x-portkey-cache-status from the response.

    The OpenAI SDK does not expose raw headers on parsed responses, so cache
    hit/miss tracking is best-effort. We inspect common attribute paths and
    fall back to 'MISS'.
    """
    for attr in ("_raw_response", "_response", "_http_response", "headers"):
        raw = getattr(response, attr, None)
        if raw is not None:
            headers = getattr(raw, "headers", None)
            if headers is not None:
                status = headers.get("x-portkey-cache-status", "")
                if status:
                    return status.upper()
    return "MISS"
