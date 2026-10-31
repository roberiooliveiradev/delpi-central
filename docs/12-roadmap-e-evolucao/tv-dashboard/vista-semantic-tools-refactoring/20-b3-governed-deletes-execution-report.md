# 20 — VISTA/TV CAPABILITY EXPANSION — Onda B3 (Exclusões e Restauração) Execution Report

**Data:** 2026-10-31
**Mandato:** `delete.playlist`, `delete.data_model` (política D-8),
`execute.playlist_history.restore` — exclusivamente pelos seis
verbos. Baseline: B2 `7928f1c320` + doc 19.

## Git

| Campo | Valor |
|---|---|
| Base HEAD | `9ed78ebb63` |
| Upstream no push | `b2d9a600f9` (rebase limpo — docs engineering) |
| Commit publicado | `5af8011ab7` — `feat(tv-dashboard): VISTA B3 — governed playlist delete, data_model delete, history restore` |
| Push | `HEAD:main` FF-only, worktree isolado `/tmp/a6-integ` |
| Arquivos | 7 em `tv-dashboard-api/` (+588/−10) |

## Arquitetura / Owners

| CAPABILITY_ID | Verbo | Owner canônico | DECISION |
|---|---|---|---|
| `delete.playlist` | `delete` | `PlaylistRepository.delete` + `notify_presentation_changed` (via `playlist_lifecycle_service`) | EXTEND |
| `delete.data_model` | `delete` | `_op_delete_data_model` (patch_service) — pipeline selado canônico | EXTEND |
| `execute.playlist_history.restore` | `execute` | `PlaylistHistoryRepository.restore` (CAS `expectedRevision`) via `playlist_lifecycle_service` | EXTEND |

- **`delete.playlist`**: PREPARE selada (`VistaProposal`
  `capability="delete.playlist"`, fingerprint do estado real) →
  consent challenge (A5) → COMMIT: `load_valid_proposal` +
  `verify_for_commit` + `target_echo==playlistId` + `consume` +
  `delete_playlist()` + consume proposta → VERIFIED.
- **`delete.data_model`**: `DELETE_ENTITIES["data_model"] =
  "delete_data_model"` — passa pelo pipeline selado existente
  (preview→consent→commit→read-back). `confirmationPolicy`
  `direct→confirm` e `risk` `mutation→destructive` (D-8: destrutiva
  exige consent verificável; dependências resolvidas pelo patch
  service — falha fecha).
- **`execute.playlist_history.restore`**: `EXECUTE_ENTITIES` com
  `playlist_history`; `restore` exige `target.{playlistId,
  historyId, expectedRevision}` → CAS (`PlaylistRevisionConflictError`
  → 409 + `currentRevision`) → read-back playlist → VERIFIED.
- **Boundary**: `gpt_actions` sem import de infra — novo
  `playlist_lifecycle_service` na application layer concentra
  repo calls + notificações (mesmos efeitos das rotas REST).

## Segurança

- `_governed_write_user` + `assert_permission(TV_WRITE)` / manage
  em todas as vias; `target_echo` ≠ consentimento; `confirm` ops
  fora do catálogo rejeitadas; `CONFIRMATION_UNAVAILABLE` fail-closed
  sem canal de consentimento; proposta de outro ator/expirada
  rejeitada pelo `load_valid_proposal`.

## Testes

- **2329/2329 PASS** (76.8s). `test_vista_b3_governed.py` (11):
  prepare→commit VERIFIED, echo mismatch → CONFIRMATION_MISMATCH
  (sem execução), 404, consent channel ausente, vocab gates, CAS
  commit, REVISION_CONFLICT 409, permission 403, refs exigidos.
- Contrato congelado atualizado honestamente: destructive set
  inclui `delete_data_model`; teste anti-restore substituído por
  propriedade real (viewer → 403).

## Produção

| Campo | Valor |
|---|---|
| Host | `srv-api` (`operador@192.168.1.237`) |
| Pipeline | `up-prod-sequential.sh --build tv-dashboard-api` |
| SHA prod | merge local contendo `5af8011ab7` |
| Imagem | `infra-tv-dashboard-api` sha256:`3124e1f1a9d9c2e734663db07c676a30f37b98456ea0de2156c21305dfad925c` |
| Container | `delpi-tv-dashboard-api` Up — startup limpo, 590 rotas |
| OpenAPI público | **exatamente 6** `vista_*` — invariante |
| Rollback | imagem `70a6ea3adcf5` / `git revert 5af8011ab7` + redeploy |
| Destrutivo em prod | **não executado** (política) |

## Vereditos

- `INTEGRATION_PASS`
- `CERTIFICATION_PASS` (2329/2329)
- `DEPLOY_VERIFIED`
- **`B3_COMPLETE`** — as três capacidades implementadas com gates.

**Residuais:** D-8 para DataModels em nível de playlist segue o
contrato slide-scoped do catálogo atual (`_op_delete_data_model`) —
escopo do owner; `delete_data_source` permanece não aprovado nesta
superfície; experiência humana de consentimento (canal confiável)
permanece gate operacional já documentado (docs 17–19).
