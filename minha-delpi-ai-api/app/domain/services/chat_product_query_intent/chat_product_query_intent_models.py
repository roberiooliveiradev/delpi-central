"""Modelos — intenção de consulta de produto."""

from __future__ import annotations


class ChatProductQueryIntent:
    DESCRIPTION = "description"
    SUMMARY = "summary"
    ANALYSER = "analyser"
    MULTI_SCOPE = "multi_scope"
    STOCK = "stock"
    SALES = "sales"
    STRUCTURE = "structure"
    PARENTS = "parents"
    FULL = "full"
