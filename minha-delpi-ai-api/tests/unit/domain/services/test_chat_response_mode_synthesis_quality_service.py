from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_response_mode_synthesis_quality_content_service import (
    ChatResponseModeSynthesisQualityContentService,
)
from app.domain.services.chat_response_mode_synthesis_quality_service import (
    ChatResponseModeSynthesisQualityService,
)

configure_domain_infrastructure_ports()


def test_mode_limits_load_numeric_json():
    assert ChatResponseModeSynthesisQualityContentService.mode_limit_int(
        "maxElapsedSec",
        "normal",
        default=180,
    ) == 5
    assert ChatResponseModeSynthesisQualityContentService.mode_limit_int(
        "maxElapsedSec",
        "thinker",
        default=180,
    ) == 15


def _factory_tool_calls(template: str, *, data_answer: dict | None = None) -> list[dict]:
    metadata = {
        "ok": True,
        "path": "/products/90269002/factory-status",
        "presentationDecision": {
            "selected": "text",
            "layoutMode": "stack",
            "presentationMode": "summary_then_evidence",
        },
        "textPresentation": {"type": "markdown", "markdown": template},
        "tablePresentations": [
            {
                "type": "table",
                "title": "Panorama fabril",
                "rows": [{"situacao": "PA PRODUZIDO", "saldo_mp": "6082"}],
            }
        ],
    }

    if data_answer:
        metadata["dataAnswer"] = data_answer

    return [{"name": "execute_external_action", "metadata": metadata}]


TEMPLATE = (
    "### Status fabril\n\n"
    "Situação consolidada: **PA PRODUZIDO**.\n\n"
    "**Destaques**\n\n"
    "- Saldo MP 6082\n"
)


def test_detects_template_clone():
    gaps = ChatResponseModeSynthesisQualityService.evaluate_turn(
        mode="normal",
        question="qual o status do produto 90269002 na fabrica hoje?",
        content=TEMPLATE,
        assistant_metadata={
            "toolCalls": _factory_tool_calls(TEMPLATE),
            "intelligence": {
                "pipeline": {
                    "responseModeEffect": "llm_synthesis",
                    "directResponse": False,
                }
            },
        },
        elapsed_sec=4.0,
    )

    assert any("template operacional" in gap for gap in gaps)


def test_accepts_data_only_decoupled_metadata():
    gaps = ChatResponseModeSynthesisQualityService.evaluate_turn(
        mode="normal",
        question="qual o status do produto 90269002 na fabrica hoje?",
        content=(
            "O produto 90269002 está com **PA PRODUZIDO** na fábrica hoje. "
            "O saldo de MP relevante aparece como 6082 nas posições consultadas. "
            "A leitura operacional indica continuidade produtiva sem bloqueios críticos no recorte consultado."
        ),
        assistant_metadata={
            "toolCalls": [
                {
                    "name": "execute_external_action",
                    "metadata": {
                        "ok": True,
                        "dataOnlyPresentation": True,
                        "llmProseDecoupled": True,
                        "proseDeliveryMode": "llm",
                        "presentationDecision": {"selected": "table"},
                        "textPresentation": {"type": "markdown", "markdown": ""},
                        "humanizedSummary": {"titulo": "Status fabril — 90269002"},
                        "tablePresentations": [
                            {
                                "type": "table",
                                "title": "Panorama fabril",
                                "rows": [{"situacao": "PA PRODUZIDO", "saldo_mp": "6082"}],
                            }
                        ],
                    },
                }
            ],
            "intelligence": {
                "pipeline": {
                    "responseModeEffect": "llm_synthesis",
                    "directResponse": False,
                }
            },
        },
        elapsed_sec=4.0,
    )

    assert gaps == []


def test_rejects_template_markdown_in_data_only_turn():
    gaps = ChatResponseModeSynthesisQualityService.evaluate_turn(
        mode="normal",
        question="qual o status do produto 90269002 na fabrica hoje?",
        content="Resposta LLM sobre 90269002 PA PRODUZIDO com saldo MP 6082.",
        assistant_metadata={
            "toolCalls": _factory_tool_calls(TEMPLATE),
            "intelligence": {
                "pipeline": {
                    "responseModeEffect": "llm_synthesis",
                    "directResponse": False,
                }
            },
        },
        elapsed_sec=4.0,
    )

    assert any("dataOnlyPresentation" in gap or "textPresentation.markdown" in gap for gap in gaps)


def test_accepts_grounded_llm_answer():
    content = (
        "O produto 90269002 está com **PA PRODUZIDO** na fábrica hoje. "
        "O saldo de MP relevante aparece como 6082 nas posições consultadas. "
        "Use o painel para ver árvore, tabela e KPI complementares."
    )
    tool_calls = _factory_tool_calls(
        "",
        data_answer={
            "profileKey": "factory_status",
            "summary": {"answer": "PA PRODUZIDO com saldo MP 6082"},
        },
    )
    tool_calls[0]["metadata"]["dataOnlyPresentation"] = True
    tool_calls[0]["metadata"]["llmProseDecoupled"] = True
    tool_calls[0]["metadata"]["proseDeliveryMode"] = "llm"
    tool_calls[0]["metadata"]["textPresentation"] = {"type": "markdown", "markdown": ""}
    tool_calls[0]["metadata"]["humanizedSummary"] = {"titulo": "Status fabril — 90269002"}

    gaps = ChatResponseModeSynthesisQualityService.evaluate_turn(
        mode="normal",
        question="qual o status do produto 90269002 na fabrica hoje?",
        content=content,
        assistant_metadata={
            "toolCalls": tool_calls,
            "intelligence": {
                "pipeline": {
                    "responseModeEffect": "llm_synthesis",
                    "directResponse": False,
                }
            },
        },
        elapsed_sec=4.0,
    )

    assert gaps == []


