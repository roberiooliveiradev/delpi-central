# 22 — VISTA/TV CAPABILITY EXPANSION — Onda B4 (MDD Import/Export) Execution Report

**Data:** 2026-10-31
**Mandato:** exportar/validar/preview/aplicar pacotes MDD (templates e
playlists) via os seis verbos, reutilizando os serviços canônicos.
Baseline: residual closure `b5a8e47a75` + doc 21.

## Git

| Campo | Valor |
|---|---|
| Base HEAD | `b5a8e47a75` |
| Upstream no push | `96f9ba03ce` (rebase limpo — docs engineering) |
| Commit publicado | `a048f18382` — `feat(tv-dashboard): VISTA B4 — MDD export/import via six verbs` |
| Push | `HEAD:main` FF-only, worktree isolado `/tmp/a6-integ` |
| Arquivos | 4 em `tv-dashboard-api/` (+420/−4) |

## Matriz de capacidades

| CAPABILITY_ID | Verbo | Owner | EQUIVALENT | DECISION | STATUS |
|---|---|---|---|---|---|
| `read.playlist.export_mdd` | `read` | `TvDeckPackageService.export_package` | YES | REUSE | PROVEN |
| `read.slide_template.export_mdd` | `read` | `SlideTemplateLibraryService.export_mdd` | YES | REUSE | PROVEN |
| `execute.playlist.import_preview` | `execute` | `TvDeckPackageService.preview_import` | YES | REUSE | PROVEN |
| `execute.playlist.import_apply` | `execute` | `TvDeckPackageService.apply_import(importToken)` | YES | REUSE | PROVEN |
| `execute.slide_template.import_preview` | `execute` | `SlideTemplateLibraryService.import_preview` | YES | REUSE | PROVEN |
| `execute.slide_template.import_apply` | `execute` | `SlideTemplateLibraryService.import_apply` → `create` | YES | REUSE | PROVEN |

## Contrato / Transporte

- **MDD = JSON** (`parse_slide_template_mdd` / `parse_package` +
  `validate_package_integrity`); transporte semântico = **JSON inline
  bounded ≤ 512 KiB** em `operations[0].mdd` — sem upload binário, sem
  Base64 ilimitado, sem caminho de arquivo.
- **`PREVIEW != APPLY`**: preview retorna `summary` + `importToken`
  (`_PreviewStore`, TTL 900 s, uso único via `pop`); apply exige
  `importToken` — o token opaco vincula o pacote validado (o modelo
  não pode substituir o pacote no COMMIT).
- Playlist apply cria programação **inativa por padrão** (mesma
  política da rota REST); `activateAfterImport` opt-in; `bindingPolicy`
  lenient|strict preservada.
- Sem segundo importador/exportador; sem converter formato.

## Segurança

- `_governed_write_user` + `assert_permission(TV_WRITE)` (playlist)
  / `TV_TEMPLATES_MANAGE` (template) em imports; `TV_READ` em exports.
- Validação canônica no owner (`parse_and_validate_mdd`,
  `validate_package_integrity`, `TvDeckPackageError` → 422); pacote
  alterado pós-preview não passa (token consome o raw armazenado).
- Conteúdo do pacote não eleva privilégio: `created_by/owner_user_id`
  = ator autenticado, nunca campos do arquivo.

## Testes

- **2343/2343 PASS** (84.5s + rerun focado). `test_vista_b4_mdd.py`
  (12): export playlist/template, ref exigido, preview sem persistência
  (`persisted=False`, `apply_import` não chamado), apply com token +
  nameOverride + created_by, token ausente, permission 403, MDD
  oversized, template preview/apply, denied sem manage.
- Contrato congelado corrigido: `playlist` tornou-se entidade válida
  → `UNKNOWN_ACTION` em `apply_mutation`; novo caso cobre
  `UNKNOWN_ENTITY` em entidade realmente inexistente.

## Produção

| Campo | Valor |
|---|---|
| Host | `srv-api` (`operador@192.168.1.237`) |
| Pipeline | `up-prod-sequential.sh --build tv-dashboard-api` |
| SHA prod | merge local contendo `a048f18382` |
| Imagem | `infra-tv-dashboard-api` sha256:`88dbfcc34c3eced67bd86680d7c619498321bdf215f532db1441ff7eff4b7762` |
| Container | `delpi-tv-dashboard-api` Up (18s) |
| OpenAPI público | **exatamente 6** `vista_*` — invariante |
| Rollback | imagem `7068fb95fb08` / `git revert a048f18382` + redeploy |
| Destrutivo em prod | **não executado** |

## Vereditos

- `INTEGRATION_PASS`
- `CERTIFICATION_PASS` (2343/2343)
- `DEPLOY_VERIFIED`
- **`B4_COMPLETE`** — as seis capacidades do escopo aprovado
  implementadas; nenhuma bloqueada (todos os owners/contratos
  existiam e foram reutilizados).

**Residuais:** pacotes acima de 512 KiB exigem o canal de upload do
editor (REST multipart — handoff fora do MCP, por contrato de
transporte); `activateAfterImport` opt-in conforme política do owner.
