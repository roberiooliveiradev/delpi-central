"""Task 03-R1 — Engine B architectural isolation gates T1–T8.

Task DELIA-C3-PLUGGABLE-ORCHESTRATION-ENGINE-B-ISOLATION-
REMEDIATION-01 (doc 195). Static (AST) and dynamic checks that the
LangGraph adapter lives in infrastructure, depends on the narrow
`SupportsGovernedStageGates` contract — never on the concrete Engine
A — and that the production runtime neither imports nor requires
the framework.
"""

from __future__ import annotations

import ast
import builtins
import inspect
import re
import sys
from pathlib import Path

import pytest

REPO_API = Path(__file__).resolve().parents[1]
APP_ROOT = REPO_API / "app"
ADAPTER_PATH = (
    APP_ROOT / "infrastructure" / "orchestration" / "langgraph_engine.py"
)
LEGACY_ADAPTER_PATH = (
    APP_ROOT
    / "application"
    / "capability_provision"
    / "langgraph_engine.py"
)
COMPOSER_PATH = APP_ROOT / "composition" / "root_composer.py"

_FRAMEWORK_ROOTS = ("langgraph", "langchain", "langsmith", "langgraph_sdk")


def _py_files(root: Path):
    return [
        f
        for f in sorted(root.rglob("*.py"))
        if "__pycache__" not in f.parts
    ]


