# CF-CHECKLIST-LIVE-002 — Entregável 2: Contrato de Sincronização Automática de Exigências Documentais

- **Status:** `PROPOSED` (Gate 1, aguardando revisão arquitetural)
- **Depende de:** ADR-005 (identidade de sequência + revisões internas)
- **Base técnica:** HEAD `ef02ef508e`; inventário runtime `CF-CHECKLIST-LIVE-001`

---

## 1. Regras funcionais (TARGET do PO — decisões tomadas)

1. Salvar alteração válida no checklist vigente propaga **automaticamente**, sem botão de sync obrigatório por competência.
2. Fechamentos em andamento (`PENDING` canônico) recebem a atualização aplicável.
3. Fechamentos concluídos e terminalmente rejeitados: **nunca** alterados.
4. Competência excluída e reaberta recebe o catálogo vigente na nova abertura (já PROVEN — `open_competence`).
5. Preview/diagnóstico pode existir para governança, **não** como condição do fluxo normal.

## 2. Predicado canônico de elegibilidade

### 2.1 Autoridade de estado — PROVEN

`ClosingPackageRepository.derive_closing_state(period)` (`closing_package_repository.py:1854-1944`) é a **única** autoridade de conclusão:

- `MONTHLY_CLOSING_COMPLETED` — todos os pacotes aplicáveis SUBMITTED + aceite humano por área requerida + zero clarification OPEN + zero rejeição terminal ativa + P3 proveniência OFFICIAL; vazio nunca conclui (D-FINAL-02).
- `TERMINALLY_REJECTED` — rejeição terminal ativa.
- `PENDING` — demais casos.

`monthly_competence.status='OPEN'` é **insuficiente** por construção (CHECK admite só 'OPEN' — V001:76-77): toda competência, inclusive concluída, é OPEN.

### 2.2 Predicado

```text
syncable(competence c) ⇔
      c.status = 'OPEN'
  AND derive_closing_state(c.period).state = 'PENDING'
```

Recomputado **dentro** da transação de aplicação (nunca confiar em valor pré-lido — §4.5).

### 2.3 Exclusão no nível do item (item-locked)

Um item de snapshot é **não sincronizável** quando:

- `state` ∉ {`EXPECTED`, `NOT_APPLICABLE`} — itens `ACCEPTED`/`CANCELLED`/em `CORRECTION`/`CORRECTED` não são tocados pelo sync (ver §3);
- o item está coberto por `closing_package_version` em status `SUBMITTED`/`FINALIZED` vigente (lock por pacote — análogo a `item_locked_by_submitted_package` usado em operações de documento);
- `exceptional = TRUE` — itens excepcionais criados manualmente são propriedade da competência, não do catálogo.

Item locked ≠ bloqueio do sync: o sync aplica o que pode e reporta o item como `skipped` com razão tipada (sem fail-hard por um item).

### 2.4 Conclusão histórica e reabertura

O estado derivado é **momentâneo**: `derive_closing_state` computa o presente, e um fechamento concluído pode regressar a `PENDING` — `reopen_version` e `create_complement` existem (`closing_package_repository.py:864`, `:926`) e uma clarification pode ser reaberta. Não assumir que "PENDING agora" prova "nunca concluído".

Tratamento proposto:

- **Fechamento concluído e permanecendo concluído:** `SKIPPED` — o predicado resolve sozinho.
- **Fechamento concluído e posteriormente reaberto** (reopen/complement legítimos): volta a `PENDING` e torna-se elegível **apenas para itens não cobertos pelas versões de pacote SUBMITTED existentes**. O item-lock de §2.3 é o mecanismo que congela o que já foi empacotado — a sincronização não pode alterar retroativamente o conteúdo já submetido e aceito.
- **Eventos irreversíveis** (rejeição terminal, pacote aceito): nunca revertidos pelo sync — item `ACCEPTED`/`CANCELLED` por decisão humana permanece fora do conjunto mutável independentemente do estado do fechamento.
- Dúvida auditável: cada `sync_run` registra `closing_state_at_apply` e `skipped[]` com razão — o histórico do fechamento fica reconstruível.

