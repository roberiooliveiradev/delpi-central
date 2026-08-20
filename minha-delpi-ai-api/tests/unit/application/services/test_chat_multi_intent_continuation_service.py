from app.application.services.chat_multi_intent_continuation_service import (
    ChatMultiIntentContinuationService,
)
from app.composition.content_composer import configure_domain_infrastructure_ports

configure_domain_infrastructure_ports()


def test_apply_limit_keeps_all_when_under_cap():
    planned = [
        {"name": "execute_external_action", "arguments": {"path": "/products/{code}/stock"}},
        {"name": "execute_external_action", "arguments": {"path": "/products/{code}/guide"}},
    ]

    executed, meta = ChatMultiIntentContinuationService.apply_limit(planned, max_calls=4)

    assert len(executed) == 2
    assert meta is None
    assert "_multiActionContinuation" not in executed[0]


def test_apply_limit_defers_remainder_and_marks_first():
    planned = [
        {
            "name": "execute_external_action",
            "arguments": {
                "path": "/products/{code}/structure",
                "parameters": {"code": "90260149"},
            },
        },
        {
            "name": "execute_external_action",
            "arguments": {
                "path": "/products/{code}/guide",
                "parameters": {"code": "90260149"},
            },
        },
    ]

    executed, meta = ChatMultiIntentContinuationService.apply_limit(planned, max_calls=1)

    assert len(executed) == 1
    assert isinstance(meta, dict)
    assert meta["deferredCount"] == 1
    assert executed[0]["_multiActionContinuation"]["deferredCount"] == 1


def test_strip_and_build_continuation_chips():
    planned = [
        {
            "name": "execute_external_action",
            "arguments": {
                "path": "/products/{code}/structure",
                "parameters": {"code": "90260149"},
            },
            "_multiActionContinuation": {
                "deferredCount": 1,
                "executedCount": 1,
                "deferred": [
                    {
                        "label": "Também consultar roteiro de produção",
                        "query": "roteiro de produção do produto 90260149",
                        "scope": "roteiro de produção",
                        "productCode": "90260149",
                        "path": "/products/{code}/guide",
                    }
                ],
            },
        }
    ]

    cleaned, continuation = ChatMultiIntentContinuationService.strip_from_planned(planned)

    assert "_multiActionContinuation" not in cleaned[0]
    assert continuation and continuation["deferredCount"] == 1

    chips = ChatMultiIntentContinuationService.build_follow_up_suggestions(continuation)

    assert len(chips) == 1
    assert "roteiro" in chips[0]["label"].lower()
    assert "90260149" in chips[0]["query"]


def test_attach_metadata_from_tool_context():
    metadata: dict = {}
    ChatMultiIntentContinuationService.attach_to_assistant_metadata(
        metadata,
        tool_context={
            "multiActionContinuation": {
                "deferred": [
                    {
                        "label": "Também consultar estoque",
                        "query": "estoque do produto 1",
                    }
                ]
            }
        },
    )

    assert metadata["multiIntentContinuationSuggestions"][0]["label"].startswith(
        "Também consultar"
    )
