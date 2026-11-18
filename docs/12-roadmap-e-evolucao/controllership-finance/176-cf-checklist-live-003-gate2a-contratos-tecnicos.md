# CF-CHECKLIST-LIVE-003 — Gate 2A: Contratos técnicos do Checklist Vivo

> **Tipo:** especificação técnica (contratos, persistência TARGET, plano).
> **Fase:** Gate 2A — autorizado para especificar, **não** para implementar.
> **Baseline:** Gate 1 `ACCEPT_WITH_RESIDUAL` em `1cb99879ef`; fontes ADR-005 + docs 174/175.
> **Status:** `TARGET` — aguardando revisão arquitetural do GPT Arquiteto. Nenhuma linha aqui autoriza código, migration ou deploy.

Identidade congelada: plugin `controllership-finance`, MFE `/apps/controllership-finance`, BFF `/apps/controllership-finance-api`, permissões `controllership-finance.access` / `controllership-finance.manage` — nenhuma permission nova.

---

## 1. Inventário de reutilização (REUSE BEFORE DESIGN)

| Necessidade | Implementação existente (HEAD) | Owner | Decisão | Justificativa |
|---|---|---|---|---|
| CRUD de template/versão/item | `admin_checklist_routes.py` + `ClosingChecklistRepository` | BFF | **EXTEND** | mesmos paths/transações; adicionar série e revisões |
| Operação unitária de exigência | `upsert_document_requirement` → `document_requirement_operation` (header+steps, V017) + `apply_document_requirement` | BFF | **EXTEND** | cada op unitária passa a registrar uma `checklist_version_revision` com 1 change — sem endpoint paralelo |
| Operações em lote | não existe | — | **NEW** | `POST .../versions/{version_id}/revisions` (header+changes atômico) |
| Série/sequência | não existe — `UNIQUE(template_id,version)` impede novo V1 (V001:33) | — | **NEW** | tabela `checklist_template_series` (§4.1) |
| Contador de revisão | `checklist_template_version.revision INT ≥1` (V001:24) | BFF | **EXTEND** | passa a denotar o nº da última revisão interna |
| Abertura de competência | `open_competence` (`closing_checklist_repository.py:798-908`): lock template→winner→`INSERT ... ON CONFLICT DO NOTHING`→snapshot integral | BFF | **EXTEND** | INSERT passa a incluir `completion_record='NEVER'` explícito (doc 174 §2.2b) |
| Marcador de conclusão | não existe (`derive_closing_state` é momentâneo) | — | **NEW** | `first_completed_at`+`completion_record`+`refresh_completion_marker` (§4.4, §6.2) |
| Encerramento de correção | `item_correction` V005 | BFF | **EXTEND** | `VARCHAR(32)`+CHECK+`closure_*` (doc 174 §3.2/R6.1) |
| Encerramento de pendência | `closing_pendency` `DISMISSED`+`dismiss_justification` (V006) | BFF | **REUSE** | `catalog_retire`, sem migration de enum |
| Outbox durável | `closing_notification_event`+`_emit_outbox`+`dispatch_pending`+`run_closing_notification_dispatch_loop` | BFF | **NEW mesma forma** | `checklist_sync_event`/`checklist_sync_run`+poller (§7) |
| Auditoria | `closing_audit_event` | BFF | **REUSE** | novos event_types apenas |
| Autorização | `authorized_user`/`authorized_admin` (access/manage) + Core | BFF | **REUSE** | nenhuma permission nova |
| Erros | `_domain_fail`→`ChecklistDomainError`→envelope vigente | BFF | **EXTEND** | novos `error_code` tipados (§3.3) |
| CLARA | `tool_bridge.py` + `ClaraGovernedWrites` + `ClaraBatchOrchestrator` | BFF/MCP | **EXTEND** | tools chamam os mesmos use cases (§8) |
| Frontend admin | páginas admin existentes (doc 175) | MFE | **EXTEND** | novas colunas/painel de revisões (§9) |

**Nada aqui justifica novo módulo, serviço ou permission.**

---

## 2. Identidade e endereçamento

`template → series → version → revision → item`:

