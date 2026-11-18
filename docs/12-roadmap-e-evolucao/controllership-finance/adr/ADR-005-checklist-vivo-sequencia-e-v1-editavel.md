# ADR-005 — Checklist vivo: identidade de sequência, nova V1 e edição publicada com revisões internas

- **Status:** `PROPOSED` (Gate 1 — CF-CHECKLIST-LIVE-002, aguardando revisão do GPT Arquiteto / PO)
- **Data:** 2026-11-17
- **Base técnica:** HEAD `ef02ef508e` (main) + inventário runtime `CF-CHECKLIST-LIVE-001` (2026-11-17)
- **Autoridades consultadas:** `platform-data-persistence`, `platform-api-contracts-integration`, `local-first-deploy`, `evidence-driven-execution`, doc 114 §8/§10/§11, doc 166, doc 173

---

## 1. Contexto e decisões do PO

Decisões funcionais **já tomadas** (não reabrir):

1. Ao excluir definitivamente todas as versões existentes, a nova sequência recomeça em **V1** — com os 16 itens hoje na V2 e vigência pretendida `2026-01`.
2. A V1 permanece `PUBLISHED` enquanto o administrador inclui, altera, retira e reordena exigências — **sem** criar versão numerada nova a cada alteração comum.
3. Alterações propagam-se **automaticamente** aos fechamentos em andamento; concluídos permanecem congelados.
4. Auditoria, identificadores, proveniência, datas e autores históricos preservados integralmente.

## 2. Problema

O modelo vigente torna incompatíveis três requisitos simultâneos do PO:

| Invariante vigente | Evidência | Conflito |
|---|---|---|
| Versão publicada = composição absoluta **imutável**; toda mudança gera nova(s) versão(ões) | `apply_document_requirement` → `planner` + `_insert_governed_version` (`closing_checklist_repository.py:1219-1603`) | §2.2 do PO: "V1 permanece PUBLISHED editável" |
| Alta-marca `max(tabela, trilha)` impede reutilização de `version` | `_next_version_locked` (`:1010-1035`), introduzido na CF-UX-054 | §2.1 do PO: "recomeçar em V1" |
| Divergência catálogo↔competência impedida por **bloqueio** (`window_covers_open_competence`) | `apply_document_requirement` :1329-1355; `publish_version` :638-672 | §2.3 do PO: "propagar automaticamente" |

## 3. Invariantes a preservar (não negociáveis)

- `closing_audit_event` append-only; nenhum evento histórico editado/removido.
- Toda referência física (`version_id`, `item_id`, `snapshot_item_id`, `document_id`) é UUID — estável e nunca reutilizada.
- `UNIQUE(template_id, version)` hoje garante não-colisão; qualquer modelo novo precisa de discriminação equivalente ou superior.
- Snapshot `competence_checklist_item` é cópia congelada com proveniência descritiva (`source_*` sem FK) — válida tanto para versões imutáveis quanto para revisões, desde que a identidade do item-fonte seja estável.
- `derive_closing_state` permanece a única autoridade de conclusão.
- Fail-closed: estado desconhecido nunca vira mutação silenciosa.

## 4. Alternativas avaliadas

### N1 — Nova linhagem (novo `template_id`, V1 nova)

**Viabilidade técnica: PARCIAL com risco oculto.** `resolve_published_version` (`:779-796`) e o winner de `open_competence` (`:826-839`) selecionam `PUBLISHED` com `effective_from_period <= period` **`ORDER BY effective_from DESC, version DESC LIMIT 1` — sem filtrar `template_id`**. Um segundo template publicado na mesma janela competiria silenciosamente com o histórico (se alguma versão do template antigo permanecesse PUBLISHED) — exigiria invariante novo "um template PUBLISHED por macroprocesso" ou filtro por template na resolução. Auditoria ficaria íntegra (eventos por `entity_id` UUID). **Vantagem:** zero ambiguidade de numeração; rollback trivial. **Risco:** semântica de "continuidade do checklist mestre" quebra — consumidores que referenciam `code='monthly-closing-checklist'`/`template_id` passam a apontar para a linhagem morta; requer migração de referências conceituais e uma guarda nova de seleção. **Descartada como caminho principal** — resolve o número mas cria um segundo agregado de vigência.

### N2 — Geração formal dentro do mesmo template