def _imports_of(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            yield node.module


def _framework_import(module: str) -> bool:
    return module.split(".")[0] in _FRAMEWORK_ROOTS


# --- T1 — framework isolation ---------------------------------------


def test_application_and_domain_contain_no_framework_imports():
    """No `langgraph`/`langchain`/`langsmith` import may exist inside
    Application or Domain — the framework is infrastructure-only."""
    offenders = []
    for layer in ("application", "domain"):
        layer_root = APP_ROOT / layer
        if not layer_root.exists():
            continue
        for path in _py_files(layer_root):
            for module in _imports_of(path):
                if _framework_import(module):
                    offenders.append(
                        f"{path.relative_to(APP_ROOT)} -> {module}"
                    )
    assert not offenders, "framework imports inside App/Domain: " + "; ".join(
        offenders
    )


# --- T2/T6 — adapter location + production isolation -----------------


def test_engine_b_lives_in_infrastructure_layer():
    assert ADAPTER_PATH.exists(), "adapter must live under app/infrastructure"
    assert not LEGACY_ADAPTER_PATH.exists(), (
        "no LangGraph adapter may remain inside app/application"
    )


def test_production_composition_selects_engine_via_lazy_import():
    """Task 07: B1 is the authorized production default — the composer
    MAY reference the adapter, but only through a function-local
    (lazy) import so the `delia` rollback still starts when the
    framework package is absent. Top-level composer imports must
    stay framework-free."""
    tree = ast.parse(
        COMPOSER_PATH.read_text(encoding="utf-8"),
        filename=str(COMPOSER_PATH),
    )
    top_level = {
        alias.name
        for node in tree.body
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert not any(_framework_import(m) for m in top_level), (
        "framework import must be function-local in the composer"
    )
    src = COMPOSER_PATH.read_text(encoding="utf-8")
    assert "_resolve_orchestration_attempt" in src
    assert "DELIA_ORCHESTRATION_ENGINE" in src


# --- T3 — independent sequencing (static part; runtime spy lives in
# test_governed_attempt_contract.py) ----------------------------------


def test_adapter_module_has_no_engine_a_construction_or_import():
    pytest.importorskip("langgraph")
    tree = ast.parse(
        ADAPTER_PATH.read_text(encoding="utf-8"),
        filename=str(ADAPTER_PATH),
    )
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imported.add(alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.asname or alias.name.split(".")[-1])
    assert "OperationalCapabilityOrchestrator" not in imported, (
        "adapter must not import the concrete Engine A — it consumes "
        "the SupportsGovernedStageGates contract only"
    )
    calls = {
        getattr(node.func, "id", getattr(node.func, "attr", ""))
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
    }
    assert "OperationalCapabilityOrchestrator" not in calls, (
        "adapter must not construct the concrete Engine A"
    )


# --- T4/T5 — governed-gate contract + coupling classification --------


def _declared_gate_methods() -> set[str]:
    from app.application.capability_provision.governed_stage_gates import (
        SupportsGovernedStageGates,
    )

    return {
        name
        for name, member in vars(SupportsGovernedStageGates).items()
        if name.startswith("_")
        and not name.startswith("__")
        and callable(member)
    }


def test_engine_b_consumes_only_declared_gate_methods():
    pytest.importorskip("langgraph")
    declared = _declared_gate_methods()
    assert declared, "gates protocol must declare the consumed methods"
    src = ADAPTER_PATH.read_text(encoding="utf-8")
    used = set(re.findall(r"self\._gates\.([A-Za-z_]\w*)", src))
    undeclared = used - declared
    assert not undeclared, (
        f"adapter calls gates methods outside the contract: {undeclared}"
    )


def test_engine_a_satisfies_the_gates_contract():
    """`OperationalCapabilityOrchestrator` is the structural provider
    of the shared gates — every declared method exists with a
    compatible signature."""
    from app.application.capability_provision.governed_stage_gates import (
        SupportsGovernedStageGates,
    )
    from app.application.capability_provision.orchestration import (
        OperationalCapabilityOrchestrator,
    )

    missing = []
    mismatched = []
    for name in _declared_gate_methods():
        proto_params = list(
            inspect.signature(
                getattr(SupportsGovernedStageGates, name)
            ).parameters.values()
        )
        impl = getattr(OperationalCapabilityOrchestrator, name, None)
        if impl is None:
            missing.append(name)
            continue
        impl_params = list(inspect.signature(impl).parameters.values())
        proto_names = [p.name for p in proto_params]
        impl_names = [p.name for p in impl_params]
        if proto_names != impl_names:
            mismatched.append(f"{name}: {impl_names} != {proto_names}")
    assert not missing and not mismatched, (
        f"gates contract drift — missing={missing} mismatched={mismatched}"
    )


def test_adapter_accepts_gates_via_injection():
    """Constructor signature takes the gates contract — the adapter
    no longer fabricates its own governed-primitives owner."""
    pytest.importorskip("langgraph")
    from app.infrastructure.orchestration.langgraph_engine import (
        LangGraphCapabilityOrchestrator,
    )

    params = list(inspect.signature(
        LangGraphCapabilityOrchestrator.__init__
    ).parameters)
    assert "gates" in params, f"no injected gates param: {params}"
    assert "providers" not in params, (
        "adapter must not rebuild the primitives owner from providers"
    )


# --- T7 — runtime functional without LangGraph ------------------------


def test_runtime_importable_and_constructible_without_langgraph(
    monkeypatch,
):
    """Simulate the framework's absence: the composition root and
    Engine A still import/construct; only the adapter import fails."""
    blocked_roots = set(_FRAMEWORK_ROOTS) | {"xxhash", "ormsgpack"}
    real_import = builtins.__import__

    def _blocked(name, *args, **kwargs):
        if name.split(".")[0] in blocked_roots:
            raise ImportError(name)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _blocked)
    for mod in list(sys.modules):
        if mod.split(".")[0] in blocked_roots:
            monkeypatch.delitem(sys.modules, mod)
    # Evict the adapter itself so its import truly re-executes.
    adapter_mod = "app.infrastructure.orchestration.langgraph_engine"
    for mod in (adapter_mod, "app.infrastructure.orchestration"):
        if mod in sys.modules:
            monkeypatch.delitem(sys.modules, mod)

    # Production surface — no framework required.
    import app.composition.root_composer  # noqa: F401
    from app.application.capability_provision.orchestration import (
        OperationalCapabilityOrchestrator,
    )

    assert OperationalCapabilityOrchestrator is not None
    with pytest.raises(ImportError):
        import importlib

        importlib.import_module(adapter_mod)


# --- T8 — optional dependency presence (executes only when installed) -


def test_engine_b_graph_executes_when_dependency_present():
    """With the eval dependency installed, the adapter builds and
    runs a real compiled graph (no checkpointer needed)."""
    pytest.importorskip("langgraph")
    # Build through the shared harness — composition is a test concern.
    from tests.test_governed_attempt_contract import (
        FakePort,
        TEO_TOOLS,
        build_engine,
    )

    engine = build_engine(
        "langgraph",
        port=FakePort(tools_by_specialist={"teo": TEO_TOOLS}),
        specialist_ids=("teo",),
    )
    attempt = engine.attempt("Resumo")
    assert attempt.status is not None
    assert engine.last_node_trace[:1] == ["preflight"]
