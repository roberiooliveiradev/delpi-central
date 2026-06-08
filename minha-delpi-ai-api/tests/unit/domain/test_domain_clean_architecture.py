import re
from pathlib import Path


def _domain_infra_imports() -> list[str]:
    domain_dir = Path("app/domain")
    patterns = (
        re.compile(r"from\s+app\.infrastructure\."),
        re.compile(r"import\s+app\.infrastructure\."),
    )
    violations: list[str] = []

    for path in sorted(domain_dir.rglob("*.py")):
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if any(pattern.search(line) for pattern in patterns):
                violations.append(f"{path}:{line_no}: {line.strip()}")

    return violations


def test_domain_has_no_infrastructure_imports():
    """DoD Fase 2 — domain não importa infrastructure."""
    assert _domain_infra_imports() == []


def test_chat_web_search_intent_has_no_application_imports():
    path = Path("app/domain/services/chat_web_search_intent_service.py")
    assert "app.application" not in path.read_text(encoding="utf-8")
