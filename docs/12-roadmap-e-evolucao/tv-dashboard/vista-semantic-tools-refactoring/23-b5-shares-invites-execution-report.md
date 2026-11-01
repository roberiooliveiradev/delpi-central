# 23 — VISTA/TV CAPABILITY EXPANSION — Onda B5 (Shares, Invites & Permissions) Execution Report

**Data:** 2026-10-31
**Mandato:** última onda do Programa B — shares, convites de edição e
permissões de recurso via os seis verbos, sem ACL/RBAC paralelo e sem
mutações de RBAC global do Core. Baseline: B4 `a048f18382` + doc 22.

## Git

| Campo | Valor |
|---|---|
| Base HEAD | `6356641b6f` |
| Upstream no push | `3b5633c70d` (rebase limpo — docs engineering) |
| Commit publicado | `0ffb9eba15` — `feat(tv-dashboard): VISTA B5 — playlist shares & edit invites via six verbs` |
| Push | `HEAD:main` FF-only, worktree isolado `/tmp/a6-integ` |
| Arquivos | 4 em `tv-dashboard-api/` (+777/−2) |

## Matriz de capacidades

| CAPABILITY_ID | Verbo | Owner | EQUIVALENT | DECISION | STATUS |
|---|---|---|---|---|---|
| `read.playlist.list_shares` | `read` | `PlaylistRepository.list_shares` + `PlaylistAccessService.can_manage` | YES | EXTEND | PROVEN |
| `execute.playlist.share` | `execute` | `PlaylistRepository.upsert_share` + notifies | YES | EXTEND | PROVEN |
| `execute.playlist.create_edit_invite` | `execute` | `create_edit_invite` (+redeemPath) | YES | EXTEND | PROVEN |
| `execute.playlist.accept_edit_invite` | `execute` | `redeem_edit_invite(token, redeemed_by=actor)` | YES | EXTEND | PROVEN |
| `delete.playlist_share` | `delete` | `revoke_share` (sealed+consent A5) | YES | EXTEND | PROVEN |
| `delete.edit_invite` | `delete` | `revoke_edit_invites` (sealed+consent A5) | YES | EXTEND | PROVEN |
| Permissões efetivas | `get_context` | resolução canônica já existente (capability surface + acesso por recurso) | YES | REUSE | PROVEN |

**Sem workflow Core RBAC nesta onda** — papéis globais, apps e grupos
permanecem `BLOCKED_BY_OWNER_CONTRACT` (owner = Core API; nenhuma
mutação de RBAC global implementada, conforme mandato).

## Arquitetura / Segurança

- `playlist_share_service` (application layer): boundary-safe — facade
  `gpt_actions` sem import de infra; delega aos métodos canônicos do
  `PlaylistRepository` e emite as mesmas notificações das rotas REST.
- `assert_can_manage` via `PlaylistAccessService.resolve().can_manage()`
  — mesma autoridade `need="manage"` das rotas (`require_playlist_access`).
- **Anti-escalation:** self-share bloqueado (contrato do owner);
  `targetUserId`/`role` apenas passam ao domínio (role máximo = política
  do owner); `accept_edit_invite` resgata com `redeemed_by=actor` do JWT
  — impossível aceitar em nome de terceiro; `created_by` sempre o ator.
- **Revogação:** `delete` entity `playlist_share`/`edit_invite` —
  proposta selada + consent challenge A5 + `target_echo` + consume +
  read-back (VERIFIED) — idêntico ao padrão destrutivo B2/B3.
- Tokens de convite nunca expostos em listas (só no invite criado,
  destinado ao manager — mesma superfície da rota REST).

## Testes

- **2357/2357 PASS** (76.1s). `test_vista_b5_shares.py` (13):
  list_shares manage/denied/ref, share upsert + self-blocked,
  create/accept/invalid invite, revoke share prepare→commit VERIFIED,
  targetUserId exigido, bulk revoke, consent channel ausente →
  `CONFIRMATION_UNAVAILABLE`.

## Produção

| Campo | Valor |
|---|---|
| Host | `srv-api` (`operador@192.168.1.237`) |
| Pipeline | `up-prod-sequential.sh --build tv-dashboard-api` |
| SHA prod | merge local contendo `0ffb9eba15` |
| Imagem | `infra-tv-dashboard-api` sha256:`778924bca21169f6f3978e91607b09864b4543ccc81886d7c01d60286c54abd7` |
| Container | `delpi-tv-dashboard-api` Up (7s) |
| OpenAPI público | **exatamente 6** `vista_*` — invariante |
| Rollback | imagem `88dbfcc34c3e` / `git revert 0ffb9eba15` + redeploy |
| Smoke destrutivo | **não executado** (política) |

## Vereditos

- `INTEGRATION_PASS`
- `CERTIFICATION_PASS` (2357/2357)
- `DEPLOY_VERIFIED`
- **`B5_COMPLETE`** — todas as capacidades do escopo aprovado
  implementadas; mutações Core RBAC corretamente fora de escopo.

## Programa B — Status global

| Onda | Status | Commit |
|---|---|---|
| B1 — playlist/slide/section ops + reads | SHIPPED | `8f268c3ed4` |
| B2 — templates lifecycle | SHIPPED | `7928f1c320` |
| B3 — deletes + restore | SHIPPED | `5af8011ab7` |
| D-8 residual closure | SHIPPED | `b5a8e47a75` |
| B4 — MDD import/export | SHIPPED | `a048f18382` |
| B5 — shares/invites | SHIPPED | `0ffb9eba15` |

**Definition of Done (Programa B):** capacidades aprovadas expostas
pelos seis verbos · zero novas tools/opIds · domínio preservado como
autoridade · consent verificável em destrutivas · editor/preview/TV
paridade mantida · testes provando comportamento · commits publicados
em `main` · deploys verificados em produção.
