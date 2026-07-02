# Playbook — Evolução do Cadastro de Kaizens

> **Arquivo:** `docs/12-roadmap-e-volucao/cadastro-kaizen/PLAYBOOK-EVOLUCAO-KAIZEN.md`
> **Status:** proposta de design — a implementar (Fases 6+ do [ROADMAP.md](./ROADMAP.md))
> **Produto:** Minha DELPI · módulo Qualidade
> **Escopo:** plugin `cadastro-kaizen` + rotas `api-delpi/quality/kaizens/*` + schema `quality`
> **Herda de:** `quality-action-plans` (PAC) e `transformometro-api` (revisões versionadas)
> **Atualizado:** 2026-07-02

---

## 1. Contexto e objetivo

O cadastro de kaizens hoje é um **CRUD plano**: uma tela de formulário (`KaizenFormPage`) que sobrescreve o registro a cada `PUT`, sem histórico, sem anexos e sem modo de visualização. Isso limita:

- **Rastreabilidade** — não há trilha de «o que mudou, quando e por quem».
- **Análise retrospectiva** — status/economia sobrescritos invalidam o passado (ver [ESPECIFICACAO-REVISOES.md](./ESPECIFICACAO-REVISOES.md)).
- **Riqueza documental** — kaizen é uma melhoria de processo; falta descrição do processo, evidências (antes/depois), participantes e contexto.
- **Experiência** — não existe o padrão maduro «ficha visual + edição por seção» que o PAC já entrega.

**Objetivo do playbook:** elevar o `cadastro-kaizen` ao mesmo patamar de maturidade do PAC, reaproveitando padrões canônicos já existentes no monorepo, sem reinventar arquitetura:

| Necessidade do usuário | Padrão-fonte | Entrega |
|---|---|---|
| Versões e melhorias («como transformômetro») | `transformometro` (revisões versionadas + `cenario_tipo`) + spec de revisões | Revisões com número, tipo de mudança e vigência |
| Estágios | **já temos** `status` | Pipeline visual de status (read) |
| Evidências do processo | PAC `quality_problem_evidences` + volume persistente | `quality.kaizen_evidences` + upload/preview |
| Mais informações (descrição, +1 responsável) | — | Novos campos + tabela de participantes |
| Modo visual + edição | PAC `PlanDetailPage` + `EditableSectionCard` | `KaizenDetailPage` read-only + edição por seção |

---

## 2. Princípios (não violar)

1. **Reaproveitar, não recriar.** Copiar os padrões do PAC (`EditableSectionCard`, `usePlanSectionEdit`, dirty state, `EvidencePanel`, revisões JSONB) e a semântica de versão do transformômetro. Nada de componente/serviço novo quando já existe canônico.
2. **Thin client.** Cálculo de economia, criação de revisão e validação ficam na `api-delpi`; o MFE orquestra ficha, seções e upload.
3. **Schema `quality` único.** Evidências, revisões, participantes e histórico do kaizen estendem o mesmo schema `quality` (onde já vive `quality.kaizens` e o PAC referencia via `linked_kaizen_id`).
4. **Storage persistente obrigatório.** Todo upload segue `persistent-upload-storage.mdc`: metadado no Postgres + binário em volume montado (**nunca** `/tmp` ou filesystem efêmero).
5. **Envelope canônico.** Toda rota nova usa `api_delpi_success(..., operation_id=...)`, entra no `route_contract_registry` e segue `new-api-route-checklist.mdc`.
6. **Textos/regex/limites em JSON** quando o consumidor for o chat/API de IA (`assistant-content-json.mdc`); no MFE, textos PT-BR ficam nos componentes/constantes do plugin.
7. **Append-only para histórico.** Revisões e auditoria não são editadas nem apagadas; correção = nova revisão.
8. **Concorrência otimista.** `PUT`/`PATCH` enviam `expected_revision_number`; API responde **409** em divergência (padrão PAC `withExpectedPlanRevision`).
9. **Validade da economia = 1 ano.** Um kaizen contabiliza ganhos financeiros por **1 ano a partir da data de implantação**; a partir do aniversário deixa de somar no run-rate (permanece no histórico). Regra pura e única em `kaizen_savings_validity` (`savings_valid_until`, `is_savings_active`, `active_days_in_range`), consumida tanto pela consolidação de ganhos quanto pelo cadastro (expõe `savings_valid_until` / `savings_active`). **Nunca** duplicar a janela de 365 dias em `if` de consolidação, presenter ou MFE.
10. **Melhoria = revisão (V033).** Lançar uma melhoria num kaizen implantado **não** cria outro kaizen: cria uma nova revisão (`change_type='melhoria'`) com economia (`daily_savings`/`annual_savings`), vigência e **evidências próprias** (`kaizen_evidences.revision_id`). Cada melhoria tem **seu próprio aniversário de 1 ano** a partir de `effective_from`. O **ganho por período** é a soma das melhorias vigentes no intervalo, com cap de 1 ano por segmento — regra pura e única em `kaizen_savings_timeline` (`period_savings`, `current_active_savings`), exposta em `GET /savings-timeline`. **Nunca** recalcular ganho por período no MFE nem duplicar o cap.
11. **Registro de alterações = 3 camadas (padrão PAC).** Auditoria do kaizen como um todo: `kaizen_revisions` (versões/diffs restauráveis-ready), `kaizen_history` (linha do tempo operacional de eventos) e `kaizen_audit_log` (governança **append-only**, trigger bloqueia UPDATE/DELETE). Gravadas na mesma transação da mutação em `create/update/delete_record`. **Nunca** editar/apagar auditoria; correção = nova revisão/evento.