```text
template_id      — checklist mestre (imutável; V001)
series_no        — geração/sequência (1 = série legada; nova série = 2+)
series_id        — UUID da série
version          — reinicia em 1 dentro de cada série (V1 antiga ≠ V1 nova)
version_id       — UUID físico da versão
revision(_no)    — revisão interna sequencial da versão publicada
revision_id      — UUID da revisão
item_key         — identidade estável do requisito DENTRO de uma versão
item_id          — UUID da linha checklist_template_item
snapshot_item_id — UUID da linha competence_checklist_item
```

Regras: rotas correntes omitindo série resolvem a **série ativa**; rotas históricas exigem `series_no`/`series_id` explícito. `UNIQUE(template_id,version)` é substituída por `UNIQUE(series_id,version)` — pré-requisito para o novo V1 (§4.1). `item_key` é imutável dentro da versão; `REACTIVATE` restaura a mesma `item_id`/`item_key`; `ADD` sempre cria identidade nova (doc 174 §3.1).

---

## 3. G2-A — Contratos HTTP/OpenAPI

Base: `POST|GET /apps/controllership-finance-api/admin/checklist-templates` (existente). Todos admin → `manage`; leituras operacionais → `access`. Toda escrita: `X-Idempotency-Key` + OCC (`expected_revision` ou `If-Match: revision`) + `reason` obrigatório onde indicado. Erros: envelope vigente com `error.code` tipado.

### 3.1 Catálogo e série

| Method | Path | Cap | Descrição |
|---|---|---|---|
| GET | `/admin/checklist-templates` | manage | lista templates |
| GET | `/admin/checklist-templates/{template_id}/series` | manage | série ativa + histórico de séries |
| GET | `/admin/checklist-templates/{template_id}/series/{series_no}` | manage | detalhe da série (versoes, alta-marca) |
| GET | `/admin/checklist-templates/{template_id}/series/active` | manage | série ativa canônica |
| POST | `/admin/checklist-templates/{template_id}/series` | manage | **start_checklist_sequence** — D4: confirmação explícita+`reason`+OCC+idempotência+audit+read-back; único `manage` |

### 3.2 Versões e revisões

| Method | Path | Cap | Descrição |
|---|---|---|---|
| GET | `…/versions` · `…/versions/{version_id}` · `…/events` | manage | existentes — estendidos com `series_no`/`revision` |
| POST | `…/versions/{version_id}/revisions` | manage | **revisão em lote atômica** — `changes[]` com `op` ∈ `ADD|UPDATE|RETIRE|REORDER|REACTIVATE`, `expected_revision`, `reason`, `idempotency_key`; retorna `revision` + `sync` (§7) |
| GET | `…/versions/{version_id}/revisions` · `…/revisions/{revision_id}` | manage | histórico + detalhe (before/after por item) |
| POST | `…/versions/{version_id}/revisions/{revision_id}/revert` | manage | nova revisão compensatória (nunca reescreve) |
| POST | `…/versions/{version_id}/impact-preview` | manage | impacto de uma revisão antes de aplicar (competências elegíveis, itens afetados) — read-only |
| PUT | `…/documents/{item_key}/requirement` | manage | existente — passa a gravar `checklist_version_revision` com 1 change |
| POST | `…/versions/{version}/submit-review|publish|inactivate|return-to-draft|delete` | manage | existentes — inalterados |
| GET | `…/versions/{version}/deletion-eligibility` | manage | existente — inalterado |

### 3.3 Operação e sync

| Method | Path | Cap | Descrição |
|---|---|---|---|
| POST | `/closing-competences` (existente `open_competence`) | access | abertura — EXTEND: `completion_record='NEVER'` no INSERT + read-back (§6.1) |
| GET | `/closing-competences/{period}/sync-status` | access | estado agregado de sync da competência (§7.6) |
| GET | `/admin/checklist-templates/{t}/sync-runs?revision_id=` | manage | runs por revisão (observabilidade admin) |
| POST | `/admin/competences/{competence_id}/completion-assessment` | manage | reconciliação governada `UNEVALUATED→NEVER|COMPLETED` — reason+audit (doc 174 §2.2) |

**Erros tipados novos** (todos no envelope vigente): `stale_revision` (OCC), `series_not_found`, `version_not_active`, `item_not_found`, `item_retired`, `item_locked_by_package`, `competence_completed`, `competence_unevaluated`, `operation_repeated` (idempotente), `idempotency_conflict`, `forbidden`, `scope_denied`, `sync_pending`, `sync_failed`, `unknown_cancel_origin`, `draft_already_open` (existente), `version_has_open_competences` (existente).