## 3. Semântica de sincronização (matriz definitiva)

Diff `snapshot(competência) × catálogo aplicável(period)` onde catálogo aplicável = itens vigentes da versão vencedora, filtrados por `applicability`/`branch_scope` do item e filial/escopo da competência.

| Alteração no catálogo | Efeito no fechamento `PENDING` | Fechamento concluído/rejeitado |
|---|---|---|
| **Inclusão** (`ADD`) | `INSERT` novo `competence_checklist_item` — `state='EXPECTED'`, `exceptional=FALSE`, `source_version_id`/`source_template_item_id` da fonte, `origin='CATALOG'` | nenhum |
| **Edição de nome/finalidade/escopo/ordem** (`UPDATE`) | `UPDATE` campos descritivos **apenas** em itens ainda `EXPECTED`/`NOT_APPLICABLE` sem evidência vinculada | nenhum |
| **Obrigatoriedade** (`required`/`applicability`) | reavaliação: item que deixa de ser aplicável → `CANCELLED` (`state_reason='catalog_retire'`); item que passa a ser aplicável → tratado como inclusão | nenhum |
| **Reordenação** | `UPDATE sort_order` | nenhum |
| **Retirada sem evidência** (`RETIRE` no catálogo) | `state='CANCELLED'` + `state_reason='catalog_retire'` + referência à revisão do catálogo — **nunca DELETE** | nenhum |
| **Retirada com evidência** | `state='CANCELLED'` (mesmo tratamento); `closing_document`, `document_version`, `document_file`, `document_message`, `evidence_decision`, `item_correction`, `closing_pendency` **preservados integralmente** — a exigência sai do conjunto ativo, o conteúdo permanece consultável no histórico | nenhum |
| **Retirada com validação (ACCEPTED)** | item já terminal → `skipped` com razão `item_terminal` (a exigência deixa de ser exigida no catálogo, mas o registro aprovado não é alterado — decisão humana preservada) | nenhum |
| **Retirada com ajuste em aberto** | `item_correction`/pendência aberta referente ao item é **encerrada por retirada** (`resolution='catalog_retire'`, evento auditado) — nunca deixada órfã pendente; o item vai a `CANCELLED` | nenhum |
| **Retirada com pacote submetido** | item coberto por `closing_package_version SUBMITTED` → `skipped` com `item_locked_by_submitted_package` — o pacote permanece íntegro; a retirada vale para períodos/competências futuras | nenhum |
| **Item excepcional** | `exceptional=TRUE` nunca é tocado pelo sync (é da competência, não do catálogo) | idem |
| **Reativação** (`REACTIVATE`) | item `CANCELLED` por `catalog_retire` com mesmo `source_template_item_id` → `EXPECTED` (restore, não novo item); caso contrário = inclusão | nenhum |
| **Competência reaberta/recriada** | reaberta: avaliada por §2.4 (items locked permanecem); excluída e recriada: recebe o catálogo vigente na nova abertura (cópia integral — caminho já existente) | nenhum |

**Estados de item vigentes (PROVEN, V005+):** `EXPECTED`, `EVIDENCE_ATTACHED` (se aplicável), `ACCEPTED`, `NOT_APPLICABLE`, `CANCELLED`, `CORRECTION_REQUESTED`/`CORRECTED`. Regra: sync **nunca** modifica item fora de {`EXPECTED`, `NOT_APPLICABLE`, `EVIDENCE_ATTACHED`} — itens com decisão (`ACCEPTED`) ou em correção ficam congelados e reportados `skipped`.

**Preservação de evidência — garantia absoluta:** o sync **jamais** executa DELETE em `competence_checklist_item`, `closing_document`, `document_version`, `document_file`, `document_message`, `evidence_decision`, `item_correction`, `closing_pendency`, `closing_package*`. Retirada é sempre tombstone lógico (`CANCELLED`), consistente com "CANCELLED != DELETED" de V005 e com a política de retenção da CF-UX-054.

## 4. Mecanismo de propagação — análise e decisão proposta

### 4.1 Opções

