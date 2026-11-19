# 177 — CF-CHECKLIST-LIVE-004 — Plano HML + Manifesto preliminar de release

**Status:** `DRAFT / NOT_RELEASE_READY` — depende de `INDEPENDENT_VERIFY_PASS`,
autorização operacional HML e `HML_PASS` no mesmo SHA.

**SHA candidato:** HEAD `main` pós CF-CLARA-RUNTIME-002 (fix do resolver
de versão multi-série + teste de regressão; revalidar no congelamento).

## 1. Escopo do release técnico

| Componente | Conteúdo | Artefato |
|---|---|---|
| BFF | controllership-finance-api — rotas admin/competences do checklist vivo | imagem `delpi-hml/controllership-finance-api` |
| MCP | 6 tools semânticas (`get_context`, `read`, `analyze`, `knowledge`, `execute`, `delete`); catálogo runtime DEV: 50 read + 2 analyze + 3 knowledge + 53 governadas — entidade `checklist`: 8 reads + 15 governadas | mesmo serviço/API |
| MFE | plugins/controllership-finance — ChecklistLivePanel + admin/version | imagem `delpi-hml/controllership-finance` |
| Persistência | migrations V031–V038 (add-only; V037 entry-audit, V038 backfill SUPERSEDED) | `controllership-finance-api/migrations/` |
| Dispatcher | checklist sync poller atrás de flag | `CF_CHECKLIST_SYNC_DISPATCH_ENABLED` |

## 2. Migrations (ordem e precondições)

| Ordem | Migration | Efeito |
|---|---|---|
| 1 | V031 | `checklist_template_series` + backfill série 1 legada |
| 2 | V032 | `checklist_version_revision` + `cancel_origin` |
| 3 | V033 | `completion_record`/`first_completed_at` + backfill |
| 4 | V034 | `closure_reason`/`closed_by`/`closed_at` (encerramento adm.) |
| 5 | V035 | `checklist_sync_event`/`checklist_sync_run` (outbox) |
| 6 | V036 | UNIQUE parcial 1 PUBLISHED/série + estado `SUPERSEDED` |
| 7 | V037 | `entry_audit` cause grouping (contexto LNF) |
| 8 | V038 | backfill PUBLISHED excedente → `SUPERSEDED` (idempotente) |

- Aplicação: runner canônico de migrations da API, ordem incremental,
  checksum imutável. **Nunca reescrever migration já aplicada.**
- **Restrição comprovada (RT-002, DB efêmero):** a V036 não aplica sobre
  base com PUBLISHED excedente na série (UniqueViolation no índice) e a
  V038 exige o CHECK novo da V036. O único caminho válido sobre excesso é
  CHECK→backfill→índice (o que a V036 interina de DEV fazia). Em bases
  onde a V036 já aplicou, não existe excesso possível — V038 é no-op.
  Confirmar ausência de PUBLISHED duplicado por série em HML/PROD antes
  do deploy (read-back §5).
- Pré-condição: backup/snapshot do banco de plugins + verificação de
  `schema_migrations` (V030 aplicada).
- Compensação: DDL aditiva — rollback por restore de backup (não por down
  migration); preserva histórico.
- Read-back: contagens de séries/versões, índice UNIQUE ativo,
  `completion_record` backfilled, outbox vazio.

## 3. Flags e configuração

- `CF_CHECKLIST_SYNC_DISPATCH_ENABLED` — **default "1"**: definir `0`
  explicitamente no deploy HML e só ativar após prova de converge/retry em
  HML; em PROD permanecer `0` até o gate da operação de catálogo.
- `CF_CHECKLIST_SYNC_DISPATCH_INTERVAL_SECONDS` — default 60.
- `CLARA_CONSENT_CHANNEL` — DEV efetivo `conversational` (runtime
  verificado em RT-002). **Não consta em `env.hml.example`/`docker-compose.hml.yml`**
  → HML assume default `portal` se `.env.hml` não definir; definir
  explicitamente no deploy HML conforme decisão do owner (doc 150 §20.16).
- `CONTROLLERSHIP_FINANCE_RUN_MIGRATIONS_ON_STARTUP` — DEV efetivo
  **unset → default `false`** (V038 pendente em DEV é deliberado); HML
  compose default `true` — V038 aplica na próxima subida HML.
- `CF_DOCUMENT_UPLOAD_DIR` — volume persistente conforme compose HML.

## 4. Inventário HML (preflight)

- [ ] Ambiente srv-api HML disponível; autorização operacional concedida
      (escopo, comandos, janela, baseline, rollback — AGENTS.md §162).
- [ ] `git pull` do SHA candidato; imagens buildadas via procedimento
      canônico `up-hml-sequential.sh` (apenas por operador autorizado).
- [ ] `schema_migrations` em V030; backup/snapshot registrado.
- [ ] Flags documentadas; dispatcher DESLIGADO na subida inicial.
- [ ] Usuários de teste com `.access` e `.manage` provisionados.
- [ ] Catálogo MCP/tools conferido no host conectado.

## 5. Matriz de testes HML (24 cenários)

