# app/tests/test_get_me_use_case.py

from app.application.use_cases.get_me_use_case import GetMeUseCase


class DummyUser:
    def __init__(self):
        self.id = "123"
        self.name = "Rob"
        self.email = "rob@delpi.com"
        self.is_superadmin = False


def test_get_me_use_case_returns_expected_structure():
    user = DummyUser()
    permissions = ["crm.read", "crm.write"]

    uc = GetMeUseCase()
    result = uc.execute(user=user, permissions=permissions)

    assert result.id == "123"
    assert result.name == "Rob"
    assert result.email == "rob@delpi.com"
    assert result.is_superadmin is False
    assert result.permissions == permissions