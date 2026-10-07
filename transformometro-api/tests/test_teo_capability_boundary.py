"""TÉO final unified boundary — canonical registry + fail-closed contracts.

TEO-UNIFIED-BOUNDARY-FINAL-CORRECTION-03:

- R1: ``tm_app.application`` must not import ``tm_app.interface.mcp.*``
  (adapters depend inward, never the reverse).
- R2/R3: capability identity lives in
  ``intelligence.capability_registry``; unknown transport mappings fail
  closed (``ProjectionContractError``) — only registered legacy names
  render as explicit tombstones.
- P6: 1→N parity has an explicit ``mcp_primary``, never a naming
  heuristic.
- P7: MCP PREPARE reporting ``persisted=True`` is an invariant violation
  on the wire — never a success.
"""

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from tm_app.application.intelligence import capability_registry as reg
from tm_app.application.intelligence.capability_registry import (
    CAPABILITY_BINDINGS,
    CapabilityBinding,
    McpToolRef,
    ProjectionContractError,
    actions_operation_for_neutral,
    actions_parity,
    actions_to_mcp_primary,
    all_mcp_tool_names,
    mcp_native_tool_names,
    mcp_tool_classes,
)
from tm_app.application.intelligence.transport_projection import (
    neutralize_for_mcp,
)

APP_ROOT = (
    Path(__file__).resolve().parents[1] / "tm_app" / "application"
)
FORBIDDEN_PREFIX = "tm_app.interface.mcp"


def _python_files() -> list[Path]:
    return sorted(APP_ROOT.rglob("*.py"))


