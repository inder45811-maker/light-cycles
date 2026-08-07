"""
API resolver — auto-detects the configured LLM provider.
Supports DeepSeek, OpenAI, and any OpenAI-compatible endpoint.
Reads from standard env vars.
"""

import os


def get_api_config() -> dict:
    """
    Returns {api_key, base_url, model} for the configured provider.
    Checks in order: DEEPSEEK, OPENAI, then any generic LLM config.
    """
    # DeepSeek
    key = os.getenv("DEEPSEEK_API_KEY")
    if key:
        return {
            "api_key": key,
            "base_url": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
            "model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            "provider": "deepseek",
        }

    # OpenAI
    key = os.getenv("OPENAI_API_KEY")
    if key:
        return {
            "api_key": key,
            "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            "model": os.getenv("OPENAI_MODEL", "gpt-4o"),
            "provider": "openai",
        }

    # Generic / OpenRouter / any OpenAI-compatible
    key = os.getenv("LLM_API_KEY")
    if key:
        return {
            "api_key": key,
            "base_url": os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"),
            "model": os.getenv("LLM_MODEL", "gpt-4o"),
            "provider": "generic",
        }

    return {"api_key": None, "base_url": None, "model": None, "provider": None}


def call_llm(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.3,
    max_tokens: int = 2000,
    model_override: str | None = None,
) -> str:
    """
    Call the configured LLM and return the response text.
    Works with DeepSeek, OpenAI, or any OpenAI-compatible endpoint.
    """
    import json
    import urllib.request

    config = get_api_config()

    if not config["api_key"]:
        raise RuntimeError("No API key configured. Set DEEPSEEK_API_KEY or OPENAI_API_KEY.")

    body = json.dumps({
        "model": model_override or config["model"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }).encode()

    req = urllib.request.Request(
        f"{config['base_url']}/chat/completions",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config['api_key']}",
        },
    )

    resp = json.loads(urllib.request.urlopen(req, timeout=120).read())
    return resp["choices"][0]["message"]["content"]
