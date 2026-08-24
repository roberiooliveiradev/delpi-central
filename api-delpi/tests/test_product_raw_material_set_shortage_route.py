from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.application.security.api_delpi_permissions import (
    PRODUCTION_CONTROL_VIEW_FILIAL_01,
)
from app.interface.http.routes.product.raw_material_set_shortage_branch_access import (
    branch_access_error,
)
from app.interface.http.routes.product_routes import get_raw_material_set_shortages


def test_raw_material_set_shortages_envelope_has_stable_contract() -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "product": {"product_code": "90263114", "product_type": "PA"},
        "sets": [],
        "summary": {"open_set_count": 0, "at_risk_set_count": 0},
        "branch": "01",
    }
    with patch(
        "app.interface.http.routes.product_routes.raw_material_set_shortage_branch_error",
        return_value=None,
    ), patch(
        "app.interface.http.routes.product_routes.build_get_product_raw_material_set_shortages_use_case",
        return_value=use_case,
    ):
        response = get_raw_material_set_shortages(
            code="90263114",
            branch="01",
            max_depth=8,
        )
    body = response.body
    if hasattr(body, "decode"):
        import json

        payload = json.loads(body.decode())
    else:
        payload = body
    assert payload["success"] is True
    assert payload["meta"]["operationId"] == "get_product_raw_material_set_shortages"
    assert payload["meta"]["entity"] == "product_raw_material_set_shortages"
    assert payload["meta"]["shape"] == "composite_analysis"


def test_raw_material_set_shortages_returns_404_when_missing() -> None:
    use_case = MagicMock()
    use_case.execute.return_value = None
    with patch(
        "app.interface.http.routes.product_routes.raw_material_set_shortage_branch_error",
        return_value=None,
    ), patch(
        "app.interface.http.routes.product_routes.build_get_product_raw_material_set_shortages_use_case",
        return_value=use_case,
    ):
        response = get_raw_material_set_shortages(code="00000000", branch="01")
    assert response.status_code == 404


def test_branch_access_error_returns_403_for_denied_branch() -> None:
    user = SimpleNamespace(
        is_superadmin=False,
        permissions=[PRODUCTION_CONTROL_VIEW_FILIAL_01],
    )
    with patch(
        "app.interface.http.branch_access_gate.get_current_user",
        return_value=user,
    ), patch(
        "app.interface.http.branch_access_gate.has_permission",
        side_effect=lambda current_user, perm: perm in user.permissions,
    ):
        response = branch_access_error("02")
    assert response is not None
    assert response.status_code == 403
