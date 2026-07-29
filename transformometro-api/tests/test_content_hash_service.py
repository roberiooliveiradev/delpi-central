from tm_app.application.services.content_hash_service import ContentHashService


def test_hash_is_deterministic_and_changes_with_content():
    payload = ContentHashService.build_version_payload(
        title="Ata", meeting_type="ordinary", meeting_date="2026-07-28",
        start_time=None, end_time=None, location=None, agenda_html="<p>Pauta</p>",
        body_html="", decisions_html="", pending_html="", observations_html="",
    )
    assert ContentHashService.hash_version_payload(payload) == ContentHashService.hash_version_payload(dict(reversed(list(payload.items()))))
    assert ContentHashService.hash_version_payload(payload) != ContentHashService.hash_version_payload({**payload, "title": "Outra"})