def test_accepts_fast_commentary_direct_with_direct_response():
    content = (
        "O produto **90269002** está com **PA PRODUZIDO** na fábrica hoje. "
        "O saldo de MP relevante aparece como 6082 nas posições consultadas. "
        "Use o painel para ver tabela e KPI complementares."
    )
    gaps = ChatResponseModeSynthesisQualityService.evaluate_turn(
        mode="fast",
        question="qual o status do produto 90269002 na fabrica hoje?",
        content=content,
        assistant_metadata={
            "toolCalls": [
                {
                    "name": "execute_external_action",
                    "metadata": {
                        "ok": True,
                        "dataOnlyPresentation": True,
                        "llmProseDecoupled": True,
                        "proseDeliveryMode": "llm",
                        "presentationDecision": {"selected": "table"},
                        "textPresentation": {"type": "markdown", "markdown": ""},
                        "tablePresentations": [
                            {
                                "type": "table",
                                "title": "Panorama fabril",
                                "rows": [{"situacao": "PA PRODUZIDO", "saldo_mp": "6082"}],
                            }
                        ],
                    },
                }
            ],
            "intelligence": {
                "pipeline": {
                    "responseModeEffect": "llm_synthesis_brief",
                    "directResponse": True,
                }
            },
        },
        elapsed_sec=1.5,
    )

    assert gaps == []


def test_rejects_deflection_without_context():
    gaps = ChatResponseModeSynthesisQualityService.evaluate_turn(
        mode="fast",
        question="qual o status do produto 90269002 na fabrica hoje?",
        content="Preciso acessar os registros da produção para responder sobre 90269002.",
        assistant_metadata={
            "toolCalls": _factory_tool_calls(TEMPLATE),
            "intelligence": {
                "pipeline": {
                    "responseModeEffect": "llm_synthesis_brief",
                    "directResponse": False,
                }
            },
        },
        elapsed_sec=7.0,
    )

    assert any("evasiva" in gap for gap in gaps)


def test_rejects_elapsed_above_mode_target():
    gaps = ChatResponseModeSynthesisQualityService.evaluate_turn(
        mode="normal",
        question="me fale do produto 10080045",
        content="O produto 10080045 está cadastrado como MP no grupo 1008.",
        assistant_metadata={
            "toolCalls": _factory_tool_calls(""),
            "intelligence": {
                "pipeline": {
                    "responseModeEffect": "llm_synthesis",
                    "directResponse": False,
                }
            },
        },
        elapsed_sec=12.0,
    )

    assert any("tempo excedido" in gap for gap in gaps)


def test_rejects_hallucination_markers():
    gaps = ChatResponseModeSynthesisQualityService.evaluate_turn(
        mode="thinker",
        question="me fale do produto 10080045",
        content="O produto 10080045 é um componente de engrenagem 2D usado na operação de preparo.",
        assistant_metadata={
            "toolCalls": _factory_tool_calls(""),
            "intelligence": {
                "pipeline": {
                    "responseModeEffect": "llm_synthesis",
                    "directResponse": False,
                }
            },
        },
        elapsed_sec=10.0,
    )

    assert any("alucinação" in gap for gap in gaps)


def test_mode_ladder_requires_distinct_contents():
    results = [
        {
            "mode": "fast",
            "content": "Resposta A curta sobre 90269002.",
            "chars": 120,
            "elapsedSec": 20.0,
        },
        {
            "mode": "normal",
            "content": "Resposta A curta sobre 90269002.",
            "chars": 130,
            "elapsedSec": 25.0,
        },
        {
            "mode": "thinker",
            "content": "Resposta B mais detalhada sobre 90269002 com PA PRODUZIDO.",
            "chars": 220,
            "elapsedSec": 40.0,
        },
    ]

    gaps = ChatResponseModeSynthesisQualityService.evaluate_mode_ladder(results)

    assert any("fast vs normal" in gap for gap in gaps)


def test_mode_ladder_prefers_fast_shorter_than_normal():
    results = [
        {
            "mode": "fast",
            "content": "Resposta curta 90269002 PA PRODUZIDO.",
            "chars": 950,
            "elapsedSec": 22.0,
        },
        {
            "mode": "normal",
            "content": "Resposta normal 90269002 PA PRODUZIDO com mais detalhes operacionais.",
            "chars": 900,
            "elapsedSec": 30.0,
        },
        {
            "mode": "thinker",
            "content": "Resposta pensador 90269002 PA PRODUZIDO com leitura ampliada e próximos passos.",
            "chars": 1100,
            "elapsedSec": 45.0,
        },
    ]

    gaps = ChatResponseModeSynthesisQualityService.evaluate_mode_ladder(results)

    assert any("Rápida deveria ser mais curto" in gap for gap in gaps)
