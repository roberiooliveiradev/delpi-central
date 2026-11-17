# CF-CHECKLIST-LIVE-002 — Entregável 2: Contrato de Sincronização Automática de Exigências Documentais

- **Status:** `PROPOSED` (Gate 1 — R3, aguardando revisão arquitetural final)
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
  AND c.completion_record != 'UNEVALUATED'  -- legado indeterminado bloqueia
  AND derive_closing_state(c.period).state = 'PENDING'
```

Recomputado **dentro** da transação de aplicação, sob `FOR UPDATE` na competência. **Fail-closed:** leitura indeterminada ou `UNEVALUATED` → `SKIPPED`/`FAILED`, nunca mutação presumida — ausência de evidência não é ausência de conclusão.

### 2.4 Exclusão no nível do item (item-locked)

Um item de snapshot é **não sincronizável** quando:

- `state` ∉ {`EXPECTED`, `NOT_APPLICABLE`} — `ACCEPTED` e `CANCELLED` são terminais e nunca revertidos pelo sync;
- coberto por `closing_package_version` `SUBMITTED`/`FINALIZED` vigente (lock por pacote — o pacote é snapshot próprio e não deve divergir da exigência que o embasou);
- `exceptional = TRUE` — propriedade da competência, não do catálogo.

Item locked ≠ bloqueio do run: vira `skipped` com razão tipada (§5).

### 2.5 Cenários de conclusão — resolução do predicado

| Cenário | `first_completed_at` | derive atual | Sync? |
|---|---|---|---|
| Nunca concluído | NULL | PENDING | ✅ |
| Concluído e estável | SET | COMPLETED | ❌ |
| Concluído, depois reaberto (pacote/clarification/complemento) | **SET** | PENDING | ❌ — marcador vence o estado derivado |
| Rejeitado terminalmente | NULL/SET | TERMINALLY_REJECTED | ❌ |
| Legado sem avaliação (`UNEVALUATED`) | NULL | qualquer | ❌ — bloqueado até reconciliação governada |
| Excluído (competence deletada) | — | — | n/a — eventos órfãos ignorados |
| Recriado para o mesmo período | NULL (novo `competence_id`) | PENDING | ✅ — identidade nova, fotografia do vigente |
| Conclusão simultânea ao apply | lock serializa; quem commita primeiro vence | — | marker set → `SKIPPED` |
| Falha na leitura de histórico | indeterminado | — | ❌ fail-closed |

## 3. Semântica de sincronização — matriz única

**Estados reais (inventário HEAD — sem enums inventados):**

- `competence_checklist_item.state`: `EXPECTED | ACCEPTED | NOT_APPLICABLE | CANCELLED` (V005:33-35). Não existem `EVIDENCE_ATTACHED`/`CORRECTION_*` como estados do item.
- `closing_document.state`: `ATTACHED | SUPERSEDED | CANCELLED` (V003:41).
- `evidence_decision.decision`: `ACCEPTED | REJECTED | REVERSED` (V005:72) — a "situação de validação" do item é derivada da decisão vigente, não de coluna no item.
- `item_correction.status`: `PENDING | APPROVED | REJECTED` (V005:116).
- `closing_pendency.state`: `OPEN | IN_ANALYSIS | WAITING_EXTERNAL | RESOLVED` (V006:25).
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
| `RETIRE` com correção `PENDING` | `EXPECTED` | `item_correction` aberta **do item retirado** | item `CANCELLED`; correção encerrada `status='REJECTED'` + `review_reason='requirement_retired'` + `reviewed_by`=autor da revisão (D6 **DECIDED_BY_PO**; campos livres — sem migration de enum; só a correção do item, nunca alheias) |
| `RETIRE` com pendência aberta | qualquer elegível | `closing_pendency` aberta **do item retirado** | pendência `state='RESOLVED'` + `resolution_notes`/`classification_reason='catalog_retire'` (D6 **DECIDED_BY_PO**; somente pendências diretamente vinculadas via `snapshot_item_id`) |
| `RETIRE` item em pacote `SUBMITTED`/`FINALIZED` | qualquer | pacote vigente | `skipped` `item_locked_by_submitted_package` |
| `RETIRE` item `exceptional` | qualquer | — | nunca tocado (não pertence ao catálogo) |
| `REORDER` | `EXPECTED`/`NOT_APPLICABLE` | — | `UPDATE sort_order` |
| `REACTIVATE` | `CANCELLED` por `catalog_retire`, mesmo `source_template_item_id` | — | `state='EXPECTED'` (restore do mesmo item — identidade preservada) |
| qualquer | competência `first_completed_at SET` | — | run inteiro `SKIPPED` `competence_completed` |

**Upload concorrente à retirada:** upload valida item ativo; após `CANCELLED` falha `item_not_active`. Upload commitado antes = evidência preservada no item cancelado. **Validação concorrente:** decisão `ACCEPTED`/`REJECTED` commitada primeiro torna o item terminal → sync skip; item já `CANCELLED` não aceita decisão nova (guard de estado). **Regra: estado terminal do item sempre vence o sync.**

**Garantia absoluta:** o sync **jamais** DELETEia `competence_checklist_item`, `closing_document`, `document_version`, `document_file`, `document_message`, `evidence_decision`, `item_correction`, `closing_pendency`, `closing_package*`. Retirada = tombstone lógico (`CANCELLED`), coerente com V005 e a política de retenção da CF-UX-054.

### 3.1 Reativação e nova exigência — regra inversa (DECIDED_BY_PO)

Retirada e reativação são **simétricas quanto à propagação automática, nunca quanto à destruição do histórico**. Distinção obrigatória:

- **`REACTIVATE`:** retorno do **mesmo** requisito — mesma identidade estável (`item_id`/`source_template_item_id`), semanticamente equivalente. No snapshot: item `CANCELLED` por `catalog_retire` volta a `EXPECTED` (restore, não novo item).
- **`ADD`:** **nova** exigência com identidade própria — novo `item_id`. **Nunca** vincula evidências de outro item apenas por semelhança de nome; novo item no snapshot nasce `EXPECTED` sem herdar histórico de terceiros.

Matriz obrigatória (`estado anterior → operação → exigência → evidências → validação → pendências → resultado`):

| Anterior | Operação | Exigência ativa | Evidências existentes | Resultado |
|---|---|---|---|---|
| retirado sem evidência | REACTIVATE | `EXPECTED` (restore) | nenhuma | aguarda documento |
| retirado, evidência anexada não validada | REACTIVATE | `EXPECTED` | `closing_document ATTACHED` preservado | **reavaliação governada**: evidência pré-existente permanece vinculada ao item (mesmo `snapshot_item_id`); validação exige decisão nova/verificação conforme regra vigente — a "validade da evidência" reaprovada automaticamente é `DECISION_REQUIRED` (D8) se depender de conceito de validade temporal ainda inexistente |
| retirado, evidência ACCEPTED | REACTIVATE | `EXPECTED`→reavaliado | documento + decisão `ACCEPTED` preservados | item volta como já atendido **somente se** a regra de negócio comprovar equivalência — caso contrário `EXPECTED` aguardando; decisão histórica nunca reescrita (D8 se sem definição de validade) |
| retirado com correção encerrada por `requirement_retired` | REACTIVATE | `EXPECTED` | correção **permanece encerrada** | nenhuma reabertura automática; nova correção só se houver condição atual que a exija |
| retirado com pendência encerrada por `catalog_retire` | REACTIVATE | `EXPECTED` | pendência **permanece encerrada** | idem |
| — | ADD (nova identidade) | `EXPECTED` novo item | evidências de item homônimo **não** vinculadas | novo item aguarda documento; sem apropriação de histórico |
| item locked por pacote SUBMITTED | REACTIVATE/ADD | — | — | `skipped` `item_locked_by_submitted_package` |
| competência `first_completed_at`/`UNEVALUATED` | qualquer | — | — | run `SKIPPED` — histórico intocável |

Regras transversais: reativação **reavalia o estado atual** (não o do momento da retirada); correções/pendências históricas encerradas **ficam** encerradas; nenhum histórico apagado ou reescrito; o card reaparece na lista ativa (doc 175).

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
- Correções/pendências encerradas por retirada mostram resolução `requirement_retired` — nunca órfãs silenciosas.
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
- AC-S9 correção/pendência aberta em item retirado → encerrada com `resolution` tipada, nunca órfã.

## 10. DECISION_REQUIRED remanescentes

1. **D8 — Validade temporal da evidência na reativação:** evidência anexada/aceita antes da retirada conta para a exigência reativada? Exige definição de "validade" (data, versão do requisito, conteúdo) ainda inexistente — sem decisão, o default conservador é: evidência permanece visível no histórico do item, mas a exigência reativada volta `EXPECTED` aguardando reavaliação humana ou nova decisão governada.
2. **`first_completed_at`/`completion_record` — momento de escrita:** em toda escrita completadora (proposto — mais forte) vs apenas no consumidor + reconciliador (menos invasivo; recomendado o proposto).
3. **Status de encerramento de correção:** `REJECTED`+`review_reason` (sem migration — proposto) vs novo valor `CANCELLED` no CHECK de `item_correction.status` (semântica mais precisa, exige migration de constraint). Decisão técnica fina no Gate 2.