**Artefato:** `contracts/checklist-live.openapi.yaml` (nesta pasta) — spec 3.1 dessas rotas; artefato de contrato, não executável.

---

## 4. G2-B — Persistência TARGET

Matriz `Tabela → AS-IS → TARGET → Migration → Backfill → Rollback`. Numeração real no HEAD termina em **V030** (`V030__home_favorites.sql`); reserva lógica **V031–V035** — número efetivo confirmado no momento da implementação.

### 4.1 Série — `checklist_template_series` (NEW)

```sql
CREATE TABLE controllership_finance.checklist_template_series (
    series_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id      UUID NOT NULL REFERENCES checklist_template(template_id) ON DELETE RESTRICT,
    series_no        INT  NOT NULL CHECK (series_no >= 1),
    status           VARCHAR(10) NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE','CLOSED')),
    start_reason     TEXT NOT NULL,
    started_by       UUID NOT NULL,
    started_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    idempotency_key  VARCHAR(80) UNIQUE,
    UNIQUE (template_id, series_no)
);
CREATE UNIQUE INDEX ck_series_one_active ON checklist_template_series(template_id) WHERE status='ACTIVE';
```

`checklist_template_version`: `ADD series_id UUID NOT NULL REFERENCES … ` (backfill: série legada `series_no=1` por template); `DROP UNIQUE(template_id,version)` → `ADD UNIQUE(series_id,version)`; **unicidade de winner passa a ser por série** (índice parcial existente ajustado: um PUBLISHED por `(series_id)`). Winner resolution (`resolve_published_version`) filtra pela série ativa — legado continua resolvendo série 1 até a migração excepcional (§10).

### 4.2 Revisões — header + linhas (NEW)

```sql
CREATE TABLE controllership_finance.checklist_version_revision (
    revision_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_id      UUID NOT NULL REFERENCES checklist_template_version(version_id) ON DELETE RESTRICT,
    revision_no     INT  NOT NULL,
    fingerprint     VARCHAR(64) NOT NULL,          -- sha256 do catálogo resultante
    reason          TEXT NOT NULL,
    idempotency_key VARCHAR(80) NOT NULL UNIQUE,
    reverted_by     UUID REFERENCES checklist_version_revision(revision_id),
    created_by      UUID NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (version_id, revision_no)
);
CREATE TABLE controllership_finance.checklist_version_revision_change (
    change_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    revision_id  UUID NOT NULL REFERENCES checklist_version_revision(revision_id) ON DELETE RESTRICT,
    seq          INT  NOT NULL,
    item_key     VARCHAR(32) NOT NULL,
    op           VARCHAR(10) NOT NULL CHECK (op IN ('ADD','UPDATE','RETIRE','REORDER','REACTIVATE')),
    before_state JSONB,
    after_state  JSONB,
    UNIQUE (revision_id, seq)
);
```

OCC: `expected_revision` comparado a `checklist_template_version.revision`; write = `UPDATE … SET revision=revision+1 WHERE version_id=$1 AND revision=$2` (0 linhas → `stale_revision`). Reversão = nova revisão com `changes` compensatórias + `reverted_by`; nunca UPDATE físico em revisão anterior (histórico reconstruível: items = replay de `changes`).

### 4.3 Itens do catálogo — retirada lógica

`checklist_template_item` (hoje só linhas vivas): `ADD item_state VARCHAR(10) NOT NULL DEFAULT 'ACTIVE' CHECK IN ('ACTIVE','RETIRED')`, `ADD retired_revision_id UUID REFERENCES checklist_version_revision`, `ADD retired_by UUID`, `ADD retired_at TIMESTAMPTZ`. `RETIRE`/`REACTIVATE` = UPDATE governado (mesmo `item_id`/`item_key`) — nunca DELETE; `ADD` = nova linha. Winner passa a projetar apenas `item_state='ACTIVE'`.

