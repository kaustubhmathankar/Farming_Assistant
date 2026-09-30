from __future__ import annotations

import re
from statistics import mean
from typing import Any

from fastapi import HTTPException, UploadFile
from groq import Groq

from app.config import settings

SUPPORTED = {
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi",
}

ALIASES = {
    "en": "en",
    "eng": "en",
    "english": "en",
    "hi": "hi",
    "hin": "hi",
    "hindi": "hi",
    "हिंदी": "hi",
    "mr": "mr",
    "mar": "mr",
    "marathi": "mr",
    "मराठी": "mr",
    "gu": "gu",
    "guj": "gu",
    "gujarati": "gu",
    "it": "it",
    "ita": "it",
    "italian": "it",
}

PROMPTS = {
    "en": (
        "Indian farming speech. Terms may include crop, cotton, soybean, "
        "soil, fertilizer, irrigation, weather, mandi, market price, "
        "disease, pest, leaves and field."
    ),
    "hi": (
        "भारतीय खेती की बातचीत। शब्दों में किसान, फसल, कपास, सोयाबीन, "
        "मिट्टी, खाद, सिंचाई, मौसम, मंडी भाव, बीमारी, कीट, पत्ते और खेत "
        "शामिल हो सकते हैं।"
    ),
    "mr": (
        "भारतीय शेतीची बातचीत. शब्दांमध्ये शेतकरी, पीक, कापूस, सोयाबीन, "
        "माती, खत, सिंचन, हवामान, बाजारभाव, रोग, किड, पाने आणि शेत "
        "यांचा समावेश होऊ शकतो."
    ),
}


def normalize_language(value: str | None) -> str | None:
    if not value:
        return None
    return ALIASES.get(str(value).strip().lower())


def normalize_supported(value: str | None, fallback: str = "mr") -> str:
    normalized = normalize_language(value)
    if normalized in SUPPORTED:
        return normalized
    fallback = normalize_language(fallback)
    return fallback if fallback in SUPPORTED else "mr"


def _attr(obj: Any, name: str, default=None):
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _text(response: Any) -> str:
    return str(_attr(response, "text", "") or "").strip()


def _avg_logprob(response: Any) -> float | None:
    values: list[float] = []
    for segment in _attr(response, "segments", []) or []:
        value = _attr(segment, "avg_logprob")
        if value is None:
            continue
        try:
            values.append(float(value))
        except (TypeError, ValueError):
            pass
    return mean(values) if values else None


def _script_counts(text: str) -> dict[str, int]:
    return {
        "dev": sum(0x0900 <= ord(c) <= 0x097F for c in text),
        "gu": sum(0x0A80 <= ord(c) <= 0x0AFF for c in text),
        "lat": sum(c.isascii() and c.isalpha() for c in text),
    }


def _needs_recovery(raw_language: str | None, transcript: str, logprob: float | None) -> bool:
    if raw_language not in SUPPORTED:
        return True
    if logprob is not None and logprob < -0.75:
        return True

    counts = _script_counts(transcript)
    non_latin = counts["dev"] + counts["gu"]

    if raw_language == "en" and non_latin > max(12, counts["lat"]):
        return True

    if raw_language in {"hi", "mr"} and counts["gu"] > 3:
        return True

    return False


def _transcribe_once(client: Groq, filename: str, data: bytes, language: str | None = None):
    payload = {
        "file": (filename, data),
        "model": settings.stt_model,
        "response_format": "verbose_json",
        "temperature": 0.0,
    }

    if language in SUPPORTED:
        payload["language"] = language
        payload["prompt"] = PROMPTS[language]

    return client.audio.transcriptions.create(**payload)


def _judge_candidates(client: Groq, candidates: list[dict], initial: str) -> str | None:
    candidate_text = "\n\n".join(
        f"{item['language']}: {item['transcript']}" for item in candidates
    )

    prompt = (
        "Identify the language actually spoken by the farmer. "
        "Only three choices are allowed: en, hi, mr. "
        "Candidate transcripts may contain speech-recognition errors. "
        "Use grammar, vocabulary, sentence structure and farming terms. "
        "Do not choose Gujarati, Italian or any other language. "
        "Return only one code.\n\n"
        f"Initial transcription:\n{initial}\n\n"
        f"Candidate transcriptions:\n{candidate_text}"
    )

    try:
        response = client.chat.completions.create(
            model=settings.groq_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a strict language classifier. Return only en, hi, or mr.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=3,
        )

        raw = str(response.choices[0].message.content or "").lower()
        match = re.search(r"\b(en|hi|mr)\b", raw)
        if match:
            return match.group(1)
    except Exception as exc:
        print(f"[VOICE] Language judge skipped: {exc}")

    return None


