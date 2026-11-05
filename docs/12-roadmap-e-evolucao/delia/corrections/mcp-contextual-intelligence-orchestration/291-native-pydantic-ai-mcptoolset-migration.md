# 291 — Native Pydantic AI MCPToolset migration

Task: `DELIA-C3-NATIVE-PYDANTIC-AI-MCPTOOLSET-FULL-MIGRATION-AND-LEGACY-REMOVAL-01`

## Change
Owner tool registration migrated from synthesized Python signatures
(`_capability_tool_signature`, `__signature__`/`__annotations__`,
`_make_owner_tool`, `_safe_tool_name`, `test_dynamic_tool_signature.py`
— all removed) to native `MCPToolset` per enabled specialist
(`filtered` on remote-name→capability_id, `RenamedToolset` so the
Agent-facing name IS the capability_id, `CombinedToolset`).

## Governance preserved (doc 231/240)
`process_tool_call` intercepts every call BEFORE the wire and delegates
to `_governed_semantic_tool_invoke` — live surface resolution, class
gate, candidate-token relay, schema validation, evidence/provenance,
audit all stay Application-owned. The SDK client performs discovery/
schema propagation only. `_EnvelopeHintedToolset` appends bounded
schema-derived usage guidance (replaces the old synthesized
description text) — presentation only, never authority.

## Deterministic fix (orchestration.py)
`_bind_identifier_args_from_utterance` now falls back to OPTIONAL
identifier-shaped fields when no required id-key exists (prefers
exact `code`/`id` when ambiguous) — binds utterance literal to the
owner-declared field. Bounded: value from user text, key from schema.

## Evidence (real turns, Ollama GPU)
- 50220013 → GROUNDED, CB18BRAN-00368/06/15-3100-0000, grp 5022, prov davi/mcp
- 99999999 → GROUNDED, PRODUTO UTILIZADO GENERICO, grp 9999, prov davi/mcp
- playlists → GROUNDED, RCA playlist real, prov vista/mcp
- Full suite: green. Loop tests migrated to `invoke_read_capability`
  meta-tool (same `_governed_invoke` path).

## SUPERSEDED/REMOVED (task NATIVE-MCPTOOLSET-DIRECT-ORCHESTRATION-01)
- `invoke_read_capability` — REMOVED. Generic proxy invoking a
  capability by textual id; native `MCPToolset` tools replace it.
- `list_read_capabilities` — REMOVED. Parallel listing surface that
  duplicated owner `tools/list`; eligibility stays internal via the
  governed catalog, never exposed to the model.
- Private-attribute config traversal (`_providers`/`_interop`/`_port`/
  `_connections`/`_credential_provider`) — REMOVED. Replaced by the
  legitimate contract chain `SupportsGovernedStageGates._native_toolset_config`
  → `McpCapabilityProvider.native_toolset_config` →
  `SpecialistInterop.native_toolset_config` →
  `SpecialistInteropPort.native_toolset_config` →
  `McpSpecialistAdapter` (profile + delegated credential, fail-closed).
- `_governed_invoke` / `_governed_semantic_tool_invoke` — PRESERVED
  (internal governance boundary, `process_tool_call` → governed path).
