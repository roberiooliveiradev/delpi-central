# CF-CHECKLIST-LIVE-002 — Entregável 2: Contrato de Sincronização Automática de Exigências Documentais

- **Status:** `PROPOSED` (Gate 1 — R5 incorporada, aguardando revisão arquitetural final)
- **Depende de:** ADR-005 (identidade de sequência + revisões internas)
- **Base técnica:** HEAD `917e5c764c`+ (evidências revalidadas; enums e consumers conferidos no código)

---

## 1. Regras funcionais (TARGET do PO — decisões tomadas)

1. Salvar alteração válida no checklist vigente propaga **automaticamente**, sem botão de sync obrigatório por competência.
2. Fechamentos em andamento elegíveis recebem a atualização aplicável.
3. **Fechamento concluído nunca mais recebe sync** — mesmo que o estado derivado regresse a `PENDING` por reabertura de pacote, complemento ou esclarecimento. Somente exclusão definitiva + recriação governada produz uma competência nova elegível (§2).
4. Evidências nunca são apagadas (§3).
5. Preview/diagnóstico existe para governança, **não** como condição do fluxo.

## 2. Autoridade de estado e elegibilidade

### 2.1 Autoridade de estado — PROVEN

`ClosingPackageRepository.derive_closing_state(period)` (`closing_package_repository.py:1854-1944`) é a **única** autoridade de conclusão: `MONTHLY_CLOSING_COMPLETED` | `TERMINALLY_REJECTED` | `PENDING`, derivada — nunca persistida. `monthly_competence.status='OPEN'` é insuficiente (CHECK admite só `'OPEN'`, V001:76-77).

### 2.2 Conclusão histórica — gap comprovado e solução

**Fatos no HEAD:**

- O estado derivado é **momentâneo**: pode regredir a `PENDING` quando clarification reabre, `reopen_version` cria nova DRAFT de pacote (somente pré-submissão, `:864-925`) ou `create_complement` (`:926`) adiciona pacote.
- **Não existe fato persistido de "já concluído"**: nenhuma coluna marcadora em `monthly_competence` e **nenhum** evento `*_COMPLETED` no vocabulário de `closing_audit_event` (inventário completo dos `event_type` emitidos — `PACKAGE_*`, `CLARIFICATION_*`, `COMPETENCE_TERMINALLY_REJECTED`, `REJECTION_REVERTED` etc.). Reconstruir "alguma vez concluído" retroativamente dos dados atuais é frágil: a composição aplicável de pacotes/áreas na data da conclusão não é reproduzível de forma confiável.
- `monthly_competence.competence_id` é UUID novo a cada abertura — **a identidade física da competência separa "fechamento recriado" de "fechamento reaberto"**, sem flag adicional.

**Solução proposta — marcador durável write-once + estado de avaliação:**

- `monthly_competence.first_completed_at TIMESTAMPTZ NULL` + evento `MONTHLY_CLOSING_COMPLETED` em `closing_audit_event` (emitido **uma única vez** por competência — fato monotônico, nunca desfeito). Migration V031+: `ALTER TABLE ... ADD COLUMN`, nullable, reversível.
- **`monthly_competence.completion_record VARCHAR(12) NOT NULL DEFAULT 'UNEVALUATED'`** com `CHECK IN ('NEVER','COMPLETED','UNEVALUATED')` — estado de avaliação da conclusão histórica, distinto do timestamp: `COMPLETED` (pares com `first_completed_at` SET), `NEVER` (avaliado e comprovado nunca concluído), `UNEVALUATED` (legado/indeterminado).
- **Escrita:** helper `refresh_completion_marker(competence_id)` chamado dentro da transação de **toda escrita governada que pode completar o fechamento** (submissão de pacote, aceite de revisão, resolução de clarification, confirmação P3): recomputa `derive_closing_state` sob o lock da competência; se `COMPLETED` e `first_completed_at IS NULL` → seta + `completion_record='COMPLETED'` + evento. Idempotente por construção (write-once).
- **Backfill (política conservadora — §6 do mandato R4):** `NULL`/`UNEVALUATED` **nunca** é prova de "nunca concluído". Regras:
  1. Derive corrente `COMPLETED` → `COMPLETED` + `first_completed_at` (reconciliação auditada).
  2. Evidência histórica positiva de conclusão (todas as áreas requeridas com aceite humano persistido + pacotes aplicáveis SUBMITTED + P3 OFFICIAL — reconstrução parcial possível por `closing_package_version`/`evidence_decision`) → `COMPLETED` com `completion_basis='backfill'`.
  3. Evidência negativa comprovável (zero pacote SUBMITTED/aceite e nenhuma trilha de conclusão) → `NEVER`.
  4. **Qualquer outro caso → `UNEVALUATED` e o registro fica BLOQUEADO para sync** — "indeterminado" trata-se como concluído até reconciliação governada (`POST /admin/competences/{id}/completion-assessment`, `manage`, motivo obrigatório, auditada) certificar `NEVER`. Precondição, read-back do predicado e rollback (re-avaliação) documentados no gate de migração. PROD hoje tem zero competências — janela teórica.
- **Safety net:** o consumidor de sync também invoca o helper antes de avaliar elegibilidade — conclusão que escapou da escrita é capturada antes de qualquer mutação.

