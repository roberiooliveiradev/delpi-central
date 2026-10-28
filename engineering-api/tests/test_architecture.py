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


MCP_ADAPTER_DIR = PACKAGE_ROOT / "interface" / "mcp"

MCP_ONLY_PREFIXES = ("mcp", "delpi_mcp")


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
            # EVA.MCP.V1: o adapter MCP e superficie legitima em
            # interface/mcp -- fora dele, mcp/delpi_mcp seguem proibidos.
            if top in MCP_ONLY_PREFIXES and path.is_relative_to(MCP_ADAPTER_DIR):
                continue
            # delpi_mcp.auth fornece os gates de transporte MCP compartilhados
            # (mesmo papel de delpi_auth) — permitido apenas no middleware.
            if top == "delpi_mcp" and path.is_relative_to(PACKAGE_ROOT / "middleware"):
                continue
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


def test_inner_layers_never_import_mcp_adapter():
    # Camadas internas nao podem depender do adapter MCP.
    inner_layers = ("application", "infrastructure", "composition")
    violations = []
    for layer in inner_layers:
        layer_dir = PACKAGE_ROOT / layer
        if not layer_dir.is_dir():
            continue
        for path in sorted(layer_dir.rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    modules = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom):
                    modules = [node.module or ""]
                else:
                    continue
                for mod in modules:
                    if mod.startswith("engineering_app.interface.mcp"):
                        violations.append(f"{path} imports {mod}")
    assert not violations, "Inner layers importing MCP adapter:\n" + "\n".join(violations)
