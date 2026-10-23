from tv_app.application.services.presentation_change_notifier import notify_presentation_changed
from tv_app.application.services.presentation_status_service import build_presentation_status


def test_presentation_status_includes_content_revision():
    result = build_presentation_status(
        {"viewCount": 0, "isActive": True},
        content_revision="2026-07-16T12:00:00+00:00|3|2026-07-16T12:05:00+00:00",
    )
    assert result["contentRevision"] == "2026-07-16T12:00:00+00:00|3|2026-07-16T12:05:00+00:00"


def test_notify_presentation_changed_includes_playlist_id(monkeypatch):
    captured: list[tuple[str, dict]] = []

    class FakeHub:
        def schedule_broadcast(self, playlist_id: str, payload: dict) -> None:
            captured.append((playlist_id, payload))

    monkeypatch.setattr(
        "tv_app.application.services.presentation_change_notifier.presentation_realtime_hub",
        FakeHub(),
    )
    monkeypatch.setattr(
        "tv_app.application.services.presentation_change_notifier.build_presentation_content_revision",
        lambda playlist_id: "rev-1",
    )

    notify_presentation_changed(
        playlist_id="00000000-0000-0000-0000-000000000001",
        reason="slide_created",
    )

    assert captured[0][0] == "00000000-0000-0000-0000-000000000001"
    assert captured[0][1]["type"] == "presentation_updated"
    assert captured[0][1]["playlistId"] == "00000000-0000-0000-0000-000000000001"
    assert captured[0][1]["revision"] == "rev-1"


def test_notify_presentation_changed_includes_playlist_revision(monkeypatch):
    """VISTA-TV-024 — evento carrega a revisão agregada pós-commit para o editor
    reconhecer commits próprios já incorporados."""
    captured: list[tuple[str, dict]] = []

    class FakeHub:
        def schedule_broadcast(self, playlist_id: str, payload: dict) -> None:
            captured.append((playlist_id, payload))

    monkeypatch.setattr(
        "tv_app.application.services.presentation_change_notifier.presentation_realtime_hub",
        FakeHub(),
    )
    monkeypatch.setattr(
        "tv_app.application.services.presentation_change_notifier.build_presentation_content_revision",
        lambda playlist_id: "rev-1",
    )
    from tv_app.infrastructure.persistence.repositories.playlist_repository import (
        PlaylistRepository,
    )

    monkeypatch.setattr(
        PlaylistRepository, "get_revision", lambda self, playlist_id: 42
    )

    notify_presentation_changed(
        playlist_id="00000000-0000-0000-0000-000000000001",
        reason="slide_updated",
    )

    assert captured[0][1]["playlistRevision"] == 42


def test_notify_presentation_changed_omits_revision_on_lookup_failure(monkeypatch):
    """Falha na resolução da revisão não quebra o notify — payload sai sem o
    campo e consumidores recarregam (safe > suppression)."""
    captured: list[tuple[str, dict]] = []

    class FakeHub:
        def schedule_broadcast(self, playlist_id: str, payload: dict) -> None:
            captured.append((playlist_id, payload))

    monkeypatch.setattr(
        "tv_app.application.services.presentation_change_notifier.presentation_realtime_hub",
        FakeHub(),
    )
    monkeypatch.setattr(
        "tv_app.application.services.presentation_change_notifier.build_presentation_content_revision",
        lambda playlist_id: "rev-1",
    )
    from tv_app.infrastructure.persistence.repositories.playlist_repository import (
        PlaylistRepository,
    )

    def _boom(self, playlist_id):
        raise RuntimeError("db down")

    monkeypatch.setattr(PlaylistRepository, "get_revision", _boom)

    notify_presentation_changed(
        playlist_id="00000000-0000-0000-0000-000000000001",
        reason="slide_updated",
    )

    assert captured[0][1]["type"] == "presentation_updated"
    assert "playlistRevision" not in captured[0][1]