---

## 3. Modelo conceitual

```text
kaizen (identidade estável — quality.kaizens)
├── status .......... ESTÁGIO operacional (em_andamento → implantado → descontinuado | cancelado)
├── melhorias/revisões  VERSÕES / melhorias no tempo (quality.kaizen_revisions)   ← "ideia do transformômetro"
│     ├── revision_number (1, 2, 3…) + change_type (implantacao | melhoria | correcao | descontinuacao)
│     ├── vigência (effective_from / effective_until) + aniversário próprio (1 ano)
│     ├── economia própria (daily_savings / annual_savings) + evidências (revision_id)
│     └── snapshot (JSONB dos campos de negócio)
├── participantes ... 1..N responsáveis (quality.kaizen_participants)
├── evidências ...... anexos do processo, incl. ANTES/DEPOIS — gerais ou por melhoria (quality.kaizen_evidences + volume)
└── registro de alterações  timeline (kaizen_history) + versões (kaizen_revisions) + governança append-only (kaizen_audit_log)
```

**Distinção explícita (pedido do usuário):**

- **Estágio = `status`.** Não vira revisão nova por si só, mas *mudança de status* dispara uma revisão (registra a data em que o estágio mudou).
- **Revisão = versão/melhoria.** Igual ao transformômetro: cada evolução relevante do kaizen (nova economia, correção de dados, melhoria incremental do processo) cria uma revisão numerada com tipo e vigência. Permite responder «quanto essa melhoria rendia em mar/2026» e «qual foi a v2 do kaizen».

---

## 4. Eixos de melhoria

### Eixo A — Modo visual + edição por seção

**Padrão-fonte:** `plugins/quality-action-plans/src/pages/PlanDetailPage.tsx`, `hooks/usePlanSectionEdit.ts`, `components/ui/EditableSectionCard.tsx`, `utils/planDetailDirtyState.ts`.

**Hoje no kaizen:** rotas `list` / `novo` / `editar/{id}`; `KaizenFormPage` sempre em formulário (`mode: "new" | "edit"`).

**Proposta:**

- Nova rota `detalhe/{id}` → `KaizenDetailPage` (**read-only por padrão**, edição inline por seção).
- Manter `novo` → `KaizenFormPage` (criação continua formulário completo).
- `editar/{id}` legado passa a **redirecionar** para `detalhe/{id}` (edição agora é por seção).

Componentes a portar (equivalentes `kz-`):

