# 18 — VISTA/TV CAPABILITY EXPANSION — Onda B1 Execution Report

**Data:** 2026-10-31
**Mandato:** PROGRAM B — expandir capacidades do domínio TV Dashboard
exclusivamente pelos seis verbos semânticos
(`get_context | read | analyze | knowledge | execute | delete`).
Baseline: consolidação six-tools `06103630cf` + relatório doc 17.

## Git

| Campo | Valor |
|---|---|
| Base HEAD | `c23e3ee25b` (six-tools publicado) |
| Upstream no push | `8f51353a73` (rebase limpo — upstream = supplies/engineering docs) |
| Commit publicado | `8f268c3ed4` — `feat(tv-dashboard): VISTA B1 — playlist/slide/section ops + preset/media reads via six verbs` |
| Push | `HEAD:main` FF-only, sem force, worktree isolado `/tmp/a6-integ` |
| Arquivos alterados | 12 arquivos em `tv-dashboard-api/` (+6.445 / −5.056) |
| Conflitos | Nenhum |
| WIP preservado | Worktree compartilhado intocado |

## Arquitetura

- **Owners:** domínio preservado — ops executam via
  `TvPresentationWriteService` → `PlaylistRepository` (CAS + notify);
  VISTA permanece interface semântica. Sem novo executor, RBAC,
  registry, tool MCP ou GPT Action.
- **Camadas cobertas por op:** catálogo (`operations` + `capabilities`),
  `PresentationPatchService` (`_op_*` handlers), HTTP command planner
  (rotas CRUD), `TvGptCommitService._execute_acquired` (op→writes),
  `_verify_postcondition` (read-back autoritativo por op).
- **Boundary:** facade `gpt_actions` não importa infra — media read
  via novo `media_query_service` (gate
  `test_application_layer_ports_no_concrete_postgres` verde).
- **Drift:** nenhum novo; idempotência permanece no envelope canônico.

## Migração / Capacidades implementadas

| CAPABILITY_ID | Verbo | Equivalente | REUSE_DECISION |
|---|---|---|---|
| `execute.update_playlist` | `execute` | `_repo.update` (name/description/transition/duration/playback/viewport/refresh) | EXTEND |
| `execute.activate_playlist` | `execute` | `_repo.set_active` | EXTEND |
| `execute.deactivate_playlist` | `execute` | `_repo.set_active` | EXTEND |
| `execute.duplicate_slide` | `execute` | `_repo.duplicate_slide` | EXTEND |
| `execute.reorder_sections` | `execute` | `_repo.reorder_sections` (planner já existia) | EXTEND |
| `read.slide_preset.list` | `read` | `list_slide_presets()` | REUSE |
| `read.media_asset.list` | `read` | `MediaRepository.list_for_playlist` via `media_query_service` | REUSE |

Todas as mutações: PREPARE → (consent se `confirm`) → COMMIT →
read-back `_verify_postcondition` — VERIFIED só com estado
persistido comprovado; `confirmation=true` continua inexistente.

## Segurança

- AuthN user-bound; `_governed_write_user` + `assert_permission`
  TV_WRITE em prepare/commit (teste de permission fail 403 verde).
- `expected_revision` encadeado (`chain_revision`) em todas as
  branches do commit — CAS preservado.
- `read.media_asset.list` exige `ref=playlistId` + whitelist de
  filtros (`mediaKind`); filter desconhecido → VALIDATION_ERROR.
- Nenhuma rota nova de escrita fora do envelope governado.

## Testes

- **2304/2304 PASS** na árvore consolidada (75.68s).
- Novo `test_vista_b1_expansion.py` — 14 casos: superfície=6,
  update fields, empty-fields fail, activate/deactivate commit,
  permission 403, duplicate slide, missing slideId, reorder
  sections, bad items, preset list, media list, ref obrigatório,
  filter rejeitado.
- Gate de catálogo (`assert_valid`) exige capability por op —
  adicionadas 5 capabilities com markers/vocabulário.

## Produção

| Campo | Valor |
|---|---|
| Host | `srv-api` (`operador@192.168.1.237`) |
| Pipeline | `up-prod-sequential.sh --build tv-dashboard-api` |
| SHA prod | merge `2ae3b0e2978` (contém `8f268c3ed4`) |
| Imagem | `infra-tv-dashboard-api` sha256:`57f34228bf9b61f1eebfa85fb16409a3630a79eb706989a523f6e1c106ac3ecc` |
| Container | `delpi-tv-dashboard-api` Up — startup limpo, catálogo 590 rotas, MCP session manager |
| OpenAPI público | **exatamente 6** `vista_*` — invariante confirmada em runtime |
| Migrations | nenhuma | 
| Rollback | imagem anterior `44f12ff61c1a` / `git revert 8f268c3ed4` + redeploy |

## Veredito

`ACCEPT` — Onda B1 completa: 5 mutations + 2 reads expostas via os
seis verbos, capacidades proven em capability surface, segurança
preservada, produção verificada.

**Próxima onda:** B2 — Templates (listar/consultar/criar/atualizar/
clonar/publicar/arquivar/excluir via `read`/`execute`/`delete`).

**Pendências:** consumidores externos (Custom GPT) continuam
precisando do re-import do OpenAPI consolidado (follow-up do
doc 17); descoberta MCP autenticada depende do canal OAuth humano.
