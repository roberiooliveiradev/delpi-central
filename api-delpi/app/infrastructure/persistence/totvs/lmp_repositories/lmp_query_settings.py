from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class LMPQuerySettings:
    branches: List[str] = field(default_factory=lambda: ["01", "02"])

    # Tempo mínimo de permanência em engenharia — aplica somente a LISTING_KIND LMP.
    min_engineering_residence_minutes: int = 30

    # work_month_lmp (padrão) | anchor_in_period | homolog_cycles_in_period | …
    period_inclusion_policy: str = "work_month_lmp"

    # Homolog LMP com permanência < min → OUTRO; remove bypass amostra pós-homolog
    strict_residence_after_homolog: bool = False

    # Prioridade quando a OV possui mais de um marcador na mesma revisão.
    listing_kind_priority: Dict[str, int] = field(
        default_factory=lambda: {
            "LMP": 2,
            "AMOSTRA": 1,
            "OUTROS": 0,
        }
    )

    lmp_anchor_process_stages: Dict[str, List[str]] = field(
        default_factory=lambda: {
            # 000002 - OPORTUNIDADE
            # 000003 = ENGENHARIA
            # 000012 = LANCAMENTO / HOMOLOGACAO
            "000002": ["000003", "000012"],

            # 000003
            "000003": ["000003", "000012"],
        }
    )

    lmp_followup_process_stages: Dict[str, List[str]] = field(
        default_factory=lambda: {
            "000002": ["000013"],
            "000003": ["000013"],
        }
    )

    engineering_support_process_stages: Dict[str, List[str]] = field(
        default_factory=lambda: {
            "000002": ["000003", "000008", "000012"],
            "000003": ["000003", "000012"],
        }
    )

    sample_anchor_process_stages: Dict[str, List[str]] = field(
        default_factory=lambda: {
            # 000002 = oportunidade — 000008 = amostra engenharia (doc TOTVS)
            "000002": ["000008"],
            # 000003 = processo engenharia — 000002/000008 = amostra
            "000003": ["000002", "000008"],
        }
    )

    # Lançamento/homologação LMP: OV que já passou por 000012 permanece LMP
    # (histórico de amostra 000008 não reclassifica como amostra na listagem).
    lmp_finalized_process_stages: Dict[str, List[str]] = field(
        default_factory=lambda: {
            "000002": ["000012"],
            "000003": ["000012"],
        }
    )

    engineering_status_labels: Dict[str, str] = field(
        default_factory=lambda: {
            "in_progress": "ABERTA",
            "finished": "FINALIZADA",
            "partial": "PARCIAL",
            "returned": "RETORNADA",
        }
    )

    root_product_types: List[str] = field(default_factory=lambda: ["PA"])
    pi_product_types: List[str] = field(default_factory=lambda: ["PI"])
    active_delete_flag: str = ""
    max_bom_level: int = 10