| # | Cenário | Superfície |
|---|---|---|
| 1 | Nova sequência → V1 | Portal + MCP |
| 2 | Inicializar catálogo (16 exigências) | Portal + MCP |
| 3 | Publicar V1 | Portal + MCP |
| 4–6 | Revisões ADD/UPDATE/REORDER append-only | Portal + MCP |
| 7 | RETIRE → item sai, evidência preservada | Portal + MCP |
| 8 | Correção PENDING → `CLOSED_REQUIREMENT_RETIRED`/`closed_administrative` | Portal + MCP |
| 9 | Pendência → `DISMISSED/catalog_retire`; alheias intactas | Portal + MCP |
| 10 | REACTIVATE só `CATALOG_RETIRE`; manual intocado | Portal + MCP |
| 11 | REVERT revisão (compensatória append-only) | Portal + MCP |
| 12 | Sync automático pós-revisão (dispatcher) | runtime |
| 13 | Falha + retry governado + dead-letter | runtime + Portal/MCP |
| 14 | Read-back divergente reabre run | runtime |
| 15 | Competência nunca concluída: sync elegível | runtime |
| 16 | Competência concluída: marker write-once, sync bloqueado | runtime |
| 17 | Reabertura não limpa marker | runtime |
| 18 | Alta-marca: descarte não reutiliza número | Portal |
| 19 | Autorização negativa: 401/403, sem `.manage`, escopo | Portal + MCP |
| 20 | PREPARE→confirmação→ACT→read-back | MCP/ChatGPT |
| 21 | Plano stale/expirado/ator divergente/idempotente | MCP |
| 22 | Paridade outcome Portal≡MCP por operação | ambas |
| 23 | Regressão funcional (pacote, P3, documentos, pendências) | Portal |
| 24 | Smoke pós-deploy: login, checklist, admin, sync-status | Portal + MCP |

## 6. Rollback

- Flags: `CF_CHECKLIST_SYNC_DISPATCH_ENABLED=0` (seguro, sem DDL).
- Serviços: retorno à imagem anterior (BFF/MCP/MFE) — schema aditivo
  permanece compatível; consumidor de sync desligado primeiro.
- Banco: restore do snapshot somente sob decisão operacional (DDL
  aditiva não exige down-migration para rollback de serviço).
- Evidências históricas nunca são objeto de rollback.

## 7. Operação governada de catálogo (PROD, pós-deploy)

Separada do deploy técnico. Exige `.manage`, motivo, confirmação,
OCC, idempotência, auditoria e read-back:

1. `start_checklist_sequence` (nova série → V1 draft).
2. `initialize_checklist_catalog` com as 16 exigências.
3. Publicar V1 (`effective_from_period` prospectivo).
4. Read-back: série ativa, V1 PUBLISHED, 16 itens, audit trail.
5. Só então ativar `CF_CHECKLIST_SYNC_DISPATCH_ENABLED=1`.

## 8. Riscos e critérios de aborto

- Abortar se: divergência de read-back > N runs, dead-letter crescente,
  marker `first_completed_at` duplicado/regredido, 403 indevido em rotas
  admin, ou qualquer mutação em competência historicamente concluída.
- Riscos remanescentes: verificação independente pendente (quota cursor/
  auth devin); paridade runtime no host ChatGPT não comprovada; build
  depende de HEAD estável.

## 8a. Evidências CF-CLARA-RUNTIME-002 (DEV, SHA worktree pós-fix)

- `checklist.series_start` — PREPARE→confirmação conversacional→ACT→
  read-back **PROVEN** em template smoke: série N+1 ACTIVE com V1 DRAFT,
  série anterior CLOSED e rastreável; idempotência `replayed=true`;
  `proposal_stale` em proposta concorrente; `forbidden` sem `.manage`.
- `checklist.catalog_initialize` — ACT **PROVEN**: 16 itens V1, keys
  únicas, fingerprint determinístico, paridade de leitura MCP≡BFF,
  auditoria completa; negativos `replayed`, `idempotency_conflict`,
  `duplicate_item_key`, `catalog_not_empty`, `forbidden` PASS.
- `checklist.sync_retry` — ACT **PROVEN**: run FAILED→PENDING, evento
  EMITTED→DISPATCHED→CONVERGED (attempts+1), run não-elegível intocado;
  negativo `sync_retry_not_allowed` em evento sem FAILED/PARTIAL;
  auditoria `CHECKLIST_SYNC_RETRIED`+`CLARA_GOVERNED_ACT`.
- `checklist.version_publish` — ACT **PROVEN** (após fix do resolver):
  PREPARE selado `REVIEW`→ACT→`PUBLISHED` com vigência; guard
  `window_covers_open_competence` respeitado; 1 PUBLISHED/série.
- **Fix de runtime aplicado:** resolver de estado de versão CLARA passa a
  usar resolução canônica por série (ORDER series_no DESC), eliminando
  `outcome_verification_failed` espúrio com múltiplas séries; pós-condição
  de `version_submit` corrigida para o status canônico `REVIEW`.
- Consentimento conversacional efetivo: PREPARE retorna
  `consent_channel=conversational`, `portal_consent_required=false`,
  `conversational_act_armed=true`; nenhum ACT exigiu Portal.
- Host ChatGPT real: **TEST_NOT_RUN** — conector/sessão autorizada
  indisponível ao executor; `HOST_CHATGPT_VERIFIED` permanece
  `INCONCLUSIVE`. Servidor MCP/OAuth validado em DEV
  (initialize, tools/list=6, PRM well-known, audience, escopos).
- V036+V038 legado: homologado em DB efêmero — backfill reclassifica
  excedentes para `SUPERSEDED`, winner=janela mais recente, snapshots e
  vínculos de competência preservados, resolução histórica por período
  intacta, reaplicação no-op. Restrição de ordem documentada no §2.

## 9. Autorizações necessárias

| Ação | Autoridade |
|---|---|
| `git pull` + `up-hml-sequential.sh` em HML | operador plataforma (AGENTS §162) |
| migrations HML | incluído na autorização HML |
| ativação do dispatcher | operador + evidência de sync convergente |
| deploy PROD | autorização operacional específica + HML PASS |
| operação de catálogo (§7) | usuário `.manage`, confirmação governada |

## 10. Campos pendentes (preencher em HML)

- SHA congelado final · imagens/checksums · janela · resultado do
  verificador independente · evidências `HML_PASS` · smoke · read-back.