### 2.3 Predicado canônico de elegibilidade

```text
syncable(competence c) ⇔
      c.status = 'OPEN'
  AND c.first_completed_at IS NULL          -- nunca concluída (§2.2)
  AND c.completion_record = 'NEVER'         -- avaliação positiva obrigatória (§2.2)
  AND derive_closing_state(c.period).state = 'PENDING'
  AND business_guards_pass(c)               -- registro existe, competência não excluída, dados determinados
```

Recomputado **dentro** da transação de aplicação, sob `FOR UPDATE` na competência. A condição é uma **lista positiva**: `completion_record` precisa valer `NEVER` comprovadamente — `COMPLETED`, `UNEVALUATED`, valor desconhecido ao enum ou ausência de registro bloqueiam; não basta "diferente de `UNEVALUATED`". **Fail-closed:** leitura indeterminada, valor fora do enum, inconsistência entre `first_completed_at` e `completion_record`, falha na derivação do estado ou na consulta → `SKIPPED`/`FAILED`, nunca mutação presumida — ausência de evidência não é ausência de conclusão. Valores futuros do enum entram no predicado somente por revisão explícita deste contrato.

### 2.4 Exclusão no nível do item (item-locked)

Um item de snapshot é **não sincronizável** quando:

- `state` ∉ {`EXPECTED`, `NOT_APPLICABLE`} — `ACCEPTED` e `CANCELLED` são terminais e nunca revertidos pelo sync;
- coberto por `closing_package_version` `SUBMITTED`/`FINALIZED` vigente (lock por pacote — o pacote é snapshot próprio e não deve divergir da exigência que o embasou);
- `exceptional = TRUE` — propriedade da competência, não do catálogo.

Item locked ≠ bloqueio do run: vira `skipped` com razão tipada (§5).

### 2.5 Cenários de conclusão — resolução do predicado

| Cenário | `first_completed_at` | `completion_record` | `derive_closing_state` | Elegível? |
|---|---|---|---|---|
| `NEVER` + nunca concluído (caso normal) | NULL | `NEVER` | PENDING | ✅ |
| `NEVER` + concluído (derivação COMPLETED) | NULL | `NEVER` | MONTHLY_CLOSING_COMPLETED | ❌ — incoerência record×derivada → `FAILED` investigável, não `SKIPPED` silencioso |
| `NEVER` + rejeitado | NULL | `NEVER` | TERMINALLY_REJECTED | ❌ |
| `COMPLETED` + qualquer estado derivado | SET | `COMPLETED` | qualquer | ❌ — marcador vence |
| Concluído, depois reaberto (pacote/clarification/complemento) | **SET** | `COMPLETED` | PENDING | ❌ — marcador vence o estado derivado |
| `UNEVALUATED` + qualquer estado | NULL | `UNEVALUATED` | qualquer | ❌ — bloqueado até reconciliação governada certificar `NEVER` |
| Timestamp presente × record `NEVER` | **SET** | `NEVER` | qualquer | ❌ — inconsistente → `FAILED` |
| Timestamp ausente × record `COMPLETED` | NULL | `COMPLETED` | qualquer | ❌ — inconsistente → `FAILED` |
| `completion_record` fora do enum (corrupção/importação) | qualquer | desconhecido | qualquer | ❌ — fail-closed `FAILED` |
| Registro de competência inexistente | — | — | — | n/a — eventos órfãos ignorados |
| Excluído (competence deletada) | — | — | — | n/a — eventos órfãos ignorados |
| Recriado para o mesmo período | NULL (novo `competence_id`) | `NEVER` (nova avaliação) | PENDING | ✅ — identidade nova, fotografia do vigente |
| Conclusão simultânea ao apply | lock serializa; quem commita primeiro vence | marker set | — | ❌ `SKIPPED` |
| Falha na leitura de histórico | indeterminado | indeterminado | — | ❌ `FAILED` fail-closed |

## 3. Semântica de sincronização — matriz única

**Estados reais (inventário HEAD — sem enums inventados):**

- `competence_checklist_item.state`: `EXPECTED | ACCEPTED | NOT_APPLICABLE | CANCELLED` (V005:33-35). Não existem `EVIDENCE_ATTACHED`/`CORRECTION_*` como estados do item.
- `closing_document.state`: `ATTACHED | SUPERSEDED | CANCELLED` (V003:41).
- `evidence_decision.decision`: `ACCEPTED | REJECTED | REVERSED` (V005:72) — a "situação de validação" do item é derivada da decisão vigente, não de coluna no item.
- `item_correction.status`: `PENDING | APPROVED | REJECTED` (V005:116).
- `closing_pendency.state`: `OPEN | IN_ANALYSIS | WAITING_EXTERNAL | RESOLVED | DISMISSED` (V006:25-30) — `DISMISSED` + `dismiss_justification` (V006:42) separam «encerrada por perda de aplicabilidade» de «resolvida por execução».
- `closing_package_version.status`: `DRAFT | FINALIZED | SUBMITTED` (+ complemento encadeado).

**Dimensões separadas (regra estrutural):** "exigência ativa" (item `state`) × "histórico operacional" (documentos, decisões, correções, pendências, pacotes). A retirada só toca a primeira; o histórico é intocável.

