# 19 — VISTA/TV CAPABILITY EXPANSION — Onda B2 (Templates) Execution Report

**Data:** 2026-10-31
**Mandato:** lifecycle de slide templates pela VISTA usando
exclusivamente os seis verbos (`get_context | read | analyze |
knowledge | execute | delete`). Baseline: B1 `8f268c3ed4` + doc 18.

## Git

| Campo | Valor |
|---|---|
| Base HEAD | `8e236a1d0f` |
| Upstream no push | `872d73c2d4` (rebase limpo — docs engineering) |
| Commit publicado | `7928f1c320` — `feat(tv-dashboard): VISTA B2 — slide_template lifecycle via six verbs` |
| Push | `HEAD:main` FF-only, worktree isolado `/tmp/a6-integ` |
| Arquivos alterados | 3 em `tv-dashboard-api/` (+624): `capability_surface.py`, `dispatch_service.py`, `tests/test_vista_b2_templates.py` |

## Arquitetura

- **Owners:** templates pertencem a `SlideTemplateLibraryService`
  (command boundary próprio — NÃO PresentationMutation). A VISTA
  integra via fachada governada: execute delega aos comandos
  canônicos do serviço; delete usa `VistaProposal` selada +
  `VistaConsentService` (A5) — mesma máquina de consentimento,
  recurso `slide_template` alvo-bound. Sem segundo owner/executor.
- **Auth:** `TV_TEMPLATES_MANAGE` (manage/library/mutations);
  `TV_READ` para lista/get de status `published` — mesma política
  das rotas REST.
- **MDD import/export:** deixado fora — fronteira B4 pendente de
  contrato próprio (`BLOCKED_BY_OWNER_CONTRACT` para esta onda).

## Migração / Capacidades

| CAPABILITY_ID | Verbo | Equivalente | DECISION |
|---|---|---|---|
| `read.slide_template.list` | `read` | `list_published`/`list_library` | REUSE |
| `read.slide_template.get` | `read` | `service.get` | REUSE |
| `execute.slide_template.create` | `execute` | `service.create` | EXTEND |
| `execute.slide_template.update` | `execute` | `service.update` | EXTEND |
| `execute.slide_template.clone` | `execute` | `service.clone` | EXTEND |
| `execute.slide_template.publish` | `execute` | `service.publish` | EXTEND |
| `execute.slide_template.unpublish` | `execute` | `service.unpublish` | EXTEND |
| `execute.slide_template.archive` | `execute` | `service.archive` (lifecycle, não-destrutivo) | EXTEND |
| `delete.slide_template` | `delete` | `service.delete` + consent A5 | EXTEND |

Lifecycle preservado: draft→published→archived via comandos do
serviço; conflitos/not-found/validation mapeados às exceções
canônicas (`SlideTemplateConflictError` etc.).

## Segurança

- `_governed_write_user` + `assert_permission(TV_TEMPLATES_MANAGE)`
  em todos os comandos e no delete.
- Delete: proposal selada (`delete.slide_template`), consent
  challenge mintado por proposta, `verify_for_commit` +
  `target_echo == templateId`, consume single-use, read-back.
- Sem `confirmation=true` em nenhum caminho.

## Testes

- **2318/2318 PASS** (78.6s). Novo `test_vista_b2_templates.py` —
  14 casos: superfície=6, list published/library/manage-denied,
  get (+ref exigido), create/publish/update/clone/unpublish/archive,
  permission 403, unknown action, delete prepare→commit VERIFIED,
  target_echo mismatch → CONFIRMATION_MISMATCH (não executa),
  consent channel ausente → CONFIRMATION_UNAVAILABLE.

## Produção

| Campo | Valor |
|---|---|
| Host | `srv-api` (`operador@192.168.1.237`) |
| Pipeline | `up-prod-sequential.sh --build tv-dashboard-api` |
| SHA prod | merge local contendo `7928f1c320` |
| Imagem | `infra-tv-dashboard-api` sha256:`70a6ea3adcf5a7b524ce0e9e1bcb9f2fff31112b3d7b5625a5e4b66e898433ac` |
| Container | `delpi-tv-dashboard-api` Up (32s), startup ok |
| OpenAPI público | **exatamente 6** `vista_*` — invariante |
| Rollback | imagem `57f34228bf9b` / `git revert 7928f1c320` + redeploy |

## Veredito

- `INTEGRATION_PASS`
- `CERTIFICATION_PASS` (2318/2318)
- `DEPLOY_VERIFIED`
- `B2_COMPLETE` — reads + mutations lifecycle + delete consent;
  MDD import/export aguarda contrato B4.

**Pendências:** B3 (exclusões/restauração playlists+data models),
B4 (MDD incl. template import/export — fronteira validada aqui),
B5 (shares/invites — exige owner do Core). Sync do Custom GPT
externo continua como follow-up operacional (doc 17).
