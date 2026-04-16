"""
Lab 11 — Configuration & API Key Setup
"""
import os


DEFAULT_OPENAI_MODEL = os.getenv("OPENAI_MODEL", "openai/gpt-4.1-mini")
DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")


def get_llm_provider() -> str:
    """Return the active LLM provider.

    Preference order:
    1. Explicit LLM_PROVIDER env var
    2. OPENAI_API_KEY if present
    3. GOOGLE_API_KEY if present
    4. Default to OpenAI
    """
    provider = os.getenv("LLM_PROVIDER", "").strip().lower()
    if provider in {"openai", "google"}:
        return provider
    if os.getenv("OPENAI_API_KEY"):
        return "openai"
    if os.getenv("GOOGLE_API_KEY"):
        return "google"
    return "openai"


def get_default_model_name() -> str:
    """Return the default model name for the active provider."""
    return DEFAULT_OPENAI_MODEL if get_llm_provider() == "openai" else DEFAULT_GEMINI_MODEL


def build_adk_model():
    """Build an ADK-compatible model object/string for the active provider."""
    provider = get_llm_provider()
    if provider == "openai":
        try:
            from google.adk.models.lite_llm import LiteLlm
        except ImportError as exc:
            raise ImportError(
                "OpenAI mode requires LiteLLM support from google-adk. "
                "Please ensure your environment is up to date."
            ) from exc

        try:
            import litellm  # noqa: F401
        except ImportError as exc:
            raise ImportError(
                "OpenAI mode requires the 'litellm' package. "
                "Install it with: pip install litellm"
            ) from exc

        return LiteLlm(model=get_default_model_name())

    return get_default_model_name()


def setup_api_key():
    """Load the API key for the active provider, preferring OpenAI."""
    provider = get_llm_provider()

    if provider == "openai":
        if "OPENAI_API_KEY" not in os.environ:
            os.environ["OPENAI_API_KEY"] = input("Enter OpenAI API Key: ")
        print(f"API key loaded for OpenAI ({get_default_model_name()}).")
        return

    if "GOOGLE_API_KEY" not in os.environ:
        os.environ["GOOGLE_API_KEY"] = input("Enter Google API Key: ")
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "0"
    print(f"API key loaded for Google ({get_default_model_name()}).")


# Allowed banking topics (used by topic_filter)
ALLOWED_TOPICS = [
    "banking", "account", "transaction", "transfer",
    "loan", "interest", "savings", "credit",
    "deposit", "withdrawal", "balance", "payment",
    "tai khoan", "giao dich", "tiet kiem", "lai suat",
    "chuyen tien", "the tin dung", "so du", "vay",
    "ngan hang", "atm",
]

# Blocked topics (immediate reject)
BLOCKED_TOPICS = [
    "hack", "exploit", "weapon", "drug", "illegal",
    "violence", "gambling", "bomb", "kill", "steal",
]
