# 177 — CF-CHECKLIST-LIVE-004 — Plano HML + Manifesto preliminar de release

**Status:** `DRAFT / NOT_RELEASE_READY` — depende de `INDEPENDENT_VERIFY_PASS`,
autorização operacional HML e `HML_PASS` no mesmo SHA.

**SHA candidato:** `fc46a3fba5` (último commit CF-004 R4; posterior apenas docs).
**Revalidar SHA no momento do congelamento de release.**

## 1. Escopo do release técnico

| Componente | Conteúdo | Artefato |
|---|---|---|
| BFF | controllership-finance-api — rotas admin/competences do checklist vivo | imagem `delpi-hml/controllership-finance-api` |
| MCP | tools de leitura (7) + capabilities governadas (6) | mesmo serviço/API |
| MFE | plugins/controllership-finance — ChecklistLivePanel + admin/version | imagem `delpi-hml/controllership-finance` |
| Persistência | migrations V031–V036 (add-only) | `controllership-finance-api/migrations/` |
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

- Aplicação: runner canônico de migrations da API, ordem incremental,
  checksum imutável. **Nunca reescrever migration já aplicada.**
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
| 3 | Publicar V1 | Portal |
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