| PAC | Kaizen (novo) |
|---|---|
| `EditableSectionCard` | `KzEditableSectionCard` (ou copiar UI para `components/ui/`) |
| `usePlanSectionEdit` | `useKaizenSectionEdit` |
| `PlanDetailReadViews` (`*ReadContent`) | `KaizenReadViews` (`KaizenIdentificationReadContent`, `KaizenSavingsReadContent`, …) |
| `planDetailDirtyState` + `PlanGlobalSaveBar` | `kaizenDetailDirtyState` + `KaizenGlobalSaveBar` |
| `SectionCard`, `ReadOnlyField`, `ReadOnlyGrid` | mesmos, prefixo `kz-` |

Seções da ficha do kaizen (modo read → edit):

1. **Identificação** — filial, título, setor, participantes, descrição do processo, datas.
2. **Estágio** — `StatusPipeline` visual + campo status na edição.
3. **Economia** — tipo, parâmetros, `daily_savings`/`annual_savings` calculados (read-only, vêm da API).
4. **Evidências do processo** — `KaizenEvidencePanel` (Eixo D).
5. **Revisões** — timeline de versões (Eixo B).
6. **Histórico / auditoria** — timeline operacional + log de governança.

CSS: reutilizar padrão `.kz-section-read` / `.kz-section-edit` dentro de `kz-card`, alinhado a `plugins-visual-design-system.mdc` (tokens do portal, dark mode, responsivo ≤768px).

---

### Eixo B — Revisões / versões (semântica do transformômetro)

**Padrões-fonte:**
- Transformômetro: `revisoes` com `versao_revisao`, `cenario_tipo` (`baseline`/`melhoria`/`automacao`/`correcao`), vigência mensal, flag `revisao_ativa`.
- PAC: `quality.quality_action_plan_revisions` com `snapshot` JSONB, `change_scope`, `expected_revision_number` (lock otimista), restore.
- Kaizen: [ESPECIFICACAO-REVISOES.md](./ESPECIFICACAO-REVISOES.md) já define vigência temporal (`effective_from`/`effective_until`) para o cálculo do dashboard.

**Reconciliação (proposta unificada):** uma única tabela `quality.kaizen_revisions` que combina os três: snapshot completo (para analytics temporal do dashboard) **+** tipo de mudança semântico (para a leitura «v1 baseline, v2 melhoria»).

```sql
-- Migration proposta: V028__create_kaizen_revisions.sql
CREATE TABLE quality.kaizen_revisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kaizen_id UUID NOT NULL REFERENCES quality.kaizens(id),
    revision_number INT NOT NULL,

    -- Semântica de versão (inspirada no transformômetro)
    change_type VARCHAR(30) NOT NULL DEFAULT 'melhoria',
    change_summary VARCHAR(500),      -- ex.: "status: em_andamento → implantado"
    change_reason  TEXT,              -- justificativa livre

    -- Vigência temporal (ver ESPECIFICACAO-REVISOES.md)
    effective_from DATE NOT NULL,
    effective_until DATE,             -- NULL = revisão corrente

    -- Snapshot completo dos campos de negócio (JSONB, padrão PAC)
    snapshot JSONB NOT NULL,
    snapshot_schema_version INT NOT NULL DEFAULT 1,

    created_by_user_id VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_kaizen_revision_number UNIQUE (kaizen_id, revision_number),
    CONSTRAINT ck_kaizen_revision_change_type CHECK (
        change_type IN ('implantacao','melhoria','correcao','descontinuacao','baseline','restauracao')
    ),
    CONSTRAINT ck_kaizen_revision_dates CHECK (
        effective_until IS NULL OR effective_until >= effective_from
    )
);

CREATE INDEX ix_kaizen_revisions_kaizen_effective
    ON quality.kaizen_revisions (kaizen_id, effective_from, effective_until);

ALTER TABLE quality.kaizens
    ADD COLUMN current_revision_number INT NOT NULL DEFAULT 0;
```

> **Decisão de projeto:** snapshot JSONB (PAC) em vez de replicar cada coluna (spec original § 4.2). Vantagem: schema estável mesmo ao adicionar campos (descrição, participantes); o cálculo temporal lê do JSONB. Custo: cálculo do dashboard extrai campos do JSON — aceitável e cacheável.

