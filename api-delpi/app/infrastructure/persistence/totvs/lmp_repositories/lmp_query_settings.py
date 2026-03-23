# app/infrastructure/persistence/totvs/lmp_repositories/lmp_query_settings.py
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class LMPQuerySettings:
    branches: List[str] = field(default_factory=lambda: ["01", "02"])

    lmp_anchor_process_stages: Dict[str, List[str]] = field(
        default_factory=lambda: {
            "000002": ["000012"],
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