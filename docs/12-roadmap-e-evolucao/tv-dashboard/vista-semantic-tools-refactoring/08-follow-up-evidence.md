# 08 — Follow-Up Evidence (pendências da Fase 1 fechadas)

HEAD: `297068f1b7` (origin/main) · Branch: `docs/vista-semantic-tools-phase1`
· 2026-10-30. Cada item revalidado contra código real.

## Sumário

| # | Item | Status |
|---|---|---|
| 1 | `preview_data_block` executa a rota? | **PROVEN** (fase 1) |
| 2 | CAS/base_revision no commit path | **PROVEN — CAS completo** |
| 3 | Auditoria de writes MCP/Actions | **PROVEN domínio / INCONCLUSIVE canal** |
| 4 | Gate parity_map ↔ capability_surface | **PROVEN — gate de cobertura total** |
| 5 | Consumidores reais das 12 tools | **PROVEN código / INCONCLUSIVE runtime** |
| 6 | Campos de `update_playlist` | **PROVEN — gap confirmado** |
| 7 | Elicitation nos hosts | **PROVEN protocolo / por-host** |
| 8 | Budget OpenAPI/Actions | **PROVEN — 100 KiB + schemas compactos cabem** |
| 9 | Política `delete_data_model` | **PROVEN — decisão declarada, não drift** |

## 1. preview_data_block executa a rota

`TvDataPreviewService.preview_block` (`tv_data_preview_service.py:44`)
delega a `SlideDataResolutionService` — mesmo pipeline do player, com
`authorization`, `force_refresh` e `playlist_defaults`. **PROVEN.**

## 2. CAS / base_revision no commit path

`commit_service.py`:
- `:231` `expected_revision = proposal.base_revision` — mintado no
  PREPARE, selado no proposal.
- `:445` `self._writes.assert_expected_revision(playlist_uuid,
  expected_revision)` antes da mutação.
- `:568-1024` `chain_revision` re-assertado entre ops compostas
  (CAS por op dentro do plano).
- `:1040+` conflito → 409 com `code`, `currentRevision`,
  `revisionBefore`/`revisionAfter` no detalhe.

**PROVEN**: commits são CAS-guardados por playlist e por op. O cenário
"edição humana simultânea" produz 409 honesto, não write cego.
Doc 05 §3 atualizado conceitualmente — a dúvida original está
resolvida a favor do backend.

## 3. Auditoria de writes MCP/Actions

**Domínio (PROVEN)**: todo write passa por `TvPresentationWriteService`
→ `PlaylistRepository._capture_before_mutation` → história persistida
com `authorName` (ator real), `reason` (proveniência técnica
allowlisted — `TECHNICAL_PROVENANCE_CODES` em
`playlist_history_digest_service.py:40`), `revision`, `createdAt`.
Commits VISTA gravam `presentation_mutation` com o actor do token —
auditoria de conteúdo real e persistida.

**Decisão/verificação (PROVEN)**: `commit_service.py` emite logs
estruturados (`tv_dashboard.gpt_commit.verify`) e warnings com
`actor`, `client_id`, `operation`, `expected_revision`,
`current_revision`, `result` nas trilhas de conflito/verificação.

**Canal (INCONCLUSIVE)**: `presentation_mutation` não distingue
origem (editor WS vs MCP vs GPT Actions). A trilha mostra *quem* e
*o quê*, não *por qual transporte*. Gap menor: se forense por canal
for exigida, adicionar provenance code ou campo `channel` no registro
de história — backend já tem o ator; falta o transporte.

## 4. Gate parity_map ↔ capability_surface

`test_vista_mcp_client_migration.py:69`
`test_surface_parity_map_matches_registered_tools`:
- `set(mapping.values()) == set(MCP_TOOL_NAMES)` — toda tool
  registrada tem entry;
- `len(mapping) == 12` + chaves == os 12 `gpt_*` opIds;
- `not_exposed_in_mcp == ["gpt_get_slide_preview_png"]` explícito.