| Critério | A. Transacional síncrono (mesma tx do catálogo) | B. Outbox transacional + consumidor idempotente | C. Job de reconciliação periódico |
|---|---|---|---|
| Garantia de persistência | total | total (INSERT na mesma tx) | risco (janela sem registro) |
| Atomicidade catálogo↔sync | total | eventual por competência | eventual global |
| Falha parcial | impossível por construção | isolada por competência, estado visível | difusa |
| Escalabilidade | linear ao nº de competências elegíveis — **N atual é ~O(1–2)**; degrada se competências concorrentes crescerem | constante no commit; trabalho deslocado | deslocado, mas latência alta |
| Locks | lock de template → N competências (ordenação por `period`); risco de deadlock com submissões simultâneas | lock por competência no consumidor | idem B |
| Observabilidade | resultado imediato, sem estado persistido | `sync_run` com estados — auditável | baixa |
| Retry | reenvio da operação toda | retry por competência | retry por lote |
| UX | "salvo e sincronizado" | "salvo; sincronizando N fechamentos" → convergência | latência inaceitável p/ PO |
| Precedente na plataforma | parcial | **`closing_notification_event`/`_emit_outbox` (`closing_package_repository.py:193-214`) — padrão já usado** | nenhum |

### 4.2 Decisão proposta: **B — outbox transacional, com fast-path inline**

O padrão de outbox já existe no domínio. Proposta:

1. **Na mesma transação** da revisão de catálogo (ADR-005 §5.3) e do `open_competence` legado quando aplicável: `INSERT` em `checklist_sync_event` (outbox) por competência elegível — `(sync_event_id, catalog_revision_seq, competence_id, status='PENDING', idempotency_key = hash(revision, competence))`.
2. **Consumidor**: mesmo processo (dispatch pós-commit imediato — latência de segundos, sem worker novo) com fila persistente como fonte de verdade. Cada evento processado em **transação própria por competência**.
3. **Estado por competência** (`checklist_sync_run`):
   `REQUESTED → APPLYING → APPLIED | PARTIALLY_APPLIED | FAILED | SKIPPED` (+ `retry_count`, `last_error`, `applied_plan`).
4. Contrato de visibilidade: resposta da revisão do catálogo inclui `sync_impact: {requested: N, status_url}` — o Portal pode exibir "sincronizando" enquanto houver runs não terminais. **Nunca** apresentar sucesso global com runs pendentes sem marcá-los (§12 do mandato).

**Fallback aceitável (registrar no ADR):** como N elegível atual é O(1–2) (uma competência por mês, poucos meses abertos), a opção A seria correta hoje — mas introduz acoplamento de latência e locks agregados; o outbox preserva a arquitetura quando N crescer e dá trilha de sincronização nativa. Se o GPT Arquiteto preferir simplicidade máxima no Gate 2, A é válido **apenas** com a trilha `checklist_sync_run` mantida (preenchida na mesma tx).

### 4.3 Transação por competência (algoritmo do consumidor)

```
FOR UPDATE competence (ordenação de lock: competence → items → audit/outbox)
recompute derive_closing_state(period)          # fail-closed se != PENDING → SKIPPED
read snapshot items + catálogo aplicável
compute diff (ops por item: insert/update/cancel/skip+reason)
para item locked-by-submitted-package → skipped, nunca mutado
apply ops; bump nada em competence (revision é do catálogo, não da competência)
INSERT closing_audit_event CHECKLIST_SYNCED
   (detail: catalog_revision, plan[{op,item_key,reason}], skipped[...],
    actor=system ou autor da revisão, sync_run_id)
UPDATE checklist_sync_run → APPLIED | PARTIALLY_APPLIED
```

Idempotência: `idempotency_key` por (revisão, competência) + replays retornam o mesmo `sync_run`. Falha: `FAILED` + `last_error`; reprocessamento administrativo `POST .../sync-runs/{id}/retry` (`manage`, idempotente, só de `FAILED`/`PARTIALLY_APPLIED`).

### 4.3b Requisitos operacionais do consumidor

