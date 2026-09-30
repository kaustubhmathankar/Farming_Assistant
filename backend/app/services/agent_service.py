from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_groq import ChatGroq
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from app.config import settings
from app.services.agriculture_tools import TOOLS
from app.services.language_service import language_instruction


SYSTEM_BASE = """
You are KrishiSaathi, an AI farming assistant for Indian farmers.

Your job is to answer only the farmer's actual question.

TOOL SELECTION:
- Use search_agricultural_knowledge for stable farming knowledge.
- Use get_weather for current weather or forecast questions.
- Use get_market_prices for current mandi/market price questions.
- Use search_government_schemes for government farmer schemes.
- Use web_search only when current information is needed and no dedicated tool is appropriate.
- Do not call multiple unrelated tools.
- Do not use agricultural RAG for a simple weather question.
- Do not use weather for a fertilizer, soil, or crop-health question unless weather is relevant.

CROP IMAGE RULES:
- Treat image observations as uncertain evidence.
- Never claim a disease is 100% confirmed from an image.
- Never invent pesticide doses, fertilizer doses, or chemical recommendations.
- When the image is unclear, say so briefly.

RESPONSE STYLE — VERY IMPORTANT:
- Answer the exact question first.
- Be concise and practical.
- Normally stay around 80-120 words.
- Never exceed about 160 words unless the farmer explicitly asks for detailed information.
- Give only the information required for the question.
- Do not repeat the same information.
- Do not repeat the farmer profile.
- Do not repeat the tool result in full.
- Do not add unrelated farming advice.
- Do not add a long introduction.
- Do not add a long conclusion.
- Do not say "I hope this helps".
- Do not mention tools, prompts, LangChain, LangGraph, RAG, models, or internal processing.

FORMATTING:
- Use a short heading only when useful.
- Prefer 3-6 short bullet points for advice.
- Use numbered steps when the farmer needs to do something.
- For weather, use compact labeled lines.
- For mandi prices, use compact labeled lines.
- For schemes, give the scheme name and only the relevant benefit/eligibility information.
- Use bold labels where useful.
- Avoid large Markdown tables unless a table is genuinely useful.
- Do not create a separate Sources section because sources are displayed by the application.
"""


def content_to_text(content: Any) -> str:
    """
    Convert any LangChain/Groq content format to a plain string.

    This prevents Groq errors where a message content unexpectedly
    arrives as a list/dict instead of a string.
    """
    if content is None:
        return ""

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = []

        for item in content:
            if isinstance(item, str):
                parts.append(item)
                continue

            if isinstance(item, dict):
                # Ignore multimodal payload blocks when sending
                # conversation history back to the text model.
                if item.get("type") in {
                    "image_url",
                    "input_audio",
                    "audio",
                }:
                    continue

                value = item.get(
                    "text",
                    item.get("content"),
                )

                if value is not None:
                    parts.append(
                        content_to_text(value)
                    )

                continue

            parts.append(str(item))

        return "\n".join(
            item
            for item in parts
            if item
        )

    if isinstance(content, dict):
        value = content.get(
            "text",
            content.get("content"),
        )

        if value is not None:
            return content_to_text(value)

        return json.dumps(
            content,
            ensure_ascii=False,
        )

    return str(content)


def sanitize_message(message):
    """
    Make sure every message sent to Groq has string content
    while preserving tool calls and message metadata.
    """
    safe_content = content_to_text(
        getattr(message, "content", "")
    )

    try:
        return message.model_copy(
            update={
                "content": safe_content
            }
        )
    except Exception:
        pass

    if isinstance(message, SystemMessage):
        return SystemMessage(
            content=safe_content
        )

    if isinstance(message, HumanMessage):
        return HumanMessage(
            content=safe_content
        )

    if isinstance(message, AIMessage):
        return AIMessage(
            content=safe_content,
            tool_calls=getattr(
                message,
                "tool_calls",
                [],
            ),
            invalid_tool_calls=getattr(
                message,
                "invalid_tool_calls",
                [],
            ),
            additional_kwargs=getattr(
                message,
                "additional_kwargs",
                {},
            ),
            response_metadata=getattr(
                message,
                "response_metadata",
                {},
            ),
        )

    if isinstance(message, ToolMessage):
        return ToolMessage(
            content=safe_content,
            tool_call_id=getattr(
                message,
                "tool_call_id",
                "",
            ),
            name=getattr(
                message,
                "name",
                None,
            ),
        )

    return HumanMessage(
        content=safe_content
    )


