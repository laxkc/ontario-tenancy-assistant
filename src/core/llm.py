"""LLM factory for Gemini (Google Generative AI)."""

import sys
from pathlib import Path
from typing import Optional

# Add root directory to path for config import
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from langchain_core.language_models import BaseChatModel
from config import GEMINI_API_KEY, LLM_MODEL_NAME, LLM_TEMPERATURE


def get_llm(
    model_name: Optional[str] = None,
    temperature: Optional[float] = None,
    **kwargs
) -> BaseChatModel:
    """
    Create a Gemini chat model instance with smart fallbacks.
    Works with the latest v1 API and model naming (gemini-1.5 / gemini-2.x).
    """
    import os
    from langchain_google_genai import ChatGoogleGenerativeAI

    api_key = os.getenv("GEMINI_API_KEY") or GEMINI_API_KEY
    if not api_key:
        raise ValueError("❌ GEMINI_API_KEY not set. Add it to .env or environment variables.")

    # defaults
    model_name = (
        model_name
        or os.getenv("LLM_MODEL_NAME")
        or LLM_MODEL_NAME
        or "models/gemini-1.5-flash-latest"
    )
    temperature = float(os.getenv("LLM_TEMPERATURE") or LLM_TEMPERATURE or 0.2)

    # try to detect available models
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        all_models = [m for m in genai.list_models() if "generateContent" in m.supported_generation_methods]
        available = [m.name for m in all_models]
        print(f"📋 Found {len(available)} Gemini models via API")

        # Normalize requested name (ensure "models/" prefix)
        normalized = model_name if model_name.startswith("models/") else f"models/{model_name}"

        if normalized in available:
            print(f"✅ Using configured model: {normalized}")
            return ChatGoogleGenerativeAI(
                model=normalized,
                temperature=temperature,
                google_api_key=api_key,
                **kwargs,
            )

        # choose best available fallback
        preferred = [
            "models/gemini-2.0-pro",
            "models/gemini-2.0-flash",
            "models/gemini-1.5-pro-latest",
            "models/gemini-1.5-flash-latest",
        ]
        for m in preferred:
            if m in available:
                print(f"✅ Using available model: {m}")
                return ChatGoogleGenerativeAI(
                    model=m,
                    temperature=temperature,
                    google_api_key=api_key,
                    **kwargs,
                )

        # fallback to first listed
        fallback = available[0]
        print(f"⚙️ Using first available model: {fallback}")
        return ChatGoogleGenerativeAI(
            model=fallback,
            temperature=temperature,
            google_api_key=api_key,
            **kwargs,
        )

    except Exception as err:
        print(f"⚠️ Could not list models ({err}). Falling back to static names.")

    # static fallback list
    candidates = [
        model_name,
        "models/gemini-2.0-pro",
        "models/gemini-2.0-flash",
        "models/gemini-1.5-pro-latest",
        "models/gemini-1.5-flash-latest",
    ]

    for m in candidates:
        try:
            print(f"🔧 Trying model: {m}")
            llm = ChatGoogleGenerativeAI(
                model=m,
                temperature=temperature,
                google_api_key=api_key,
                **kwargs,
            )
            print(f"✅ Created LLM with: {m}")
            return llm
        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                print(f"⚠️ Model '{m}' not found, trying next...")
                continue
            raise

    raise RuntimeError("❌ No valid Gemini models found. Check your API key and model availability at https://aistudio.google.com/apikey")
