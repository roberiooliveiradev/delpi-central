# Documento 102 — Revisão arquitetural independente do incremento P6-MIN + P2-READ

**Data:** 2026-10-24. **Task:** `CF-C3-P6-MIN-P2-READ-GPT-ARCHITECTURE-REVIEW-001`.
**BASE/HEAD revisado:** `f27dc307a48a5c9b37e6469e1c12d5f56ddbd896` (main) — commit da implementação. **Branch/worktree:** detached HEAD limpa.
**Método:** leitura adversarial do diff, revisão linha-a-linha de persistência/AuthZ/contratos/MFE, reexecução de suítes e **probes adicionais em PostgreSQL real** além dos testes reportados. O relatório do executor (doc 100) foi tratado como evidência, não como prova — duas imprecisões dele foram corrigidas nesta revisão (operationIds reais e path de `open`).

## 1. Arquivos efetivamente revisados

- `migrations/V001__create_closing_checklist_schema.sql` + `V002__seed_monthly_closing_checklist_v1.sql` (integral)
- `infrastructure/persistence/{plugins_db, migrations_runner, closing_checklist_repository}.py` (662 linhas, integral)
- `interface/http/{authz.py, routes/admin_checklist_routes.py, routes/competences_routes.py}` (integral)
- `domain/closing_checklist/errors.py`, `startup/run_migrations_on_startup.py`, `config.py`, `main.py`, `requirements.txt`, `infra/docker-compose.yml` (diff)
- `shared/delpi_auth/{authz_core.py, middleware/fastapi_auth.py}` — autoridade de effective permissions e fail-closed
- MFE: `competencesApi.ts`, `httpClient.ts` (`httpPost`), `ClosingChecklistPage.tsx`, manifest, rotas, catálogo, Help
- Testes: `test_pg_closing_checklist.py`, `test_admin_checklist_routes.py`, `test_closing_competences_routes.py`, `test_migrations_runner.py`, `ClosingChecklistPage.test.tsx`, estruturais

## 2. Matriz RQ/AC → implementação → teste → evidência

| Invariante/contracto | Implementação | Evidência | Estado |
|---|---|---|---|
| Schema isolado `controllership_finance` | V001; `_q()` qualifica toda tabela | PG real: nenhum objeto fora do schema | PROVEN |
| Migrations imutáveis + SHA-256 | `migrations_runner.run_migrations` | restart no-op + checksum divergence → `MigrationError` (teste unitário) | PROVEN |
| Seed 53 itens `DRAFT`, sem publish automático | V002 (53 tuplas verificadas, contagem SQL) | `test_seed_53_items_draft` | PROVEN |
| DRAFT não abre competência | `resolve_published_version` filtra `PUBLISHED` | `test_open_without_publish_fails` → `no_published_template` 409 | PROVEN |
| Publish só por operação autorizada | rota `manage` efetivo + UPDATE `status='DRAFT'` atômico | route tests + probe real: 4 threads → 1 winner, 3×`version_not_draft` | PROVEN |
| Edição de publicado negada | `WHERE status='DRAFT' AND revision=%s` | `test_published_immutable` | PROVEN |
| OCC/stale revision | `revision` otimista | `test_stale_revision_rejected` | PROVEN |
| Um DRAFT por template | índice parcial único | `test_second_draft_rejected` | PROVEN |
| Abertura concorrente ⇒ 1 competência | `UNIQUE(period)` + `ON CONFLICT DO NOTHING` + refetch | **probe real nesta revisão: 8 threads → 1 created, 7 replays, 1 registro, 53 `EXPECTED`** | PROVEN |
| Replay idempotente | retorna existente, 200 | `test_open_replay_idempotent` + probe | PROVEN |
| Snapshot imutável, v1×v2 isolados | cópia congelada `competence_checklist_item`, `source_*` sem FK | `test_competence_resolution_uses_vigente` | PROVEN |
| `EXPECTED ≠ entregue/validado` (RQ-P2-13) | `CHECK (state IN ('EXPECTED'))`; UI explícita | PG: `all(state='EXPECTED')`; teste UI | PROVEN |
| Sem R-ID sem automação fictícia (RQ-P2-14) | `totvs_report_ref` nullable, propagado nulo | seed + render honesta | PROVEN |
| Audit append-only (draft/publish/inactivate/open) | `_audit` dentro da mesma transação, só em criação real | `test_audit_trail_append_only` | PROVEN |
| ACCESS ≠ MANAGE | `authorized_user`/`authorized_admin` separados | `test_access_only_is_forbidden`, `test_manage_only_is_forbidden` | PROVEN |
| Service principal rejeitado | `principal_type != "user"` → 403 | `test_service_principal_denied` | PROVEN |
| Core indisponível ⇒ fail-closed | `rbac_unavailable` → 503; sem claims de permissão | `test_rbac_unavailable_fails_closed` | PROVEN |
| Sem permission nova | manifest permanece 2 permissions | manifest + residual search | PROVEN |
| Deep link/F5, Help, estados honestos | rotas `:period`, `CfQueryErrorBanner`, Help no diff | 100 vitest + 25 estruturais | PROVEN |
| Smoke autenticado E2E | — | não executado | TEST_NOT_RUN |

