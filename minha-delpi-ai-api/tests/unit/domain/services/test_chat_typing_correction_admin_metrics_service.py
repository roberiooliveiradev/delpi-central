from app.domain.services.chat_typing_correction_admin_metrics_service import (
    ChatTypingCorrectionAdminMetricsService,
)


def test_snapshot_from_request_requires_accepted():
    assert (
        ChatTypingCorrectionAdminMetricsService.snapshot_from_request(
            {
                "original": "estouque",
                "corrected": "estoque",
                "accepted": False,
            }
        )
        is None
    )


def test_snapshot_from_event():
    snapshot = ChatTypingCorrectionAdminMetricsService.snapshot_from_event(
        event="typing_correction_offered",
        metadata={
            "original": "estouque do produto",
            "corrected": "estoque do produto",
            "changeCount": 1,
        },
    )

    assert snapshot == {
        "event": "typing_correction_offered",
        "original": "estouque do produto",
        "corrected": "estoque do produto",
        "changeCount": 1,
    }


def test_enrich_audit_metadata():
    audit_metadata: dict = {}

    ChatTypingCorrectionAdminMetricsService.enrich_audit_metadata(
        audit_metadata,
        typing_correction={
            "original": "estouque",
            "corrected": "estoque",
            "accepted": True,
            "source": "domain_dictionary",
            "changes": [{"from": "estouque", "to": "estoque", "kind": "word"}],
        },
    )

    assert audit_metadata["typingCorrectionMetrics"]["accepted"] is True
    assert audit_metadata["typingCorrectionMetrics"]["changeCount"] == 1


def test_aggregate_typing_correction_metrics():
    summary = ChatTypingCorrectionAdminMetricsService.aggregate(
        acceptance_entries=[
            {
                "loggedAt": "2026-06-10T12:00:00Z",
                "snapshot": {
                    "accepted": True,
                    "original": "estouque do produto",
                    "corrected": "estoque do produto",
                    "changeCount": 1,
                    "source": "domain_dictionary",
                },
            }
        ],
        event_entries=[
            {
                "loggedAt": "2026-06-10T11:59:00Z",
                "snapshot": {
                    "event": "typing_correction_offered",
                    "original": "estouque do produto",
                    "corrected": "estoque do produto",
                    "changeCount": 1,
                },
            },
            {
                "loggedAt": "2026-06-10T12:00:00Z",
                "snapshot": {
                    "event": "typing_correction_accepted",
                    "original": "estouque do produto",
                    "corrected": "estoque do produto",
                    "changeCount": 1,
                },
            },
            {
                "loggedAt": "2026-06-10T11:58:00Z",
                "snapshot": {
                    "event": "typing_correction_dismissed",
                    "original": "filail 01",
                    "corrected": "filial 01",
                    "changeCount": 1,
                },
            },
        ],
        hours=168,
        since_iso="2026-06-03T12:00:00Z",
    )

    assert summary["offeredCount"] == 1
    assert summary["acceptedCount"] == 1
    assert summary["dismissedCount"] == 1
    assert summary["acceptedTurnsCount"] == 1
    assert summary["acceptanceRate"] == 1.0
    assert summary["dismissRate"] == 1.0
    assert summary["avgChangesPerAcceptance"] == 1.0
    assert summary["topCorrections"][0]["label"] == "estouque do produto → estoque do produto"
    assert summary["recentEvents"]
    assert summary["recentAcceptances"]
