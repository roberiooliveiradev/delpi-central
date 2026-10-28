"""Guardas arquiteturais do bounded context engineering-api.

Garantem que o pacote não acopla a outros bounded contexts, frameworks de IA,
persistence providers ou superfícies de integração fora do contrato.
"""

import ast
from pathlib import Path

SERVICE_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = SERVICE_ROOT / "engineering_app"

FORBIDDEN_IMPORT_PREFIXES = (
    "app",  # api-delpi/app
    "commercial_app",
    "requests_app",
    "si_app",
    "tm_app",
    "tv_app",
    "delia_app",
    "minha_delpi",
    "core_app",
    "supplies_app",
    "external_data_app",
)

FORBIDDEN_DEPENDENCY_PREFIXES = (
    "psycopg",
    "sqlalchemy",
    "asyncpg",
    "openai",
    "anthropic",
    "langchain",
    "mcp",
    "flask",
    "delpi_mcp",
)


def _iter_imports():
    for path in sorted(PACKAGE_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    yield path, node.lineno, alias.name
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                yield path, node.lineno, module


def _top_level(module: str) -> str:
    return module.split(".")[0]


def test_no_cross_context_imports():
    violations = []
    for path, line, module in _iter_imports():
        top = _top_level(module)
        if top in FORBIDDEN_IMPORT_PREFIXES:
            violations.append(f"{path}:{line} imports {module}")
    assert not violations, "Cross-context imports found:\n" + "\n".join(violations)


def test_no_forbidden_dependencies():
    violations = []
    for path, line, module in _iter_imports():
        top = _top_level(module)
        if top in FORBIDDEN_DEPENDENCY_PREFIXES:
            violations.append(f"{path}:{line} imports {module}")
    assert not violations, "Forbidden dependencies found:\n" + "\n".join(violations)


def test_no_domain_layer_for_bff():
    """engineering-api é BFF — camadas application/infrastructure/composition
    existem a partir da F2a (contratos, ports, gateways, composer), mas
    `domain` é proibido: regras de domínio pertencem aos owners oficiais."""
    present = [d.name for d in PACKAGE_ROOT.iterdir() if d.is_dir()]
    assert "domain" not in present, (
        "engineering-api não deve criar camada de domínio — BFF apenas compõe"
    )