## 3. Achados adversariais

### R1 — Erro não tipado em `item_key` duplicado (menor)
`update_draft_items` com payload contendo `item_key` repetido dispara `UniqueViolation` **não mapeada** → exceção crua → HTTP 500 em vez de 409/422 tipado. Provado em PG real (probe P3). Critério de correção: traduzir `UniqueViolation` de `checklist_template_item` para erro de domínio (ex.: `duplicate_item_key`, 409/422) com teste.

### R2 — Fallback de `_actor` para e-mail quebra coluna UUID (menor)
`_actor(user) = user.id or user.email`; `actor_subject`/`opened_by` são `UUID`. Principal humano real sempre tem `id` = sub UUID do Core, então o caminho é inalcançável em produção — mas o fallback sugere semântica que falharia com `InvalidTextRepresentation` → 500 (probe P4). Correção mínima: remover fallback ou validar UUID.

### R3 — Drift de nomenclatura contratual vs doc 96 (não material)
Doc 96 era candidato, não congelamento: `:{publish,inactivate}` → implementado `/publish`, `/inactivate`; operationIds camelCase → snake_case (impl segue a convenção real dos irmãos — `list_portal_purchase_requests`); `already_published` → `version_not_draft` (409 equivalente); `db_unavailable` → `persistence_unavailable`. Recomendado reconciliar doc 96 ou registrar variantes aceitas. Doc 100 foi corrigido nesta revisão (operationIds reais e path de `open` = `POST /closing/competences {period}`, como o contrato).

### R4 — Fixture PG faz `DROP SCHEMA controllership_finance CASCADE` (observação)
`test_pg_closing_checklist.py` destrói o schema no banco-alvo. Hoje é opt-in via `CF_TEST_PG_*` e roda só em ambiente de teste; se apontado para um banco com dados reais, apaga. Sugerido: schema de teste dedicado/sufixo ou guarda explícita de ambiente. Não é migration — não viola `plugins-migrations-no-reset-prod`, mas merece endurecimento.

### R5 — RBAC com fallback de cache stale (observação de plataforma)
`load_user_rbac` (middleware compartilhado) serve cache stale quando o Core falha; permissões revogadas podem ser servidas dentro da janela de stale. Política transversal vigente, idêntica nos irmãos; mutações materiais poderiam futuramente usar `force_refresh`. Não é defeito do slice.

### R6 — Append-only por convenção (observação)
`closing_audit_event` é append-only por contrato de aplicação; não há `REVOKE UPDATE/DELETE`. Idêntico ao padrão dos irmãos.