| Operação no catálogo | Item do snapshot | Evidência/validação/pacote | Resultado |
|---|---|---|---|
| `ADD` | — | — | `INSERT` item `EXPECTED`, `exceptional=FALSE`, `source_*` da fonte |
| `UPDATE` (nome/finalidade/escopo/ordem/obrigatoriedade) | `EXPECTED`/`NOT_APPLICABLE` | qualquer | `UPDATE` dos campos; decisões/anexos intactos |
| `UPDATE` | `ACCEPTED`/`CANCELLED` | — | `skipped` `item_terminal` — registro humano não reescrito |
| `RETIRE` sem arquivo | `EXPECTED`/`NOT_APPLICABLE` | nenhuma | `CANCELLED` + `state_reason='catalog_retire'` + ref. revisão |
| `RETIRE` com arquivo não validado | `EXPECTED` | doc `ATTACHED`, sem decisão | item `CANCELLED`; documento **permanece `ATTACHED`** e navegável no histórico |
| `RETIRE` com arquivo validado | `ACCEPTED` | decisão vigente | `skipped` `item_terminal` — item já fora do conjunto de demanda e registro aprovado preservado |
| `RETIRE` com correção `PENDING` | `EXPECTED` | `item_correction` aberta **do item retirado** | item `CANCELLED`; correção **encerrada administrativamente** com motivo tipado `requirement_retired` + `closed_by`=autor da revisão — **nunca** `status='REJECTED'` (reservado à rejeição humana; contrato de encerramento em §3.2). Só a correção do item, nunca alheias |
| `RETIRE` com pendência aberta | qualquer elegível | `closing_pendency` aberta **do item retirado** | pendência `state='DISMISSED'` + `dismiss_justification='catalog_retire'` (D6 **DECIDED_BY_PO**; `DISMISSED` já existe no CHECK V006 — "encerrada por perda de aplicabilidade" ≠ "resolvida por execução"; somente pendências diretamente vinculadas via `snapshot_item_id`) |
| `RETIRE` item em pacote `SUBMITTED`/`FINALIZED` | qualquer | pacote vigente | `skipped` `item_locked_by_submitted_package` |
| `RETIRE` item `exceptional` | qualquer | — | nunca tocado (não pertence ao catálogo) |
| `REORDER` | `EXPECTED`/`NOT_APPLICABLE` | — | `UPDATE sort_order` |
| `REACTIVATE` | `CANCELLED` por `catalog_retire`, mesmo `source_template_item_id` | — | `state='EXPECTED'` (restore do mesmo item — identidade preservada) |
| qualquer | competência `first_completed_at SET` | — | run inteiro `SKIPPED` `competence_completed` |

**Upload concorrente à retirada:** upload valida item ativo; após `CANCELLED` falha `item_not_active`. Upload commitado antes = evidência preservada no item cancelado. **Validação concorrente:** decisão `ACCEPTED`/`REJECTED` commitada primeiro torna o item terminal → sync skip; item já `CANCELLED` não aceita decisão nova (guard de estado). **Regra: estado terminal do item sempre vence o sync.**

**Garantia absoluta:** o sync **jamais** DELETEia `competence_checklist_item`, `closing_document`, `document_version`, `document_file`, `document_message`, `evidence_decision`, `item_correction`, `closing_pendency`, `closing_package*`. Retirada = tombstone lógico (`CANCELLED`), coerente com V005 e a política de retenção da CF-UX-054.

### 3.1 Reativação e nova exigência — regra inversa (DECIDED_BY_PO)

Retirada e reativação são **simétricas quanto à propagação automática, nunca quanto à destruição do histórico**. Regra geral: **itens `CANCELLED` permanecem protegidos contra alterações automáticas** — `CANCELLED` é terminal e nunca revertido pelo sync **salvo a exceção estrita abaixo**.

**Origem do cancelamento — inventário (R5, PROVEN no HEAD):** `state` CHECK admite `EXPECTED|ACCEPTED|NOT_APPLICABLE|CANCELLED` (V005:33-35); `state_reason TEXT` é **livre** — hoje carrega a justificativa humana de `ITEM_CANCELLED`/`ITEM_NOT_APPLICABLE` (`_transition_item`, `closing_validation_repository.py:717-798`); **não existe** campo tipado de origem. Identificação segura da origem passa a ser **dupla e obrigatória**: (a) `state_reason` com convenção `'catalog_retire'` + referência da revisão (texto de exibição); (b) **`closing_audit_event.detail->>'reason_code' = 'catalog_retire'` no evento `ITEM_CANCELLED` do próprio item** — JSONB tipado, append-only, é a prova canônica da origem; sem esse evento tipado a exceção não se aplica.

Distinção obrigatória de operação:

- **`REACTIVATE`:** retorno do **mesmo** requisito — mesma identidade estável (`item_id`/`source_template_item_id`), nova revisão do catálogo. No snapshot: item `CANCELLED` **comprovadamente por `catalog_retire`** volta a `EXPECTED` (restore, não novo item).
- **`ADD`:** **nova** exigência com identidade própria — novo `item_id`. **Nunca** vincula evidências de outro item apenas por semelhança de nome; novo item no snapshot nasce `EXPECTED` sem herdar histórico de terceiros; `item_key` de item cancelado não é reaproveitado por ADD.

