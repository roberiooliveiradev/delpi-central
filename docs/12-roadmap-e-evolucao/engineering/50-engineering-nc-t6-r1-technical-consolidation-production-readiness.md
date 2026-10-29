# Engineering NC — T6.R1: Technical Consolidation & Production Readiness Evidence

Data: 2026-10-30 · Executor: Devin · Missão: `ENGINEERING.NC.T6.R1` (Plano Mestre 48)

## 1. Âncoras

| Item | Valor |
|---|---|
| BASE_HEAD (reancoragem) | `cd4e41c438c7b1a27c703a6a97c755056f94ddd9` |
| origin/main na reancoragem | `cd4e41c438` — idêntico ao HEAD; sem divergência |
| HEAD final desta consolidação | o commit que contém este documento |
| Trabalho concorrente preservado | `delia-api` (modificações não relacionadas ao NC; não tocadas) |

## 2. R1-A — Correção do drift de autorização

**Achado:** o doc 49 atribuía WRITE/PREPARE a `engineering.manage`; o código e os
testes sempre usaram `engineering.access`. Decisão vinculante da Coordenação:

| Permissão | Responsabilidade |
|---|---|
| `engineering.access` | READ, CREATE, UPDATE, DELETE, IMPORT e PREPARE funcionais autorizados |
| `engineering.manage` | administração/configurações — **não** concede acesso operacional |

**Correção aplicada:** doc 49 corrigido (tabela de contratos E-NC-07..10 e PREPARE
e ledger de capacidades EVA — nomes reais das tools `search_nonconformities`,
`get_nonconformity_history`, `get_nonconformity_tags`). Nenhum endpoint alterado.

**Verificação do código** (`nonconformity_routes.py`): todas as 12 rotas usam
`require_any_permission(["engineering.access"])`; nenhum uso de
`engineering.manage` ou permissão legada (`api-delpi.access`, `lmps.*`).

**Matriz AuthZ efetiva (testes em `test_nonconformity_routes.py`):**

| Caso | Resultado | Teste |
|---|---|---|
| Sem bearer token | 401 | `test_unauthenticated_denied` |
| Token inválido | 401 | `test_invalid_token_denied` |
| Sem `engineering.access` | 403 | `test_missing_permission_denied` |
| Somente `engineering.manage` | 403 | `test_manage_alone_does_not_grant_operational_access` |
| Permissão legada apenas | 403 | rejeição de permissão legada |
| Identidade de serviço | 403 WRITE | `test_service_principal_denied_write` |
| Core indisponível | fail-closed (401/403/503 conforme estágio) | cenários de falha Core |
| `engineering.access` | operações funcionais legítimas | casos positivos READ/WRITE |

Confirmação humana para ações destrutivas (`confirm_replace`, `allow_replace`)
é camada **independente** da autorização funcional — não confundidas.

## 3. R1-B — Inventário e reconciliação de regressões

| # | Teste | Classificação | Relação com NC | Causa-raiz | Correção | SHA afetado |
|---|---|---|---|---|---|---|
| 1 | `test_avatar_distribution_official_metadata` | ENVIRONMENTAL | nenhuma | `PUBLIC_BASE_URL` dev (`http://localhost`) vs contrato oficial `https` | fixture autouse que limpa `PUBLIC_BASE_URL` nos testes → fallback canônico `https://minhadelpi.com.br` | trabalho concorrente (rota avatar) |
| 2 | `test_avatar_distribution_in_persona_context` | ENVIRONMENTAL | nenhuma | idem | idem | idem |
| 3 | `test_constants_match_semantics_spec` | ENVIRONMENTAL | nenhuma | compose não montava `api-delpi/contracts` no container eng-api → `FileNotFoundError` do `lmp_semantics.v1.yaml` canônico | mount read-only `../api-delpi/contracts:/api-delpi/contracts:ro` em `infra/docker-compose.dev.yml` | configuração runtime dev |