- **Retry**: automático com backoff (política padrão do domínio) até `max_attempts`; esgotado → `FAILED` terminal + alerta. Não há DLQ separada: `FAILED` **é** o estado terminal visível (N é O(competências)); a fila admin `GET /admin/checklist-sync-runs?status=FAILED` funciona como dead-letter operacional com retry governado.
- **Métricas/alertas**: `sync_runs` por status, latência de processamento por evento, contagem `FAILED` > 0 → alerta operacional (reuso do padrão de observabilidade da plataforma).
- **Reconciliação após indisponibilidade**: ao subir, o consumidor processa `sync_event` em `PENDING`/`APPLYING` (recover por scan do outbox — mesmo padrão de retomada do notification outbox); nenhum evento se perde porque o INSERT é transacional com a revisão.
- **Quando o Portal pode informar sucesso**: a resposta da revisão de catálogo retorna `sync_impact { requested: N, runs_url }` imediatamente após o commit — "salvo" é verdadeiro nesse instante. "Sincronizado" só pode ser declarado quando **todos** os `sync_run` daquela revisão estiverem em estado terminal (`APPLIED`/`PARTIALLY_APPLIED`/`SKIPPED`/`FAILED`); enquanto houver `REQUESTED`/`APPLYING`, a UI mostra "sincronizando". `FAILED`/`PARTIALLY_APPLIED` exibem estado distinto, nunca sucesso. Evento na outbox ≠ sincronização concluída — a pós-condição real é o read-back do diff vazio por competência.

### 4.4 Gatilhos de sync

- Revisão de catálogo aplicada (ADD/UPDATE/RETIRE/REORDER/REACTIVATE) → fan-out para `OPEN AND period >= effective_afetado`.
- `start_checklist_sequence` → nenhum sync (série nova não tem competências — pré-condição).
- Abertura de competência → nenhum sync (a cópia já é do vigente).
- Reprocessamento manual governado → mesmo caminho do consumidor.

## 5. Modelo de concorrência

| # | Conflito | Proteção |
|---|---|---|
| 1 | Duas edições de catálogo simultâneas | lock `FOR UPDATE` no template (existente) + OCC `expected_revision` |
| 2 | Inclusão concorrente do mesmo requisito | `UNIQUE(version_id, item_key)` + idempotency_key |
| 3 | Edição durante `open_competence` | ambos tomam lock do template (ordenação: sempre template antes de competence) — serializado |
| 4 | Edição durante conclusão (`derive_closing_state` transitando para COMPLETED) | consumidor trava competence `FOR UPDATE` antes de recomputar o predicado — submissão de pacote também trava competência/versões; ordem de lock documentada: **template → competence → competence_items → package** para evitar deadlock |
| 5 | Upload concorrente à retirada | retirada só marca `CANCELLED`; upload valida item ativo — upload em item já `CANCELLED` falha com `item_not_active`; upload já persistido permanece vinculado (evidência preservada) |
| 6 | Validação (decisão) simultânea ao sync | item com decisão `ACCEPTED` é frozen; decisão em andamento e `CANCELLED` concorrentes: decisão vence se commitar primeiro e o item sai do conjunto elegível; item já `CANCELLED` não aceita decisão nova (guard existente de estado) — regra: **estado terminal do item sempre vence o sync** |
| 7 | Submissão de pacote concorrente | item_locked: itens cobertos por `closing_package_version SUBMITTED` ficam `skipped`; a composição do pacote é snapshot próprio (JSONB) e não corrompe |
| 8 | Dois syncs simultâneos | `sync_run` tem `UNIQUE(competence_id, catalog_revision)` + lock na competence serializa; segundo consumidor vê run já terminal → no-op idempotente |
| 9 | Retry após timeout | idempotency_key + re-leitura de estado — replay retorna resultado, não reaplica |
| 10 | Falha após mutação parcial | **impossível** — transação por competência é atômica; falha = zero mutação naquela competência |

Ordem de locks canônica (anti-deadlock): `checklist_template` → `monthly_competence` (por `period` crescente) → `competence_checklist_item` → `closing_package_version` → `closing_audit_event`/`outbox`.

## 6. Contratos propostos

### 6.1 Reutilizados sem alteração

- `derive_closing_state` (autoridade), `open_competence` (cópia vigente), `closing_audit_event` (trilha), `_emit_outbox` (mecanismo), OCC/idempotency-key, `manage`/`access` authorization.