`checklist_template_version.series INT NOT NULL DEFAULT 1`, `UNIQUE(template_id, series, version)`; alta-marca por série; `detail.series` nos eventos de auditoria; `list_template_events` resolve `(series, version)`; `base_version` OCC por série ativa; apenas uma série `ACTIVE` por template (check/índice parcial). **Vantagem:** preserva `template_id` e todas as FKs; "V1 da série 2" é inequívoco; trilha das séries anteriores permanece consultável por `(entity_id)` ou `(series,version)`. **Custo:** migration V031 + ~12 pontos de consumo que assumem `version` inteiro simples (ver §6). **Adotada como mecanismo de identidade.**

### N3 — Reinício excepcional sem discriminador

Reiniciar contagem no mesmo template sem `series`. **Rejeitada:** reintroduz exatamente a ambiguidade que a alta-marca eliminou (`list_template_events` usa `COALESCE(v.version, detail->>'version')` — eventos da V1 antiga seriam atribuídos à V1 nova ao filtrar por número; `document_requirement_operation.result.published_versions` históricos ambíguos; `ORDER BY version DESC` perde monotonicidade). O mandato proíbe expressamente "remover o cálculo de alta-marca" — e qualquer preservação real de ambiguidade zero exige discriminador, o que torna N3 ≡ N2 com nome pior.

### E1 — Versão publicada com revisões internas (edição in-place auditada)

A V1 publicada passa a ser **mutável por revisões**, não por novas versões:

- Nova tabela append-only `checklist_version_revision` (ver §5.3): cada alteração administrativa grava operação, item afetado, before/after, autor, motivo, `idempotency_key` e incrementa `checklist_template_version.revision` (âncora OCC já existente).
- `checklist_template_item` ganha `retired_at`/`retired_revision` (tombstone): itens **nunca** são apagados fisicamente de uma versão publicada — retirada = marca; `item_id` permanece resolvível para `source_template_item_id` histórico.
- `item_key` tratado como **identidade imutável dentro da série** (renomear = retirar + adicionar, com link de sucessão opcional no evento); reutilizar `item_key` aposentado é permitido **somente** via reativação explícita do mesmo item (mesmo `item_id`), nunca para significado diverso.
- Janelas de vigência por item migram do modelo "boundary versions" para atributos do item: `effective_from_period`/`effective_until_period` no item vigente — a "versão vigente para o período" continua resolvida pela versão, mas a composição aplicável é filtrada pela janela de cada item.
- **`apply_document_requirement` NÃO é descartado:** permanece para o fluxo prospectivo multi-boundary (janelas de término futuro propagam versões de remoção em `until+1`). As duas superfícies compartilham o mesmo lock de template, o mesmo ledger e os mesmos guards — ver §7 sobre a fronteira.

**Trade-off assumido:** a versão publicada deixa de ser "composição imutável". A imutabilidade é substituída por **revisão append-only equivalente em expressividade** (qualquer estado passado é reconstruível pela trilha de revisões + trilha de auditoria), com ganho direto: identidade de lista estável, sem churn numérico.

### E2 — Manter boundary-versions e escondê-las na UX

**Rejeitada:** é precisamente a alternativa que o PO excluiu ("não apenas esconder V2/V3/V4 enquanto o fluxo interno continua exigindo novas versões"). Além disso, o churn de versões infla o espaço de numeração e de auditoria com artefatos sem significado de negócio.

## 5. Decisão proposta

**Adotar N2 (série/geração) + E1 (revisões internas na versão publicada), mantendo `apply_document_requirement` para vigências com término futuro.**

### 5.1 Modelo de identidade

```
checklist_template (template_id UUID, code)          ← identidade do catálogo
 └── série/geração (series_no INT, única ACTIVE)      ← "nova sequência"
      └── checklist_template_version                 ← número visível V1, V2…
            (version_id UUID, series_no, version,
             status, revision, effective_from_period)
             └── checklist_template_item             ← tipos documentais
                   (item_id UUID — identidade estável,
                    item_key — imutável na série,
                    effective_from/until, retired_at/revision)
                    └── checklist_version_revision   ← trilha de revisões (append-only)
                          (revision_seq, operation, item_key,
                           before/after JSONB, actor, reason,
                           idempotency_key)
 └── competence_checklist_item                      ← snapshot do fechamento
       (source_version_id, source_template_item_id — proveniência UUID)
```

