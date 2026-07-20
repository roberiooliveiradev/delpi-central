FILIAIS = {"01": "Santa Catarina", "02": "Espírito Santo"}

DEFAULT_SETORES = (
    "engenharia",
    "qualidade",
    "pcp",
    "producao",
    "comercial",
    "compras",
    "almoxarifado",
)

STATUS_SETOR = ("ativo", "inativo")
STATUS_FILIAL = ("ativo", "inativo")
STATUS_PROCESSO = ("ativo", "descontinuado", "em_implantacao")
CENARIO_TIPO = ("baseline", "melhoria", "automacao", "correcao")
TIPO_INVESTIMENTO = ("fixo", "variavel", "recorrente", "unico")
TIPO_CUSTO_RECURSO = ("fixo", "variavel", "assinatura", "licenca")
CATEGORIAS = ("software", "treinamento", "consultoria", "equipamento", "horas_internas", "terceiros")
RECORRENCIAS = ("unico", "mensal", "anual")
CRITERIO_RATEIO = ("igualitario", "por_revisoes_ativas", "por_peso")
BASE_COMPETENCIA_RECURSO = ("mensal_cheio", "proporcional_dias")
STATUS_RECURSO = ("ativo", "inativo")
ESCOPO_RECURSO = ("empresa", "filial", "setor")
STATUS_APROVACAO_REVISAO = ("rascunho", "em_analise", "aprovada", "rejeitada")

# Playbook 22 — categoria de cálculo de benefício (revisão vs. referência)
BENEFICIO_CALCULO_CATEGORIA_DEFAULT = "economia_tempo"
BENEFICIO_CALCULO_CATEGORIA = (
    "economia_tempo",
    "reducao_volume",
    "ganho_capacidade",
    "economia_qualidade",
    "misto",
    "automatico",
)

BENEFICIO_CALCULO_CATEGORIA_LABELS: dict[str, str] = {
    "economia_tempo": "Economia de tempo",
    "reducao_volume": "Redução de execuções",
    "ganho_capacidade": "Ganho de capacidade",
    "economia_qualidade": "Economia de qualidade",
    "misto": "Misto",
    "automatico": "Automático",
}


def assert_in(value: str, allowed: tuple[str, ...], field: str) -> None:
    if value not in allowed:
        raise ValueError(f"{field} inválido: {value}")


def normalize_beneficio_calculo_categoria(value: str | None) -> str:
    raw = (value or "").strip().lower() or BENEFICIO_CALCULO_CATEGORIA_DEFAULT
    if raw not in BENEFICIO_CALCULO_CATEGORIA:
        raise ValueError(f"beneficio_calculo_categoria inválido: {value}")
    return raw


def options_payload(
    setores: list[dict] | None = None,
    filiais: list[dict] | None = None,
) -> dict:
    if setores is None:
        setores = [
            {"id": setor_id, "label": setor_id, "filiais": list(FILIAIS.keys())}
            for setor_id in DEFAULT_SETORES
        ]
    if filiais is None:
        filiais = [{"id": k, "label": v} for k, v in FILIAIS.items()]
    return {
        "filiais": filiais,
        "setores": setores,
        "status_setor": list(STATUS_SETOR),
        "status_filial": list(STATUS_FILIAL),
        "status_processo": list(STATUS_PROCESSO),
        "cenario_tipo": list(CENARIO_TIPO),
        "tipo_investimento": list(TIPO_INVESTIMENTO),
        "tipo_custo": list(TIPO_CUSTO_RECURSO),
        "categorias": list(CATEGORIAS),
        "recorrencias": list(RECORRENCIAS),
        "criterio_rateio": list(CRITERIO_RATEIO),
        "base_competencia_recurso": list(BASE_COMPETENCIA_RECURSO),
        "status_recurso": list(STATUS_RECURSO),
        "escopo_recurso": list(ESCOPO_RECURSO),
        "status_aprovacao_revisao": list(STATUS_APROVACAO_REVISAO),
        "beneficio_calculo_categoria": list(BENEFICIO_CALCULO_CATEGORIA),
        "beneficio_calculo_categoria_default": BENEFICIO_CALCULO_CATEGORIA_DEFAULT,
        "beneficio_calculo_categoria_labels": dict(BENEFICIO_CALCULO_CATEGORIA_LABELS),
    }
