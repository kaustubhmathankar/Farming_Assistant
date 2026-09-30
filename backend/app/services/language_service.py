SUPPORTED_LANGUAGES = {"en": "English", "hi": "Hindi", "mr": "Marathi"}
ALIASES = {
    "english": "en", "en": "en",
    "hindi": "hi", "हिंदी": "hi", "hi": "hi",
    "marathi": "mr", "मराठी": "mr", "mr": "mr",
}


def normalize_language(value: str | None) -> str:
    if not value:
        return "mr"
    key = value.strip().lower()
    return ALIASES.get(key, "mr")


def language_name(code: str) -> str:
    return SUPPORTED_LANGUAGES.get(normalize_language(code), "Marathi")


def speech_code(code: str) -> str:
    return {"en": "en-IN", "hi": "hi-IN", "mr": "mr-IN"}.get(normalize_language(code), "mr-IN")


def language_instruction(code: str) -> str:
    return (
        f"Respond in {language_name(code)}. Use simple, practical farmer-friendly language. "
        "Prefer short steps, local-friendly units, and explain technical terms."
    )