### 5.2 Nova sequência (o "recomeçar em V1")

Operação governada `start_checklist_sequence` (admin — **um único usuário com `controllership-finance.manage` efetivo**, D4 **DECIDED_BY_PO**: sem segundo aprovador/four-eyes; exige confirmação explícita da operação excepcional, `reason` obrigatório, inventário de dependências, OCC, idempotência, auditoria e read-back; sem novo permission code):

1. **Pré-condição fail-closed:** todas as versões da série ativa eliminadas definitivamente (`delete_template_version` — já existe, com manifesto OCC) **ou** explicitamente encerradas; zero `monthly_competence` viva vinculada à série anterior (fail-closed se houver).
2. Em uma transação: marca série anterior `CLOSED` (coluna `series_state` ou derivável), `series_no = max(series)+1`, insere nova versão `version=1` PUBLISHED com `effective_from_period` informado e `series_no` novo.
3. Alta-marca passa a ser **por série**: `max(version) WHERE series_no = série ativa` + trilha filtrada por `detail->>'series'` — a V1 histórica permanece referenciável como `série 1 · V1`.
4. Eventos: `CHECKLIST_SEQUENCE_STARTED` (detail: `series_no`, `supersedes_series`, `effective_from`, `reason`, `actor`) + `DRAFT_CREATED`/`VERSION_PUBLISHED` da nova V1 (com `series` no detail).
5. `list_template_events`: `COALESCE(v.version, detail->>'version')` passa a compor `(detail->>'series', version)` — sem ambiguidade.

### 5.3 Revisões internas — Modelo A (cabeçalho + linhas de alteração)

**Alternativas avaliadas:** (B) evento único com `changes[]` JSONB — mais simples mas impede query por item e auditoria relacional; (C) snapshot completo por revisão — reconstrução trivial mas custo O(itens) por alteração e duplicidade com a própria tabela de itens. **Modelo A adotado** — espelha o padrão já vigente `document_requirement_operation` (cabeçalho) + steps do planner (filhos) e `closing_audit_event` (evento por item): auditável por item, replayável, consultável.

```sql
-- Cabeçalho: uma linha por operação administrativa atômica
checklist_version_revision (
  revision_id    UUID PK DEFAULT gen_random_uuid(),
  version_id     UUID NOT NULL REFERENCES checklist_template_version,
  revision_seq   INT  NOT NULL,              -- == version.revision após aplicar
  operation      VARCHAR(16) NOT NULL        -- ADD|UPDATE|RETIRE|REORDER|REACTIVATE|REVERT|BATCH
                 CHECK (operation IN (...)),
  reason         TEXT,                       -- obrigatório em RETIRE/REVERT/migração
  actor_subject  UUID NOT NULL,
  idempotency_key VARCHAR(80) NOT NULL,
  fingerprint    CHAR(64) NOT NULL,          -- sha256 da composição resultante (read-back)
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (version_id, revision_seq),
  UNIQUE (version_id, idempotency_key)
);

-- Filhos: uma linha por item afetado (deltas completos por item)
checklist_version_revision_change (
  change_id      UUID PK DEFAULT gen_random_uuid(),
  revision_id    UUID NOT NULL REFERENCES checklist_version_revision,
  item_key       VARCHAR(32) NOT NULL,
  item_id        UUID NOT NULL,              -- identidade estável
  change_kind    VARCHAR(16) NOT NULL,       -- ADD|UPDATE|RETIRE|REORDER|REACTIVATE
  before_json    JSONB,
  after_json     JSONB,
  UNIQUE (revision_id, item_key)
);
```

`version.revision` = contador de revisões aplicadas à versão (semântica compatível com os draft-updates atuais — monotônica por versão). OCC: `expected_revision` no cabeçalho da operação.

**Operações** (mesmo lock `FOR UPDATE` do template, mesma transação única — uma revisão cobre N itens atomicamente):

