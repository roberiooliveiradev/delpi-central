from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ProcessoCreateBody(BaseModel):
    nome_processo: str = Field(min_length=1, max_length=500)
    filial_id: str = Field(min_length=1, max_length=16)
    setor_id: str = Field(min_length=1, max_length=64)
    status_processo: str = Field(min_length=1, max_length=32)
    descricao_processo: Optional[str] = None
    gestor_responsavel: Optional[str] = None
    objetivo_processo: Optional[str] = None
    codigo_processo: Optional[str] = None
    familia_processo: Optional[str] = Field(default=None, max_length=64)
    agrupador_ferramenta: Optional[str] = Field(default=None, max_length=128)


class ProcessoUpdateBody(ProcessoCreateBody):
    pass


class ProcessoDuplicateBody(BaseModel):
    nome_processo: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Nome do processo cópia. Padrão: nome original + ' (cópia)'.",
    )


class RevisaoBody(BaseModel):
    processo_id: str
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