`test_vista_unified_boundary.py:261`
`test_one_parity_map_change_flows_to_both_projections` — alterar o
mapa muda a projeção Actions (fonte única, não duas listas).

**PROVEN**: drift parity↔surface falha no CI. A "duplicação"
registrada na fase 1 é governada por teste, não apenas por convenção.

## 5. Consumidores reais das 12 tools

**Código (PROVEN)**:
- `minha-delpi-ai-api/app/domain/services/chat_tv_dashboard_handoff_service.py`
  — handoff interno **só orienta**; docstring: "nunca emite tool
  calls". O Chat interno NÃO é consumidor das tools.
- Consumidores reais: Custom GPT externo (importa
  `openapi-gpt-actions.json` — 12 `gpt_*` opIds) e hosts MCP
  (Claude/outros — descobrem 12 tools via `tools/list`).

**Runtime (INCONCLUSIVE)**: volume/uso efetivo por consumidor não é
mensurável no repositório. Não inventamos telemetria — remover tools
exige evidência de migração externa (ver doc 11, E7).

## 6. Campos de `update_playlist`

`UpdatePlaylistBody` (`playlist_routes.py:69-80`): `name`,
`description`, `viewportProfile`, `viewportWidth`, `viewportHeight`,
`transitionStyle`, `defaultDurationSec`, `playbackMode`,
`globalRefreshSec`, `dataDefaults`, `masterConfig`.

Typed ops playlist-level: `create_playlist`, `patch_native_config`,
`patch_playlist_data_defaults`, `re_layer_playlist_filters`.

**PROVEN gap**: `name`, `description`, `viewport*`, `transitionStyle`,
`defaultDurationSec`, `playbackMode`, `globalRefreshSec` e
`masterConfig` (parcial via `patch_native_config`) **não têm typed op**
— playlist.update pós-criação é impossível para a VISTA hoje.

## 7. Elicitation nos hosts

- `delpi_mcp` shared **não expõe** elicitation (0 ocorrências).
- EVA usa `ctx.elicit()` do FastMCP diretamente
  (`engineering_app/interface/mcp/semantic_bridge.py:115-198`) —
  feature do framework/protocolo, não do substrate shared.
- Hosts: MCP clients que implementam elicitation (Claude Code/Desktop)
  suportam; hosts sem suporte recebem `confirmation_unavailable`
  (comportamento honesto EVA). **GPT Actions não têm elicitation** —
  o transporte HTTP/OpenAPI não carrega esse primitivo; precisa de
  prova equivalente (`target_echo` no payload) ou confirmação de
  plataforma do host.

**PROVEN**: elicitation é viável em MCP por-host, não universal;
Actions exige mecanismo alternativo — decisão arquitetural D-5
resolve com `target_echo` transport-neutral + elicitation quando
disponível.

## 8. Budget OpenAPI/Actions

`test_gpt_actions_catalog_budget.py`: hard gate de ~100 KiB no
catalog envelope (ResponseTooLargeError); "operations are index
without input schema" — o catalog já é projetado magro.

6 tools semânticas com schemas por-verbo (Literals fechados de
`entity`/`action`) são **menores** que 12 schemas por-operação:
vocabulário cabe em um schema compacto por tool (~1-3 KiB cada).

**PROVEN**: 6 verbos cabem com folga no orçamento; a compressão
principal vem de substituir 12 opIds por 6.

## 9. Política `delete_data_model`

`presentation_ops_content.json`: `"delete_data_model": {"risk":
"mutation", "confirmationPolicy": "direct"}` — a classificação é
**declarada** (`mutation`, não `destructive`). Data models vivem em
`nativeConfig`; a deleção não remove conteúdo visível diretamente.

**PROVEN**: não é drift nem omissão — é política registrada. Porém
`delete_data_model` pode órfanar bindings (consumidores do model) —
recomendar ao owner revisar se deveria ser `confirm` quando o model
tem consumidores. Fica como decisão D-8: owner-review, não bug.