| Operação | Entrada | Esperado | Resultado |
|---|---|---|---|
| `add_item` / `add_items` | item(s), `effective_from/until?`, `expected_revision`, reason?, idem-key | rev atual | N changes ADD, `revision++` |
| `update_item` / `update_items` | `{item_key: patch}`, `expected_revision`, reason?, idem-key | rev + item ativo | N changes UPDATE (before/after por item); `item_key` nunca editável |
| `retire_item` / `retire_items` | `{item_key}`, `expected_revision`, **reason**, idem-key | rev + item ativo | item `retired_at/retired_revision` (tombstone); N changes RETIRE |
| `reorder_items` | `ordering[]`, `expected_revision`, idem-key | rev + conjunto íntegro | N changes REORDER (sort_order before/after) |
| `reactivate_item` | `item_key`, `expected_revision`, idem-key | tombstone do mesmo `item_id` | change REACTIVATE, tombstone removido |
| `revert_revision` | `revision_seq`, `expected_revision`, **reason**, idem-key | rev alvo existe | nova revisão REVERT com `after := before` da alvo (trilha preservada, nunca delete) |

Cada operação: lock → replay por `idempotency_key` → OCC `expected_revision` → guards §5.4 → mutações + `revision++` → header + changes + `fingerprint` → `closing_audit_event` (`CATALOG_ITEM_ADDED|UPDATED|RETIRED|REORDERED|REACTIVATED|REVISION_REVERTED` com `series`,`version`,`revision_seq`) → gatilho de sync (doc 174) → read-back por fingerprint.

**Reconstrução histórica (§7.4 do mandato):**

- **V1 revisão N:** replay dos changes por `revision_seq` ≤ N sobre o conjunto base (seed da versão) — ou filtro `retired_at IS NULL OR retired_revision > N` se tombstones carregam `retired_revision`.
- **Item em revisão N:** último `change` por `item_key` com `revision_seq ≤ N`.
- **Composição em data D:** mesma consulta filtrando `created_at ≤ D`.
- **Composição na abertura do fechamento X:** `competence_checklist_item` já é a cópia congelada — não depende de reconstrução (PROVEN, invariante preservado).
- **V1 antiga × V1 nova:** `(series=1, version=1)` vs `(series=2, version=1)` — sem ambiguidade por construção.
- **Fingerprint determinístico:** sha256 sobre o conjunto canônico `(item_id, item_key, campos vigentes, sort_order)` ordenado — verificável por read-back independente.

**Identidades (§7.5):** `template` = catálogo; `series` = geração de numeração; `version` = número visível na série; `version_id` = identidade física; `revision`/`revision_seq` = passo de edição dentro da versão publicada; `revision_id` = operação administrativa; `item_id` = identidade estável do requisito; `item_key` = chave de negócio imutável na série. Sem sobrecarga de campos.

### 5.4 Guards preservados e revisados

| Guard vigente | Destino |
|---|---|
| `operation_busy` (lock 5s) | mantido |
| `idempotency_conflict` | mantido (por version_id) |
| `stale_revision` (OCC) | mantido — âncora passa a ser `version.revision` |
| `catalog_draft_conflict` | **mantido** — edição in-place só em PUBLISHED da série ativa; DRAFT/REVIEW coexistem pelo fluxo legado de baseline |
| `retroactive_effective_period` | **mantido** para `effective_from` de itens (exceção: operação governada de migração, §8) |
| `window_covers_open_competence` | **substituído pela sincronização automática** — a divergência deixa de ser proibida e passa a ser propagada; elegibilidade pelo predicado `OPEN ∧ first_completed_at IS NULL ∧ completion_record='NEVER' ∧ PENDING` — **lista positiva fail-closed**, `COMPLETED`/`UNEVALUATED`/valor desconhecido bloqueiam (doc 174 §2.3) — competência historicamente concluída nunca sincroniza |
| `empty_resulting_checklist` | mantido — retirar o último item exige `allow_empty` explícito |
| `WindowCoversOpenCompetence` no `publish_version`/`inactivate_version` legados | mantido — fluxo de nova versão numerada segue prospectivo |

### 5.5 Consulta de histórico e comparação

- `GET /admin/checklist-templates/{id}/versions/{series}/{version}/revisions[?item_key=]` — revisões (headers) + changes por item + eventos correlatos.
- `GET .../revisions/{seq}` — revisão puntual: header + `changes[]` + `fingerprint`.
- Diferença entre revisões: composição de changes `> seqA AND <= seqB`; estado de item/data por replay (§5.3).
- Reversão governada: `POST .../revisions/{seq}/revert` — nova revisão `REVERT` (motivo obrigatório); trilha nunca deletada.

