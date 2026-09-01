from uuid import uuid4

from production_pulse_app.domain.services.binding_validation_service import (
    BindingValidationError,
    compose_placement_key_base,
    compose_placement_label,
    normalize_binding_input,
)


def test_compose_equipment_placement():
    binding = normalize_binding_input(
        {"anchorType": "equipment", "equipmentLabel": "Ventilador exaustão setor A"}
    )
    assert compose_placement_label(binding, device_name="ignored") == "Ventilador exaustão setor A"
    key = compose_placement_key_base(binding, branch="01", device_id=uuid4())
    assert key == "e:01:ventilador-exaustao-setor-a"


def test_work_center_requires_code():
    try:
        normalize_binding_input({"anchorType": "work_center"})
    except BindingValidationError as exc:
        assert "work_center_code" in str(exc)
    else:
        raise AssertionError("expected BindingValidationError")
