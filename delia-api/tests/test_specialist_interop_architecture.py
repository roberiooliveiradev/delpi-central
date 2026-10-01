"""Architecture tests for C3-MCP-INTEROP-01.

Locks the boundary shape: Domain/Application import no MCP SDK, HTTP, or
specialist-vendor code; planning carries no DAVI/TÉO/VISTA branching; no
generic proxies/routers/registries; and no direct business adapters for
API DELPI products, Transformômetro, or TV Dashboard were added.
"""

from __future__ import annotations

import ast
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1] / "app"
DOMAIN_APP_DIRS = (
    APP_ROOT / "domain",
    APP_ROOT / "application",
)

FORBIDDEN_IMPORT_FRAGMENTS = (
    "mcp",
    "fastmcp",
    "requests",
    "httpx",
    "urllib",
    "aiohttp",
    "flask",
    "fastapi",
    "sqlalchemy",
    "api_delpi",
    "tm_app",
    "tv_app",
)

FORBIDDEN_TYPE_NAMES = (
    "McpRouter",
    "ProviderRouter",
    "AgentRegistry",
    "McpRegistry",
    "UniversalToolRegistry",
    "AgentEngine",
    "ToolEngine",
    "DelegationEngine",
    "MultiAgentOrchestrator",
    "GenericHttpPort",
    "GenericToolPort",
    "UniversalApiPort",
    "UniversalMcpProxy",
    "DaviPort",
    "TeoPort",
    "VistaPort",
    "ProductSearchPort",
    "TransformometroPort",
    "TvDashboardPort",
)

FORBIDDEN_DIRECT_ADAPTERS = (
    "product_search",
    "transformometro_repository",
    "tv_dashboard_repository",
)


def _tree(path: Path) -> ast.AST:
    return ast.parse(path.read_text())


def _top_level_modules(path: Path) -> set[str]:
    modules: set[str] = set()
    for node in ast.walk(_tree(path)):
        if isinstance(node, ast.Import):
            modules.update(
                a.name.split(".")[0].lower() for a in node.names
            )
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            modules.add((node.module or "").split(".")[0].lower())
    return modules


def test_domain_and_application_have_no_mcp_or_http_imports():
    for directory in DOMAIN_APP_DIRS:
        for path in directory.rglob("*.py"):
            if "__pycache__" in str(path):
                continue
            imported = _top_level_modules(path)
            for fragment in FORBIDDEN_IMPORT_FRAGMENTS:
                assert fragment not in imported, (
                    f"{path} imports forbidden '{fragment}'"
                )


def test_no_forbidden_abstractions_anywhere():
    for path in APP_ROOT.rglob("*.py"):
        if "__pycache__" in str(path):
            continue
        for node in ast.walk(_tree(path)):
            if isinstance(node, ast.ClassDef):
                assert node.name not in FORBIDDEN_TYPE_NAMES, (
                    f"{path} defines {node.name}"
                )


def test_planner_core_has_no_specialist_branching():
    planning = APP_ROOT / "domain" / "planning"
    for path in planning.rglob("*.py"):
        if "__pycache__" in str(path):
            continue
        text = path.read_text().lower()
        for name in ("davi", "teo", "vista", '"teo"', "'teo'"):
            assert name not in text, f"{path} references specialist {name}"


def test_interaction_runtime_has_no_specialist_branching():
    path = (
        APP_ROOT
        / "application"
        / "interaction"
        / "handle_interactive_turn.py"
    )
    text = path.read_text().lower()
    for name in ("davi", "teo", "vista", "specialist"):
        assert name not in text


def test_no_direct_specialist_business_adapters():
    for path in APP_ROOT.rglob("*.py"):
        if "__pycache__" in str(path):
            continue
        lowered = str(path).lower()
        for marker in FORBIDDEN_DIRECT_ADAPTERS:
            assert marker not in lowered, f"direct adapter found: {path}"


def test_specialist_ids_only_exist_in_canonical_registry():
    """No scattered specialist literals outside the registry/composition."""
    for path in APP_ROOT.rglob("*.py"):
        if "__pycache__" in str(path):
            continue
        rel = path.relative_to(APP_ROOT).as_posix()
        if rel in (
            "domain/specialist_interop/rules.py",
            "infrastructure/interoperability/config.py",
            "infrastructure/config/settings.py",
            "composition/root_composer.py",
        ):
            continue
        text = path.read_text()
        for literal in ('"davi"', '"teo"', '"vista"', "'davi'", "'teo'", "'vista'"):
            assert literal not in text, f"{path} hard-codes specialist id"