**Exceção estrita — `CANCELLED → EXPECTED` somente quando TODOS os guards passarem:**

1. competência sincronizável (predicado §2.3, incluindo `completion_record='NEVER'`);
2. cancelamento do item comprovadamente por retirada anterior do catálogo — `state_reason='catalog_retire'` **e** `ITEM_CANCELLED` com `detail.reason_code='catalog_retire'` na trilha do `snapshot_item_id`;
3. identidade do requisito inalterada — mesmo `source_template_item_id`/`item_id` e mesmo `item_key`;
4. item não coberto por pacote `SUBMITTED`/`FINALIZED` vigente;
5. nenhuma decisão operacional posterior incompatível (validação/correção/pendência nova após o cancelamento);
6. trilha do cancelamento preservada e auditável (evento de reativação §3.3);
7. operação idempotente (dedupe por `item_id`+revisão; replay = no-op);
8. OCC e locks do apply (§4.2/§5) respeitados.

Matriz de transições (anterior × origem × operação → resultado):

| Estado anterior | Origem do cancelamento | Operação | Resultado esperado |
|---|---|---|---|
| `CANCELLED` | `catalog_retire` (provado pela origem dupla — guard 2) | `REACTIVATE` | `EXPECTED` — restore do mesmo item, guards 1–8 |
| `CANCELLED` | cancelamento manual (`ITEM_CANCELLED` sem `reason_code='catalog_retire'`) | `REACTIVATE` | **não restaura** — `skipped` `cancel_not_catalog_origin` tipado; exige reversão humana governada |
| `CANCELLED` | origem desconhecida/ausente | `REACTIVATE` | **bloquear e registrar** — `skipped` `cancel_origin_unknown` + alerta; fail-closed |
| `EXPECTED` | — | `REACTIVATE` | no-op idempotente (item já ativo) |
| `ACCEPTED` | — | `REACTIVATE` | **não sobrescrever decisão** — item preservado |
| `NOT_APPLICABLE` | — | `REACTIVATE` | decisão vigente preservada; reavaliação só por operação humana |
| item inexistente | — | `ADD` | novo snapshot `EXPECTED`, identidade nova |
| item locked por pacote `SUBMITTED`/`FINALIZED` | qualquer | `REACTIVATE`/`ADD` | `skipped` `item_locked_by_submitted_package` |

Matriz de evidências na reativação (retirado por `catalog_retire` → `REACTIVATE`):

| Evidências existentes | Resultado |
|---|---|
| nenhuma | `EXPECTED` aguarda documento |
| `closing_document ATTACHED` não validado | preservado e vinculado ao item; **não satisfaz automaticamente** — exige decisão nova/verificação conforme regra vigente (validade temporal = `DECISION_REQUIRED` D8) |
| documento + decisão `ACCEPTED` | preservados; item volta como atendido **somente se** regra de negócio comprovar validade — caso contrário `EXPECTED` aguardando; decisão histórica nunca reescrita (D8) |
| correção encerrada por `requirement_retired` | **permanece encerrada** — nenhuma reabertura automática; nova correção só por condição atual |
| pendência `DISMISSED` por `catalog_retire` | **permanece encerrada** — idem |
| — `ADD` (nova identidade) | evidências de item homônimo **não** vinculadas; novo item aguarda documento |
| competência `first_completed_at`/`UNEVALUATED`/`COMPLETED` | run `SKIPPED` — histórico intocável |

**Regra de evidências anteriores (conservadora, vigente até regra específica):** preservar arquivos/versões, decisões humanas, validações e mensagens; correções e pendências históricas encerradas **ficam** encerradas; **nenhuma validação histórica é reutilizada automaticamente** para satisfazer a exigência reativada — a situação documental é reavaliada; nova pendência/correção só se a regra vigente exigir; registro histórico encerrado nunca reabre por mero reaparecimento do requisito. Se a validade temporal da evidência não puder ser comprovada, a exigência permanece `EXPECTED`.

### 3.2 Encerramento administrativo × decisão humana (R5 — semântica única)

`item_correction.status` CHECK admite `PENDING|APPROVED|REJECTED` (V005:116) e `REJECTED` só é escrito por `review_correction` (decisão humana, `CORRECTION_REJECTED`). Usá-lo para encerramento automático por retirada **confundiria** rejeição humana com encerramento administrativo em listagens (`list_item_corrections`, CLARA `_correction_state`, manifesto de exclusão). Contrato de encerramento (D6 **DECIDED_BY_PO** — o PO decidiu *que* encerra, a representação é decisão técnica):

- **Correção:** novo estado terminal **`CLOSED_REQUIREMENT_RETIRED`** (alternativa A — CHECK V031+) com `closure_reason='requirement_retired'` + `closed_by`=autor da revisão + `closed_at` + audit `CORRECTION_CLOSED_REQUIREMENT_RETIRED`. `REJECTED` permanece exclusivo de rejeição humana. Aplicado somente às correções `PENDING` do item retirado; correções `APPROVED`/`REJECTED` ficam como estão.
- **Pendência:** `state='DISMISSED'` + `dismiss_justification='catalog_retire'` + `resolution_notes` com referência da revisão — `DISMISSED` já existe no CHECK (V006) e separa "encerrada por perda de aplicabilidade" de "resolvida por execução" (`RESOLVED`); nunca apresentada como documento entregue/validado.
- **Preservação obrigatória:** identidade, origem, histórico, datas, vínculo com item, eventos anteriores, relação com documentos e motivo do encerramento — nada é apagado.

