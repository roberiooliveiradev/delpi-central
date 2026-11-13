# PRC-TRACK — G0 inventário reancorado e G1 pacote de decisões para Coordination

> **DECISÃO DO PO RECEBIDA — 2026-11-13:** Ler [Deliberações G1 do PO](./PRC-TRACK-G1-PO-DECISIONS-2026-11-13.md). ADR-01–07 têm escolha funcional registrada; **isso não equivale à ratificação pela Coordination**. Os pontos de snapshot PRC vs valor oficialmente verificado, no-op, projeção de flags e corte temporal precisam de contratos. Referências anteriores neste inventário são evidência de código e propostas, não decisões finais conflitantes.

> **Data:** 2026-11-13 · **Estado:** `G0_PARTIAL / G1_DECISION_REQUIRED`. **Não é ADR ratificada.**  
> **Escopo:** preparação para B1–B3 do [pacote integrado](./PRC-TRACKED-PRODUCTS-IMPLEMENTATION-PACKAGE-PLAN.md).  
> **Não autoriza:** migration, implementação, deploy, alteração de owner/authority ou conclusão do gate PRC-UI-EXTRACT-01.

## 1. Evidence ledger: GitHub default branch

| Evidência | Origem | Classificação |
|---|---|---|
| Migração de 4 componentes `FlagFieldAction`, `FlagLegend`, `FlagSummaryView`, `FlagEditorDialog` | Relatório do executor fornecido em conversa, com worktree não commitado | `REPORTED / PENDING_ACCEPTANCE` |
| `plugins/plugin-ui/src/components/prc/PrcFlags.tsx` | `fetch_file` GitHub retornou 404 nesta inspeção | `NOT_PROVEN_ON_DEFAULT_BRANCH` |
| `plugins/plugin-ui/src/index.ts` | arquivo consultado, sem os quatro símbolos na inspeção | `NOT_PROVEN_ON_DEFAULT_BRANCH` |
| `product_registration_records` e `product_registration_revisions` | `api-delpi/migrations/plugins/engineering/V012__product_registration_core.sql` | `PROVEN_CODE` |
| Leitura técnica por record/revision | `engineering-api/.../interface/http/routes/product_registration_routes.py` rotas 13–15 | `PROVEN_CODE`, não prova listagem de produtos |
| Lock e versão sequencial no encerramento | `engineering-api/.../infrastructure/persistence/product_registration/postgres_repository.py::complete_request` | `PROVEN_CODE` |
| Revisão persistida com snapshot construído do draft | `engineering-api/.../application/use_cases/product_registration/service.py::_build_snapshot` = `dict(draft_data)`; `_complete_with_official_verification` usa esse valor | `PROVEN_CODE / EXECUTION_DRIFT` com regra funcional de snapshot oficial observado |
| Flag `FIELD` / `SUPPLIER_LINK`, OPEN/RESOLVED, GENERAL legado | `engineering-api/.../domain/product_registration/flags.py` | `PROVEN_CODE` |
| Unicidade atualmente centrada na solicitação | `flags.py::normalize_target_key` documenta `request`; `postgres_repository.find_open_flag_by_target` filtra `request_id` e `target_key` | `PROVEN_CODE / GAP` para transversalidade |
| Aplicação real de migrations, grants, RBAC, deployment, screenshots/entitlement | Requer ambiente de execução e conta autorizada | `TO_INVENTORY / TEST_NOT_RUN` |

**Limite da inspeção:** GitHub remoto permite leitura de código publicado; não estabelece git status/HEAD do worktree local, containers, migrations efetivamente aplicadas, entitlement nem teste browser. Antes de modificar código, agente executor deve revalidar HEAD/status, divergência de branches, referências canônicas e testes no SHA.

## 2. Dossiê G1: decisões que precisam de ratificação

### ADR-01 — Authority e identidade do produto acompanhado

**Recomendação para Coordination:** manter `Engineering API / PRC` como owner do acompanhamento derivado exclusivamente de workflows PRC; TOTVS/Domain API permanece owner dos dados oficiais. Reusar `records`/`revisions` existentes. Identidade: `official_source + official_product_code` **sujeita à verificação de empresa/filial**; não assumir unicidade global além do schema atual.

- **Efeito:** nenhuma escrita direta TOTVS por esta função; nenhuma auditoria automática de mudanças externas; V1 é primeira versão acompanhada, não criação ERP.
- **Decisão necessária:** `APPROVE / REVISE / REJECT`; owner do contrato; se empresa/filial exigem mudança de chave/migration.
- **Estado:** `ARCHITECTURE_DECISION_REQUIRED`.

### ADR-02 — Materialização e proveniência da versão

**Recomendação:** capturar **snapshot oficial efetivamente observado**, com campos/vínculos e cobertura `present/unknown`, fonte, evidência e schemaVersion; somente conclusão validada produz versão, inclusive UPDATE não acompanhado gera V1. Não promover `technicalDraft` a estado confirmado; separar `requestedChanges` de `observedState`.

- **Gap comprovado:** `_build_snapshot` copia `draft_data`; verificação `matched` por caminhos não equivale a snapshot completo de origem TOTVS.
- **Decisão necessária:** extensão do contrato do leitor oficial, tratamento de leitura parcial, falhas antes/depois da conclusão, política de materialização recuperável e revisões legadas imutáveis. Não fabricar backfill nem reescrever revisões.
- **Opção preferencial:** materialização oficial atômica com conclusão quando leitura suficiente ocorre antes da transação; eventual falha pós-commit requer estado de pendência/retry governado.
- **Estado:** `ARCHITECTURE_DECISION_REQUIRED`.