def _imports_interface_mcp(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith(FORBIDDEN_PREFIX):
                    hits.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module.startswith(FORBIDDEN_PREFIX):
                hits.append(module)
            # from tm_app.interface import mcp (relative sibling form)
            if module == "tm_app.interface" and any(
                a.name == "mcp" for a in node.names
            ):
                hits.append("tm_app.interface.mcp")
    return hits


class TestDependencyDirection:
    def test_application_never_imports_mcp_adapter(self):
        offenders = {
            str(p.relative_to(APP_ROOT.parent.parent)): _imports_interface_mcp(p)
            for p in _python_files()
            if _imports_interface_mcp(p)
        }
        assert offenders == {}

    def test_registry_and_projection_have_no_adapter_imports(self):
        for module in (reg,):
            path = Path(module.__file__)
            assert _imports_interface_mcp(path) == []


class TestCanonicalSingleSource:
    def test_adapter_maps_derive_from_one_binding_table(self):
        parity = actions_parity()
        primary = actions_to_mcp_primary()
        classes = mcp_tool_classes()
        names = set(all_mcp_tool_names())
        # Every parity entry comes from the same binding; no second list.
        assert set(parity) == {
            b.actions_operation
            for b in CAPABILITY_BINDINGS
            if b.actions_operation
        }
        assert set(primary.values()) <= names
        assert set(classes) == names

    def test_one_binding_change_updates_both_projections(self):
        synthetic = CAPABILITY_BINDINGS + (
            CapabilityBinding(
                id="synthetic.probe",
                actions_operation="gpt_synthetic_probe",
                mcp_tools=(McpToolRef("synthetic_probe", "READ"),),
                mcp_primary="synthetic_probe",
            ),
        )
        assert actions_parity(synthetic)["gpt_synthetic_probe"] == (
            "synthetic_probe",
        )
        assert "synthetic_probe" in all_mcp_tool_names(synthetic)
        assert actions_to_mcp_primary(synthetic)[
            "gpt_synthetic_probe"
        ] == "synthetic_probe"

    def test_mcp_native_capabilities_have_no_actions_projection(self):
        natives = mcp_native_tool_names()
        # Tool Surface Rationalization V1: MCP-native diagnostics are the
        # consolidated family tools.
        assert natives == {
            "diagnostic_read",
            "prepare_diagnostic_change",
        }
        for name in natives:
            with pytest.raises(ProjectionContractError):
                actions_operation_for_neutral(name)


class TestFailClosedMapping:
    def test_unknown_neutral_name_fails_closed(self):
        with pytest.raises(ProjectionContractError):
            actions_operation_for_neutral("totally_unknown_tool")

    def test_unknown_gpt_name_in_prose_fails_closed(self):
        with pytest.raises(ProjectionContractError):
            neutralize_for_mcp("call gpt_never_existed_operation now")

    def test_residual_commit_now_token_fails_closed(self):
        with pytest.raises(ProjectionContractError):
            neutralize_for_mcp("commit_now_flag_unmapped")

    def test_known_legacy_names_are_explicit_tombstones(self):
        out = neutralize_for_mcp(
            "legacy ops gpt_create_record and gpt_commit_improvement_package"
        )
        assert "removed_legacy_create_record" in out
        assert "removed_legacy_package_commit" in out
        assert "gpt_" not in out

    def test_binding_rejects_primary_not_in_tools(self):
        with pytest.raises(ProjectionContractError):
            CapabilityBinding(
                id="bad.primary",
                actions_operation="gpt_bad",
                mcp_tools=(McpToolRef("some_tool", "READ"),),
                mcp_primary="unrelated_tool",
            )

    def test_binding_rejects_non_gpt_actions_operation(self):
        with pytest.raises(ProjectionContractError):
            CapabilityBinding(
                id="bad.actions",
                actions_operation="not_a_gpt_op",
                mcp_tools=(McpToolRef("some_tool", "READ"),),
                mcp_primary="some_tool",
            )


class TestExplicitPrimaryMapping:
    def test_one_to_many_primary_is_explicit(self):
        # Family surface: multiple capabilities may share one family tool,
        # but every binding still declares its primary explicitly — never
        # derived by prefix/order.
        binding = next(
            b for b in CAPABILITY_BINDINGS if b.id == "meeting_minute.manage"
        )
        names = {ref.name for ref in binding.mcp_tools}
        assert names == {"prepare_meeting_minute_change"}
        assert binding.mcp_primary == "prepare_meeting_minute_change"
        # N capabilities → 1 family tool is now the common shape.
        shared = next(
            b for b in CAPABILITY_BINDINGS if b.id == "task.change.prepare"
        )
        assert shared.mcp_primary == "prepare_collaboration_change"

    def test_every_binding_declares_a_bound_primary(self):
        for binding in CAPABILITY_BINDINGS:
            assert binding.mcp_primary in {
                ref.name for ref in binding.mcp_tools
            }


class TestMcpPreparePersistedFailClosed:
    """P7/R4 — persisted=true on MCP PREPARE is a contract violation."""

    def _auth(self):
        from delpi_auth.request_context import (
            set_current_user,
            set_request_authorization,
        )

        user = SimpleNamespace(
            id="u1",
            email="teo@example.com",
            name="Téo",
            roles=[],
            groups=[],
            permissions=["transformometro.access"],
            is_superadmin=False,
        )
        return set_current_user(user), set_request_authorization("Bearer t")

    def _reset(self, user_token, auth_token):
        from delpi_auth.request_context import (
            reset_current_user,
            reset_request_authorization,
        )

        reset_request_authorization(auth_token)
        reset_current_user(user_token)

    def test_record_change_persisted_true_is_error(self):
        from tm_app.interface.mcp import tool_bridge as bridge

        user_token, auth_token = self._auth()
        try:
            with patch.object(
                bridge._governed,
                "prepare_record_change",
                return_value={"status": "ok", "persisted": True},
            ):
                result = bridge.tool_prepare_record_change(
                    entity="process_document",
                    operation="create",
                    changes={"titulo": "Doc"},
                )
            assert result.is_error is True
            payload = result.structured_content
            assert payload["success"] is False
            assert "contract violation" in payload["message"]
            assert payload["data"]["error_code"] == (
                "prepare_persisted_state_violation"
            )
        finally:
            self._reset(user_token, auth_token)

    def test_capability_prepare_persisted_true_is_error(self):
        from tm_app.interface.mcp import tool_bridge as bridge

        user_token, auth_token = self._auth()
        try:
            with patch.object(
                bridge._governed,
                "prepare_capability",
                return_value={"status": "ok", "persisted": True},
            ):
                result = bridge.tool_prepare_activate_revision(id="r1")
            assert result.is_error is True
            payload = result.structured_content
            assert payload["success"] is False
            assert payload["data"]["error_code"] == (
                "prepare_persisted_state_violation"
            )
        finally:
            self._reset(user_token, auth_token)
