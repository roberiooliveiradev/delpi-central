from fastapi import APIRouter

router = APIRouter(prefix="/transformometro", tags=["Transformômetro"])


@router.get("/health")
def module_health():
    return {
        "status": "online",
        "module": "transformometro",
        "phase": "0",
    }


@router.get("/options")
def list_options():
    """Catálogos estáticos (Fase 0). Expandido na Fase 1."""
    return {
        "success": True,
        "message": "Catálogos carregados.",
        "data": {
            "filiais": [
                {"id": "01", "label": "Matriz"},
                {"id": "02", "label": "Filial"},
            ],
            "setores": [
                "engenharia",
                "qualidade",
                "pcp",
                "producao",
                "comercial",
                "compras",
                "almoxarifado",
            ],
            "status_processo": ["ativo", "descontinuado", "em_implantacao"],
            "cenario_tipo": ["baseline", "melhoria", "automacao", "correcao"],
            "criterio_rateio": ["igualitario", "por_revisoes_ativas", "por_peso"],
        },
    }
