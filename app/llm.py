from __future__ import annotations

import json
import site
import sys
from dataclasses import dataclass
from urllib import error, request

from app.config import AppConfig

user_site_packages = site.getusersitepackages()
if user_site_packages and user_site_packages not in sys.path:
    sys.path.append(user_site_packages)

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - optional dependency during bootstrap
    OpenAI = None


@dataclass(frozen=True)
class InsightResult:
    status: str
    content: str


def _fallback_message() -> InsightResult:
    config = AppConfig()
    if not config.openai_api_key and not config.gemini_api_key:
        return InsightResult(
            status="missing_api_key",
            content=(
                "Add `OPENAI_API_KEY` or `GEMINI_API_KEY` to your `.env` file or deployment secrets "
                "to enable live LLM insights."
            ),
        )
    return InsightResult(status="unavailable", content="LLM service is unavailable.")


def generate_executive_insight(context: dict, question: str | None = None) -> InsightResult:
    config = AppConfig()
    if not config.openai_api_key and not config.gemini_api_key:
        return _fallback_message()

    prompt = _build_prompt(context, question)

    try:
        if config.openai_api_key and OpenAI is not None:
            client = OpenAI(api_key=config.openai_api_key)
            if hasattr(client, "responses"):
                response = client.responses.create(
                    model=config.openai_model,
                    input=prompt,
                )
                content = getattr(response, "output_text", "").strip()
            else:  # pragma: no cover - backward compatibility for older SDKs
                response = client.chat.completions.create(
                    model=config.openai_model,
                    messages=[{"role": "user", "content": prompt}],
                )
                content = response.choices[0].message.content.strip()
        elif config.openai_api_key:
            content = _generate_with_http(
                api_key=config.openai_api_key,
                model=config.openai_model,
                prompt=prompt,
            )
        else:
            content = _generate_gemini_with_http(
                api_key=config.gemini_api_key,
                model=config.gemini_model,
                prompt=prompt,
            )
    except Exception as exc:  # pragma: no cover - network/runtime dependent
        return InsightResult(status="error", content=f"LLM request failed: {exc}")

    return InsightResult(
        status="success",
        content=content or "The model returned an empty response.",
    )


def _build_prompt(context: dict, question: str | None = None) -> str:
    analyst_brief = [
        "You are an executive sales analyst.",
        "Review the filtered dashboard data and write concise, decision-ready insights.",
        "Cover trend, opportunities, risks, and recommended actions.",
        "Use short sections with bullets when useful.",
        "Do not invent metrics that are not present in the input.",
    ]
    if question:
        analyst_brief.append(f"User question: {question}")

    payload = json.dumps(context, indent=2, default=str)
    return "\n".join(analyst_brief) + f"\n\nDashboard context:\n{payload}"


def _generate_with_http(api_key: str, model: str, prompt: str) -> str:
    payload = json.dumps({"model": model, "input": prompt}).encode("utf-8")
    req = request.Request(
        url="https://api.openai.com/v1/responses",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=60) as response:
            body = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:  # pragma: no cover - runtime dependent
        details = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"OpenAI HTTP error {exc.code}: {details}") from exc
    except error.URLError as exc:  # pragma: no cover - runtime dependent
        raise RuntimeError(f"OpenAI network error: {exc.reason}") from exc

    output_text = body.get("output_text", "").strip()
    if output_text:
        return output_text

    fragments: list[str] = []
    for item in body.get("output", []):
        for content in item.get("content", []):
            text = content.get("text")
            if text:
                fragments.append(text)

    return "\n".join(fragments).strip()


def _generate_gemini_with_http(api_key: str, model: str, prompt: str) -> str:
    payload = json.dumps(
        {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt,
                        }
                    ]
                }
            ]
        }
    ).encode("utf-8")
    req = request.Request(
        url=f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=60) as response:
            body = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:  # pragma: no cover - runtime dependent
        details = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Gemini HTTP error {exc.code}: {details}") from exc
    except error.URLError as exc:  # pragma: no cover - runtime dependent
        raise RuntimeError(f"Gemini network error: {exc.reason}") from exc

    candidates = body.get("candidates", [])
    if not candidates:
        raise RuntimeError(f"Gemini returned no candidates: {body}")

    fragments: list[str] = []
    for part in candidates[0].get("content", {}).get("parts", []):
        text = part.get("text")
        if text:
            fragments.append(text)

    return "\n".join(fragments).strip()