def _recover(client: Groq, filename: str, data: bytes, initial: str, preferred: str, raw_language: str | None):
    candidates: list[dict] = []

    for language in ("mr", "hi", "en"):
        try:
            response = _transcribe_once(client, filename, data, language)
            transcript = _text(response)
            if not transcript:
                continue

            logprob = _avg_logprob(response)
            score = logprob if logprob is not None else -1.5
            score += min(1.5, len(transcript) / 40)

            counts = _script_counts(transcript)
            if language in {"hi", "mr"}:
                score += min(2.0, counts["dev"] / 30)
            else:
                score += min(2.0, counts["lat"] / 30)

            candidates.append({
                "language": language,
                "transcript": transcript,
                "score": score,
            })

            print(
                f"[VOICE] Candidate {language}: score={score:.3f}, "
                f"logprob={logprob}, transcript={transcript}"
            )

        except Exception as exc:
            print(f"[VOICE] Candidate {language} failed: {exc}")

    if not candidates:
        return initial, preferred

    candidates.sort(key=lambda item: item["score"], reverse=True)
    selected = candidates[0]

    if len(candidates) >= 2 and (candidates[0]["score"] - candidates[1]["score"]) < 0.85:
        judged = _judge_candidates(client, candidates, initial)
        if judged:
            selected = next(
                (item for item in candidates if item["language"] == judged),
                selected,
            )

    print("\n============================================================")
    print("[VOICE] Smart recovery")
    print(f"[VOICE] Whisper language: {raw_language}")
    print(f"[VOICE] Final language: {selected['language']}")
    print(f"[VOICE] Final transcript: {selected['transcript']}")
    print("============================================================")

    return selected["transcript"], selected["language"]


async def transcribe(
    upload: UploadFile,
    preferred_language: str | None = None,
    language_hint: str | None = None,
) -> tuple[str, str]:
    preferred = normalize_supported(preferred_language)
    requested = normalize_language(language_hint)

    max_bytes = settings.audio_max_size_mb * 1024 * 1024
    data = await upload.read(max_bytes + 1)

    if len(data) > max_bytes:
        raise HTTPException(status_code=413, detail="Audio is too large.")
    if not data:
        raise HTTPException(status_code=400, detail="Audio is empty.")

    filename = upload.filename or "voice.webm"
    client = Groq(api_key=settings.groq_api_key)

    # Explicit language selected by the farmer.
    if requested in SUPPORTED:
        try:
            response = _transcribe_once(client, filename, data, requested)
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail="Speech recognition failed. Please try speaking again.",
            ) from exc

        transcript = _text(response)
        if not transcript:
            raise HTTPException(
                status_code=400,
                detail="Could not understand the audio. Please speak clearly and try again.",
            )

        print(f"[VOICE] Explicit mode: {requested}")
        print(f"[VOICE] Transcript: {transcript}")
        return transcript, requested

    # Auto detection.
    try:
        response = _transcribe_once(client, filename, data, None)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Speech recognition failed. Please try speaking again.",
        ) from exc

    transcript = _text(response)
    if not transcript:
        raise HTTPException(
            status_code=400,
            detail="Could not understand the audio. Please speak clearly and try again.",
        )

    raw_language = _attr(response, "language", None)
    raw_language = normalize_language(str(raw_language) if raw_language else None)
    logprob = _avg_logprob(response)

    print("\n============================================================")
    print("[VOICE] Auto detection")
    print(f"[VOICE] Raw language: {raw_language}")
    print(f"[VOICE] Log probability: {logprob}")
    print(f"[VOICE] Transcript: {transcript}")
    print("============================================================")

    if not _needs_recovery(raw_language, transcript, logprob):
        return transcript, raw_language  # type: ignore[return-value]

    print("[VOICE] Entering supported-language recovery.")
    return _recover(
        client,
        filename,
        data,
        transcript,
        preferred,
        raw_language,
    )