**Quando cria revisão** (conjunto `REVISION_TRIGGER_FIELDS`): `status`, datas, `savings_type` e todos os parâmetros de economia, `branch_code`, `title`. Campos cosméticos (`notes`) atualizam só a cabeça. Regras completas na spec § 5.

**Tipo de mudança automático** (sugestão de heurística no `KaizenRevisionService`):
- status → `implantado`: `implantacao`
- status → `descontinuado`: `descontinuacao`
- só campos de economia mudaram: `melhoria` (ou `correcao` se usuário marcar «correção retroativa»)
- criação: revisão 1 = `baseline` (ou `implantacao` se já nasce implantado)

**API (novas rotas):**

| Método | Rota | operationId | shape |
|---|---|---|---|
| GET | `/quality/kaizens/records/{id}/revisions` | `list_kaizen_revisions` | `paged_list` |
| GET | `/quality/kaizens/records/{id}/revisions/{n}` | `get_kaizen_revision` | `scalar` |
| GET | `/quality/kaizens/records/{id}/at?date=YYYY-MM-DD` | `get_kaizen_at_date` | `scalar` |

**Frontend:** `KaizenRevisionTimeline` (lista versões, badge de `change_type`, diff vs. estado atual — padrão `planRevisionDiff.ts`). Campo **«Vigente a partir de»** no modo edição quando status/economia mudam.

---

### Eixo C — Estágios (status) visual

**Padrão-fonte:** `StatusPipeline` do PAC (`PlanStatusReadContent`).

Status já existe (`em_andamento`, `implantado`, `descontinuado`, `cancelado`). Melhoria = **representação visual**:

- Modo read: pipeline horizontal com o estágio atual destacado; `descontinuado`/`cancelado` como estados terminais.
- Modo edit: `select` de status + campo de data/vigência que alimenta a revisão (Eixo B).
- Cores por estágio via tokens semânticos do portal (`success`/`warning`/`danger`).

Sem mudança de schema — só UI + o vínculo com revisão.

---

### Eixo D — Evidências do processo

**Padrão-fonte:** PAC — `quality.quality_problem_evidences`, `PacEvidenceStorage`, `EvidencePanel`/`EvidenceAttachForm`/`EvidenceListTable`, rotas `/quality/action-plans/{id}/evidences*`, volume `${DELPI_DATA_HOST_DIR}/pac-evidences`.

```sql
-- Migration proposta: V029__create_kaizen_evidences.sql
CREATE TABLE quality.kaizen_evidences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kaizen_id UUID NOT NULL REFERENCES quality.kaizens(id),
    type VARCHAR(30) NOT NULL DEFAULT 'attachment',   -- attachment | photo | document | link
    stage VARCHAR(20) NOT NULL DEFAULT 'geral',       -- antes | depois | geral  ← "antes/depois"
    file_name VARCHAR(500),
    stored_name VARCHAR(200),
    mime_type VARCHAR(150),
    size_bytes BIGINT,
    description TEXT,
    external_url VARCHAR(1000),                        -- para type = link
    uploaded_by_user_id VARCHAR(100) NOT NULL,
    uploaded_by_name VARCHAR(200),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX ix_kaizen_evidences_kaizen ON quality.kaizen_evidences (kaizen_id) WHERE deleted_at IS NULL;
```

**Storage (persistent-upload-storage.mdc — obrigatório):**

| Item | Valor |
|---|---|
| Env var | `KAIZEN_EVIDENCE_UPLOAD_DIR` (default `/app/data/kaizen-evidences`) |
| Config | `api-delpi/app/config.py` |
| Volume (prod **e** dev) | `${DELPI_DATA_HOST_DIR:-/var/lib/delpi}/kaizen-evidences:/app/data/kaizen-evidences` |
| Doc | `infra/README-ambiente.md` + `env.local.example` |
| Homologação | recreate do serviço → arquivo persiste no host |

**API (novas rotas — espelham PAC):**

