#!/usr/bin/env python3
"""Alinha runtime admin + reindex de embeddings das external actions (dev local)."""

from __future__ import annotations

import argparse
import json
import sys

from app.application.services.chat_intelligence_settings_service import (
    ChatIntelligenceSettingsService,
)
from app.application.use_cases.admin_chat_intelligence_use_cases import (
    ReindexExternalActionEmbeddingsUseCase,
    SaveAdminChatIntelligenceSettingsUseCase,
)
from app.composition.root_composer import create_application
from app.extensions.db import db
from app.infrastructure.config.settings import Settings

# Perfil dev operacional (infra/.env + Onda 11): heurística primeiro, RAG keyword-first.
LOCAL_DEV_INTELLIGENCE_PAYLOAD = {
    "ragContextMinScore": float(Settings.RAG_CONTEXT_MIN_SCORE),
    "externalActionSemanticMinScore": float(Settings.EXTERNAL_ACTION_SEMANTIC_MIN_SCORE),
    "externalActionSemanticRankEnabled": bool(Settings.EXTERNAL_ACTION_SEMANTIC_RANK_ENABLED),
    "chatToolRouterEnabled": bool(Settings.CHAT_TOOL_ROUTER_ENABLED),
    "chatHistorySummaryEnabled": bool(Settings.CHAT_HISTORY_SUMMARY_ENABLED),
    "ragHybridEnabled": bool(Settings.CHAT_RAG_HYBRID_ENABLED),
    "ragRerankEnabled": bool(Settings.CHAT_RAG_RERANK_ENABLED),
    "ragFtsEnabled": bool(Settings.CHAT_RAG_FTS_ENABLED),
    "nativeToolCallingEnabled": bool(Settings.CHAT_NATIVE_TOOL_CALLING_ENABLED),
    "agenticLoopEnabled": bool(Settings.CHAT_AGENTIC_LOOP_ENABLED),
    "agenticLoopMaxSteps": int(Settings.CHAT_AGENTIC_LOOP_MAX_STEPS),
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-save",
        action="store_true",
        help="Não grava chat_intelligence_settings no admin runtime.",
    )
    parser.add_argument(
        "--skip-reindex",
        action="store_true",
        help="Não reindexa embeddings das external actions.",
    )
    parser.add_argument(
        "--provider-key",
        default=None,
        help="Filtra reindex por provider (opcional).",
    )
    args = parser.parse_args()

    app = create_application()
    report: dict = {}

    with app.app_context():
        if not args.skip_save:
            saved = SaveAdminChatIntelligenceSettingsUseCase().execute(
                LOCAL_DEV_INTELLIGENCE_PAYLOAD
            )
            db.session.commit()
            report["savedSettings"] = {
                k: v
                for k, v in saved.items()
                if k != "defaults"
            }

        if not args.skip_reindex:
            report["reindex"] = ReindexExternalActionEmbeddingsUseCase().execute(
                provider_key=args.provider_key
            )
            db.session.commit()

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
