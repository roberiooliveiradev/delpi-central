"""Planejamento puro de configuração documental — DR-1 (doc 114 §8).

Porta canônica do algoritmo `planDocumentSave` do MFE (UX-012-RW01),
agora executado no backend dentro da transação única da operação
`apply_document_requirement`. Funções puras sobre a timeline de versões
publicadas — determinístico e testável sem banco.

Invariantes (espelham `resolve_published_version`):
- A versão vencedora de uma competência é a PUBLISHED com
  `effective_from_period <= period`, desempate por `version DESC`.
- Versões são conjuntos ABSOLUTOS de itens: propagar uma exigência exige
  republicar o conjunto completo em cada boundary futuro coberto.
- Passos cujo alvo já é a configuração vigente são omitidos — o plano é
  naturalmente idempotente.
"""

from __future__ import annotations

import re
from typing import Any

PERIOD_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

Item = dict[str, Any]
VersionWithItems = dict[str, Any]
PublishStep = dict[str, Any]


def next_period(period: str) -> str:
    year, month = int(period[:4]), int(period[5:7])
    return f"{year + 1}-01" if month == 12 else f"{year}-{month + 1:02d}"


def sort_published(versions: list[VersionWithItems]) -> list[VersionWithItems]:
    """Versões PUBLISHED na ordem da resolução canônica (eff, version)."""
    return sorted(
        (
            v
            for v in versions
            if v["status"] == "PUBLISHED" and v["effective_from_period"]
        ),
        key=lambda v: (v["effective_from_period"], v["version"]),
    )


def winner_at(
    published: list[VersionWithItems], period: str
) -> VersionWithItems | None:
    """Versão vencedora de `period`: PUBLISHED, eff <= period, (eff, ver)."""
    winner = None
    for version in published:
        if version["effective_from_period"] <= period:
            winner = version
    return winner


def timeline_boundaries(published: list[VersionWithItems]) -> list[str]:
    """Boundaries distintos da timeline publicada, em ordem crescente."""
    return sorted(
        {v["effective_from_period"] for v in published}
    )


def _item_fingerprint(item: Item) -> tuple:
    """Conteúdo semântico do item — ordem/sort_order não são semântica."""
    return (
        item["item_key"],
        item["name"],
        item.get("purpose"),
        item["origin_kind"],
        item.get("recipient_area"),
        item.get("applicability") or "REQUIRED",
        item.get("branch_scope") or "BOTH",
        item["sheet"],
        item.get("totvs_report_ref"),
        item.get("requirement_notes"),
        item.get("validation_scope") or "PER_ATTACHMENT",
    )


def items_equal(a: list[Item], b: list[Item]) -> bool:
    """Igualdade estrutural de dois conjuntos de itens."""
    fingerprints = {_item_fingerprint(item) for item in a}
    if len(fingerprints) != len(b):
        return False
    return all(_item_fingerprint(item) in fingerprints for item in b)


def to_draft_items(items: list[Item]) -> list[Item]:
    return [
        {
            "item_key": item["item_key"],
            "sort_order": item.get("sort_order"),
            "sheet": item["sheet"],
            "name": item["name"],
            "purpose": item.get("purpose"),
            "origin_kind": item["origin_kind"],
            "recipient_area": item.get("recipient_area"),
            "applicability": item.get("applicability"),
            "branch_scope": item.get("branch_scope"),
            "totvs_report_ref": item.get("totvs_report_ref"),
            "requirement_notes": item.get("requirement_notes"),
            "validation_scope": item.get("validation_scope"),
        }
        for item in items
    ]


def _merge_item(base_items: list[Item], document: Item) -> list[Item]:
    """`base + item`: substitui mesma chave preservando sort_order; novo
    item entra com sort_order = max+10."""
    items = to_draft_items(base_items)
    index = next(
        (i for i, entry in enumerate(items)
         if entry["item_key"] == document["item_key"]),
        -1,
    )
    if index >= 0:
        sort_order = items[index].get("sort_order")
    else:
        sort_order = (
            max([0, *[i.get("sort_order") or 0 for i in items]]) + 10
        )
    merged = to_draft_items([document])[0]
    merged["sort_order"] = sort_order
    if index >= 0:
        items[index] = merged
    else:
        items.append(merged)
    return items


def plan_document_upsert(
    versions: list[VersionWithItems],
    document: Item,
    effective_from: str,
    effective_until: str | None,
) -> list[PublishStep]:
    """Passos de publicação da exigência `document` na janela
    [`effective_from`, `effective_until`] (sem término quando None).

    - Para cada boundary `b` em [from, until]: publicar `winner@b + item`
      (propagação — versões são conjuntos absolutos).
    - Com `until`: publicar em `next_period(until)` o conteúdo
      `winner@(until+1) − item` contra o estado PÓS-inserção.
    - Passos já vigentes são omitidos (idempotência por conteúdo).
    """
    published = sort_published(versions)
    steps: list[PublishStep] = []
    limit = effective_until or "9999-12"
    targets = sorted(
        {
            effective_from,
            *[
                b
                for b in timeline_boundaries(published)
                if b >= effective_from
            ],
        }
    )
    targets = [b for b in targets if b <= limit]
    for boundary in targets:
        winner = winner_at(published, boundary)
        base = winner["items"] if winner else []
        target = _merge_item(base, document)
        if not items_equal(target, base):
            steps.append({"effective_from": boundary, "items": target})
    if effective_until:
        at = next_period(effective_until)
        winner = winner_at(published, at)
        base = winner["items"] if winner else []
        target = [
            item
            for item in to_draft_items(base)
            if item["item_key"] != document["item_key"]
        ]
        # Estado efetivo em `at` APÓS as inserções do plano: a última
        # versão inserida com eff <= at passa a vencer — é ela que a
        # remoção precisa superar.
        last_insert = steps[-1] if steps else None
        current = last_insert["items"] if last_insert else base
        if not items_equal(target, current):
            steps.append({"effective_from": at, "items": target})
    return steps


def plan_document_removal(
    versions: list[VersionWithItems],
    item_key: str,
    effective_from: str,
) -> list[PublishStep]:
    """Passos para encerrar a exigência de `item_key` a partir de
    `effective_from` — remove o item do vencedor de cada boundary
    coberto (uma reintrodução posterior não deve ressuscitar a
    exigência encerrada)."""
    published = sort_published(versions)
    steps: list[PublishStep] = []
    targets = sorted(
        {
            effective_from,
            *[
                b
                for b in timeline_boundaries(published)
                if b >= effective_from
            ],
        }
    )
    last_insert: PublishStep | None = None
    for boundary in targets:
        winner = winner_at(published, boundary)
        base = winner["items"] if winner else []
        target = [
            item
            for item in to_draft_items(base)
            if item["item_key"] != item_key
        ]
        current = last_insert["items"] if last_insert else base
        if not items_equal(target, current):
            steps.append({"effective_from": boundary, "items": target})
            last_insert = steps[-1]
    return steps