### R7 — TOCTOU resolve×inactivate (observação teórica)
`resolve_published_version` executa fora da transação de `open_competence`; uma inativação concorrente na janela permite abertura com a versão recém-inativada. O snapshot é ponto-no-tempo, logo o efeito é defensável (a versão estava publicada no instante da resolução); registrado como janela teórica, sem impacto prático observado.

### R8 — `opened_by` retornado ao leitor (observação)
`open`/`get` retornam `opened_by` (UUID do abridor). Baixo risco (UUID opaco, rota access-gated); consistente com auditoria visível.

## 4. Checkpoints adicionais do handoff (doc 101)

- **Seed × matriz doc 95:** 53/53 tuplas conferidas; `CK-E-27` com nome exato da fonte, `totvs_report_ref=NULL` e `requirement_notes` honesta ("Produtor R-ID pendente (CP-D03 / TO_INVENTORY)") — sem R-ID inventado; distribuição de R-IDs confere (R13×12 extratos, R14×4 importações/câmbio, R01×3, R02×2 etc.); `recipient_area=NULL` preservado onde a fonte deixa lacuna; contexto industrial legado não vazou; planilha privada não versionada. `PROVEN`.
- **Admin scope:** implementação interpreta "escopo administrativo" como o próprio `manage` efetivo — única permission administrativa do produto — padrão `can_administer` dos irmãos e decisão CP-D05=A. **Advertência registrada:** se o PO pretender roster administrativo mais restrito que "todo usuário manage", será necessário mecanismo de escopo dedicado (não existe hoje no Core para este produto). Interpretação corrente: aceita; risco documentado.
- **Sem acesso direto à api-delpi pelo MFE:** confirmado — cliente bate só na BFF do produto (`cfApiUrl`).

## 5. Residual search e escopo

Confirmado no HEAD: zero upload/anexo, zero validação documental, zero R01–R15 oficial, zero P3/P4/P5, zero CLARA, zero permission/página DRE, zero escrita ERP/TOTVS, zero deploy. Imports cross-domain: nenhum. Segredos em logs/migrations: nenhum. Seed: rótulos oficiais apenas, sem bancos/pessoas/valores — lacunas (responsável/validador/destinatário) preservadas como `NULL`, sem invenção (CP-D02/03 honestos).

## 6. Testes executados nesta revisão

- BFF: `131 passed` (10 PG reais) — reexecutado no HEAD.
- MFE: `100 passed`/13 arquivos, `tsc` OK, eslint 0 problemas, estruturais `25/0`, build OK.
- Probes novos em PG real: concorrência 8 threads (1 competência), publish concorrente (1 winner), `item_key` duplicado (R1), actor não-UUID (R2).
- Smoke autenticado: `TEST_NOT_RUN` — declarado, não inflado.

## 7. Avaliação do GO e veredito

O GO `CF-C3-P6-MIN-P2-READ-RUNTIME-GO-001` foi cumprido: menor diff correto, decisões CP-D01/04/05 respeitadas, invariantes provados em PostgreSQL real (incluindo concorrência verdadeira, agora evidenciada), AuthZ backend-first fail-closed, UI honesta sem falso entregue. Nenhum desvio de escopo, nenhuma brecha de autorização material, nenhuma regressão.

**Veredito: `ACCEPT_WITH_RESIDUAL`.** Nenhum achado bloqueia o aceite. R1/R2 são endurecimento de erros tipados (REWORK menor recomendado como task de higiene, ~30 linhas + 2 testes); R3 é reconciliação documental; R4–R8 são observações de prateleira.

## 8. Próximo checkpoint permitido

`CF-C3-P2-UPLOAD-CONTRACT-GATE-001` — **documental apenas**: contrato de upload (documentos externos, PDFs/extratos/planilhas, storage persistente, metadados+hash, versionamento, download autorizado, retenção/auditoria, vínculo ao item do checklist). `P2-Upload ≠ validação humana`. Implementação exige contrato fechado e GO próprio; `DEPLOY_PRODUCTION_AUTHORIZED=NO` permanece.