`competence_checklist_item`: `ADD cancel_origin VARCHAR(14) CHECK (cancel_origin IS NULL OR cancel_origin IN ('MANUAL','CATALOG_RETIRE'))`, `ADD cancelled_revision_id UUID` — proveniência que autoriza REACTIVATE no sync (doc 174 §3.1) e bloqueia `unknown_cancel_origin`.

### 4.4 Conclusão histórica — `monthly_competence`

`ADD first_completed_at TIMESTAMPTZ NULL`, `ADD completion_record VARCHAR(12) NOT NULL DEFAULT 'UNEVALUATED' CHECK IN ('NEVER','COMPLETED','UNEVALUATED')`, `ADD completion_basis VARCHAR(10) CHECK IS NULL OR IN ('MARKER','BACKFILL','GOVERNED')`. Write-once: `first_completed_at` só transita `NULL→SET` (trigger/constraint na app); `completion_record` transições legais `UNEVALUATED→{NEVER,COMPLETED}`, `NEVER→COMPLETED`; nunca regressa. Backfill (§6.3).

### 4.5 Correções — `item_correction`

`ALTER status TYPE VARCHAR(32)`; `DROP CONSTRAINT item_correction_status_check` + `ADD CHECK IN ('PENDING','APPROVED','REJECTED','CLOSED_REQUIREMENT_RETIRED')`; `ADD closure_reason VARCHAR(80) NULL`, `ADD closed_by UUID NULL`, `ADD closed_at TIMESTAMPTZ NULL`. Zero reclassificação (doc 174 §3.2/R6.1).

### 4.6 Pendências — REUSE

`closing_pendency`: `DISMISSED`+`dismiss_justification='catalog_retire'`+`resolution_notes` já suportam — **sem migration**. Vínculo ao item: `pendency → evidence_decision/item` via colunas existentes; sync só encerra pendências cuja `item_key`/`snapshot_item_id` seja do item retirado (filtro obrigatório no WHERE — nunca por competência inteira).

### 4.7 Outbox — `checklist_sync_event` + `checklist_sync_run` (NEW)

```sql
CREATE TABLE controllership_finance.checklist_sync_event (
    event_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    revision_id    UUID NOT NULL REFERENCES checklist_version_revision(revision_id) ON DELETE RESTRICT,
    state          VARCHAR(10) NOT NULL DEFAULT 'EMITTED' CHECK (state IN ('EMITTED','DISPATCHED','FAILED')),
    attempts       INT NOT NULL DEFAULT 0,
    last_error     TEXT,
    emitted_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE controllership_finance.checklist_sync_run (
    run_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id      UUID NOT NULL REFERENCES checklist_sync_event(event_id) ON DELETE RESTRICT,
    competence_id UUID NOT NULL REFERENCES monthly_competence(competence_id) ON DELETE RESTRICT,
    revision_id   UUID NOT NULL,
    state         VARCHAR(24) NOT NULL DEFAULT 'PENDING'
        CHECK (state IN ('PENDING','APPLIED','APPLIED_WITH_EXCLUSIONS','SKIPPED','PARTIAL','FAILED')),
    skip_reason   VARCHAR(40),
    exclusions    JSONB NOT NULL DEFAULT '[]',
    started_at    TIMESTAMPTZ,
    finished_at   TIMESTAMPTZ,
    UNIQUE (revision_id, competence_id)      -- idempotência natural
);
```

### 4.8 Plano de migrations (ordem, sem DDL executável)

| # | Conteúdo | Tipo | Rollback |
|---|---|---|---|
| V031 | `checklist_template_series` + `series_id` em versions + backfill série 1 + `UNIQUE(series_id,version)` + índice winner por série | schema+dados | compensação documentada (série 1 preserva comportamento) |
| V032 | `checklist_version_revision` + `_change` + colunas de retirada em `checklist_template_item` + `cancel_origin`/`cancelled_revision_id` em `competence_checklist_item` | schema | additive-only |
| V033 | `monthly_competence` markers + CHECKs + **backfill** `completion_record` (§6.3) | schema+dados | additive; backfill reversível (re-avaliação) |
| V034 | `item_correction` VARCHAR(32)+CHECK+`closure_*` | schema | widening irreversível porém não-destrutivo |
| V035 | `checklist_sync_event`+`checklist_sync_run`+índices | schema | additive-only |

Cada migration validada por: apply em banco limpo + em banco com dados + checksum + read-back; `plugins-migrations-no-reset-prod` — nunca rewrite de migration aplicada.

