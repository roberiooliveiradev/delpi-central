from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class LMPQuerySettings:
    branches: List[str] = field(default_factory=lambda: ["01"])

    lmp_process_stages: Dict[str, List[str]] = field(
        default_factory=lambda: {
            "000002": ["000012"],
            "000003": ["000012"],
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
            "in_progress": "EM_ANDAMENTO",
            "finished": "FINALIZADA",
            "partial": "PARCIAL",
        }
    )

    root_product_types: List[str] = field(default_factory=lambda: ["PA"])
    pi_product_types: List[str] = field(default_factory=lambda: ["PI"])
    active_delete_flag: str = ""
    max_bom_level: int = 999