### 3.3 Evento de auditoria da reativação

Cada restore `CANCELLED→EXPECTED` por `catalog_retire` grava `closing_audit_event` com `competence_id`, `snapshot_item_id`, `source_template_item_id`, `catalog_revision`, `from_state`, `to_state`, `previous_cancel_reason_code`, `revision_actor` (autor da mudança de catálogo), `created_at` e `idempotency_key`. O evento `ITEM_CANCELLED` anterior **nunca** é apagado ou alterado.

## 4. Propagação — outbox transacional + consumidor durável canônico

### 4.1 Precedente real (PROVEN — corrige a versão anterior)

A plataforma **já possui** o padrão completo, não apenas a escrita:

- `closing_notification_event` escrita na mesma tx de negócio por `_emit_outbox` (`closing_package_repository.py:193-214`).
- Consumidor durável: `run_closing_notification_dispatch_loop` (`startup/notification_dispatch_job.py`) — asyncio poller no `lifespan` da BFF (`main.py:143-171`), flag `CF_NOTIFICATION_DISPATCH_ENABLED`, intervalo ≥15s (default 60s), `asyncio.to_thread`, exceções logadas nunca fatais. Mesmo padrão de `cipa-api` e `purchase-requests-api` (documentado no próprio módulo).
- Claim concorrente: `dispatch_pending` seleciona `EMITTED`/`FAILED` `FOR UPDATE SKIP LOCKED` (`core_notifications_gateway.py:147-160`) → `DISPATCHED|FAILED`. Sobrevive a restart (evento persiste; poller retoma), a múltiplas réplicas (SKIP LOCKED) e é observável por `delivery_state` + logs.

### 4.2 Arquitetura de sync (mesma forma canônica)

1. **Na tx da revisão de catálogo:** `INSERT checklist_sync_event` por competência elegível — `(event_id, competence_id, requested_catalog_revision, status='PENDING', dedupe_key = competence_id + revision)` — atômico com a revisão.
2. **Consumidor:** `run_checklist_sync_dispatch_loop` no lifespan, flag `CF_CHECKLIST_SYNC_DISPATCH_ENABLED`, `to_thread`, claim `FOR UPDATE SKIP LOCKED` por evento → `checklist_sync_run` por (competência, evento).
3. **Coalescência por reconciliação:** o evento é *gatilho*, não payload de verdade — ao aplicar, o consumidor recomputa o diff `snapshot × catálogo vigente atual`. Eventos empilhados/fora de ordem para a mesma competência convergem naturalmente para o estado mais recente: processar o mais antigo primeiro já aplica o catálogo corrente; os seguintes viram no-op idempotente (`diff vazio → APPLIED`, `applied_revision` registrado). Nenhuma revisão se perde — todas aparecem na trilha como eventos consumidos; o efeito líquido é o do catálogo vigente, determinístico.
4. **Apply por competência** (transação própria):
   ```
   FOR UPDATE monthly_competence (ordem: competence → items → audit/outbox)
   refresh_completion_marker()                    -- §2.2 safety net
   recompute derive_closing_state + first_completed_at
   não elegível → run SKIPPED (razão tipada) + evento DISPATCHED
   diff snapshot × catálogo aplicável
   apply ops; itens locked → skipped[]
   audit CHECKLIST_SYNCED(detail: requested_revision, applied_revision,
     plan[{op,item_key,reason}], skipped[], actor, sync_run_id)
   run → APPLIED | PARTIALLY_APPLIED | FAILED
   ```
5. **Ordenação dentro do lote:** eventos por `requested_revision ASC, competence_id` — monotonicidade da trilha preservada; coalescência garante correção mesmo com reordenação de transporte.

### 4.3 Máquina de estados do `sync_run`

| Estado | Entrada | Saída | Semântica |
|---|---|---|---|
| `REQUESTED` | INSERT na tx da revisão | claim do consumidor | trabalho persistido, não iniciado |
| `APPLYING` | claim SKIP LOCKED | commit/rollback da apply-tx | em processamento; crash → volta elegível a retry |
| `APPLIED` | diff aplicado + read-back vazio | terminal | convergência **total** confirmada |
| `PARTIALLY_APPLIED` | apply ok, `skipped[]` não-vazio **e** skips justificáveis (item-locked/terminal) | terminal-com-exclusões ou retry | convergência parcial justificada — **não** é sucesso integral |
| `FAILED` | exceção/estado indeterminado | retry automático (backoff, `max_attempts`) → terminal | convergência não confirmada |
| `SKIPPED` | competência não elegível no apply | terminal | nada a fazer (concluída/rejeitada) |

**Critério global de sucesso por revisão** (`sync_impact.status`):

- `APPLIED` — todos os runs `APPLIED` ou `SKIPPED` por regra de negócio e **zero** divergência aplicável remanescente;
- `APPLIED_WITH_EXCLUSIONS` — `PARTIALLY_APPLIED` cujo `skipped[]` é integralmente justificado (itens locked/terminais) + read-back sem divergência aplicável;
- `PENDING` — algum run em `REQUESTED`/`APPLYING`;
- `PARTIAL` — runs `FAILED` com retry pendente;
- `FAILED` — falha permanente (retry esgotado) — **nunca** reportado como sucesso.