---

## 5. Domain/Application — casos de uso TARGET

Novos/estendidos em `application/checklist/` (domain em `domain/closing_checklist/`):

| Use case | Regra central | Guards |
|---|---|---|
| `start_checklist_sequence` | fecha série ativa (`CLOSED`), cria série `n+1` + V1 `DRAFT`; registra evento | manage, confirm, reason, OCC, idempotency; série anterior íntegra |
| `apply_revision` | aplica `changes[]` atômicas sob lock da versão; emite `checklist_sync_event` na mesma tx | `expected_revision` (OCC), `reason`, `idempotency_key`, versão `PUBLISHED` |
| `revert_revision` | gera revisão compensatória com `changes` invertidas | mesmos guards; revisão alvo existente e não revertida |
| `preview_revision` | diff catálogo×changes + candidatos elegíveis | read-only |
| `reconcile_competence` | algoritmo §7.3 por competência | predicado §7.1 reavaliado na tx |
| `refresh_completion_marker` | §6.2 | sob lock da competência |
| `assess_completion` | reconciliação `UNEVALUATED` | manage+reason+audit |

Erros → `ChecklistDomainError` com `error_code` tipado (§3.3); domain nunca importa Flask/SQLAlchemy.

---

## 6. G2-C — Abertura e conclusão

### 6.1 Abertura (EXTEND `open_competence`)

Sequência transacional TARGET (já definida em doc 174 §2.2b — aqui o contrato de implementação): lock templates → winner **da série ativa** → `INSERT monthly_competence(period, template_version_id, completion_record='NEVER', first_completed_at NULL) ON CONFLICT (period) DO NOTHING` → se `created=false` retorna existente **sem reatribuir** `completion_record` → cópia integral dos itens `ACTIVE` → audit `COMPETENCE_OPENED` com `detail.completion_record` → commit → read-back do predicado. `UNIQUE(period)` serializa corridas. Falha em qualquer ponto = rollback integral (impossível competência parcial).

### 6.2 Writers que completam o fechamento (inventário → contrato)

`refresh_completion_marker(competence_id)` invocado **dentro da tx** de: `submit_package`, `review/accept` de validação, resolução de clarification, `confirm` P3, `create_complement`, `reopen_version` (reavalia), `apply` do sync (safety net). Regra: recomputa `derive_closing_state` sob `FOR UPDATE` da competência; se `COMPLETED ∧ first_completed_at IS NULL` → `SET first_completed_at=now(), completion_record='COMPLETED', completion_basis='MARKER'` + audit `MONTHLY_CLOSING_COMPLETED` (write-once, idempotente).

### 6.3 Backfill `completion_record` (V033)

`derive_atual=COMPLETED` → `COMPLETED(MARKER)`; evidência positiva reconstruível (pacote `FINALIZED`/`SUBMITTED` histórico + trilha) → `COMPLETED(BACKFILL)`; evidência negativa comprovável (zero pacote/decisão/documento/mensagem) → `NEVER`; **todo o resto → `UNEVALUATED`** (bloqueado; reconciliação via `completion-assessment`, manage+reason+audit). `NULL` nunca é prova. Read-back: amostra + contadores por classe; rollback = re-avaliação. PROD tem zero competências — janela teórica, mas o contrato não presume.

### 6.4 Testes preparados (§11)

Falha transacional, reabertura idempotente, complemento, rejeição terminal, conclusão concorrente, exclusão+recriação (UUID novo+NEVER), histórico indeterminado bloqueado — todos `TEST_NOT_RUN`.

---

## 7. G2-D — Sincronização automática

Forma canônica **PROVEN** (doc 174 §4.1): outbox na tx de `apply_revision` → poller `run_checklist_sync_dispatch_loop` no lifespan (flag `CF_CHECKLIST_SYNC_DISPATCH_ENABLED`, `to_thread`, SKIP LOCKED) → reconciliação idempotente por competência.

### 7.1 Elegibilidade (predicado congelado — doc 174 §2.3)

```text
syncable(c) ⇔ c.status='OPEN' ∧ c.first_completed_at IS NULL
  ∧ c.completion_record='NEVER'
  ∧ derive_closing_state(c.period).state='PENDING'
  ∧ business_guards_pass(c)
```

