FILIAIS = {"01": "Matriz", "02": "Filial"}

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
STATUS_PROCESSO = ("ativo", "descontinuado", "em_implantacao")
CENARIO_TIPO = ("baseline", "melhoria", "automacao", "correcao")
TIPO_INVESTIMENTO = ("fixo", "variavel", "recorrente", "unico")
TIPO_CUSTO_RECURSO = ("fixo", "variavel", "assinatura", "licenca")
CATEGORIAS = ("software", "treinamento", "consultoria", "equipamento", "horas_internas", "terceiros")
RECORRENCIAS = ("unico", "mensal", "anual")
CRITERIO_RATEIO = ("igualitario", "por_revisoes_ativas", "por_peso")
BASE_COMPETENCIA_RECURSO = ("mensal_cheio", "proporcional_dias")
STATUS_RECURSO = ("ativo", "inativo")
STATUS_APROVACAO_REVISAO = ("rascunho", "em_analise", "aprovada", "rejeitada")


def assert_in(value: str, allowed: tuple[str, ...], field: str) -> None:
    if value not in allowed:
        raise ValueError(f"{field} inválido: {value}")


def options_payload(setores: list[dict] | None = None) -> dict:
    if setores is None:
        setores = [
            {"id": setor_id, "label": setor_id, "filiais": list(FILIAIS.keys())}
            for setor_id in DEFAULT_SETORES
        ]
    return {
        "filiais": [{"id": k, "label": v} for k, v in FILIAIS.items()],
        "setores": setores,
        "status_setor": list(STATUS_SETOR),
        "status_processo": list(STATUS_PROCESSO),
        "cenario_tipo": list(CENARIO_TIPO),
        "tipo_investimento": list(TIPO_INVESTIMENTO),
        "tipo_custo": list(TIPO_CUSTO_RECURSO),
        "categorias": list(CATEGORIAS),
        "recorrencias": list(RECORRENCIAS),
        "criterio_rateio": list(CRITERIO_RATEIO),
        "base_competencia_recurso": list(BASE_COMPETENCIA_RECURSO),
        "status_recurso": list(STATUS_RECURSO),
        "status_aprovacao_revisao": list(STATUS_APROVACAO_REVISAO),
    }