**Resultado:** suíte Engineering API `410 passed, 1 warning in 12.29s` (warning
Starlette/AnyIO ambiental). Asserts não foram alterados para obter verde; as duas
correções atacam a causa-raiz (determinismo de ambiente e mount de contrato).

## 4. R1-C — Contratos e paridade funcional

Revalidação de `nonconformity_routes.py` + use cases + adapter vs legado:

| Contrato | Verificação | Estado |
|---|---|---|
| E-NC-01 list | filtros, sort whitelist (`registered_at\|occurrence_date\|sale_number\|lmp_number\|customer_name\|status`), paginação | PASS |
| E-NC-02 detail | UUID; 404 honesto | PASS |
| E-NC-03 history | append-only via trigger V008 | PASS |
| E-NC-04 indicators | streak legado preservado | PASS |
| E-NC-05 tags | normalização case-insensitive, ordenadas | PASS |
| E-NC-06 export | mesmo shape legado | PASS |
| E-NC-07 create | ator correto; status `open\|in_progress\|done` | PASS |
| E-NC-08 update | full-replace; `occurrence_date` obrigatória; `expected_updated_at` → 409 | PASS |
| E-NC-09 delete | cascade transacional sob trigger-guard | PASS |
| E-NC-10 import | `dry_run`; `confirm_replace`; status inválido → `skipped` por item | PASS |
| E-NC-11 context | OV/produto/BOM via facts oficiais eng-api→api-delpi | PASS |
| PREPARE | sem side effects; `requires_human_confirmation` | PASS |

Nenhuma rota NC chama api-delpi para lógica funcional — apenas enriquecimento
TOTVS via facts oficiais. Nenhuma divergência de semântica de negócio detectada.

## 5. R1-D — PostgreSQL e writer único

| Guarda | Evidência |
|---|---|
| Port sem psycopg | driver restrito a `infrastructure/persistence/` (teste arquitetural evoluído) |
| Principal dedicado | `ENG_NC_DB_*` exclusivo; construção **rejeita** `ENG_NC_DB_USER == PLUGINS_DB_USER` |
| Sem segundo writer | sandbox `delpi-nc-sandbox` = único writer em dev; produção não tocada |
| Domínio não mascarado | `_db()` propaga `NcConcurrencyError`/erros de domínio; só envolve inesperados em `NcRepositoryError` |
| Trigger append-only | deletes de histórico só sob GUC `app.allow_lmp_nc_history_delete` por transação |
| Replace-all bloqueado | `allow_replace` + `confirm_replace` + `ENG_NC_IMPORT_REPLACE_ENABLED=true` |
| Suíte sandbox | **10/10** com `NC_SANDBOX_DSN` explícito; fixture `reseed_sandbox` (session, autouse) torna a suíte idempotente — validada em 2 execuções consecutivas |
| Schema | fiel às migrations V001–V009; migrations produtivas **não aplicadas** (T7) |
| Secrets | nenhuma credencial em logs/artefatos/commits |

## 6. R1-E — EVA READ e PREPARE

Ledger API ↔ EVA (nomes efetivos):

| Contrato | EVA tool | Classe | Estado |
|---|---|---|---|
| E-NC-01 | `search_nonconformities` | READ | PASS |
| E-NC-02 | `get_nonconformity` | READ | PASS |
| E-NC-03 | `get_nonconformity_history` | READ | PASS |
| E-NC-04 | `get_nonconformity_indicators` | READ | PASS |
| E-NC-05 | `get_nonconformity_tags` | READ | PASS |
| E-NC-11 | `get_nonconformity_context` | READ | PASS |
| PREPARE | `prepare_nonconformity_mutation` | PREPARE | PASS — `read_only=True`, `side_effects="none"` |
| ACT | — | — | `DESTRUCTIVE_ACT_TOOLS` vazio — **PENDING por design** |