Reavaliado na tx do run, sob `FOR UPDATE` na competência; `UNEVALUATED`/`COMPLETED`/desconhecido → `SKIPPED`/`FAILED` (fail-closed).

### 7.2 Fluxo do evento

`apply_revision` commita `checklist_version_revision` + `checklist_sync_event(EMITTED)` na mesma tx → dispatcher claim (`FOR UPDATE SKIP LOCKED`) → para cada competência candidata (`OPEN`): upsert `checklist_sync_run(revision_id, competence_id)` (UNIQUE = idempotência) → `reconcile_competence` → `state` final + `exclusions[]` → evento `DISPATCHED`; exceção → `FAILED` + `attempts++` + `last_error` → retry com backoff; `attempts ≥ max` → `FAILED` permanente (dead-letter observável).

**Coalescência por reconciliação:** o evento é gatilho; o run recomputa `diff(snapshot, winner_vigente)` ao vivo — ordem de eventos é irrelevante; evento duplicado/atrasado converge para o mesmo estado.

### 7.3 `reconcile_competence` (transação por competência)

lock `monthly_competence FOR UPDATE` → predicado §7.1 → winner vigente → diff por `item_key`:

| Diff | Ação |
|---|---|
| novo `item_key` aplicável | `INSERT competence_checklist_item` (proveniência `source_template_item_id`/`source_version_id`, `state='EXPECTED'`) |
| descritivo alterado, item `EXPECTED` sem decisão | UPDATE de campos descritivos apenas |
| item retirado (`item_state='RETIRED'`) | `state='CANCELLED'`+`cancel_origin='CATALOG_RETIRE'`+`cancelled_revision_id`; correções `PENDING` do item → `CLOSED_REQUIREMENT_RETIRED`+`closure_*`+audit; pendências abertas do item → `DISMISSED`+`catalog_retire` |
| reativado | restore `CANCELLED→EXPECTED` **somente** se `cancel_origin='CATALOG_RETIRE'`; nunca `MANUAL`/`NULL` (`unknown_cancel_origin`) |
| item `ACCEPTED`/`NOT_APPLICABLE`/em pacote submetido/bloqueado | `exclusions[]` com reason tipado — nunca revertido |

Audit por mutação + `closing_audit_event` agregado com `revision_id`. Read-back: reconverge o diff (esperado vazio) — sucesso = **pós-condições verificadas**, não "transação commitada".

### 7.4 Locks e concorrência (ordem fixa)

`checklist_template` → `checklist_template_version` → `checklist_version_revision` → `checklist_template_item` — depois, por competência: `monthly_competence` → `competence_checklist_item` → `item_correction`/`closing_pendency` → `closing_document`/`document_version` — outbox por último. Edição de catálogo trava o template primeiro (serializada com `open_competence` — mesmo lock); sync nunca trava o catálogo (lê snapshot vigente). Deadlock potencial: sync×upload/validação na mesma competência → mitigação = lock único `FOR UPDATE` na competência antes de qualquer filho (todos os writers já o tomam) + `SKIP LOCKED` no claim de runs.

### 7.5 Critério de sucesso

`EMITTED` ≠ `DISPATCHED` ≠ run `APPLIED` ≠ convergência. Sucesso funcional = todo run `APPLIED|APPLIED_WITH_EXCLUSIONS|SKIPPED` com read-back do diff vazio; agregado da revisão expõe contagens por estado; `FAILED|PARTIAL` bloqueia o selo "sincronizado" na UI/CLARA.

### 7.6 `GET …/sync-status`

`{state, revision_applied, pending_events, runs:{applied,applied_with_exclusions,skipped,failed,partial}, exclusions[]}` — derivado de `checklist_sync_run`+eventos pendentes.

---

## 8. G2-E — CLARA

Nenhuma regra paralela: tools em `interface/mcp/tool_bridge.py` chamam os mesmos use cases (paridade classe A/B já existente).