**O Portal só declara "sincronizado" quando `APPLIED` ou `APPLIED_WITH_EXCLUSIONS`.** Evento na outbox ≠ convergência; `SKIPPED`/`FAILED`/`PARTIALLY_APPLIED` nunca contam como sucesso integral. A pós-condição é o **read-back do diff vazio** por competência — não a existência do evento nem o estado terminal por si só.

### 4.4 Falha, retry, dead-letter, observabilidade

- Retry automático com backoff do poller; esgotado `max_attempts` → `FAILED` terminal + alerta. Fila admin `GET /admin/checklist-sync-runs?status=FAILED` atua como dead-letter operacional; `POST .../{id}/retry` (`manage`, idempotente) reprocessa.
- Métricas/logs por ciclo (`cf_checklist_sync_dispatch_cycle`, mesmo padrão do notification dispatch), latência por evento, contagem `FAILED>0` → alerta.
- Restart/crash: eventos `PENDING`/`APPLYING` são recuperados pelo scan do poller — durabilidade dada pelo INSERT transacional; `APPLYING` interrompido libera o SKIP LOCKED no rollback e volta ao conjunto elegível.
- Nenhum efeito duplicado: `UNIQUE(competence_id, event_id)` no run + idempotência por diff+read-back.

## 5. Concorrência — ordem de locks verificada

Lock-order canônica proposta: `checklist_template` → `monthly_competence` (period ASC) → `competence_checklist_item` → `closing_package_version` → `closing_audit_event`/outbox.

| # | Conflito | Proteção |
|---|---|---|
| 1 | Duas edições de catálogo | lock `FOR UPDATE` no template (existente) + OCC `expected_revision` |
| 2 | Mesmo requisito incluso 2× | `UNIQUE(version_id, item_key)` + idempotency_key |
| 3 | Edição durante `open_competence` | ambos travam o template primeiro — serializado |
| 4 | Edição durante conclusão | lock na competence no apply + `refresh_completion_marker` na mesma tx — quem commita primeiro define |
| 5 | Upload × retirada | `item_not_active` pós-CANCELLED; evidência commitada permanece |
| 6 | Validação × sync | estado terminal do item vence (§3) |
| 7 | Submissão × sync | item-locked `skipped`; pacote é snapshot próprio |
| 8 | Dois syncs simultâneos | SKIP LOCKED + `UNIQUE(competence_id,event_id)` + coalescência |
| 9 | Retry pós-timeout | idempotência por diff/read-back — replay não reaplica |
| 10 | Falha pós-mutação parcial | impossível — tx por competência atômica |

**Drift a verificar no Gate 2:** a ordem de locks acima deve ser conferida contra os producers existentes (submissão/validação/upload tomam competence→items→package hoje — compatível; qualquer producer que trave package antes de competence exigiria ajuste).

## 6. Contratos

### 6.1 Reutilizados sem alteração
`derive_closing_state`, `open_competence` (cópia vigente), `closing_audit_event`, poller/outbox/claim SKIP LOCKED (forma canônica), OCC/idempotency-key, `access`/`manage`.

### 6.2 Novos
| Contrato | Descrição |
|---|---|
| `checklist_sync_event` (tabela/outbox) | gatilho por competência — INSERT na tx da revisão |
| `checklist_sync_run` (tabela) | estado por (competência,evento): máquina §4.3 + `applied_plan` + `skipped[]` + `closing_state_at_apply` |
| `first_completed_at` + evento `MONTHLY_CLOSING_COMPLETED` | marcador durável §2.2 — migration |
| `GET /closing/competences/{p}/checklist-sync-status` | último run: estado, revisão, plano, skipped |
| `GET /admin/checklist-catalog/sync-impact/preview` | preview governado (diagnóstico, não condição) |
| `GET /admin/checklist-sync-runs?status=FAILED` + `POST .../{id}/retry` | fila admin + reprocessamento governado |
| Eventos audit | `CHECKLIST_SYNCED`, `CHECKLIST_SYNC_SKIPPED`, `CHECKLIST_SYNC_FAILED`, `MONTHLY_CLOSING_COMPLETED` |
| Erros tipados | `competence_not_syncable`, `competence_completed`, `item_locked_by_submitted_package`, `item_not_active`, `sync_in_progress`, `catalog_revision_stale`, `idempotency_conflict` |
| CLARA | **nenhuma capability nova** — mesmos casos de uso; leitura via `read`/`knowledge` |

## 7. Histórico na interface

- Itens `CANCELLED` por `catalog_retire` aparecem como cards de histórico ("Exigência retirada pelo checklist em {data}") colapsáveis — documentos/decisões/mensagens permanecem navegáveis no detalhe.
- Correções encerradas por retirada mostram resolução `requirement_retired` e estado de encerramento administrativo — **nunca** exibidas como "rejeitadas"; pendências aparecem `DISMISSED`/`catalog_retire` — nunca órfãs silenciosas nem apresentadas como resolvidas por execução.
- Badge "sincronizando/sincronizado/falhou" a partir de `checklist-sync-status` (doc 175).

