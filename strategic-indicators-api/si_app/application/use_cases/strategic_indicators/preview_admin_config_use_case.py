from __future__ import annotations


def _empty_planned() -> dict[str, int]:
    return {
        "in_file": 0,
        "insert": 0,
        "update": 0,
        "skip": 0,
        "delete": 0,
    }


class PreviewStrategicIndicatorsAdminConfigUseCase:
    """Dry-run do bundle administrativo. Persistência entra em E1.S2."""

    def execute(
        self,
        *,
        bundle: dict,
        mode: str = "replace",
        include_goals: bool = True,
    ) -> dict:
        if not isinstance(bundle, dict):
            raise ValueError("Pacote de importação inválido.")

        schema_version = int(bundle.get("schema_version") or 0)
        if schema_version != 1:
            raise ValueError("schema_version incompatível: esperado 1.")

        _ = include_goals
        return {
            "valid": True,
            "errors": [],
            "mode": mode,
            "current_counts": {
                "departments": 0,
                "department_indicators": 0,
                "indicator_goals": 0,
            },
            "planned": {
                "departments": _empty_planned(),
                "department_indicators": _empty_planned(),
                "indicator_goals": _empty_planned(),
                "module_settings": _empty_planned(),
            },
        }
