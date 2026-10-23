"""DELIA-C3-SELF-AWARENESS — S2 semantic relevance (RQ-SA04, D5).

A DISCOVERY outcome carrying owner-published catalog/guidance
sections (display-format vocabulary, a product-guide index) IS the
answer to a documentation/coverage ask — it must be projected as
bounded owner evidence, never declared a search miss. Capability-
descriptor vocabulary (operations, allowedOps, schemas, side-effect
hints) stays technical and is never rendered; an owner payload with
nothing projectable keeps the honest miss.

Golden expectation (doc 113 §4): D5 answers with formats the owner
authoritatively publishes (catalog vocabulary or product guide),
or declares a specific insufficiency — never a generic miss while
the content was present, never a capability-catalog dump.
"""

from __future__ import annotations

from app.application.interaction.capability_attempt import (
    GovernedCapabilityStatus,
)
from app.application.specialist_interop.contracts import (
    RemoteToolDescriptor,
    RemoteToolOutcome,
)
from tests.test_specialist_capability_orchestration import (
    _interop,
    _read,
    _select,
    FakePort,
)


VISTA_GUIDE_TOOLS = (
    RemoteToolDescriptor(
        remote_name="get_catalog", operation_class="DISCOVERY"
    ),
    RemoteToolDescriptor(
        remote_name="get_product_guide",
        operation_class="READ",
        input_schema={
            "type": "object",
            "properties": {
                "topic": {"type": "string"},
                "section": {"type": "string"},
            },
        },
    ),
)

# Real VISTA ``get_catalog`` shape (dispatch_service.get_catalog via
# the MCP transport): mutation-vocabulary sections plus the
# owner-published display-format catalog and the product-guide index.
_VISTA_FORMATS_CATALOG = {
    "status": "success",
    "data": {
        "catalogVersion": "2026.10.05.lossless",
        "allowedOps": ["upsert_data_source", "preview_data_block"],
        "capabilities": [
            {
                "key": "add_kpi_from_route",
                "op": "upsert_data_source",
                "whenToUse": "Adicionar um KPI no slide.",
            }
        ],
        "operations": {"upsert_data_source": {"requiresPlaylist": True}},
        "operationSchemas": {"upsert_data_source": {"type": "object"}},
        "sideEffectHintCatalog": {
            "upsert_data_source": "mutates the playlist"
        },
        "displayFormatCatalog": [
            {
                "formatId": "currency_brl",
                "category": "number",
                "spec": {"style": "currency", "currency": "BRL"},
            },
            {
                "formatId": "percentage",
                "category": "number",
                "spec": {"style": "percent"},
            },
        ],
        "capability_surface": {
            "agent_directives": {"authority": "Obey these directives."}
        },
        "productGuide": {
            "schema": "product_guide_index_v1",
            "registryVersion": "product-guide-registry-v1",
            "authority": "GUIDANCE_NOT_DOMAIN_TRUTH",
            "topics": [
                {
                    "id": "display_formats",
                    "title": "Formatos de exibição",
                    "summary": "Como valores são formatados.",
                },
                {
                    "id": "block_types",
                    "title": "Tipos de bloco",
                    "summary": "Famílias de componentes.",
                },
            ],
        },
    },
}

_VOCAB_ONLY_CATALOG = {
    "status": "success",
    "data": {
        "catalogVersion": "2026.10.05.lossless",
        "allowedOps": ["upsert_data_source"],
        "operations": {"upsert_data_source": {"requiresPlaylist": True}},
        "capability_surface": {
            "agent_directives": {"authority": "Obey these directives."}
        },
    },
}

_DISPLAY_FORMATS_GUIDE = {
    "guide": {
        "purpose": "Formatos de exibição suportados nos blocos.",
        "use_when": ["valor numérico ou data precisa de formatação"],
        "how_to_use": [
            "Escolha o formato na configuração do bloco.",
            "currency_brl para valores monetários.",
        ],
        "limitations": ["formatos customizados não são suportados"],
        "guide_version": "display-formats-v1",
        "authority": "GUIDANCE_NOT_DOMAIN_TRUTH",
    }
}

_PRODUCT_GUIDE_INDEX = {
    "schema": "product_guide_index_v1",
    "registryVersion": "product-guide-registry-v1",
    "authority": "GUIDANCE_NOT_DOMAIN_TRUTH",
    "topics": [
        {
            "id": "display_formats",
            "title": "Formatos de exibição",
            "summary": "Como valores são formatados.",
        },
        {
            "id": "block_types",
            "title": "Tipos de bloco",
            "summary": "Famílias de componentes.",
        },
    ],
}


