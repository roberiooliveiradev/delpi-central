# 24 — VISTA/TV FINAL E2E CERTIFICATION & OPERATIONAL HARDENING REPORT

**Data:** 2026-10-31
**HEAD certificado:** `f08076ea81` (= origin/main, worktree `/tmp/a6-integ`)
**Mandato:** certificação transversal pós-B1–B5 — sem novas
capabilities, sem novas tools/Actions.

## GATES G1–G10

| Gate | Condição | Veredito | Evidência |
|---|---|---|---|
| G1 — HEAD | Contratos/código revalidados | **PASS** | `f08076ea81` rebaseado; docs 17–23 e catálogo conferidos no HEAD |
| G2 — Six-tools | 6 tools + 6 Actions | **PASS** | `MCP_TOOL_NAMES=6` em teste; OpenAPI prod = exatamente 6 `vista_*` (todas as ondas); auxiliar `gpt_get_slide_preview_png` fora das Actions semânticas (documentado) |
| G3 — Capabilities | B1–B5 expostas | **PASS** | matriz abaixo — todas as capacidades com owner+contrato+teste |
| G4 — AuthZ | Core RBAC + resource scope | **PASS** | `assert_permission`/`PlaylistAccessService`/`require_governed_write` em todas as vias; negativos 403/404/409 verdes; zero Core-RBAC mutations (fora de escopo) |
| G5 — Consentimento A5 | Fluxo humano | **PENDING_EXTERNAL_VERIFICATION** | `BACKEND_CONSENT_PASS`: challenge→approve(step_up)→artifact→verify→consume único — `vista_consent_routes` + `test_vista_consent_foundation.py`. Canal humano externo (GPT Builder/Portal) não exercitável aqui → `EXTERNAL_CHANNEL_UNVERIFIED` |
| G6 — Shares/invites | Concessão/revogação efetivas | **PASS** | `playlist_share_service`: manage-gated, self-share bloqueado, redeem actor-bound, revokes selados+consent — 13/13 |
| G7 — MDD | Preview/apply/token | **PASS** com ressalva documentada | `_PreviewStore` in-memory single-process TTL900s single-use → `SINGLE_INSTANCE_CONSTRAINT` (válido p/ topologia atual de 1 container); token não actor-bound — 12/12 |
| G8 — Paridade | EDITOR≡PREVIEW≡TV | **PASS** | mutations passam pelos owners canônicos (patch/write service + notify `presentation_changed`) — sem render compensatório |
| G9 — Regressão | Suite completa | **PASS** | **2357/2357** em `f08076ea81` (77.4s) — nenhum skip |
| G10 — Runtime | Produção saudável | **PASS** | `delpi-tv-dashboard-api` Up 36min, imagem `778924bca211` (B5), 590→591 rotas, **tráfego MCP real: `POST /mcp/ 200 OK`**, OpenAPI 6 ops |

## MATRIZ DE CAPABILITIES B1–B5

| Capability | Verbo | Owner | Status | Tests |
|---|---|---|---|---|
| `execute.update_playlist` | execute | `PlaylistRepository.update` | PROVEN | B1 14/14 |
| `execute.activate_playlist`/`deactivate_playlist` | execute | `set_active` | PROVEN | B1 |
| `execute.duplicate_slide` | execute | `duplicate_slide` | PROVEN | B1 |
| `execute.reorder_sections` | execute | `reorder_sections` | PROVEN | B1 |
| `read.slide_preset.list` | read | `list_slide_presets` | PROVEN | B1 |
| `read.media_asset.list` | read | `media_query_service` | PROVEN | B1 |
| `read.slide_template.*` | read | `SlideTemplateLibraryService` | PROVEN | B2 14/14 |
| `execute.slide_template.*` (create/update/clone/publish/unpublish/archive) | execute | idem | PROVEN | B2 |
| `delete.slide_template` | delete | sealed+consent+`service.delete` | PROVEN | B2 |
| `delete.playlist` | delete | `playlist_lifecycle_service` | PROVEN | B3 11→13/13 |
| `delete.data_model` | delete | sealed pipeline + D-8 impact | PROVEN | B3+RC |
| `execute.playlist_history.restore` | execute | `restore` CAS | PROVEN | B3 |
| `read.*.export_mdd` | read | `export_package`/`export_mdd` | PROVEN | B4 12/12 |
| `execute.*.import_preview/apply` | execute | `preview_import`/`apply_import` token | PROVEN | B4 |
| `read.playlist.list_shares` | read | `playlist_share_service` | PROVEN | B5 13/13 |
| `execute.playlist.share/create_edit_invite/accept_edit_invite` | execute | idem | PROVEN | B5 |
| `delete.playlist_share`/`delete.edit_invite` | delete | sealed+consent+revoke | PROVEN | B5 |

## DESCOBERTAS / RESSALVAS

1. **`_PreviewStore` in-memory** (SINGLE_INSTANCE_CONSTRAINT): token de
   import expira em restart ou múltiplas réplicas. Topologia atual = 1
   container → válido; **deve ser reavaliado se escalar réplicas** —
   `NO_PATCH_REQUIRED` agora (contrato aceita volátil; `TOKEN_NOT_ACTOR_BOUND`
   — bind ao pacote, não ao ator; risco mitigado por TTL+URLsafe-24+single-use).
2. **Canal humano externo** (`EXTERNAL_CHANNEL_UNVERIFIED`): backend
   completo; UX de aprovação no Portal/GPT Builder fora do alcance
   desta sessão — gate G5 pendente de verificação por canal real.
3. **OpenAPI GPT Builder**: re-import externo segue follow-up (doc 17)
   — `PENDING_EXTERNAL_VERIFICATION`, consumidor MCP real já observado
   em produção (200 OK) sem bloqueio.
4. Deploy: **NO_DEPLOY_REQUIRED** — nenhuma mudança executável nesta
   certificação (documentação apenas).

## VEREDITO

**`PROGRAM_B_FINAL_ACCEPTANCE = PENDING_EXTERNAL_VERIFICATION`**

- 8/10 gates `PASS`; G5 = `BACKEND_CONSENT_PASS` +
  `EXTERNAL_CHANNEL_UNVERIFIED`; G3 = `PASS` (OpenAPI Builder sync
  pendente mas não-bloqueante).
- Nenhuma falha técnica. A pendência é verificação de canal humano
  externo + re-import do OpenAPI no GPT Builder — ambos operacionais,
  não de engenharia. Ao comprovar ambos: `PASS`.