## 8. Segurança

- Sync = efeito sistêmico da operação governada de catálogo (`manage`); ator da trilha = autor da revisão ou `system`.
- Leitura de status `access`; retry admin `manage`. Nenhuma bypass de `derive_closing_state`/`first_completed_at`.

## 9. Critérios de aceite

- AC-S1 `PENDING`+nunca concluída → item sincronizado, `CHECKLIST_SYNCED`, read-back diff vazio.
- AC-S2 `first_completed_at` SET (mesmo `PENDING` regredido) → `SKIPPED` `competence_completed`, zero mutação.
- AC-S3 retirada com evidência → `CANCELLED` + docs/decisões/correções/pendências preservados ou encerrados por contrato, navegáveis.
- AC-S4 pacote SUBMITTED → item `skipped` tipado; pacote íntegro.
- AC-S5 crash entre commit e consumo → evento `PENDING` processado na retomada.
- AC-S6 replay/retry → sem efeito duplicado.
- AC-S7 sucesso declarado **somente** `APPLIED`/`APPLIED_WITH_EXCLUSIONS` + diff vazio.
- AC-S8 eventos fora de ordem → convergência ao catálogo vigente, trilha completa.
- AC-S9 correção/pendência aberta em item retirado → encerramento administrativo tipado (`CLOSED_REQUIREMENT_RETIRED`/`DISMISSED`+`catalog_retire`), nunca `REJECTED` humano, nunca órfã.
- AC-S10 elegibilidade: `OPEN ∧ completion_record='NEVER' ∧ first_completed_at IS NULL ∧ PENDING` → sincroniza; `COMPLETED`/`UNEVALUATED`/desconhecido/ausente → bloqueado fail-closed.
- AC-S11 reativação: `CANCELLED` por `catalog_retire` provado (state_reason + `ITEM_CANCELLED` com `reason_code` tipado) + guards → `EXPECTED` restore; cancelamento manual/desconhecido → `skipped` tipado, zero mutação.
- AC-S12 evidência histórica em item reativado → visível e preservada, não satisfaz automaticamente a exigência (sem prova de validade → permanece `EXPECTED`).

## 9.1 Matriz de testes contratuais (mapeada — **TEST_NOT_RUN**, nenhum teste de runtime neste gate)

Formato: `ID | Pré-condição | Operação | Resultado esperado | Contrato | Teste | Classificação`. Todos os testes são **novos** (Gate 2) e **TEST_NOT_RUN** — este gate é documental.

### T1 — Elegibilidade

| ID | Pré-condição | Operação | Resultado esperado | Contrato | Teste | Classificação |
|---|---|---|---|---|---|---|
| T1-1 | `OPEN`, `first_completed_at` NULL, `NEVER`, derivada `PENDING` | apply sync | itens aplicados, `CHECKLIST_SYNCED`, `APPLIED` com read-back diff vazio | §2.3 | novo | TEST_NOT_RUN |
| T1-2 | `COMPLETED` + `PENDING` regredido (reaberto) | apply sync | `SKIPPED` `competence_completed`, zero mutação | §2.3/§2.5 | novo | TEST_NOT_RUN |
| T1-3 | `UNEVALUATED` + qualquer derivada | apply sync | `SKIPPED`/`FAILED` tipado, zero mutação | §2.3 | novo | TEST_NOT_RUN |
| T1-4 | `first_completed_at` SET × `completion_record='NEVER'` | apply sync | `FAILED` inconsistente, zero mutação | §2.5 | novo | TEST_NOT_RUN |
| T1-5 | `first_completed_at` NULL × `completion_record='COMPLETED'` | apply sync | `FAILED`/`SKIPPED`, zero mutação | §2.5 | novo | TEST_NOT_RUN |
| T1-6 | `completion_record` fora do enum (corrupção) | apply sync | `FAILED` fail-closed | §2.5 | novo | TEST_NOT_RUN |
| T1-7 | `derive_closing_state`=`COMPLETED`/`TERMINALLY_REJECTED` | apply sync | `SKIPPED`, zero mutação | §2.5 | novo | TEST_NOT_RUN |
| T1-8 | erro de consulta ao marcador/derivada | apply sync | `FAILED`, retry, zero mutação presumida | §4.4 | novo | TEST_NOT_RUN |
| T1-9 | competência excluída e recriada (novo `competence_id`) | apply sync | avaliação nova, identidade nova, fotografia do vigente | §2.2/§2.5 | novo | TEST_NOT_RUN |

### T2 — Reativação

