"""
API resolver — auto-detects LLM provider with free fallbacks.
Priority: user key → free APIs → mock agents.
"""

import os
import json
import urllib.request

# Free API endpoints that work without credit card
FREE_APIS = [
    {
        "name": "Google Gemini",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "key_env": "GEMINI_API_KEY",
        "model": "gemini-2.0-flash",
        "signup": "https://aistudio.google.com/apikey",
    },
    {
        "name": "Groq",
        "base_url": "https://api.groq.com/openai/v1",
        "key_env": "GROQ_API_KEY",
        "model": "llama-3.3-70b-versatile",
        "signup": "https://console.groq.com/keys",
    },
    {
        "name": "OpenRouter (free)",
        "base_url": "https://openrouter.ai/api/v1",
        "key_env": "OPENROUTER_API_KEY",
        "model": "google/gemini-2.0-flash-001",
        "signup": "https://openrouter.ai/keys",
    },
]


def get_api_config() -> dict:
    """
    Returns {api_key, base_url, model, provider} for the best available provider.
    Checks in order: user keys → free APIs.
    """
    # 1. User's own keys
    for env_key, base_url, model, provider in [
        ("DEEPSEEK_API_KEY", "https://api.deepseek.com/v1", "deepseek-chat", "deepseek"),
        ("OPENAI_API_KEY", "https://api.openai.com/v1", "gpt-4o", "openai"),
    ]:
        key = os.getenv(env_key)
        if key:
            return {"api_key": key, "base_url": base_url, "model": model, "provider": provider}

    # 2. Free APIs
    for api in FREE_APIS:
        key = os.getenv(api["key_env"])
        if key:
            return {
                "api_key": key,
                "base_url": api["base_url"],
                "model": api["model"],
                "provider": api["name"],
            }

    return {"api_key": None, "base_url": None, "model": None, "provider": None}


def get_free_api_status() -> list[dict]:
    """Return status of all free APIs (which are configured)."""
    results = []
    for api in FREE_APIS:
        key = os.getenv(api["key_env"])
        results.append({
            "name": api["name"],
            "configured": bool(key),
            "model": api["model"],
            "signup_url": api["signup"],
        })
    return results


def call_llm(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.3,
    max_tokens: int = 2000,
    model_override: str | None = None,
) -> str:
    """
    Call the best available LLM. Tries user keys first, then free APIs.
    """
    config = get_api_config()

    if not config["api_key"]:
        raise RuntimeError(
            "No API key configured. Set DEEPSEEK_API_KEY or get a free key from:\n"
            + "\n".join(f"  {a['name']}: {a['signup']}" for a in FREE_APIS)
        )

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