| Capability existente (tool_bridge) | Contrato novo/mantido | AuthZ | Observação |
|---|---|---|---|
| `tool_get_competence_state`, `tool_get_checklist_items` | mantido — DTO ganha `sync_status`, `completion_record` | access | leitura |
| `tool_list_documents`, `tool_list_pendencies` | mantido | access | reflete item `CANCELLED` por retirada |
| `ClaraGovernedWrites` (correções, validação) | mantido — lê `CLOSED_REQUIREMENT_RETIRED` como encerramento administrativo | access/escopo | `_correction_state` precisa mapear o novo estado (§4.5) |
| `ClaraBatchOrchestrator` | EXTEND — batch de exigências passa a gravar revisão | manage | reaproveita orquestração existente |
| **start_checklist_sequence** | **capability nova — não criada neste gate** | manage | `DECISION_REQUIRED`: expor à CLARA (PREPARE/ACT) ou manter Portal-only? Recomendação: **Portal-only** no MVP — operação excepcional sem ganho em chat |

Apresentação de `CLOSED_REQUIREMENT_RETIRED` em `operation_presentation`/`_correction_state`/"manifesto de exclusão" (`competence_deletion`): classificar como `closed_administrative`, nunca `rejected` — atualização no mesmo gate de implementação.

---

## 9. G2-F — UX/cards (contratos para implementação)

Doc 175 vigente + mapeamento `Banco→BFF→DTO→API→Componente`:

| Tela/card | Dados novos | Endpoint |
|---|---|---|
| Admin V1 publicada — painel "Revisões" | lista `revisions` (nº, autor, data, fingerprint, nº changes, status sync) | `GET …/revisions` |
| Editor de catálogo | form ADD/UPDATE/RETIRE/REORDER/REACTIVATE → revisão em lote + `impact-preview` antes de confirmar | `POST …/impact-preview`, `POST …/revisions` |
| Histórico de exigências retiradas | itens `item_state='RETIRED'` + revisão de origem | `GET …/versions/{id}` (incluir `retired:true` no DTO) |
| Card do documento no fechamento | `sync_status`, item `CANCELLED`→"exigência retirada" com histórico clicável | `listCompetenceItems`+`sync-status` |
| Status de sync (admin) | agregado por revisão | `GET …/sync-runs` |
| Banner legado | competência `UNEVALUATED` → "em reconciliação histórica" | `listCompetences`/`getCompetence` |

Estados obrigatórios: loading/empty/error/**forbidden**/`sync parcial`/`sync_failed`; kit `@delpi/plugin-ui`; Help sincronizado (`feature-help-sync`); acessibilidade teclado/leitor para o painel de revisões e badges de estado.

---

## 10. G2-G — Plano excepcional da nova V1 (não executar)

1. **Inventário read-only** do ambiente-alvo: revalidar estado (V1 antiga `INACTIVE`, V2 `REVIEW` com 16 itens, competências, propostas CLARA) — dados históricos podem ter mudado.
2. **Manifesto dos 16 itens** (item_key→campos) + `fingerprint` sha256 — artefato versionado junto ao runbook.
3. **Dry-run** da sequência completa em cópia: `start_checklist_sequence` → V1 DRAFT → 16×ADD via revisão em lote → `effective_from_period='2026-01'` → `publish` → read-back → sync de candidatas (esperado: zero competências ou comportamento documentado).
4. **Exclusões governadas** só se o inventário confirmar necessidade (fluxo CF-UX-054 já existente).
5. **Execução** com `manage`+confirmação+motivo+idempotência; sem four-eyes (D4).
6. **Read-back + evidências**: série ativa=2, winner=V1(2,1), 16 itens ACTIVE, fingerprint confere, eventos de audit íntegros.
7. **Rollback/compensação**: reversão por revisão compensatória; série nunca é apagada — `CLOSED` por operação governada se abortada pré-publicação.
8. **Autorização separada futura** — este gate não executa.

---

## 11. Matriz mestra de testes (RQ-G2 / AC-G2) — todos `TEST_NOT_RUN`

