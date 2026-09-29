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


def test_rewrite_skips_engineering_integrations_en_contract():
    """api-delpi chama paths EN; rewrite /processes|/summary quebrava o contrato (404→500)."""
    summary = (
        "/transformometro/integrations/engineering/transforma-mais/processes/summary"
    )
    listing = "/transformometro/integrations/engineering/transforma-mais/processes"
    assert rewrite_en_path_to_legacy_pt(summary) == summary
    assert rewrite_en_path_to_legacy_pt(listing) == listing


def test_rewrite_skips_gpt_actions_en_surface():
    """Custom GPT Actions usam paths EN; /catalog→/catalogo quebrava gpt_get_catalog."""
    catalog = "/transformometro/gpt-actions/v1/catalog"
    activate = "/transformometro/gpt-actions/v1/revisions/r1/activate"
    duplicate = "/transformometro/gpt-actions/v1/records/process/p1/duplicate"
    recalc = "/transformometro/gpt-actions/v1/dashboard/recalculate"
    assert rewrite_en_path_to_legacy_pt(catalog) == catalog
    assert rewrite_en_path_to_legacy_pt(activate) == activate
    assert rewrite_en_path_to_legacy_pt(duplicate) == duplicate
    assert rewrite_en_path_to_legacy_pt(recalc) == recalc
    # gateway path com prefixo /apps/... também deve preservar
    gw = "/apps/transformometro-api/transformometro/gpt-actions/v1/catalog"
    assert rewrite_en_path_to_legacy_pt(gw) == gw


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


def test_rewrite_hybrid_legacy_mfe_paths():
    """MFE antigo chamava /decomposition-escopo (híbrido) — deve mapear ao legado PT."""
    assert (
        rewrite_en_path_to_legacy_pt("/transformometro/instances/i1/decomposition-escopo")
        == "/transformometro/instancias/i1/decomposicao-escopo"
    )
    assert (
        rewrite_en_path_to_legacy_pt("/transformometro/instances/i1/diagram-escopo")
        == "/transformometro/instancias/i1/diagrama-escopo"
    )

def test_rewrite_skips_diagnostic_en_native_surface():
    """Diagnostic V1 é EN-canônico: /revisions/{id}/diagnostics não deve virar
    /revisoes/{id}/diagnostics — não há rota PT registrada (404 em produção)."""
    base = "/transformometro/revisions/816b1c54-8b5b-464e-ba55-242a7ec4a22e"
    assert rewrite_en_path_to_legacy_pt(f"{base}/diagnostics") == f"{base}/diagnostics"
    assert (
        rewrite_en_path_to_legacy_pt(f"{base}/diagnostics/prepare")
        == f"{base}/diagnostics/prepare"
    )
    detail = "/transformometro/diagnostics/72550c29-464f-4d28-9ce9-31986a09273d"
    assert rewrite_en_path_to_legacy_pt(detail) == detail
    assert rewrite_en_path_to_legacy_pt(f"{detail}/prepare") == f"{detail}/prepare"
    commit = "/transformometro/governed-proposals/commit"
    assert rewrite_en_path_to_legacy_pt(commit) == commit
    # gateway path com prefixo /apps/... também deve preservar
    gw = f"/apps/transformometro-api{base}/diagnostics"
    assert rewrite_en_path_to_legacy_pt(gw) == gw


def test_rewrite_still_maps_legacy_revision_siblings():
    """Irmãos PT continuam reescritos — a isenção é apenas de /diagnostics."""
    base = "/transformometro/revisions/r1"
    assert rewrite_en_path_to_legacy_pt(base) == "/transformometro/revisoes/r1"
    assert (
        rewrite_en_path_to_legacy_pt(f"{base}/evidences")
        == "/transformometro/revisoes/r1/evidencias"
    )
    assert (
        rewrite_en_path_to_legacy_pt(f"{base}/diagram")
        == "/transformometro/revisoes/r1/diagrama"
    )
    # /diagnostico-rateio (PT) não é o token /diagnostics — não pode casar.
    pt = "/transformometro/revisoes/r1/diagnostico-rateio"
    assert rewrite_en_path_to_legacy_pt(pt) == pt