| ID | Pré-condição | Operação | Resultado esperado | Contrato | Teste | Classificação |
|---|---|---|---|---|---|---|
| T2-1 | `CANCELLED` + `state_reason='catalog_retire'` + `ITEM_CANCELLED` com `reason_code='catalog_retire'` | `REACTIVATE` | restore `EXPECTED`, mesmo `snapshot_item_id`, audit de reativação | §3.1/§3.3 | novo | TEST_NOT_RUN |
| T2-2 | `CANCELLED` manual (sem `reason_code`) | `REACTIVATE` | `skipped` `cancel_not_catalog_origin`, zero mutação | §3.1 | novo | TEST_NOT_RUN |
| T2-3 | `CANCELLED` com origem ausente/desconhecida | `REACTIVATE` | `skipped` `cancel_origin_unknown` + alerta, zero mutação | §3.1 | novo | TEST_NOT_RUN |
| T2-4 | `EXPECTED` | `REACTIVATE` | no-op idempotente | §3.1 | novo | TEST_NOT_RUN |
| T2-5 | `ACCEPTED` / `NOT_APPLICABLE` | `REACTIVATE` | decisão preservada, sem sobrescrita | §3.1 | novo | TEST_NOT_RUN |
| T2-6 | item inexistente no snapshot | `ADD` | novo item `EXPECTED`, identidade nova, sem herança | §3.1 | novo | TEST_NOT_RUN |
| T2-7 | `ADD` com `item_key` homônimo de item cancelado | `ADD` | nova identidade, evidências não vinculadas | §3.1 | novo | TEST_NOT_RUN |
| T2-8 | item reativado com evidência `ATTACHED` | `REACTIVATE` | evidência preservada e visível; item permanece `EXPECTED` sem validade automática | §3.1 | novo | TEST_NOT_RUN |
| T2-9 | correção/pendência encerrada por retirada | `REACTIVATE` | permanece encerrada — nunca reabre | §3.1 | novo | TEST_NOT_RUN |
| T2-10 | pacote `SUBMITTED` cobrindo o item | `REACTIVATE`/`ADD` | `skipped` `item_locked_by_submitted_package` | §3.1 | novo | TEST_NOT_RUN |
| T2-11 | replay do mesmo `REACTIVATE` (idempotency key) | `REACTIVATE` | no-op, sem efeito duplicado | §3.1/§4 | novo | TEST_NOT_RUN |
| T2-12 | reativação concorrente a upload | `REACTIVATE` × upload | lock serializa; um vence, outro reavalia — sem estado intermediário | §5 | novo | TEST_NOT_RUN |

### T3 — Correções

| ID | Pré-condição | Operação | Resultado esperado | Contrato | Teste | Classificação |
|---|---|---|---|---|---|---|
| T3-1 | correção `PENDING` do item | `RETIRE` | `CLOSED_REQUIREMENT_RETIRED`+`closure_reason`+`closed_by`+audit | §3.2 | novo | TEST_NOT_RUN |
| T3-2 | correção `APPROVED`/`REJECTED` do item | `RETIRE` | inalterada | §3.2 | novo | TEST_NOT_RUN |
| T3-3 | correção `PENDING` de **outro** item | `RETIRE` | inalterada — nunca alheia | §3.2 | novo | TEST_NOT_RUN |
| T3-4 | `list_item_corrections`/CLARA `_correction_state` | consulta pós-retirada | encerramento administrativo distinguível de `REJECTED` | §3.2 | novo | TEST_NOT_RUN |
| T3-5 | retirada concorrente a decisão humana | `RETIRE` × review | lock serializa, sem estado intermediário, audit completa | §5 | novo | TEST_NOT_RUN |
| T3-6 | replay da retirada | `RETIRE` | idempotente, sem duplo encerramento | §4 | novo | TEST_NOT_RUN |

### T4 — Pendências

| ID | Pré-condição | Operação | Resultado esperado | Contrato | Teste | Classificação |
|---|---|---|---|---|---|---|
| T4-1 | pendência `OPEN`/`IN_ANALYSIS`/`WAITING_EXTERNAL` do item | `RETIRE` | `DISMISSED`+`dismiss_justification='catalog_retire'`+nota da revisão | §3.2 | novo | TEST_NOT_RUN |
| T4-2 | pendência `RESOLVED`/`DISMISSED` | `RETIRE` | inalterada | §3.2 | novo | TEST_NOT_RUN |
| T4-3 | pendência vinculada a outro item | `RETIRE` | inalterada | §3.2 | novo | TEST_NOT_RUN |
| T4-4 | pendência `DISMISSED`/`catalog_retire` | `REACTIVATE` | permanece encerrada | §3.1 | novo | TEST_NOT_RUN |
| T4-5 | cockpit/listagem pós-retirada | consulta | pendência exibida como encerrada por retirada, **nunca** como resolvida por execução | §3.2/doc 175 | novo | TEST_NOT_RUN |
| T4-6 | replay da retirada | `RETIRE` | idempotente | §4 | novo | TEST_NOT_RUN |

## 10. DECISION_REQUIRED remanescentes

1. **D8 — Validade temporal da evidência na reativação:** evidência anexada/aceita antes da retirada conta para a exigência reativada? Exige definição de "validade" (data, versão do requisito, conteúdo) ainda inexistente — sem decisão, o default conservador é: evidência permanece visível no histórico do item, mas a exigência reativada volta `EXPECTED` aguardando reavaliação humana ou nova decisão governada.
2. **`first_completed_at`/`completion_record` — momento de escrita:** em toda escrita completadora (proposto — mais forte) vs apenas no consumidor + reconciliador (menos invasivo; recomendado o proposto).
3. **Status de encerramento de correção — RESOLVIDO (R5):** `REJECTED` fica exclusivo de rejeição humana; encerramento por retirada usa estado tipado novo `CLOSED_REQUIREMENT_RETIRED` + `closure_reason` (§3.2) — migration de CHECK no Gate 2. Pendência usa `DISMISSED`+`catalog_retire` (valor já existente, sem migration).