| RQ | AC | Cenário | Existe? |
|---|---|---|---|
| RQ-G2-01 série | AC-G2-01 | nova série reinicia version em 1, `UNIQUE(series_id,version)`; série anterior `CLOSED` | novo |
| RQ-G2-02 série | AC-G2-02 | `start_sequence` idempotente por key; OCC; audit; sem four-eyes | novo |
| RQ-G2-03 revisão | AC-G2-03 | revisão em lote atômica — falha de 1 change → rollback total | novo |
| RQ-G2-04 revisão | AC-G2-04 | `expected_revision` stale → `stale_revision`; fingerprint do catálogo resultante | novo |
| RQ-G2-05 revisão | AC-G2-05 | reversão gera revisão compensatória; histórico reconstruível por replay | novo |
| RQ-G2-06 itens | AC-G2-06 | `item_key` imutável; RETIRE→mesma `item_id`; REACTIVATE só `CATALOG_RETIRE`; `MANUAL`/`NULL`→`unknown_cancel_origin` | novo |
| RQ-G2-07 abertura | AC-G2-07 | INSERT com `NEVER` explícito; retry não duplica (`UNIQUE(period)`); falha reverte tudo; read-back | ext. |
| RQ-G2-08 conclusão | AC-G2-08 | `refresh_completion_marker` write-once em cada writer; conclusão concorrente serializada | novo |
| RQ-G2-09 backfill | AC-G2-09 | 4 classes (MARKER/BACKFILL/NEVER/UNEVALUATED); NULL nunca vira NEVER | novo |
| RQ-G2-10 predicado | AC-G2-10 | `UNEVALUATED`/`COMPLETED`/desconhecido → bloqueado fail-closed | novo |
| RQ-G2-11 retirada | AC-G2-11 | correções `PENDING` do item →`CLOSED_REQUIREMENT_RETIRED`+`closure_*`; `REJECTED`/`APPROVED` intactos; pendências do item →`DISMISSED`+`catalog_retire`; alheias intactas | novo |
| RQ-G2-12 correção | AC-G2-12 | CHECK aceita 4 estados; rejeita desconhecido; CLARA/DTO apresentam como encerramento | novo |
| RQ-G2-13 reativação | AC-G2-13 | restore mesmo `snapshot_item_id`→`EXPECTED`; evidências visíveis, não auto-válidas (D8 conservador) | novo |
| RQ-G2-14 pacotes | AC-G2-14 | item em pacote submetido → `exclusions[item_locked_by_package]`, nunca revertido | novo |
| RQ-G2-15 outbox | AC-G2-15 | evento persiste restart; SKIP LOCKED multi-réplica; `FAILED`+retry+dead-letter | novo |
| RQ-G2-16 ordem | AC-G2-16 | eventos fora de ordem/duplicados → convergência por reconciliação | novo |
| RQ-G2-17 sync | AC-G2-17 | parcial→`APPLIED_WITH_EXCLUSIONS`/`PARTIAL` com exclusion reasons; `sync-status` agregado correto | novo |
| RQ-G2-18 CLARA | AC-G2-18 | paridade read/write; novo estado de correção apresentado corretamente; sem capability de start_sequence no MVP | novo |
| RQ-G2-19 authz | AC-G2-19 | `access` negado em rotas admin; `manage` exigido; escopo avaliado pelo Core | ext. |
| RQ-G2-20 UX | AC-G2-20 | estados loading/empty/error/forbidden/sync-parcial; teclado/leitor; Help | novo |
| RQ-G2-21 migração | AC-G2-21 | dry-run da V1 com 16 itens; fingerprint; read-back | novo (op.) |

Existentes aproveitáveis: `test_pg_checklist_version_delete`, `test_clara_parity_*`, testes de `open_competence`/documents/validations — estendidos, não reescritos.

---

## 12. Segurança

Backend autoridade: `effective capability (Core) ∧ escopo ∧ regra`; JWT contextualiza. `access`=operação; `manage`=admin (série, revisões, reconciliação). Fail-closed em elegibilidade/AuthZ. Toda escrita auditada com `reason`+ator+idempotência. Nenhum novo permission code. CLARA herda PREPARE/ACT do padrão governado onde aplicável.

## 13. Resíduos e decisões

- **D8 — validade temporal da evidência (PO, DECISION_REQUIRED):** contratado conservador — visível, não auto-válida; mecanismo de reaproveitamento não projetado.
- **start_sequence na CLARA:** recomendado Portal-only no MVP (§8) — confirmar com GPT Arquiteto.
- **Nº efetivo das migrations V031–V035:** reserva lógica; confirmar HEAD no Gate 2B.
- **Gate 2A aprovação:** pendente do GPT Arquiteto — este documento não se auto-aprova.
