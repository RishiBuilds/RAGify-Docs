from __future__ import annotations
import json
import logging
from typing import Any
from langchain_core.documents import Document
from openai import OpenAI
from pydantic import ValidationError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
from app.config import settings
from app.schemas import QAResponse, SourceReference

logger = logging.getLogger(__name__)

_llm_client: OpenAI | None = None

def _get_client() -> OpenAI:
    global _llm_client
    if _llm_client is None:
        _llm_client = OpenAI(
            api_key=settings.groq_api_key,
            base_url=settings.groq_base_url,
        )
    return _llm_client

_SYSTEM_PROMPT = """\
You are a precise document question-answering assistant.

RULES:
1. Answer ONLY using the provided context chunks. Do NOT use prior knowledge.
2. If the answer is not in the context, respond with exactly:
   "I don't know based on the provided documents."
3. Return your response as a SINGLE valid JSON object matching this schema:

{schema}

IMPORTANT:
- "page_number" values come from the chunk metadata - use them as-is.
- "snippet" should be a short, relevant excerpt from the chunk that supports
  your answer.
- "confidence" should be "high", "medium", or "low" based on how well the
  context supports the answer. Note: this is a rough self-assessment.
- Do NOT wrap the JSON in markdown code fences.
- Do NOT include any text outside the JSON object.
"""

def _build_messages(
    question: str, context_chunks: list[Document]
) -> list[dict[str, str]]:
    schema_str = json.dumps(QAResponse.model_json_schema(), indent=2)

    context_parts: list[str] = []
    for i, doc in enumerate(context_chunks, 1):
        source = doc.metadata.get("source", "unknown")
        page = doc.metadata.get("page", "?")
        context_parts.append(
            f"--- Chunk {i} [source: {source}, page: {page}] ---\n"
            f"{doc.page_content}\n"
        )

    context_text = "\n".join(context_parts)

    return [
        {"role": "system", "content": _SYSTEM_PROMPT.format(schema=schema_str)},
        {
            "role": "user",
            "content": (
                f"Context:\n{context_text}\n\n"
                f"Question: {question}"
            ),
        },
    ]

@retry(
    retry=retry_if_exception_type((TimeoutError, ConnectionError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=15),
    reraise=True,
)
def _call_groq(
    messages: list[dict[str, str]],
    response_format: dict[str, str] | None = None,
) -> str:
    client = _get_client()
    kwargs: dict[str, Any] = {
        "model": settings.groq_model,
        "messages": messages,
        "temperature": 0.1,
    }
    if response_format:
        kwargs["response_format"] = response_format

    try:
        completion = client.chat.completions.create(**kwargs)
    except Exception as exc:
        if response_format and "response_format" in str(exc).lower():
            logger.warning(
                "Groq may not support response_format; retrying without it."
            )
            kwargs.pop("response_format", None)
            completion = client.chat.completions.create(**kwargs)
        else:
            raise

    return completion.choices[0].message.content or ""

def _truncate_snippet(text: str) -> str:
    limit = settings.snippet_max_length
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"

def _extract_json(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

def _parse_response(raw: str) -> QAResponse | None:
    cleaned = _extract_json(raw)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        return None

    if "sources" in data and isinstance(data["sources"], list):
        for src in data["sources"]:
            if "snippet" in src and isinstance(src["snippet"], str):
                src["snippet"] = _truncate_snippet(src["snippet"])

    try:
        return QAResponse.model_validate(data)
    except ValidationError:
        return None

def generate_answer(
    question: str,
    context_chunks: list[Document],
) -> QAResponse:
    if not context_chunks:
        return QAResponse(
            answer="No relevant context was found in the uploaded documents.",
            sources=[],
            confidence="low",
        )

    messages = _build_messages(question, context_chunks)

    logger.debug("LLM Tier 1: JSON mode request")
    raw = _call_groq(messages, response_format={"type": "json_object"})
    result = _parse_response(raw)
    if result is not None:
        logger.debug("Tier 1 succeeded.")
        return result

    logger.warning("Tier 1 JSON parsing failed; trying Tier 2 reprompt.")
    schema_str = json.dumps(QAResponse.model_json_schema(), indent=2)
    repair_messages = messages + [
        {"role": "assistant", "content": raw},
        {
            "role": "user",
            "content": (
                "Your previous response was not valid JSON. "
                "Please reformat your answer as a single valid JSON object "
                f"matching this schema:\n{schema_str}\n"
                "Do NOT include any text outside the JSON."
            ),
        },
    ]
    raw2 = _call_groq(repair_messages, response_format={"type": "json_object"})
    result2 = _parse_response(raw2)
    if result2 is not None:
        logger.debug("Tier 2 succeeded.")
        return result2

    logger.warning(
        "Tier 2 also failed; falling back to Tier 3 (raw text as answer)."
    )
    return QAResponse(
        answer=raw.strip(),
        sources=[],
        confidence="low",
    )