@lru_cache(maxsize=1)
def graph():
    llm = ChatGroq(
        api_key=settings.groq_api_key,
        model=settings.groq_model,
        temperature=0,
        max_tokens=320,
    )

    llm_with_tools = llm.bind_tools(
        TOOLS,
        parallel_tool_calls=False,
    )

    def call_model(state: MessagesState):
        safe_messages = [
            sanitize_message(message)
            for message in state.get(
                "messages",
                [],
            )
        ]

        response = llm_with_tools.invoke(
            safe_messages
        )

        return {
            "messages": [response]
        }

    builder = StateGraph(
        MessagesState
    )

    builder.add_node(
        "agent",
        call_model
    )

    builder.add_node(
        "tools",
        ToolNode(TOOLS)
    )

    builder.add_edge(
        START,
        "agent"
    )

    builder.add_conditional_edges(
        "agent",
        tools_condition
    )

    builder.add_edge(
        "tools",
        "agent"
    )

    builder.add_edge(
        "agent",
        END
    )

    return builder.compile()


def _extract(result):
    answer = ""
    sources = []
    tools_used = []

    for message in result.get(
        "messages",
        [],
    ):
        if isinstance(
            message,
            ToolMessage,
        ):
            raw = content_to_text(
                message.content
            )

            try:
                payload = json.loads(raw)

                if (
                    isinstance(payload, dict)
                    and isinstance(
                        payload.get("sources"),
                        list,
                    )
                ):
                    sources.extend(
                        item
                        for item in payload["sources"]
                        if isinstance(item, dict)
                    )

            except (
                TypeError,
                ValueError,
            ):
                pass

            tool_name = getattr(
                message,
                "name",
                None,
            )

            if tool_name:
                tools_used.append(
                    str(tool_name)
                )

        elif isinstance(
            message,
            AIMessage,
        ):
            text = content_to_text(
                message.content
            ).strip()

            if text:
                answer = text

    unique_sources = []
    seen = set()

    for source in sources:
        key = (
            source.get("title"),
            source.get("url"),
        )

        if key in seen:
            continue

        seen.add(key)
        unique_sources.append(source)

    return (
        answer,
        unique_sources[:10],
        list(dict.fromkeys(tools_used)),
    )


def run_agent(
    message: str,
    *,
    language: str,
    history: list[dict] | None = None,
    farmer_context: str = "",
    visual_observations: str = "",
):
    system = (
        SYSTEM_BASE
        + "\n\n"
        + language_instruction(language)
    )

    if farmer_context:
        system += (
            "\n\nFARMER PROFILE CONTEXT:\n"
            + content_to_text(
                farmer_context
            )
        )

    if visual_observations:
        system += (
            "\n\nCROP IMAGE OBSERVATIONS "
            "(uncertain evidence):\n"
            + content_to_text(
                visual_observations
            )
        )

    messages = [
        SystemMessage(
            content=system
        )
    ]

    for item in history or []:
        if not isinstance(
            item,
            dict,
        ):
            continue

        content = content_to_text(
            item.get(
                "content",
                "",
            )
        )

        if not content.strip():
            continue

        if item.get("role") == "user":
            messages.append(
                HumanMessage(
                    content=content
                )
            )

        elif item.get("role") == "assistant":
            messages.append(
                AIMessage(
                    content=content
                )
            )

    current = content_to_text(message)

    if not current.strip():
        raise ValueError(
            "The user's message is empty."
        )

    messages.append(
        HumanMessage(
            content=current
        )
    )

    result = graph().invoke(
        {
            "messages": messages
        }
    )

    return _extract(result)