"""Testes unitários do planner de configuração documental (DR-1).

Matriz portada de `documentCatalog.test.ts` (UX-012-RW01) para o módulo
canônico do domínio — puro, sem banco.
"""

from __future__ import annotations

from controllership_finance_app.domain.closing_checklist import (
    document_requirement as dr,
)

BASE_ITEM = {
    "sheet": "ELETRONICO",
    "origin_kind": "EXTERNAL",
    "recipient_area": None,
    "applicability": "REQUIRED",
    "branch_scope": "BOTH",
    "totvs_report_ref": None,
    "purpose": None,
    "requirement_notes": None,
    "validation_scope": "PER_ATTACHMENT",
}


def _item(key: str, name: str | None = None, **overrides):
    item = {
        "item_key": key,
        "name": name or f"Doc {key}",
        "sort_order": 10,
        **BASE_ITEM,
    }
    item.update(overrides)
    return item


def _version(
    version: int,
    eff: str,
    items: list,
    status: str = "PUBLISHED",
):
    return {
        "version": version,
        "status": status,
        "effective_from_period": eff,
        "items": items,
    }


ITEM_A = _item("ITEM_A", "Nota fiscal")
ITEM_B = _item("ITEM_B", "Balancete")
ITEM_C = _item("ITEM_C", "Relatório extra")


class TestPlanUpsert:
    def test_future_inclusion_single_step(self):
        versions = [_version(1, "2026-01", [ITEM_A])]
        steps = dr.plan_document_upsert(
            versions, ITEM_C, "2026-11", None
        )
        assert steps == [
            {
                "effective_from": "2026-11",
                "items": steps[0]["items"],
            }
        ]
        keys = {i["item_key"] for i in steps[0]["items"]}
        assert keys == {"ITEM_A", "ITEM_C"}

    def test_propagates_across_future_boundaries(self):
        # A em 01; B entra em 03; C sai em 05 — inserir X em 04 deve
        # propagar aos boundaries 04 (winner B+C? não: winner@04 = v2)
        versions = [
            _version(1, "2026-01", [ITEM_A]),
            _version(2, "2026-03", [ITEM_A, ITEM_B]),
            _version(3, "2026-05", [ITEM_A]),
        ]
        steps = dr.plan_document_upsert(
            versions, ITEM_C, "2026-04", None
        )
        assert [s["effective_from"] for s in steps] == [
            "2026-04",
            "2026-05",
        ]
        keys04 = {i["item_key"] for i in steps[0]["items"]}
        keys05 = {i["item_key"] for i in steps[1]["items"]}
        assert keys04 == {"ITEM_A", "ITEM_B", "ITEM_C"}
        assert keys05 == {"ITEM_A", "ITEM_C"}

    def test_window_end_publishes_removal_at_until_plus_one(self):
        versions = [_version(1, "2026-01", [ITEM_A, ITEM_B])]
        steps = dr.plan_document_upsert(
            versions, ITEM_C, "2026-04", "2026-06"
        )
        assert [s["effective_from"] for s in steps] == [
            "2026-04",
            "2026-07",
        ]
        keys_insert = {i["item_key"] for i in steps[0]["items"]}
        keys_remove = {i["item_key"] for i in steps[1]["items"]}
        assert keys_insert == {"ITEM_A", "ITEM_B", "ITEM_C"}
        assert keys_remove == {"ITEM_A", "ITEM_B"}

    def test_removal_compares_against_post_insert_state(self):
        # Sem o fix RW01 a remoção comparava contra o vencedor ORIGINAL
        # de until+1 e não removia o item propagado.
        versions = [_version(1, "2026-01", [ITEM_A])]
        steps = dr.plan_document_upsert(
            versions, ITEM_C, "2026-04", "2026-05"
        )
        assert [s["effective_from"] for s in steps] == [
            "2026-04",
            "2026-06",
        ]
        keys_remove = {i["item_key"] for i in steps[1]["items"]}
        assert keys_remove == {"ITEM_A"}

    def test_noop_when_already_effective(self):
        versions = [_version(1, "2026-01", [ITEM_A, ITEM_C])]
        steps = dr.plan_document_upsert(
            versions, ITEM_C, "2026-04", None
        )
        # winner@2026-04 já contém ITEM_C idêntico → sem versão nova
        assert steps == []

    def test_out_of_order_publication(self):
        # Publicar boundary 06 antes de 04 — o plano cobre os dois.
        versions = [_version(1, "2026-01", [ITEM_A])]
        steps = dr.plan_document_upsert(
            versions, ITEM_C, "2026-04", "2026-06"
        )
        effs = [s["effective_from"] for s in steps]
        assert effs == ["2026-04", "2026-07"]

    def test_overlapping_existing_window(self):
        versions = [
            _version(1, "2026-01", [ITEM_A]),
            _version(2, "2026-06", [ITEM_A, ITEM_B]),
        ]
        steps = dr.plan_document_upsert(
            versions, ITEM_C, "2026-03", "2026-08"
        )
        effs = [s["effective_from"] for s in steps]
        assert effs == ["2026-03", "2026-06", "2026-09"]
        keys06 = {i["item_key"] for i in steps[1]["items"]}
        assert keys06 == {"ITEM_A", "ITEM_B", "ITEM_C"}

    def test_edit_replaces_same_key(self):
        edited = _item("ITEM_A", "Nota fiscal (revisada)")
        versions = [_version(1, "2026-01", [ITEM_A, ITEM_B])]
        steps = dr.plan_document_upsert(versions, edited, "2026-05", None)
        assert len(steps) == 1
        found = [
            i
            for i in steps[0]["items"]
            if i["item_key"] == "ITEM_A"
        ]
        assert found[0]["name"] == "Nota fiscal (revisada)"
        assert len(steps[0]["items"]) == 2

    def test_tie_same_effective_from_higher_version_wins(self):
        versions = [
            _version(1, "2026-03", [ITEM_A]),
            _version(2, "2026-03", [ITEM_A, ITEM_B]),
        ]
        winner = dr.winner_at(dr.sort_published(versions), "2026-03")
        assert winner["version"] == 2


