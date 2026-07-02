from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, model_validator


class ProcessoCreateBody(BaseModel):
    nome_processo: str = Field(min_length=1, max_length=500)
    filial_id: Optional[str] = Field(
        default=None,
        max_length=16,
        description="Opcional: cria a primeira instância operacional junto com o mestre.",
    )
    setor_id: Optional[str] = Field(
        default=None,
        max_length=64,
        description="Opcional: par filial × setor da primeira instância.",
    )
    status_processo: str = Field(min_length=1, max_length=32)
    descricao_processo: Optional[str] = None
    gestor_responsavel: Optional[str] = None
    objetivo_processo: Optional[str] = None
    codigo_processo: Optional[str] = None
    familia_processo: Optional[str] = Field(default=None, max_length=64)
    agrupador_ferramenta: Optional[str] = Field(default=None, max_length=128)


class ProcessoUpdateBody(BaseModel):
    nome_processo: str = Field(min_length=1, max_length=500)
    status_processo: str = Field(min_length=1, max_length=32)
    descricao_processo: Optional[str] = None
    gestor_responsavel: Optional[str] = None
    objetivo_processo: Optional[str] = None
    codigo_processo: Optional[str] = None
    familia_processo: Optional[str] = Field(default=None, max_length=64)
    agrupador_ferramenta: Optional[str] = Field(default=None, max_length=128)


class ProcessoDuplicateBody(BaseModel):
    nome_processo: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Nome do processo cópia. Padrão: nome original + ' (cópia)'.",
    )


class InstanciaDuplicateBody(BaseModel):
    filial_id: str = Field(min_length=1, max_length=16)
    setor_id: str = Field(min_length=1, max_length=64)
    setor_ids: list[str] = Field(default_factory=list)
    rotulo_instancia: Optional[str] = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def _normalize_setores(self) -> "InstanciaDuplicateBody":
        if not self.setor_ids and self.setor_id:
            self.setor_ids = [self.setor_id]
        return self


class InstanciaBody(BaseModel):
    filial_id: Optional[str] = Field(
        default=None,
        max_length=16,
        description="Filial da instância. Omita quando todas_filiais_ativas=true.",
    )
    todas_filiais_ativas: bool = Field(
        default=False,
        description="Instância válida em todas as filiais ativas.",
    )
    setor_ids: list[str] = Field(
        default_factory=list,
        description="Um ou mais setores amarrados à instância.",
    )
    setor_id: Optional[str] = Field(
        default=None,
        max_length=64,
        description="Atalho legado para um único setor.",
    )
    rotulo_instancia: Optional[str] = Field(default=None, max_length=255)
    status_instancia: str = Field(default="ativo", max_length=32)

    @model_validator(mode="after")
    def _normalize_setores(self) -> "InstanciaBody":
        if not self.setor_ids and self.setor_id:
            self.setor_ids = [self.setor_id]
        if not self.todas_filiais_ativas and not (self.filial_id or "").strip():
            raise ValueError("Informe filial_id ou marque todas_filiais_ativas.")
        if not self.setor_ids:
            raise ValueError("Informe ao menos um setor em setor_ids.")
        return self


class InstanciaUpdateBody(BaseModel):
    rotulo_instancia: Optional[str] = Field(default=None, max_length=255)
    status_instancia: str = Field(default="ativo", max_length=32)
    setor_ids: list[str] = Field(min_length=1)
    filial_id: Optional[str] = Field(
        default=None,
        max_length=16,
        description="Nova filial da instância (ignorada quando todas_filiais_ativas=true).",
    )
    todas_filiais_ativas: Optional[bool] = Field(
        default=None,
        description="Alterna a instância entre filial específica e consolidada (todas as filiais).",
    )

    @model_validator(mode="after")
    def _normalize_setores(self) -> "InstanciaUpdateBody":
        if not self.setor_ids:
            raise ValueError("Informe ao menos um setor em setor_ids.")
        return self