**Regra de `reason` (D7 resolvida por direção):** `RETIRE`, `REVERT` e operações de migração exigem motivo; `ADD`/`UPDATE`/`REORDER`/`REACTIVATE` registram autor+before/after com motivo opcional — sem regra vigente mais restritiva no contrato atual.

## 6. Matriz de impacto contratual

| Consumidor | Contrato atual | Impacto | Mudança |
|---|---|---|---|
| Rotas admin `/versions/{version}/...` | `version` inteiro no path | path passa a `/series/{series}/versions/{version}` **ou** `{version}` resolve na série ativa com legado | versioning de rota ou resolução default |
| `base_version` OCC (`doc_requirement`, FE `catalogBaseVersion`) | `max(version)` | vira `max(version)` **da série ativa** ou `version.revision` por operação nova | contrato |
| `list_template_events` | filtro por `version` | compõe `(series, version)` | query + response |
| `resolve_published_version`/`open_competence` winner | `version DESC` desempate | passa a `series DESC, version DESC` (série ativa) e **filtro por série ativa** | query |
| `monthly_competence.template_version_id`, `source_version_id`, `source_template_item_id` | UUIDs | **inalterado** | nenhuma |
| `checklist_template_item` | linha viva | +`retired_at`, `retired_revision`, `effective_until_period` | migration |
| `document_requirement_operation` | ledger | +`series` no result | schema leve |
| CLARA `checklist.*` params `version` | inteiro | aceita `series` opcional (default série ativa) — mesmo capability, sem caminho paralelo | contrato |
| Frontend admin | versões como unidade | apresenta "catálogo vigente" + histórico de revisões | UX (Entregável 3) |
| Relatórios/cockpit | leem snapshot | inalterado | nenhum |
| `delete_template_version` | exclui versão | exige série CLOSED ou versão da série ativa — mesma operação | regra |
| Scripts (`consolidate_checklist_baseline`) | reescreve itens | avaliar aposentadoria (mantém para saneamento pontual) | revisão |

## 7. Fronteira entre revisão in-place e `document_requirement`

- **Revisões in-place**: alterações de conteúdo com vigência "a partir de agora/período corrente" — add/update/retire/reorder/reactivate. Janela do item: `effective_from` (≥ período corrente) / `effective_until` (fim declarado sem gerar versão de remoção — o item simplesmente deixa de ser aplicável após `until`).
- **`document_requirement` (boundary versions)**: mantido para janelas complexas com múltiplos boundaries já existentes na linha do tempo e para a semântica "remover em `until+1` propagando versão". **Alternativa de simplificação (recomendada):** unificar — item-level `effective_from/until` absorve o caso de `document_requirement`, tornando o planner legado interno (o comando continua existindo, mas materializa revisões no lugar de versões). Decisão fina delegada ao Gate 2 (ver §10).

## 8. Migração excepcional do estado PROD (projeto, não execução)

**Estado:** V1 `INACTIVE` (1 item), V2 `REVIEW` (16 itens), 0 competências, proposals `version_delete` v1/v2 `PREPARED` não consumidas (**não reusar handles**).

Ordem transacional proposta (operação governada única, dry-run obrigatório antes):
1. Export manifesto read-only (fingerprint sha256 — `competence_inventory_backup.py` adaptado ao escopo checklist; comparar com os 16 itens reais).
2. Consumir/descartar as proposals pendentes por caminho próprio (novas proposals, não handles antigos).
3. `version_delete` V1 e V2 (trilha `VERSION_DELETED` preserva histórico) — pré-condição de série limpa.
4. `start_checklist_sequence` → série 2 V1 PUBLISHED `effective_from=2026-01` — **exceção governada ao guard de retroatividade**, com `reason` + `CHECKLIST_SEQUENCE_STARTED` auditado (a competência que cobrisse a janela não existe; fail-closed se existir).
5. Seed dos 16 itens na V1 nova via `add_item` em lote (mesma tx da sequência ou lote de revisões).
6. Read-back: contagem 16, fingerprint do manifesto = fingerprint aplicado, `winner@2026-01` = nova V1, trilha íntegra consultável (`series=1` e `series=2`).
7. Reversão: como trilha é append-only, "rollback" = nova operação governada revertendo a série (os dados históricos nunca foram apagados de fato — apenas as versões vivas; um restore-point de `checklist_template_version`/`checklist_template_item` dumpado previamente cobre catastrófico).

