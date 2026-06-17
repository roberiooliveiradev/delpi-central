from app.application.services.chat_presentation_format_refinement_resolver_service import (
    ChatPresentationFormatRefinementResolverService,
)
from app.composition.content_composer import configure_domain_infrastructure_ports


class _FakeLlmGateway:
    def __init__(self, response: str):
        self.response = response
        self.calls = 0

    def generate(self, messages):
        self.calls += 1
        return self.response


def setup_module() -> None:
    configure_domain_infrastructure_ports()


def test_llm_resolves_ambiguous_format_refinement():
    gateway = _FakeLlmGateway('{"format":"chart"}')
    resolver = ChatPresentationFormatRefinementResolverService(llm_gateway=gateway)
    history = [
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/production/consumption/top-items",
                            "actionId": "production-consumption-top-items",
                            "presentation": {"type": "table", "rows": []},
                        },
                    }
                ]
            },
        }
    ]

    intent = resolver.resolve(
        "reformate de outro jeito o resultado anterior",
        previous_messages=history,
    )

    assert intent.is_refinement is True
    assert intent.requested_format == "chart"
    assert intent.source == "llm"
    assert gateway.calls == 1


def test_build_failure_direct_answer_when_no_prior_result():
    resolver = ChatPresentationFormatRefinementResolverService()

    answer = resolver.build_failure_direct_answer(
        "mostre em gráfico",
        previous_messages=[],
        reason="unrecognized",
    )

    assert "consulta anterior" in answer.lower()