class TestPlanRemoval:
    def test_removal_from_period(self):
        versions = [_version(1, "2026-01", [ITEM_A, ITEM_C])]
        steps = dr.plan_document_removal(versions, "ITEM_C", "2026-09")
        assert len(steps) == 1
        assert steps[0]["effective_from"] == "2026-09"
        keys = {i["item_key"] for i in steps[0]["items"]}
        assert keys == {"ITEM_A"}

    def test_removal_propagates_over_reintroduction(self):
        versions = [
            _version(1, "2026-01", [ITEM_A]),
            _version(2, "2026-04", [ITEM_A, ITEM_C]),
            _version(3, "2026-07", [ITEM_A]),
        ]
        steps = dr.plan_document_removal(versions, "ITEM_C", "2026-03")
        # Boundary 04 tem o item; 01 < from não entra; 07 já sem item —
        # mas a remoção em 03/04 deixa o estado pós-inserção sem o item.
        effs = [s["effective_from"] for s in steps]
        assert "2026-04" in effs
        assert all(
            "ITEM_C" not in {i["item_key"] for i in s["items"]}
            for s in steps
        )

    def test_removal_noop_when_not_required(self):
        versions = [_version(1, "2026-01", [ITEM_A])]
        steps = dr.plan_document_removal(versions, "ITEM_C", "2026-09")
        assert steps == []

    def test_removal_of_last_item_produces_empty(self):
        versions = [_version(1, "2026-01", [ITEM_C])]
        steps = dr.plan_document_removal(versions, "ITEM_C", "2026-09")
        assert len(steps) == 1
        assert steps[0]["items"] == []


class TestItemsEqual:
    def test_equal_ignores_sort_order(self):
        a = [_item("A", sort_order=10), _item("B", sort_order=20)]
        b = [_item("B", sort_order=5), _item("A", sort_order=99)]
        assert dr.items_equal(a, b)

    def test_different_content_not_equal(self):
        a = [_item("A", "Nome X")]
        b = [_item("A", "Nome Y")]
        assert not dr.items_equal(a, b)
