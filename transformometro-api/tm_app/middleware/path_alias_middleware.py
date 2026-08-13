"""Rewrite EN canonical HTTP paths to legacy PT route registrations (dual alias)."""

from __future__ import annotations

from starlette.requests import Request

# Longest-first: EN segment → legado PT ainda registrado nos routers.
_EN_TO_PT: tuple[tuple[str, str], ...] = (
    ("/revision-shared-resources", "/revisao-recursos-compartilhados"),
    ("/shared-resources", "/recursos-compartilhados"),
    ("/resource-costs", "/recurso-custos"),
    ("/impact-effort-matrix", "/matriz-impacto-esforco"),
    ("/allocation-diagnosis", "/diagnostico-rateio"),
    ("/scope-decomposition", "/decomposicao-escopo"),
    # Híbrido legado do MFE (EN stem + PT suffix) — bundles em cache até rebuild.
    ("/decomposition-escopo", "/decomposicao-escopo"),
    ("/scope-diagram", "/diagrama-escopo"),
    ("/diagram-escopo", "/diagrama-escopo"),
    ("/validate-flow-links", "/validar-vinculos-fluxo"),
    ("/suggest-draft", "/sugerir-rascunho"),
    ("/snapshot/summary", "/snapshot/resumo"),
    ("/snapshot/processes", "/snapshot/processos"),
    ("/snapshot/instances", "/snapshot/instancias"),
    ("/snapshot/rows", "/snapshot/linhas"),
    ("/collaboration", "/colaboracao"),
    ("/measurements", "/medicoes"),
    ("/investments", "/investimentos"),
    ("/departments", "/setores"),
    ("/branches", "/filiais"),
    ("/processes", "/processos"),
    ("/instances", "/instancias"),
    ("/revisions", "/revisoes"),
    ("/evidences", "/evidencias"),
    ("/decomposition", "/decomposicao"),
    ("/diagram", "/diagrama"),
    ("/catalog", "/catalogo"),
    ("/presence", "/presenca"),
    ("/duplicate", "/duplicar"),
    ("/activate", "/ativar"),
    ("/comparison", "/comparativo"),
    ("/calculated", "/calculados"),
    ("/recalculate", "/recalcular"),
    ("/summary", "/resumo"),
    ("/evolution", "/evolucao"),
    ("/alerts", "/alertas"),
    ("/due-dates", "/vencimentos"),
    ("/by-family", "/por-familia"),
    ("/files", "/arquivos"),
    ("/file", "/arquivo"),
    ("/lock", "/travar"),
    ("/unlock", "/liberar"),
    ("/context", "/contexto"),
)

_SKIP_PREFIXES: tuple[str, ...] = (
    "/transformometro/meeting-minutes",
    "/public/meeting-minutes",
    "/transformometro/atas",
    "/public/atas",
    "/transformometro/signatures",
    "/health",
)


def _replace_path_token(path: str, en: str, pt: str) -> str:
    """Replace ``en`` only as a full path token (bounded by ``/``, ``?`` or EOS).

    Naive ``str.replace('/diagram', '/diagrama')`` corrupts ``/diagrama-escopo``
    into ``/diagramaa-escopo`` because ``/diagrama`` starts with ``/diagram``.
    """
    if not en or en not in path:
        return path
    out: list[str] = []
    i = 0
    while i < len(path):
        j = path.find(en, i)
        if j < 0:
            out.append(path[i:])
            break
        end = j + len(en)
        after_ok = end >= len(path) or path[end] in "/?"
        if after_ok:
            out.append(path[i:j])
            out.append(pt)
            i = end
        else:
            # Prefix of a longer segment (e.g. /diagram inside /diagrama-escopo).
            out.append(path[i : j + 1])
            i = j + 1
    return "".join(out)


def rewrite_en_path_to_legacy_pt(path: str) -> str:
    """Map canonical EN path segments onto legacy PT route paths."""
    if not path or any(path == p or path.startswith(p + "/") or path.startswith(p + "?") for p in _SKIP_PREFIXES):
        # Exact skip prefixes: still allow rewrite only outside these trees.
        if any(path == p or path.startswith(p + "/") for p in _SKIP_PREFIXES):
            return path
    rewritten = path
    for en, pt in _EN_TO_PT:
        rewritten = _replace_path_token(rewritten, en, pt)
    return rewritten


async def path_alias_middleware(request: Request, call_next):
    path = request.scope.get("path") or ""
    root_path = (request.scope.get("root_path") or "").rstrip("/")
    local_path = path
    if root_path and path.startswith(root_path):
        local_path = path[len(root_path) :] or "/"
    rewritten_local = rewrite_en_path_to_legacy_pt(local_path)
    if rewritten_local != local_path:
        request.scope["path"] = f"{root_path}{rewritten_local}" if root_path else rewritten_local
    return await call_next(request)
