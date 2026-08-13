from tm_app.middleware.path_alias_middleware import rewrite_en_path_to_legacy_pt


def test_rewrite_processes_and_branches():
    assert rewrite_en_path_to_legacy_pt("/transformometro/processes") == "/transformometro/processos"
    assert (
        rewrite_en_path_to_legacy_pt("/transformometro/processes/p1/instances/i1/revisions/r1")
        == "/transformometro/processos/p1/instancias/i1/revisoes/r1"
    )
    assert rewrite_en_path_to_legacy_pt("/transformometro/branches") == "/transformometro/filiais"
    assert (
        rewrite_en_path_to_legacy_pt("/transformometro/collaboration/presence")
        == "/transformometro/colaboracao/presenca"
    )


def test_rewrite_skips_meeting_minutes_dual_mount():
    assert (
        rewrite_en_path_to_legacy_pt("/transformometro/meeting-minutes/pending-signatures")
        == "/transformometro/meeting-minutes/pending-signatures"
    )
    assert rewrite_en_path_to_legacy_pt("/public/atas/sign-invites/t") == "/public/atas/sign-invites/t"


def test_rewrite_dashboard_verbs():
    assert (
        rewrite_en_path_to_legacy_pt("/transformometro/dashboard/recalculate")
        == "/transformometro/dashboard/recalcular"
    )
    assert (
        rewrite_en_path_to_legacy_pt("/transformometro/dashboard/snapshot/summary")
        == "/transformometro/dashboard/snapshot/resumo"
    )


def test_rewrite_scope_diagram_not_corrupted_by_diagram_alias():
    """Regressão: replace ingênuo de /diagram virava /diagramaa-escopo (404)."""
    assert (
        rewrite_en_path_to_legacy_pt(
            "/transformometro/instances/c84ed1c0-70c4-44c6-aff2-2313ef29c614/scope-diagram"
        )
        == "/transformometro/instancias/c84ed1c0-70c4-44c6-aff2-2313ef29c614/diagrama-escopo"
    )
    assert (
        rewrite_en_path_to_legacy_pt("/transformometro/instances/i1/diagram")
        == "/transformometro/instancias/i1/diagrama"
    )
    assert (
        rewrite_en_path_to_legacy_pt("/transformometro/instances/i1/scope-decomposition")
        == "/transformometro/instancias/i1/decomposicao-escopo"
    )