class RevisaoBody(BaseModel):
    processo_id: str
    instancia_id: Optional[str] = None
    versao_revisao: str = Field(min_length=1, max_length=32)
    cenario_tipo: str
    data_inicio_vigencia: str
    revisao_ativa: bool = False
    descricao_revisao: Optional[str] = None
    motivo_revisao: Optional[str] = None
    data_implantacao: Optional[str] = None
    data_fim_vigencia: Optional[str] = None
    observacoes: Optional[str] = None


class MedicaoBody(BaseModel):
    revisao_id: str
    volume_mensal: float = 0
    tempo_medio_execucao_min: float = 0
    tempo_retrabalho_min: float = 0
    percentual_retrabalho: float = 0
    percentual_erro: float = 0
    quantidade_erros_mes: float = 0
    custo_hora_mao_obra: float = 0
    custo_unitario_erro: float = 0
    custo_unitario_retrabalho: float = 0
    custo_outros_desperdicios: float = 0
    base_referencia_mes: Optional[str] = None
    observacoes: Optional[str] = None


class InvestimentoBody(BaseModel):
    revisao_id: str
    tipo_investimento: str
    descricao_item: str
    quantidade: float = 1
    valor_unitario: float = 0
    recorrencia: str = "unico"
    categoria_investimento: Optional[str] = None
    data_investimento: Optional[str] = None
    meses_vigencia: Optional[int] = None
    centro_custo: Optional[str] = None
    observacoes: Optional[str] = None


class InvestimentoUpdateBody(BaseModel):
    tipo_investimento: str
    descricao_item: str
    quantidade: float = 1
    valor_unitario: float = 0
    recorrencia: str = "unico"
    categoria_investimento: Optional[str] = None
    data_investimento: Optional[str] = None
    meses_vigencia: Optional[int] = None
    centro_custo: Optional[str] = None
    observacoes: Optional[str] = None


class RecursoCustoBody(BaseModel):
    valor_mensal: float = Field(ge=0)
    data_inicio_vigencia: str
    data_fim_vigencia: Optional[str] = None
    observacoes: Optional[str] = None


class RecursoCustoReajusteBody(BaseModel):
    valor_mensal: float = Field(ge=0)
    vigente_desde: str
    observacoes: Optional[str] = None


class FilialBody(BaseModel):
    codigo_filial: str = Field(min_length=1, max_length=16)
    nome_filial: str = Field(min_length=1, max_length=255)
    status_filial: str = Field(default="ativo", max_length=32)


class FilialUpdateBody(BaseModel):
    nome_filial: str = Field(min_length=1, max_length=255)
    status_filial: str = Field(default="ativo", max_length=32)


class SetorBody(BaseModel):
    setor_id: str = Field(min_length=1, max_length=64)
    nome_setor: str = Field(min_length=1, max_length=255)
    filiais: list[str] = Field(min_length=1)
    status_setor: str = Field(default="ativo", max_length=32)


class SetorUpdateBody(BaseModel):
    nome_setor: str = Field(min_length=1, max_length=255)
    filiais: list[str] = Field(min_length=1)
    status_setor: str = Field(default="ativo", max_length=32)


class RecursoBody(BaseModel):
    nome_recurso: str
    tipo_custo: str
    recorrencia: str
    valor_total_recorrente: float = 0
    criterio_rateio: str = "igualitario"
    escopo_recurso: str = Field(default="empresa", max_length=32)
    base_competencia: str = "mensal_cheio"
    status_recurso: str = "ativo"
    categoria_recurso: Optional[str] = None
    fornecedor: Optional[str] = None
    data_inicio_vigencia: Optional[str] = None
    data_fim_vigencia: Optional[str] = None
    centro_custo: Optional[str] = None
    observacoes: Optional[str] = None
    codigo_recurso: Optional[str] = None


class VinculoBody(BaseModel):
    revisao_id: str
    recurso_compartilhado_id: str
    ativo: bool = True
    data_inicio_uso: Optional[str] = None
    data_fim_uso: Optional[str] = None
    peso_rateio: Optional[float] = Field(default=None, ge=0)
    observacoes: Optional[str] = None


class VinculoUpdateBody(BaseModel):
    ativo: bool = True
    data_inicio_uso: Optional[str] = None
    data_fim_uso: Optional[str] = None
    peso_rateio: Optional[float] = Field(default=None, ge=0)
    observacoes: Optional[str] = None