EVA não acessa PostgreSQL diretamente; todas as tools passam pelo composer da
Engineering API com o mesmo contexto de autorização (`_require_engineering_human`
+ token humano propagado). `_PLANNED_CAPABILITIES` marca itens não implementados
como `not_implemented` — nunca apresentados como PROVEN.

## 7. R1-F — Portal Engenharia

- Rota nativa `/apps/engineering/nonconformities` standalone: listagem, filtros,
  busca, sort, paginação, detalhe, histórico, contexto, tags, produtos, criar,
  editar, excluir, importar, exportar.
- `NC_HELP` canônico em `ncCopy.ts`; hints de ajuda em contexto/histórico
  (detalhe) e data de ocorrência (form).
- Botões CREATE/EDIT/DELETE/IMPORT não exigem `engineering.manage` — backend é a
  autoridade e usa `engineering.access`.
- Bridge legado `/lmps/nonconformities` preserva o registro legado; dashboard
  LMP intacto; sem cutover.
- MFE nunca chama api-delpi diretamente.

## 8. R1-G — Homologação no SHA final

| Superfície | Resultado |
|---|---|
| Engineering API (full) | `410 passed, 10 skipped*, 1 warning` |
| Adapter Postgres sandbox | `10/10` (com `NC_SANDBOX_DSN`) ×2 execuções |
| MCP/EVA (dentro da suíte) | 83 testes — contract freeze, authz, propagação |
| MFE `npm run ci` | lint 0 erros · 141 vitest · typecheck · build OK |
| Playwright real (Portal/SSO) | **10/10** — desktop 5/5 + mobile 5/5, zero pageerrors |

\* skips = suíte adapter sem `NC_SANDBOX_DSN` no run padrão — por design.

Negativos cobertos: 401, 403 (sem permissão, manage-only, legada, service
principal), 404, 409 optimistic-lock, indisponível honesto, import sem
`confirm_replace` bloqueado.

## 9. R1-H — Pacote de decisão T7 (runbook — **não executado**)

### 9.1 Ownership

| Item | Estado |
|---|---|
| Owner atual dos dados | legado api-delpi storage compartilhado `plugins` |
| Owner futuro | Engineering API — bounded context NC, schema `engineering` |
| Autorizações pendentes | grant de migração de dados, role DB dedicada em produção, freeze de writers legados — **não presumidos** |

### 9.2 Banco

- Role dedicada `eng_nc` (nome a definir pelo owner de dados) com grants mínimos:
  `SELECT/INSERT/UPDATE/DELETE` nas tabelas NC + `INSERT` no history; sem `DELETE`
  no history (enforce pela trigger V008).
- Schema: `engineering.lmp_nonconformities`, `..._products`,
  `..._problem_tags`, `..._history` — DDL = V001–V009.
- Runner de migrations: **requisito em aberto** — decidir runner (up-only,
  checksum, imutável) antes de T7; sandbox usou bootstrap manual, produção exige
  runner versionado.
- Backup pré-cutover + verificação de checksums das migrations aplicadas.
- Exclusividade de escrita: `ENG_NC_DB_*` é o único writer; guarda anti-`PLUGINS_DB_USER` já em código.

### 9.3 Cutover

1. Janela acordada + freeze dos writers legados NC.
2. Aplicar migrations V001–V009 no Postgres produtivo (runner versionado).
3. Criar role dedicada + grants mínimos.
4. Migrar dataset (import reconciliado ou cópia SQL auditada).
5. Apontar `ENG_NC_*` de produção; health check; smoke READ/WRITE.
6. Atualizar consumidores (catálogo Portal já pronto; legado permanece).
7. Reconciliação: contagens e amostragem vs legado.
8. Rollback: revert do env + reativação do writer legado; writes posteriores ao
   cutover no novo storage precisam de replay documentado.
9. Monitoramento: latência, erros 5xx, volume de writes NC por 30–60 dias.

### 9.4 Segurança