### ADR-03 — Flags transversais por produto/alvo

**Recomendação:** registro lógico da flag com ID estável, alvo `record_id + FIELD/path` ou `record_id + SUPPLIER_LINK(supplierCode,store,attribute)`; requestId como origem/contexto auditável. No máximo **uma OPEN por produto+alvo** por constraint concorrente. A flag não se replica em Vn e mudança de atributo não resolve flag automaticamente.

- **Gap comprovado:** CRUD/finder atual é `request_id`-centric; cross-case query por código não representa ownership de flags por record.
- **Decisão necessária:** evolução/migration da D16, vínculo pré-código oficial, preservar IDs/histórico, colisões OPEN legadas, índices, grants e compatibilidade dos endpoints request-centric.
- **Opção preferencial:** extensão backward-compatible dos registros e ledger; migrar somente dados com identidade inequívoca, exceções para revisão manual.
- **Estado:** `ARCHITECTURE_DECISION_REQUIRED`.

### ADR-04 — Corte temporal e alvo inativo

**Recomendação:** consultar separadamente estado atual e estado no instante de publicação de Vn. Eventos append-only auditáveis permitem reconstruir OPEN/RESOLVED/cancelamento/reabertura; resolução posterior não altera estado mostrado em V3. Vínculo de fornecedor removido permanece consultável historicamente como inativo.

- **Decisão necessária:** timestamp/corte canônico, ordem e tie-break de eventos, tratamento de alterações concorrentes, soft-delete, reabertura e política de mutação a partir da ficha histórica.
- **Proposta UX aprovada parcialmente:** novas flags apenas na última versão; vista histórica consulta e navega ao contexto atual antes da mutação.
- **Estado:** `ARCHITECTURE_DECISION_REQUIRED`.

### ADR-05 — Concorrência, no-op, versões e causação

**Recomendação:** preservar CAS/lock/idempotência da conclusão; não duplicar revisão por replay; não sobrescrever revisão anterior; diff entre dois snapshots é **diferença observada**, não causalidade da última PRC. Capturar `requestId` de origem de cada Vn.

- **Decisão necessária:** política de conclusão no-op (cria Vn ou não), comportamento quando `base_revision` não está preenchida e há concorrência, retentativa e materialização tardia.
- **Estado:** `ARCHITECTURE_DECISION_REQUIRED`.

### ADR-06 — Contratos de consulta e segurança

**Recomendação:** endpoints da Engineering API para lista paginada de acompanhados, DTO de snapshot/provenance, flags `current/asOfRevision`, operações de flags por produto e comparação ou leitor de snapshots para comparador puro; DTOs e erros antes do frontend.

- Leitura: `AuthZ` live por produto/solicitação conforme política Core; filtros não vazam existência de registros negados.
- Escrita: `AuthZ` live, CAS, Idempotency-Key, auditoria, 403/409/422, limits e observabilidade.
- Entitlement de conta teste não pode ser burlado.
- **Estado:** `ARCHITECTURE_DECISION_REQUIRED`.

### ADR-07 — Plugin UI acceptance e rollout

**Recomendação:** fechar PRC-UI-EXTRACT-01 com commit/sha, exports reais no remote, testes e QA autorizado antes de desenvolver U1–U3. Componentes neutros no Plugin UI; adapters de contexto/HTTP permanecem Engineering.

- **Bloqueio atual:** code remote consultado não mostra `PrcFlags.tsx` nem exports; relato local não é evidência do default branch.
- **Decisão:** definir branch/PR de integração e aceite visual compatível com entitlement real, sem declarar `PASS` indevido.
- **Estado:** `PENDING` operacional, não mudança de authority.

## 3. Matriz de readiness

| Gate | Saída obrigatória | Estado atual |
|---|---|---|
| G0.1 | Worktree HEAD/status e drift de branch | `PENDING` (requer executor) |
| G0.2 | Inventário GitHub: schema, rotas, kit, flags | `PASS` **somente inspeção de código nos caminhos citados** |
| G0.3 | Aceite Plugin UI, exports MF, consumer tests, screenshot autorizado | `PENDING` / visual `TEST_NOT_RUN` |
| G1.1 | ADR-01…ADR-06 ratificadas na Coordination | `PENDING / ARCHITECTURE_DECISION_REQUIRED` |
| G1.2 | DTOs/request-response/erros/AuthZ/idempotência versionados | `PENDING` |
| G1.3 | Plano de migration/backfill e rollback | `PENDING` |
| B1 | Snapshot oficial com proveniência e cobertura, unit/integration test | **BLOQUEADO por G1** |
| B2 | Identidade de flag por produto e histórico temporal | **BLOQUEADO por G1** |
| U1–U3 | frontend das três páginas | **BLOQUEADO por G0/G1/backend** |

## 4. Encaminhamento objetivo para Coordination

Pedir decisão registrada para ADR-01…ADR-06 com `owner, consumers, canonical source, interface, schema, AuthN/AuthZ, compatibility, audit, rollback` e classificação `READY_CONFIRMED / READY_BOUNDED / BLOCKED`. Se aprovar sem mudar boundary, os prompts de execução devem ser fatiados B1 (snapshot) → B2 (flags) → B3 (queries/diff) → U1/U2/U3. Se mudar ownership/source of truth, **não executar** e retornar à Coordination para nova decisão formal.

**Próxima ação de execução independente e limitada:** fechar PRC-UI-EXTRACT-01 no worktree do Cursor, verificar publication/exports/QA, sem desenvolver telas novas e sem alterar autorização.

Nenhuma ratificação foi assumida neste arquivo. Evidência de deploy e browser continua não executada.
