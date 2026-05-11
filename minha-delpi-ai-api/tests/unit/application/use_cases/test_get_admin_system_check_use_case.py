from app.application.use_cases.get_admin_system_check_use_case import (
    GetAdminSystemCheckUseCase,
)


class FakeAdminSystemCheckRepository:
    def check(self):
        return {
            "status": "ok",
            "database": {"status": "ok", "reachable": True},
            "pgvector": {"status": "ok", "installed": True},
            "tables": {"status": "ok", "missing": []},
            "llm": {"status": "ok", "provider": "ollama"},
        }


def test_get_admin_system_check():
    use_case = GetAdminSystemCheckUseCase(FakeAdminSystemCheckRepository())

    result = use_case.execute()

    assert result["status"] == "ok"
    assert result["database"]["reachable"] is True
    assert result["llm"]["provider"] == "ollama"