- **Risco legado:** `api-delpi.access` ainda concede WRITE no endpoint legado —
  hardening/revogação na janela de cutover (owner: api-delpi).
- Matriz de consumidores afetados: inventário de chamadores legados (TO_INVENTORY
  na telemetria 30–60d).
- Testes de autorização pós-deploy: positivo `engineering.access`, negativos
  manage-only/legada/anônimo.
- Estratégia de revogação: desligar permissão legada de write somente após
  reconciliação completa.

### 9.5 EVA

- READ tools disponíveis e PROVEN em dev.
- PREPARE validado sem side effects.
- ACT permanece bloqueado; critérios para habilitação futura: grants de
  produção concedidos, autorização explícita da Coordenação, matriz de
  confirmação humana implementada e auditada.

## 10. Produção — o que **não** foi feito

- Nenhum deploy, migration, grant, cutover ou desativação de legado.
- Nenhum double-write.
- EVA ACT não habilitado.
- Nenhum ACT produtivo executado.

## 11. Riscos e decisões pendentes

| Item | Status |
|---|---|
| Role/grants de produção | PENDING — requer aprovação do owner de dados |
| Runner de migrations | PENDING — decisão técnica pré-T7 |
| Guard legado `api-delpi.access ⇒ write` | PENDING — hardening na janela |
| Telemetria de consumidores legados | TO_INVENTORY 30–60d |
| Soft vs hard delete funcional | decisão funcional pendente |
| EVA ACT | bloqueado sem autorização separada |

## 12. Critérios de aceite NCR1

| ID | Critério | Status |
|---|---|---|
| NCR1-01 | Reancoragem e authorities | PASS |
| NCR1-02 | Documentação AuthZ corrigida | PASS |
| NCR1-03 | READ/WRITE protegidos por `engineering.access` | PASS |
| NCR1-04 | `engineering.manage` não concede acesso operacional | PASS |
| NCR1-05 | Regressões reconciliadas | PASS |
| NCR1-06 | Contratos E-NC-01..11 revalidados | PASS |
| NCR1-07 | PostgreSQL sandbox íntegro | PASS |
| NCR1-08 | Writer único preservado | PASS |
| NCR1-09 | Sem acesso indevido a credenciais compartilhadas | PASS |
| NCR1-10 | Histórico/auditoria e destrutivos protegidos | PASS |
| NCR1-11 | EVA READ validada | PASS |
| NCR1-12 | EVA PREPARE sem side effects | PASS |
| NCR1-13 | EVA ACT desabilitado | PASS |
| NCR1-14 | Portal NC funcional | PASS |
| NCR1-15 | Testes de navegador real | PASS |
| NCR1-16 | Boundary API DELPI preservado | PASS |
| NCR1-17 | Dashboard legado intacto | PASS |
| NCR1-18 | Runbook T7 completo | PASS |
| NCR1-19 | Documentação e ledger atualizados | PASS |
| NCR1-20 | Testes vinculados ao SHA final | PASS |
| NCR1-21 | Nenhum ACT produtivo executado | PASS |

## 13. Reworks desta missão

- Doc 49: `engineering.manage` → `engineering.access` em E-NC-07..10/PREPARE;
  nomes reais das tools EVA no ledger.
- `infra/docker-compose.dev.yml`: mount read-only de `api-delpi/contracts`.
- `test_eva_avatar_discovery_projection.py`: fixture determinística de
  `PUBLIC_BASE_URL`.
- `test_nonconformity_postgres_adapter.py`: fixture session `reseed_sandbox`
  para idempotência da suíte.

## 14. Commits e SHA final

| Commit | Conteúdo |
|---|---|
| este commit (seção de commits do relatório / `git log`) | Consolidação T6.R1: correção doc 49, mount de contracts, fixture avatar determinística, reseed sandbox, este documento |

**SHA final testado:** o commit que contém este documento — todas as evidências
das seções 2–8 foram executadas sobre a working tree que o compõe.
