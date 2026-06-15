from dataclasses import asdict, dataclass, field
from typing import Any, List, Optional


@dataclass
class EficienciaFabrilSummary:
    weighted_efficiency_pct: Optional[float] = None
    total_mod_result: Optional[float] = None
    total_mod_profit: Optional[float] = None
    total_mod_loss: Optional[float] = None
    total_hours_gained_lost: Optional[float] = None
    appointment_count: int = 0
    invalid_record_count: int = 0


@dataclass
class EficienciaFabrilCharts:
    efficiency_by_day: List[dict] = field(default_factory=list)
    mod_result_by_day: List[dict] = field(default_factory=list)
    efficiency_by_operator: List[dict] = field(default_factory=list)
    hours_by_work_center: List[dict] = field(default_factory=list)


@dataclass
class EficienciaFabrilDashboardItem:
    appointment_id: Optional[int] = None
    filial: Optional[str] = None
    op: Optional[str] = None
    produto: Optional[str] = None
    centro_trabalho: Optional[str] = None
    operacao: Optional[str] = None
    descricao_produto: Optional[str] = None
    unidade: Optional[str] = None
    cod_operador: Optional[str] = None
    login_operador: Optional[str] = None
    nome_operador: Optional[str] = None
    data_producao: Optional[str] = None
    hora_inicio: Optional[str] = None
    hora_final: Optional[str] = None
    qtd_apontada: Optional[float] = None
    tempo_real_horas: Optional[float] = None
    tempo_previsto_horas: Optional[float] = None
    eficiencia_percentual: Optional[float] = None
    valor_mod_hora: Optional[float] = None
    tempo_ganho_perdido_horas: Optional[float] = None
    resultado_mod: Optional[float] = None
    lucro_mod: Optional[float] = None
    prejuizo_mod: Optional[float] = None
    status_resultado_mod: Optional[str] = None
    status_registro: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class EficienciaFabrilPagination:
    page: int
    page_size: int
    total: int

    @property
    def total_pages(self) -> int:
        if self.page_size <= 0:
            return 0
        return (self.total + self.page_size - 1) // self.page_size

    def to_dict(self) -> dict[str, Any]:
        return {
            "page": self.page,
            "page_size": self.page_size,
            "total": self.total,
            "total_pages": self.total_pages,
        }


@dataclass
class EficienciaFabrilDashboardResponse:
    summary: EficienciaFabrilSummary
    charts: EficienciaFabrilCharts
    items: List[EficienciaFabrilDashboardItem]
    pagination: EficienciaFabrilPagination

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": asdict(self.summary),
            "charts": asdict(self.charts),
            "items": [item.to_dict() for item in self.items],
            "pagination": self.pagination.to_dict(),
        }
