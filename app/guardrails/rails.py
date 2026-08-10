try:
    from nemoguardrails import LLMRails, RailsConfig
    NEMO_AVAILABLE = True
except ImportError:
    LLMRails = None
    RailsConfig = None
    NEMO_AVAILABLE = False

from app.config import settings
from app.guardrails.colang_rules import COLANG_CONTENT, RAIL_INDICATORS, YAML_CONTENT

_rails = None


def initialize_rails() -> None:
    """
    Mark NeMo guardrails ready for lazy initialization.
    LLMRails builds lazily on first query to ensure instant port binding.
    """
    logfire.info("🛡️ NeMo Guardrails registered for lazy initialization.")


def _get_rails():
    global _rails
    if not NEMO_AVAILABLE:
        return None
    if _rails is not None:
        return _rails

    if settings.GROQ_API_KEY:
        guard_llm = ChatOpenAI(api_key=settings.GROQ_API_KEY, base_url="https://api.groq.com/openai/v1", model=settings.GROQ_MODEL)
    else:
        api_key = settings.OPENAI_API_KEY or "sk-dummy-key-for-initial-setup"
        guard_llm = ChatOpenAI(api_key=api_key, model="gpt-4o-mini")

    config = RailsConfig.from_content(colang_content=COLANG_CONTENT, yaml_content=YAML_CONTENT)
    _rails = LLMRails(config, llm=guard_llm)
    return _rails


def guard(message: str) -> tuple[bool, str | None]:
    if not NEMO_AVAILABLE:
        return False, None

    try:
        rails = _get_rails()
        if rails is None:
            return False, None
        result = rails.generate(messages=[{"role": "user", "content": message}])

        # NeMo returns {'role': 'assistant', 'content': '...'} — extract text
        content = result.get("content", "") if isinstance(result, dict) else str(result)

        fired = any(indicator in content for indicator in RAIL_INDICATORS)

        if fired:
            return True, content

        return False, None
    except Exception as e:
        return False, None