| Método | Rota | operationId |
|---|---|---|
| GET | `/quality/kaizens/records/{id}/evidences` | `list_kaizen_evidences` |
| POST | `/quality/kaizens/records/{id}/evidences` (multipart) | `attach_kaizen_evidence` |
| GET | `/quality/kaizens/records/{id}/evidences/{ev}/file` | `download_kaizen_evidence` |
| PATCH | `/quality/kaizens/records/{id}/evidences/{ev}` | `update_kaizen_evidence` |
| DELETE | `/quality/kaizens/records/{id}/evidences/{ev}` | `delete_kaizen_evidence` |

**Frontend:** `KaizenEvidencePanel` (copiar `EvidencePanel` do PAC), com destaque para o par **Antes / Depois** (galeria lado a lado) — que é o registro visual mais valioso de um kaizen. `readOnly` no modo visual, editável quando a seção entra em edição.

---

### Eixo E — Mais informações (descrição, múltiplos responsáveis)

Pedido explícito do usuário: **campo de descrição do processo** e **mais de um responsável**.

```sql
-- Migration proposta: V030__extend_kaizens_richer_fields.sql
ALTER TABLE quality.kaizens
    ADD COLUMN process_description TEXT,        -- descrição do processo / situação
    ADD COLUMN problem_description TEXT,        -- problema/oportunidade (opcional)
    ADD COLUMN improvement_description TEXT,    -- o que foi feito (o "kaizen")
    ADD COLUMN category VARCHAR(50),            -- tema/categoria (ver Eixo F)
    ADD COLUMN expected_result TEXT;            -- resultado esperado (qualitativo)

-- Múltiplos responsáveis (mantém `accountable` legado como responsável principal / cache)
CREATE TABLE quality.kaizen_participants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kaizen_id UUID NOT NULL REFERENCES quality.kaizens(id),
    name VARCHAR(200) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'participante',  -- responsavel | participante | apoio
    user_id VARCHAR(100),                               -- se vier do diretório/Keycloak
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_kaizen_participant_role CHECK (role IN ('responsavel','participante','apoio'))
);
CREATE INDEX ix_kaizen_participants_kaizen ON quality.kaizen_participants (kaizen_id);
```

Notas de compatibilidade:
- `accountable` (coluna atual) é mantida como **responsável principal** (espelho do primeiro `role = 'responsavel'`) para não quebrar dashboard/Sheets e import.
- Frontend: campo de participantes vira lista dinâmica (add/remove), com um marcado como principal. Tipos TS estendidos em `types/kaizen.ts` (`participants: KaizenParticipant[]`).
- Descrições entram na seção **Identificação** (modo read = texto formatado; edit = `textarea`).

---

## 5. Eixo F — Sugestões adicionais (backlog priorizável)

Além do pedido, sugiro (ordenar com o negócio):

| # | Sugestão | Fonte / padrão | Valor |
|---|---|---|---|
| F1 | **Antes/Depois** como seção de 1ª classe (galeria) | Eixo D `stage` | Comunicação visual do ganho |
| F2 | **Categoria/tema + tags** (ergonomia, segurança, custo, qualidade, 5S…) | novo `category` + tabela tags | Filtro e análise por tema |
| F3 | **Vínculo com PAC** (mostrar plano de ação que originou o kaizen) | `quality_action_plans.linked_kaizen_id` (V012 já existe) | Rastreabilidade problema→melhoria |
| F4 | **Checklist de implantação** (mini-ações do kaizen) | PAC `quality_actions` | Acompanhar execução |
| F5 | **Resultado real vs. estimado** (`realized_savings`) | novo campo + revisão | Medir efetividade, não só estimativa |
| F6 | **Matriz esforço × impacto** (priorização) | novos campos `effort`, `impact` | Priorização visual no dashboard |
| F7 | **Workflow de validação leve** (submeter → aprovar kaizen) | PAC `effectiveness_approval_status` | Governança sem burocratizar |
| F8 | **Autoria / reconhecimento** (quem sugeriu) + adesão por filial/setor | novo `suggested_by` + dashboard | Cultura de melhoria contínua |
| F9 | **Duplicar kaizen para outra filial** | transformômetro «duplicar instância» | Replicar boas práticas |
| F10 | **Export ficha A3 / one-pager PDF** | PAC export 8D | Compartilhar/imprimir o kaizen |
| F11 | **Auditoria de governança append-only** | PAC `quality_audit_log` (V008) | Trilha imutável de eventos sensíveis |
| F12 | **Comentários/discussão** no kaizen | — | Colaboração |
| F13 | **Integração agente/chat** (Fase 8 do roadmap) | `openapi_agent_metadata` + actions | «quantos kaizens implantados na filial 01 este mês?» |
| F14 | **Notificações** (kaizen implantado, revisão criada) | dispatch padrão PAC | Engajamento |

