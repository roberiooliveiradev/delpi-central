"""Gate 075 — sweep de itens obsoletos por source_id na ingestão.

A busca da CLARA filtra ``status='PUBLISHED'``; o supersede por locator
só cobre segmentos que retornaram. Este teste prova que itens cuja
heading desapareceu são varridos para SUPERSEDED na reingestão.
"""
from controllership_finance_app.application.clara.corpus_ingestion import (
    SourceSpec,
    ingest_source,
)


class FakeRepo:
    def __init__(self):
        self.swept = None
        self.items = {}

    def register_source(self, **_kwargs):
        return {}

    def ingest_item(self, *, source_id, title, **_kw):
        kid = f"kid-{title}"
        self.items.setdefault(source_id, []).append(kid)
        return {"knowledge_id": kid}

    def supersede_stale_items(self, *, source_id, keep_ids):
        self.swept = (source_id, list(keep_ids))
        return 7


def _spec():
    return SourceSpec(
        source_id="ficha-r12",
        path="fichas/R12-ficha.md",
        source_type="DOCUMENT",
        name="Ficha R12",
        origin_authority="TO_INVENTORY",
        evidence_classification="OWNER_REPORTED_VIA_PO",
        topic="closing",
    )


def test_sweep_called_with_current_segment_ids(tmp_path):
    doc = tmp_path / "fichas"
    doc.mkdir()
    (doc / "R12-ficha.md").write_text(
        "# Titulo\n\n## Secao A\n\nConteudo A.\n", encoding="utf-8"
    )
    repo = FakeRepo()
    out = ingest_source(_spec(), docs_root=tmp_path, repository=repo)
    assert repo.swept is not None
    sid, kept = repo.swept
    assert sid == "ficha-r12"
    assert kept == repo.items["ficha-r12"]
    assert out["stale_swept"] == 7