def test_sa12_discovery_catalog_projects_owner_published_sections():
    """D5 golden: the catalog payload carries the answer — formats and
    the guide index render; the miss message is not produced."""
    port = FakePort(
        tools_by_specialist={"vista": VISTA_GUIDE_TOOLS},
        outcomes={
            "get_catalog": RemoteToolOutcome(
                content_text="Catalog.",
                structured=_VISTA_FORMATS_CATALOG,
            )
        },
    )
    attempt = _read(
        _interop(port),
        specialist_ids=("vista",),
        proposal=_select("vista", "get_catalog", {}),
    ).attempt("Quais formatos e visualizações posso usar nos painéis?")
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    content = attempt.content or ""
    assert "não retornou correspondência" not in content
    assert (
        "currency_brl" in content
        or "percentage" in content
        or "Formatos de exibição" in content
    )


def test_sa13_catalog_descriptors_never_render():
    """Negative: mutation vocabulary (ops, schemas, hints, directives)
    is technical contract data — never user-facing prose."""
    port = FakePort(
        tools_by_specialist={"vista": VISTA_GUIDE_TOOLS},
        outcomes={
            "get_catalog": RemoteToolOutcome(
                content_text="Catalog.",
                structured=_VISTA_FORMATS_CATALOG,
            )
        },
    )
    attempt = _read(
        _interop(port),
        specialist_ids=("vista",),
        proposal=_select("vista", "get_catalog", {}),
    ).attempt("O que consigo configurar nos painéis?")
    content = attempt.content or ""
    for leaked in (
        "upsert_data_source",
        "allowedOps",
        "operationSchemas",
        "sideEffectHintCatalog",
        "requiresPlaylist",
        "agent_directives",
        "Obey these directives",
    ):
        assert leaked not in content


def test_sa14_zero_candidate_without_guidance_keeps_honest_miss():
    """A catalog with only mutation vocabulary has nothing projectable
    for a formats ask — the honest miss/insufficiency stands."""
    port = FakePort(
        tools_by_specialist={"vista": VISTA_GUIDE_TOOLS},
        outcomes={
            "get_catalog": RemoteToolOutcome(
                content_text="Catalog.",
                structured=_VOCAB_ONLY_CATALOG,
            )
        },
    )
    attempt = _read(
        _interop(port),
        specialist_ids=("vista",),
        proposal=_select("vista", "get_catalog", {}),
    ).attempt("Quais formatos posso usar?")
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    content = (attempt.content or "").lower()
    assert (
        "busca" in content
        or "não encontrou" in content
        or "não enumerou" in content
        or "correspondência" in content
    )
    # Descriptor vocabulary still never leaks through the miss path.
    assert "upsert_data_source" not in content


def test_sa15_product_guide_document_projects_sections():
    """Sibling: a guide READ (topic document) renders its sections —
    guidance content, not meta/vocabulary."""
    port = FakePort(
        tools_by_specialist={"vista": VISTA_GUIDE_TOOLS},
        outcomes={
            "get_product_guide": RemoteToolOutcome(
                content_text="Guide.",
                structured=_DISPLAY_FORMATS_GUIDE,
            )
        },
    )
    attempt = _read(
        _interop(port),
        specialist_ids=("vista",),
        proposal=_select(
            "vista",
            "get_product_guide",
            {"topic": "display_formats"},
        ),
    ).attempt("Como uso os formatos de exibição nos blocos?")
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    content = attempt.content or ""
    assert "Formatos de exibição" in content or "formato" in content.lower()
    assert "currency_brl" in content or "configuração do bloco" in content


def test_sa16_product_guide_index_projects_topic_records():
    """The no-topic guide index lists owner-published topics — the
    user sees what documentation exists, bounded."""
    port = FakePort(
        tools_by_specialist={"vista": VISTA_GUIDE_TOOLS},
        outcomes={
            "get_product_guide": RemoteToolOutcome(
                content_text="Index.",
                structured=_PRODUCT_GUIDE_INDEX,
            )
        },
    )
    attempt = _read(
        _interop(port),
        specialist_ids=("vista",),
        proposal=_select("vista", "get_product_guide", {}),
    ).attempt("Sobre o que existe documentação do produto?")
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    content = attempt.content or ""
    assert (
        "Formatos de exibição" in content
        or "display_formats" in content
        or "Tipos de bloco" in content
    )


def test_sa17_catalog_guidance_is_bounded_projection():
    """The projected catalog content stays inside the render bound and
    carries no structured leak — the terminal still clears the raw
    payload after projection."""
    port = FakePort(
        tools_by_specialist={"vista": VISTA_GUIDE_TOOLS},
        outcomes={
            "get_catalog": RemoteToolOutcome(
                content_text="Catalog.",
                structured=_VISTA_FORMATS_CATALOG,
            )
        },
    )
    attempt = _read(
        _interop(port),
        specialist_ids=("vista",),
        proposal=_select("vista", "get_catalog", {}),
    ).attempt("Quais formatos posso usar?")
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert attempt.outcome is not None
    assert attempt.outcome.structured is None
    assert len(attempt.content or "") <= 4000