> **Recomendação de priorização:** F1, F3, F5 e F11 têm o melhor custo/benefício e reaproveitam padrões prontos. F7/F13 dependem de decisão de negócio (há aprovação formal de kaizen hoje?).

---

## 6. Impacto por camada (resumo de implementação)

### api-delpi

- **Migrations** (`migrations/plugins/quality/`): `V028` revisões, `V029` evidências, `V030` campos ricos + participantes.
- **Config:** `KAIZEN_EVIDENCE_UPLOAD_DIR` em `config.py`.
- **Domain:** `KaizenRevisionService` (diff → revisão → sync cabeça), `KaizenRevisionSnapshotService`, `KaizenEvidenceStorage` (copiar `PacEvidenceStorage`), extensão do `KaizenSavingsCalculator` para `realized_savings` (F5).
- **Repositories:** `KaizenRevisionRepository`, `KaizenEvidenceRepository`, `KaizenParticipantRepository`.
- **Router:** estender `kaizen_records_router.py` com `/revisions*`, `/evidences*`, `/at`; body do `POST`/`PUT` ganha `process_description`, `participants[]`, `effective_from`, `change_reason`, `expected_revision_number`.
- **Contratos:** registrar operationIds em `route_contract_registry.py` + `openapi_agent_metadata.py` (rotas chat-critical).
- **Testes:** `test_kaizen_revision_service`, fixtures `kaizen_revision_regression_cases.py`, smoke meta das novas rotas, teste de storage persistente.

### infra

- Volume `kaizen-evidences` nos **dois** composes (`docker-compose.yml` + `docker-compose.dev.yml`) + `env.local.example` + `infra/README-ambiente.md`.

### plugins/cadastro-kaizen (MFE)

- **Páginas:** nova `KaizenDetailPage` (read/edit por seção); `KaizenFormPage` só criação; `parseRoute` ganha `detalhe/{id}`.
- **Componentes:** `components/ui/` (`KzEditableSectionCard`, `SectionCard`, `ReadOnlyField`), `components/evidence/` (`KaizenEvidencePanel` + upload/preview), `KaizenRevisionTimeline`, `StatusPipeline`, `KaizenParticipantsField`.
- **Hooks/utils:** `useKaizenSectionEdit`, `kaizenDetailDirtyState`, `withExpectedRevision`.
- **Tipos/API:** estender `types/kaizen.ts` e `api/kaizenApi.ts` (revisions, evidences, participants).
- **CSS:** manter raiz `.dashboard-cadastro-kaizen` + prefixo `kz-`; adicionar `.kz-section-read/edit`, galeria antes/depois, pipeline. Validar dark mode + mobile (`plugins-visual-design-system.mdc`).
- **Build:** `npm run build` verde antes de entregar (`plugins-frontend-build.mdc`).

### Regras a observar

`clean-architecture-chat-api.mdc` (domain sem infra), `new-api-route-checklist.mdc` (rotas + registry + perfil + gates), `persistent-upload-storage.mdc` (volume), `schema-first-presentation-delivered.mdc` (se expor ao chat), `assistant-content-json.mdc` (textos/limites do lado IA), `test-and-commit.mdc`.

---

## 7. Fases de entrega (incremental)

Desdobra a Fase 6 do [ROADMAP.md](./ROADMAP.md) e adiciona 6f–6h. **Não** exige que tudo saia junto; cada fase é entregável e testável.

