import os
from dotenv import load_dotenv

# This will load variables from a .env file in the same directory
load_dotenv()


# --- Salesforce Credentials ---
SF_USERNAME = os.getenv("SF_USERNAME")
SF_PASSWORD = os.getenv("SF_PASSWORD")
SF_SECURITY_TOKEN = os.getenv("SF_SECURITY_TOKEN")
SF_CLIENT_ID = os.getenv("SF_CLIENT_ID")
SF_CLIENT_SECRET = os.getenv("SF_CLIENT_SECRET")
SF_DOMAIN = os.getenv("SF_DOMAIN", "login")  # 'login' for prod, 'test' for sandbox

# --- LLM Provider Selection ---
# Options: 'gemini', 'openai', or 'anthropic'. Default to 'gemini' to preserve existing behavior.
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").strip().lower()

# --- Google Gemini Credentials ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.1"))

# --- OpenAI (GPT-5) Credentials ---
# Model and API key are specified in the .env file
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5")
# Optional tuning parameters for GPT-5 Responses API
OPENAI_REASONING_EFFORT = os.getenv("OPENAI_REASONING_EFFORT", "medium")  # minimal|low|medium|high
OPENAI_VERBOSITY = os.getenv("OPENAI_VERBOSITY", None)  # low|medium|high or None
# PDF input method: 'upload' (file upload) or 'base64' (base64 encoding)
OPENAI_PDF_METHOD = os.getenv("OPENAI_PDF_METHOD", "base64")  # upload|base64

# --- Anthropic Claude Credentials ---
# Model and API key are specified in the .env file
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
# Max tokens for Claude response (set high for effectively unlimited responses)
ANTHROPIC_MAX_TOKENS = int(os.getenv("ANTHROPIC_MAX_TOKENS", "8000"))
# Timeout for Claude requests (in seconds) - default to 20 minutes for long translations
ANTHROPIC_TIMEOUT = float(os.getenv("ANTHROPIC_TIMEOUT", "1200"))

# Cronitor keys
# CRONITOR_API_KEY = os.getenv("CRONITOR_API_KEY")
# CRONITOR_MONITOR_ID = os.getenv("CRONITOR_MONITOR_ID")

def validate_salesforce_creds():
    """Ensure all required Salesforce environment variables are set."""
    required_vars = [
        "SF_USERNAME",
        "SF_PASSWORD",
        "SF_SECURITY_TOKEN",
        "SF_CLIENT_ID",
        "SF_CLIENT_SECRET",
    ]
    missing_vars = [v for v in required_vars if not globals().get(v)]
    if missing_vars:
        raise EnvironmentError(f"Missing required Salesforce environment variables: {', '.join(missing_vars)}")

def validate_gemini_creds():
    """Ensure the Gemini API key environment variable is set."""
    if not GEMINI_API_KEY:
        raise EnvironmentError("Missing required environment variable: GEMINI_API_KEY") 


def validate_salesforce_creds():
    """Check that all required Salesforce environment variables are set."""
    required = [
        "SF_USERNAME",
        "SF_PASSWORD",
        "SF_SECURITY_TOKEN",
        "SF_CLIENT_ID",
        "SF_CLIENT_SECRET",
    ]
    missing = [v for v in required if not globals().get(v)]
    if missing:
        raise ValueError(f"Missing required Salesforce env vars in .env: {', '.join(missing)}")
    return True

def validate_gemini_creds():
    """Check that the Gemini API Key is set."""
    if not GEMINI_API_KEY:
        raise ValueError("Missing required Gemini env var in .env: GEMINI_API_KEY")
    return True 

def validate_openai_creds():
    """Check that the OpenAI API Key is set when provider is OpenAI."""
    if not OPENAI_API_KEY:
        raise ValueError("Missing required OpenAI env var in .env: OPENAI_API_KEY")
    return True

def validate_anthropic_creds():
    """Check that the Anthropic API Key is set when provider is Anthropic."""
    if not ANTHROPIC_API_KEY:
        raise ValueError("Missing required Anthropic env var in .env: ANTHROPIC_API_KEY")
    return True

def validate_llm_provider():
    """Validate that required credentials exist for the selected LLM provider."""
    if LLM_PROVIDER == "gemini":
        return validate_gemini_creds()
    if LLM_PROVIDER == "openai":
        return validate_openai_creds()
    if LLM_PROVIDER == "anthropic":
        return validate_anthropic_creds()
    raise ValueError("LLM_PROVIDER must be 'gemini', 'openai', or 'anthropic'")