**Autorização necessária:** gate separado, com aprovação explícita do PO para operações em dados produtivos (mesmo padrão CF-UX-054).

## 9. Testes (proposta)

- `test_pg_checklist_sequence.py`: start_sequence (pré-condições, série limpa, alta-marca por série, trilha separada, winner por série ativa).
- `test_pg_catalog_revisions.py`: add/update/retire/reorder/reactivate, tombstone, OCC, idempotência, histórico, reversão, `allow_empty`, reutilização `item_key` proibida/permitida-por-reativação.
- Rotas: série default/legado, 401/403, erros tipados.
- Regressão: `test_pg_document_requirement.py`, `test_pg_closing_checklist.py`, `test_pg_checklist_version_delete.py` devem permanecer verdes (compat) ou ser ajustados conscientemente.

## 10. DECISION_REQUIRED remanescentes (reconciliadas R3)

1. **D1 — Unificação do `document_requirement`** — direção: **um único caso de uso canônico** de alteração de exigências (o de revisões §5.3); o adapter legado `apply_document_requirement` delega a ele traduzindo os steps, preservando o contrato existente. Dois writers independentes são proibidos. *Decisão técnica — GPT Arquiteto.*
2. **D2 — Paths de série** — direção: **série ativa por padrão** nas operações correntes; série explícita exigida apenas em consultas de histórico. Sem ambiguidade (só existe uma série `ACTIVE`). *Fechável tecnicamente.*
3. **D3 — `effective_until` retroativo** — direção: **manter guard conservador** até existir política temporal comprovada. *Fechável tecnicamente.*
4. **D4 — Four-eyes em `start_checklist_sequence`** — **DECIDED_BY_PO**: aprovação única com `manage` efetivo, sem duplo aprovador; confirmação explícita + `reason` + OCC + idempotência + auditoria + read-back (§5.2). A decisão de autorização não autoriza executar a migração agora.
5. **D5 — Outbox vs síncrono** — resolvido por evidência: padrão outbox+poller durável já é canônico na BFF (doc 174 §4.1). *Fechado tecnicamente.*
6. **D6 — Correção/pendência aberta em item retirado** — **DECIDED_BY_PO**: encerramento automático, restrito ao requisito retirado — correção com **encerramento administrativo** `CLOSED_REQUIREMENT_RETIRED`+`closure_reason='requirement_retired'`+`closed_by`=autor da revisão — `REJECTED` permanece exclusivo de rejeição humana (migration Gate 2: `status` `VARCHAR(12)→VARCHAR(32)`, CHECK `item_correction_status_check` ampliado preservando os 3 estados, `closure_reason/closed_by/closed_at` nullable — doc 174 §3.2/R6.1); pendência `DISMISSED`+`dismiss_justification='catalog_retire'` — «perda de aplicabilidade» ≠ «resolvida por execução» (doc 174 §3). Reativação é simétrica na propagação, nunca na destruição do histórico, e **só** se aplica a item `CANCELLED` comprovadamente por `catalog_retire` — cancelamento manual ou de origem desconhecida nunca é revertido pelo sync (doc 174 §3.1).
7. **D7 — `reason` obrigatório** — resolvido por direção (§5.5).
8. **D8 — Validade da evidência na reativação** — `DECISION_REQUIRED` (PO): evidência pré-retirada conta para a exigência reativada? Default conservador até decisão: exigência volta `EXPECTED` e evidência fica visível no histórico (doc 174 §10).

## 11. Consequências

- **Positivas:** V1 estável e visível, edição contínua com trilha mais granular que a atual (antes: versão inteira por mudança), numeração reiniciável com história inequívoca, reutilização de 80% da infraestrutura (lock, ledger, OCC, guards, CLARA).
- **Negativas:** invariante "PUBLISHED imutável" deixa de existir — substituído por "PUBLISHED revisado append-only"; toda a superfície de `version` inteiro vira `(series, version)`; migration + adaptação de ~12 pontos de consumo; `revision` ganha semântica dupla histórica (draft updates vs catalog revisions — documentar).
- **Não alterar:** snapshot por cópia, `derive_closing_state`, `closing_document.link_kind`, autorização `manage`, CLARA PREPARE/ACT.
