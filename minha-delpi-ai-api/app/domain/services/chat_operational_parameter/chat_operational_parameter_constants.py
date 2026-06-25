"""Constantes — parâmetros operacionais."""

from __future__ import annotations

from app.domain.services.chat_product_query_intent_service import ChatProductQueryIntent

INTENTS_REQUIRING_CODE = frozenset(
        {
            ChatProductQueryIntent.STOCK,
            ChatProductQueryIntent.STRUCTURE,
            ChatProductQueryIntent.PARENTS,
            ChatProductQueryIntent.DESCRIPTION,
            ChatProductQueryIntent.ANALYSER,
            ChatProductQueryIntent.SUMMARY,
        }
    )