```text
Fase 6a — Revisões: schema V028 + KaizenRevisionService + API /revisions + backfill rev.1   ★ base
Fase 6b — Cálculo temporal (KaizenTemporalSavingsCalculator) + fixtures                       (ver spec)
Fase 6c — Summary → Postgres lendo revisões (feature flag KAIZEN_SUMMARY_SOURCE)              (ver spec)
Fase 6d — Modo visual + edição por seção (KaizenDetailPage) + StatusPipeline                  ← Eixo A/C
Fase 6e — Campos ricos: descrição do processo + múltiplos responsáveis (V030)                 ← Eixo E
Fase 6f — Evidências do processo + Antes/Depois (V029 + volume + KaizenEvidencePanel)          ← Eixo D
Fase 6g — Timeline de revisões (UI) + diff + "vigente a partir de"                            ← Eixo B (UI)
Fase 6h — Extras priorizados (F1/F3/F5/F11…) conforme decisão de negócio                       ← Eixo F
```

**Ordem recomendada de execução:** 6a → 6e → 6d → 6f → 6g (entrega valor visível cedo com modo visual + campos ricos), deixando 6b/6c (analytics temporal) para quando o dashboard for migrar do Sheets.

---

## 8. Riscos e decisões em aberto

| # | Questão | Recomendação |
|---|---|---|
| 1 | Snapshot JSONB vs. colunas na revisão | **JSONB** (PAC) — schema estável ao crescer campos |
| 2 | Editar `editar/{id}` legado | Redirecionar para `detalhe/{id}`; edição por seção |
| 3 | `accountable` vs. tabela de participantes | Manter `accountable` como principal (compat Sheets/dashboard/import) |
| 4 | Kaizen tem aprovação formal hoje? (F7) | Confirmar com qualidade antes de implementar workflow |
| 5 | Import da planilha cria participantes/evidências? | Não — import gera revisão 1 e campos básicos; enriquecimento é manual |
| 6 | Retenção de revisões | Seguir PAC (≈50 por registro) ou sem limite inicial — decidir com volume |
| 7 | Antes/Depois é obrigatório em `implantado`? | Sugerir (não bloquear) — evita fricção |

---

## 9. Referências

| Documento / código | Uso |
|---|---|
| [ROADMAP.md](./ROADMAP.md) · [status-atual.md](./status-atual.md) | Fases e estado |
| [ESPECIFICACAO-REVISOES.md](./ESPECIFICACAO-REVISOES.md) | Revisões temporais (cálculo dashboard) |
| `plugins/quality-action-plans/src/pages/PlanDetailPage.tsx` | Modo visual + edição por seção |
| `plugins/quality-action-plans/src/components/ui/EditableSectionCard.tsx` · `hooks/usePlanSectionEdit.ts` | Edição por seção |
| `plugins/quality-action-plans/src/components/evidence/` | Padrão de evidências (UI) |
| `api-delpi/app/application/services/quality_action_plans/pac_evidence_storage.py` | Storage persistente |
| `api-delpi/migrations/plugins/quality-action-plans/V027__pac_plan_revisions.sql` | Revisões JSONB + lock otimista |
| `transformometro-api/migrations/` · `docs/12-roadmap-e-evolucao/transformometro-app/PLAYBOOK-MODELAGEM.md` | Revisões versionadas + `cenario_tipo` + vigência |
| `api-delpi/migrations/plugins/quality/V027__create_kaizens.sql` | Schema atual do kaizen |
| `.cursor/rules/persistent-upload-storage.mdc` · `new-api-route-checklist.mdc` | Guardrails obrigatórios |

---

## 10. Próxima ação recomendada

1. **Validar com o negócio** os itens em aberto (§ 8): aprovação formal (F7), obrigatoriedade de Antes/Depois, campos de participante.
2. **Fase 6a + 6e** como primeiro incremento técnico (revisões + campos ricos) — base para tudo.
3. **Fase 6d/6f** (modo visual + evidências) para valor visível ao usuário.

> Este playbook é proposta de design. Nenhuma migration/código foi implementado ainda — cada fase deve seguir o checklist da regra correspondente antes do merge.