### 6.2 Novos (sem implementação)

| Contrato | Descrição |
|---|---|
| `POST /admin/checklist-catalog/items` etc. (revisões — ADR-005) | resposta inclui `sync_impact { requested, runs_url }` |
| `GET /admin/checklist-catalog/sync-impact/preview?period=` | preview governado (diagnóstico, não condição) |
| `GET /closing/competences/{period}/checklist-sync-status` | último `sync_run`: estado, revisão aplicada, plano, skipped |
| `GET /admin/checklist-sync-runs?status=FAILED` | fila admin |
| `POST /admin/checklist-sync-runs/{id}/retry` | reprocessamento governado |
| Eventos audit | `CHECKLIST_SYNCED`, `CHECKLIST_SYNC_SKIPPED`, `CHECKLIST_SYNC_FAILED` |
| CLARA | **nenhuma capability nova** — `checklist.doc_requirement`/`item.*` continuam; leitura de sync via `read`/`knowledge` existentes (paridade, sem caminho paralelo) |

Erros tipados: `competence_not_syncable` (concluída/rejeitada), `item_locked_by_submitted_package`, `sync_in_progress`, `catalog_revision_stale`, `idempotency_conflict` — mesmo envelope de erros do BFF.

## 7. Histórico na interface

- Itens `CANCELLED` por `catalog_retire`: o painel documental passa a renderizá-los como **card de histórico** ("Exigência retirada pelo checklist em {data}"), colapsado por padrão mas expansível — conteúdo do documento/decisões permanece acessível no detalhe.
- `closing_document`/`document_message`/`evidence_decision` permanecem intactos e navegáveis via o mesmo `DocumentDetailPanel` (rota por `document_id`).
- Badge/filtro opcional "mostrar retiradas" — toggle de visibilidade, nunca delete.

## 8. Segurança

- Sync executa como **efeito sistêmico** da operação governada — não é capability separada nem autoridade paralela; o ator da trilha é o autor da revisão de catálogo (`actor` propagado) ou `system` se disparo interno.
- `manage` para qualquer operação de catálogo/retry; leitura de status = `access`.
- Nenhuma bypass de `derive_closing_state`.

## 9. Critérios de aceite (resumo — matriz completa em §8 do mandato)

- AC-S1: alteração de catálogo em competência `PENDING` → item sincronizado na mesma época, evento `CHECKLIST_SYNCED`, read-back diff vazio.
- AC-S2: competência `MONTHLY_CLOSING_COMPLETED`/`TERMINALLY_REJECTED` → `SKIPPED`, zero mutação, evento registrado.
- AC-S3: retirada com evidência → item `CANCELLED`, documentos/decisões/pendências intactos e navegáveis.
- AC-S4: item locked por pacote SUBMITTED → `skipped` tipado, pacote íntegro.
- AC-S5: kill do processo entre commit e consumo → evento `PENDING` processado na retomada (durabilidade do outbox).
- AC-S6: replay/retry → nenhum efeito duplicado (idempotência por run).
- AC-S7: resposta do catálogo nunca reporta sucesso global com runs não terminais sem marcador visível.
- AC-S8: edição simultânea à conclusão → serializado por lock; quem commitar primeiro define o resultado, sem half-write.

## 10. DECISION_REQUIRED remanescentes

1. **Mecanismo**: outbox B (recomendado) vs transacional síncrono A (válido no N atual). Decisão arquitetural — o contrato de estados `sync_run` é exigido em ambos.
2. **Consumidor**: dispatch inline pós-commit (recomendado — latência mínima, zero infra nova) vs worker dedicado.
3. **`EVIDENCE_ATTACHED` editável pelo sync?** Recomendo sim para campos descritivos (nome/finalidade/ordem) e não para retirada (retirada com evidência → `CANCELLED` preservando vínculo — já coberto); confirmar com PO se "documento anexado" congela metadados.
4. **Filial como filtro de elegibilidade**: competência atual não modela filial no nível da linha (itens carregam `branch_scope` por item) — a aplicação por item já resolve; confirmar se haverá competência por filial (mudaria fan-out).
