#!/usr/bin/env python3
"""Smoke local: pergunta de identidade deve usar RAG + LLM (não resposta enlatada)."""

from __future__ import annotations

import json
import sys

from app.application.dto.send_chat_message_request import SendChatMessageRequest
from app.composition.chat_composer import make_stream_chat_message_use_case
from app.main import create_app


def main() -> int:
    if len(sys.argv) < 4:
        print(
            "Uso: python scripts/smoke_identity_rag.py <user_id> <session_id> <mensagem>",
            file=sys.stderr,
        )
        return 2

    user_id, session_id, message = sys.argv[1], sys.argv[2], sys.argv[3]

    app = create_app()
    with app.app_context():
        use_case = make_stream_chat_message_use_case()
        request = SendChatMessageRequest(
            user_id=user_id,
            session_id=session_id,
            message=message,
            access_token=None,
        )
        events = list(use_case.stream(request))

    done = next((event for event in events if event.get("type") == "done"), {})
    admin = done.get("adminDebug") or {}
    pipeline = admin.get("pipeline") or {}
    rag = admin.get("rag") or {}
    llm = admin.get("llm") or {}

    print(json.dumps({
        "eventTypes": [event.get("type") for event in events],
        "skipRag": pipeline.get("skipRag"),
        "sourceCount": len(rag.get("sources") or []),
        "sourceTitles": [
            (source.get("title") or source.get("documentTitle") or "?")
            for source in (rag.get("sources") or [])[:5]
        ],
        "llmMessageCount": len(llm.get("messages") or []),
        "answerPreview": (done.get("answer") or "")[:280],
    }, ensure_ascii=False, indent=2))

    # adminDebug no evento done pode estar filtrado; validação mínima: não é resposta enlatada.
    answer = (done.get("answer") or "").lower()
    canned_markers = (
        "orquestrado pelo backend da minha delpi",
        "não sou uma pessoa: sou software",
    )
    looks_canned = any(marker in answer for marker in canned_markers)

    ok = not looks_canned and bool(answer.strip())
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
