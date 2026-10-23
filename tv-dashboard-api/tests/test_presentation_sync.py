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


def test_notify_revision_is_floor_under_interleaved_commit(monkeypatch):
    """024-R1 — A commitou N+1; B commitou N+2 antes do notify de A rodar.
    O evento carrega o piso N+2 (revisão corrente pós-commit): pode superestimar
    o commit originador, mas nunca subestima — o consumidor que suprime por
    `eventRev <= incorporado` no pior caso recarrega uma vez a mais, e a
    remota de B jamais fica permanentemente ignorada."""
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

    a_commit_rev = 41  # rev produzida pela escrita de A
    monkeypatch.setattr(
        PlaylistRepository,
        "get_revision",
        lambda self, playlist_id: a_commit_rev + 1,  # B avançou p/ N+2
    )

    notify_presentation_changed(
        playlist_id="00000000-0000-0000-0000-000000000001",
        reason="slide_updated",
    )

    # piso: evento >= rev de A — não afirma identidade de commit
    assert captured[0][1]["playlistRevision"] == 42
    assert captured[0][1]["playlistRevision"] >= a_commit_rev


def test_notify_explicit_playlist_revision_wins_over_lookup(monkeypatch):
    """Caller que conhece a revisão confirmada repassa — lookup não sobrescreve."""
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
        reason="slide_updated",
        playlist_revision=7,
    )

    assert captured[0][1]["playlistRevision"] == 7
