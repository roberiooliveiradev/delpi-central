# ENGINEERING.LMP.G1 — Domain Ownership, Facts Contract & Unified Access

**Data:** 2026-10-28
**Baseline Git:** `BASE_HEAD = 0e39cbc9a8c98ce30959c42ef243634149b9bd57` (`HEAD = origin/main`; doc 32 `90b6e8abf9` ancestral)
**Referência obrigatória:** `32-engineering-lmp-g0-inventory-consumers-migration.md` — revalidado nesta missão
**Natureza:** desenho de arquitetura e contratos — **nenhuma alteração funcional**

---

## 0. Resumo executivo

Esta missão converte o inventário G0 em decisões de arquitetura implementáveis:

- **Ownership:** das 33 regras catalogadas, **19 migram para engineering-api** (domínio), **9 permanecem na api-delpi** (integração de fonte), **3 são CROSS_DOMAIN** (metas/IDD = SI; auditoria de ator = plataforma), **2 são PRESENTATION** (cache de dashboard = decisão de implementação, não regra).
- **Facts contract:** api-delpi já possui a fronteira natural — `get_lmp_dashboard_summary_facts` (fatos por OV, sem KPI) + `get_lmp_pi_counts_by_ovs` (lote PI por (branch, sale_number, revision)). Propõe-se **1 contrato facts de leitura** (`GET /engineering/lmps/facts`) + **facts de histórico** e **facts de detalhe**, sem computar `status`/`nivel`/`data_limite`/`percent_dentro_prazo` — essas derivações passam a ser de Engenharia.
- **Interservice auth:** o mecanismo aprovado da plataforma já existe — **S2S JWT Keycloak client-credentials** (`delpi_auth.service_token_validator`: `azp`/`client_id` allowlist + escopos obrigatórios + audience dedicada) para chamadas técnicas, e **Bearer humano delegado** para dados personalizados. O legado `X-Delpi-Service-Token` (segredo compartilhado) existe como sinal de composição, não como autoridade — e a api-delpi **rejeita** identidade de máquina em superfícies de dados de usuário (`auth_middleware.py:84-91`).
- **SI:** estratégia **C → A** formalizada com contrato *realized-only* (`GET /v1/lmps/summary`) — engineering-api nunca consulta SI dentro desse contrato; SI continua owner de metas/IDD/scores.
- **NC:** subdomínio operacional com trilha própria. Recomendação: **opção B** (persistência migra com o owner — schema `engineering.lmp_nonconformities` passa a ser gerido por engineering-api) após decisão formal de dados; opção A (api-delpi como store transitório) é o fallback incremental. Achado `api-delpi.access→NC write`: transição proposta com `engineering.access` + testes negativos, **sem correção silenciosa**.
- **Permissões:** `engineering.access` (operacional — já existente e enforceada) para todas as operações LMP incl. writes de NC; `engineering.manage` (**nova — a registrar no Core**) reservada a configuração/administração do Portal. Permissões legadas permanecem até cutover.

**Achado arquitetural adicional da G1:** a api-delpi já registra uso por `caller_app`+`route_path` (`caller_request_stats_service`, `app_usage_tracker` → Core app-usage). Isso fornece o **mecanismo concreto** para a janela de 30–60d de evidência de consumidores externos — sem depender de logs nginx crus.

---

## 1. Baseline, authorities e decisões da Coordenação

### 1.1 Reancoragem

```
HEAD        = 0e39cbc9a8c98ce30959c42ef243634149b9bd57
origin/main = 0e39cbc9a8c98ce30959c42ef243634149b9bd57
branch      = main
Últimos commits: 0e39cbc9a8 (delia task04 doc196), 90b6e8abf9 (doc 32),
77b1e808b0, 1f34403767, 68b10b81dd ...
Worktree: delia-api/app/application/capability_provision/orchestration.py (M),
delia-api/app/infrastructure/orchestration/langgraph_engine.py (M) —
trabalho concorrente, PRESERVADO intocado.
```

### 1.2 Authorities lidas

Regras always-on (centralized-rules-first, clean-code-architecture-guardrails, development-standards-index, evidence-driven-execution); docs 32 (obrigatório, revalidado), ARCHITECTURE.md, SCOPE-OWNERSHIP.md, 06-f1-g0-core-authz-contract, 12-f2a, 18–22, 31. Revalidação: nenhuma divergência material desde `90b6e8abf9` — código LMP/AuthZ/consumidores inalterado (`git diff 90b6e8abf9..HEAD` não tocou api-delpi/engineering-api/SI/plugins).

### 1.3 Decisões da Coordenação (baseline aprovada — vinculante)

| # | Decisão | Status neste doc |
|---|---|---|
| C-1 | engineering-api = owner-alvo das regras LMP | APROVADA — operacionalizada §2 |
| C-2 | api-delpi = integração de fonte (TOTVS, SQL, normalização técnica, paginação técnica, provenance) | APROVADA — contrato §3 |
| C-3 | `engineering.access` = operacional; `engineering.manage` = gerenciamento/configuração do Portal; não-implicação automática; Core = autoridade | APROVADA — modelo §6 |
| C-4 | NC = fluxo operacional de Engenharia; write ≠ admin | APROVADA — §8 |
| C-5 | SI: eng-api owner do realizado; SI owner de metas/IDD; sem ciclos; delegação humana | APROVADA — §7 |
| C-6 | EVA evolui só sobre contratos implementados | APROVADA — §14 |

---

## 2. Ownership das 33 regras — matriz definitiva

Legenda de estratégia: **Migrate** (portar p/ eng-api), **Preserve** (permanece api-delpi), **Refactor** (permanece mas reembalada como fato/contrato), **External-owner** (outro bounded context).

| Rule | Implementação atual | Owner atual | Owner-alvo | Classificação | Estratégia | Justificativa | Risco |
|---|---|---|---|---|---|---|---|
| R01 SLA por nível (4/8/20d úteis) | `lmp_business_rules.py:24-27` | api-delpi | **eng-api** | ENGINEERING_DOMAIN | Migrate | Convenção de negócio Engenharia; insumo de R04 | B — tabela pura, trivial |
| R02 Nível por qtd_pi (≤10/≤20/>20) | :112-119 | api-delpi | **eng-api** | ENGINEERING_DOMAIN | Migrate | Proxy de complexidade definido por Engenharia | B |
| R03 Tolerância +1d útil | :29,:126-140 | api-delpi | **eng-api** | ENGINEERING_DOMAIN | Migrate | Idem | B |
| R04 Status dashboard (Retornada/Andamento/Pontual-or/Atrasado) | :189-230 | api-delpi | **eng-api** | ENGINEERING_DOMAIN | Migrate | Regra central do KPI; `OR` data×minutos é semântica sutil — fixture obrigatória | A |
| R05 Dias úteis (só fds; feriados TO_INVENTORY) | :78-110 | api-delpi | **eng-api** | ENGINEERING_DOMAIN | Migrate | Calendário operacional; feriados pendentes de confirmação de negócio | M — se feriado existir, muda KPI |
| R06 Labels `engineering_status` | :31-35,:147-187 | api-delpi | **eng-api** | SOURCE_NORMALIZATION→domínio no uso | Migrate (interpretação) / Preserve (rótulos crus no fato) | Rótulo é dado da fonte; mapear para semântica é regra | B |
| R07 Datas Protheus↔ISO | :39-75 | api-delpi | **api-delpi (input) / eng-api (output)** | SOURCE_NORMALIZATION/PRESENTATION | Refactor | Parse da fonte permanece na integração; serialização HTTP é do contrato de quem responde | B |
| R08 Enriquecimento item dashboard | `list_lmp_dashboard_use_case.py:32-59` | api-delpi | **eng-api** | ENGINEERING_DOMAIN | Migrate | Composição de R01-R07 sobre fatos | B |
| R09 `%dentro_prazo` = ≠Atrasado/total (inclui Andamento!) | :158-177 | api-delpi | **eng-api** | ENGINEERING_DOMAIN | Migrate | KPI oficial — semântica sensível, fixture dedicada | A |
| R10 `avg_lead_time` | :167-172 | api-delpi | **eng-api** | ENGINEERING_DOMAIN | Migrate | KPI oficial | B |
| R11 Charts (nível/status/lead médio) | :69-97 | api-delpi | **eng-api** | ENGINEERING_DOMAIN | Migrate | Agregação derivada dos itens | B |
| R12 Summary kpi vs full (PI só FINALIZADA) | :246-268 | api-delpi | **eng-api (política) + api-delpi (execução lote PI)** | ENGINEERING_DOMAIN | Migrate | Decidir "quem precisa de PI" é regra; executar BOM é integração | M — acoplamento facts↔política |
| R13 Cache dashboard/summary | `services/lmp/*cache*` | api-delpi | **decisão de implementação do owner** | PRESENTATION/infra | Preserve-like | Cache não é regra; reimplementar na eng-api conforme SLO | B |
| R14 Enrich metas SI (`goal_*`) | `dashboard_goal_enrichment.py` | api-delpi | **consumer (eng-api/SI-boundary)** | CROSS_DOMAIN | External-owner | Meta é do SI; eng-api pode repassar contrato SI oficial sem recalcular | M — quem enriquece muda o contrato |
| R15 Enriquecimento eventos histórico | `lmp_history_event_enrichment.py` (266) | api-delpi | **eng-api** | ENGINEERING_DOMAIN | Migrate | Correlação próximo-evento/revisão de referência = semântica Engenharia | M |
| R16 Fluxo + labels processo/estágio | `lmp_history_flow_transition.py`, `lmp_process_stage_labels.py` | api-delpi | **eng-api** | ENGINEERING_DOMAIN | Migrate | Tradução de códigos TOTVS em narrativa de Engenharia | B |
| R17 Semânticas listing_kind/período/ciclo | `lmp_*_semantics_service.py` (220 linhas) | api-delpi | **eng-api (fonte de verdade da semântica)** | ENGINEERING_DOMAIN | Migrate + **reconciliar com SQL** | Hoje SQL decide na query E o serviço interpreta depois — dupla fonte | A — risco de divergência já existe |
| R18 NC: diff histórico, sort, tags, streak | `domain/services/lmp/*` | api-delpi | **eng-api** | ENGINEERING_DOMAIN | Migrate | Dado e regra DELPI-criados | M — trilha própria |
| R19 Ator/auditoria (`_current_actor`) | `lmp_nonconformity_router.py:215` | api-delpi | **plataforma (delpi_auth) consumida por eng-api** | CROSS_DOMAIN | External-owner | Identidade do ator vem do principal autenticado | B |
| S01 Tabelas AD1010/AIJ010/SB1010/SG1010/view | repository+`LMPS_VIEWS.SQL` | api-delpi | **api-delpi** | SOURCE_EXTRACTION | Preserve | Acesso físico à fonte oficial | — |
| S02 Filiais escopo `["01","02"]` | settings | api-delpi | **api-delpi (param) / eng-api (filtro funcional)** | SOURCE_EXTRACTION | Preserve | Config técnica da extração | B |
| S03 Residência ≥30min p/ LMP | settings+`_engineering_residence_filter_sql`:118 | api-delpi | **eng-api (owner) — execução SQL ou híbrida: REQUIRES_DECISION** | ENGINEERING_DOMAIN em SQL | Migrate (semântica) | Define elegibilidade da listagem — denominador do KPI | A |
| S04 Mapa processo→estágios (âncora/followup/suporte/amostra/finalizado) | settings+repo :535-600 | api-delpi | **eng-api (owner) — execução SQL: REQUIRES_DECISION** | ENGINEERING_DOMAIN em SQL | Migrate (semântica) | **É a definição de "o que é LMP"** — regra nuclear | A |
| S05 Prioridade LMP>AMOSTRA>OUTROS | settings | api-delpi | **eng-api — REQUIRES_DECISION** | ENGINEERING_DOMAIN | Migrate | Classificação por revisão | M |
| S06 Política de período (`work_month_lmp` etc.) | settings+`_period_inclusion_policy`:200 | api-delpi | **eng-api (owner) — execução SQL: REQUIRES_DECISION** | ENGINEERING_DOMAIN em SQL | Migrate (semântica) | Define o conjunto universo dos KPIs | A |
| S07 `strict_residence_after_homolog` (default False) | settings | api-delpi | **eng-api — REQUIRES_DECISION** | ENGINEERING_DOMAIN | Migrate | Flag de política | M |
| S08 Minutos de engenharia por evento/revisão (CTEs) | repo :319-532 | api-delpi | **eng-api (owner semântica) / api-delpi (execução computacional — REQUIRES_DECISION)** | ENGINEERING_DOMAIN em SQL | Refactor como **fato derivado declarado** | Insumo de R04; medir em escala — ver §4 | A |
| S09 qtd_pi via BOM recursiva ≤10, PA/PI | settings+`:4184` | api-delpi | **api-delpi (fato numérico) / eng-api (uso em R02)** | SOURCE_EXTRACTION+regra | Preserve como fato | Contar PI é extração BOM; interpretar é R02 | B |
| S10 `D_E_L_E_T_`, NOLOCK | repo :49 | api-delpi | **api-delpi** | SOURCE_EXTRACTION | Preserve | Higiene de leitura TOTVS | — |
| S11 Dedup/ordenação de eventos (ROW_NUMBER/OUTER APPLY) | `LMPS_VIEWS.SQL` | api-delpi | **api-delpi (fato técnico)** | SOURCE_NORMALIZATION | Preserve como fato | Ordenação física da fonte; enriquecimento semântico é R15 | B |
| S12 Candidatas por revisão/ciclo/mês | repo :205-218 | api-delpi | **eng-api (semântica) — REQUIRES_DECISION** | ENGINEERING_DOMAIN em SQL | Migrate | Mesma família de S06 | A |
| S13 list/get/painéis/paginação | repo :3655-3962 | api-delpi | **api-delpi** | SOURCE_EXTRACTION | Preserve | Leitura de entidade | — |
| S14 facts vs full batch | repo :4104,:4212 | api-delpi | **api-delpi (facts) — vira contrato §3** | SOURCE_EXTRACTION | Refactor → contrato facts | Já é a fronteira natural | B |

**Resumo:** ENGINEERING_DOMAIN→eng-api: R01–R06(uso), R08–R12, R15–R18 + semânticas S03–S08, S12 (~19–20). SOURCE_INTEGRATION→api-delpi: S01,S02,S09(fato),S10,S11,S13,S14 + parse de R07. CROSS_DOMAIN: R14 (SI), R19 (plataforma). PRESENTATION: R13 (cache por owner), R07 (serialização por contrato).

**REQUIRES_DECISION (5):** S03, S04, S05/S07, S06/S12, S08 — todas "eng-api é dono da semântica; onde executar" é decisão de §4.

---

## 3. Contrato FACTS da api-delpi

### 3.1 Campos de fato (comprovados — sem invenção)

Da projeção real (`lmp_query_repository.py:825-836, :2750-2764`, entidade `LMP`):

```
branch, sale_number, sale_description, listing_kind (C.LISTING_KIND bruto),
start_date (YYYYMMDD→ISO), end_date, reference_revision, measurement_revision,
homolog_revision, homolog_date, cycle_index,
engineering_status (rótulo fonte), engineering_total_minutes,
qtd_engineering_entries, qtd_engineering_closed,
qtd_advanced_from_engineering, qtd_returned_from_engineering,
qtd_pi (via lote separado), costumer_code, costumer_store, costumer_name,
seller_code, seller_name
```

Sinalizadores internos necessários para que eng-api reexecute S03–S07 sem duplicar SQL — **expostos como fatos derivados declarados** (não como regra): `has_sample_anchor`, `has_lmp_finalized`, `sample_eng_minutes` (`TEMPO_MINUTOS_AMOSTRA_ENG`), `residence_minutes` (= `engineering_total_minutes` por revisão), `period_anchor` (qual política qualificou a candidata), `stage_path` (sequência processo/estágio por revisão — já presente em eventos de histórico).

Eventos de histórico (entidade `LMPHistoryEvent`): `revision, process_code, stage_code, process_description, stage_description, start_date/time, limit_date/time, end_date/time, duration_minutes, status, history_flag, is_engineering, next_*/previous_*` (correlação vem da view `VW_DELPI_OV_EVENTOS_ENRIQUECIDOS`).

### 3.2 Endpoints facts propostos

**F-LMP-01 — `GET /engineering/lmps/facts`**
- OWNER: api-delpi (integração) — CONSUMERS: engineering-api (único)
- REQUEST: `start_date`, `end_date` (YYYYMMDD|ISO aceito, normalizado p/ fonte), `branch`, `listing_type` (filtro da fonte — pass-through da política corrente), `page`, `page_size` (máx 500), `include_qtd_pi` (default false → lote separado)
- RESPONSE (envelope `api_delpi_success`): `items[]` com todos os campos §3.1 (fatos + sinalizadores declarados), `page`, `page_size`, `total`, `period_policy_used`, `source: "totvs"`, `generated_at`
- **Proibições:** sem `status`/`nivel`/`dias_uteis_sla`/`sla_minutos`/`data_limite`/`lead_time_util`/`percent_*` — esses campos NÃO existem no fato
- AUTHN: JWT obrigatório (humano delegado **ou** S2S client-credentials — ver §6.3)
- AUTHZ: contrato técnico — não replica RBAC funcional; aceita (a) Bearer humano (AuthZ funcional fica na eng-api que o repassou) ou (b) S2S com `azp` allowlisted + escopo `engineering-facts:read`
- LIMITS: page_size≤500; timeout 30s; LIMITS de volume documentados
- PROVENANCE: `source_system:"TOTVS"`, tabelas em metadados de contrato (não por linha)
- VERSIONING: `/engineering/lmps/facts` v1 no mesmo router; mudança breaking → v2

**F-LMP-02 — `GET /engineering/lmps/facts/{sale_number}`** — detalhe por OV (mesma projeção + `list_products`, `list_history` opcionais via `include=products,history`).

**F-LMP-03 — `GET /engineering/lmps/facts/{sale_number}/history/events` e `…/history/flow`** — eventos crus + correlação (S11 preservado), sem `process_label`/`stage_label`/transição — labels são R16 (eng-api).

**F-LMP-04 — `POST /engineering/lmps/facts/pi-counts`** (lote): body `{ovs:[{branch,sale_number,revision}]}` (≤500) → `{counts:[{branch,sale_number,revision,qtd_pi}]}` — formaliza `get_lmp_pi_counts_by_ovs` (repo :4184) que hoje é interno. POST por tamanho de chave composta; semântica de leitura, idempotente.

### 3.3 Fronteiras explícitas (anti-fato-enriquecido)

| Camada | Pertence a | Exemplo |
|---|---|---|
| Dado de origem | api-delpi facts | `AIJ_DTENCE`, `AIJ_STATUS`, `AD1_REVISA` |
| Normalização técnica | api-delpi facts | YYYYMMDD→ISO, `ISNULL→0`, rótulos crus |
| Derivação operacional declarada | api-delpi facts **(declarada no schema)** | `residence_minutes`, `has_sample_anchor`, `period_anchor` — sinalizadores insumo, com docstring de semântica |
| Regra de domínio | **eng-api** | `listing_kind` efetivo, `status`, `nivel`, `data_limite`, KPI |
| KPI agregado | **eng-api** | `percent_dentro_prazo`, `avg_lead_time` |

Sinalizadores derivados são aceitáveis como fato **somente quando declarados e insumo-não-resultado** — o nome `derived:true`/`fact_kind` por campo no schema evita confundir com regra.

---

## 4. Matriz SQL × domínio (S03, S04, S06, S08 + correlatas)

| Regra | Definição funcional extraída | Execução hoje | Proposta | Razão |
|---|---|---|---|---|
| **S03** residência ≥30min p/ LMP (amostra/outro: só presença de estágio eng) | `IF listing==LMP: tempo_total_eng ≥ 30min` (ou `has_sample_anchor` no modo não-estrito) | WHERE sobre `EngenhariaResumo` (repo :118-146) | **eng-api aplica sobre fato `residence_minutes`** — filtro em memória/streaming pós-extração | O fato `residence_minutes` já vem calculado; o predicado é trivial e pertence ao owner. Volume: filtra após extração — custo = transferir não-qualificadas. Alternativa: `min_residence_minutes` como parâmetro do contrato facts (push-down opt-in). **Decisão: push-down como parâmetro opcional** — preserva performance, eng-api é owner do valor |
| **S04** mapa processo→estágios | âncora `{000002,000003}→{000003,000012}`; followup→`000013`; suporte→`{000003,000008,000012}`; amostra→`{000002,000008}`; finalizado→`000012` | CTEs de escopo/candidata (repo :535-600, settings) | **eng-api é dono do mapa; api-delpi expõe `stage_path` por OV como fato** e mantém escopo físico temporariamente | Migrar o matching para eng-api exige transferir **todos** os eventos de todas as OVs — volume proibitivo (AIJ010 é grande). Pragmático: fato declara `qualified_kind_raw` + `stage_path` (só das candidatas já restritas por período); eng-api revalida a classificação sobre o stage_path recebido — semântica auditável em Python, sem mover o scan pesado. **Decisão: classificação dual documentada — settings passam a ser espelhados de uma spec YAML única (fonte de verdade) consumida pelos dois lados** (elimina divergência silenciosa) |
| **S06/S12** política de período (`work_month_lmp` padrão; âncoras; ciclos de homolog; mês de trabalho) | qualifica OVs cuja atividade LMP intersecta o período segundo a política | CTEs de candidata por política (`_uses_*` :205-218, `_sql_candidate_period_where_clause` :261) | **eng-api escolhe política (parâmetro do contrato); api-delpi executa a seleção física e devolve `period_anchor` declarado** | Seleção de universo em SQL é correta por volume; a **política é input do owner** — eng-api passa `period_policy=work_month_lmp` e valida `period_anchor` no fato. Semântica documentada na spec única |
| **S08** minutos de engenharia por evento/revisão | soma de permanência em estágios de suporte-engenharia por revisão | CTEs `EngenhariaEventos/EngenhariaMinutosPorRevisao` (:404-532) | **api-delpi devolve `residence_minutes` por (ov, revisão) como fato derivado declarado** | Recalcular em Python exigiria todos os eventos brutos — o somatório SQL é a extração correta; eng-api apenas consome. Risco: se a definição de "estágio de engenharia" divergir do mapa S04 → resolvido pela spec única |
| **S05/S07** prioridade de classificação + flag estrita | `LMP(2)>AMOSTRA(1)>OUTROS(0)`; homolog<30min→OUTRO se estrito | `_effective_listing_kind_expr` (:153) | **eng-api reclassifica** usando `has_sample_anchor`, `has_lmp_finalized`, `sample_eng_minutes`, `residence_minutes` (todos fatos §3.1) | Todos os insumos viram fatos — eng-api executa o CASE em Python (barato, auditável) |

**Princípio adotado:** *ownership semântico ≠ local de execução.* Regras cujo custo de execução em Python exigiria mover o dataset inteiro ficam como **fatos derivados declarados** na api-delpi, sob spec única versionada + fixtures de paridade. Nenhuma duplicação silenciosa: cada semântica tem 1 fonte na spec e 2 execuções justificadas (física + verificativa).

**Benchmark:** sem ambiente/dados autorizados nesta missão → **TEST_NOT_RUN**, protocolo reproduzível em §12.

---

## 5. Semântica única de LMPs (especificação canônica proposta)

| Conceito | Definição oficial (a ratificar) | Fonte atual | Divergências notadas |
|---|---|---|---|
| **LMP** | OV cuja revisão qualifica como LISTING_KIND=LMP pelo mapa S04 (âncora/finalizado) e passa no filtro S03 (residência ≥30min não-estrito; estrito quando flag) | SQL candidata | Domain service `lmp_listing_kind_semantics_service.py` reinterpreta — divergência latente documentada em doc 32 §17 |
| **OV** | Ordem de venda Protheus identificada por (AD1_FILIAL, AD1_NROPOR); revisão corrente = AD1_REVISA | AD1010 | — |
| **listing_type (filtro)** | `Todos|LMP|Amostra|Outro` — filtro de listagem sobre `listing_kind` efetivo | `list_lmp_request.py` (`resolve_listing_type_filter`) | Frontend usa `lmp`/`Todos` — normalização case-insensitive documentada |
| **listing_kind (classificação)** | LMP/AMOSTRA/OUTROS — classe efetiva pós reclassificação S05/S07 | `_effective_listing_kind_expr` | Idem divergência SQL×domain service |
| **start_date** | âncora temporal da qualificação (início eng/homolog conforme política) | `LMP_START_DATE` projeção | Semântica varia por política de período — documentar por `period_policy` |
| **end_date** | fim do ciclo de medição (fim eng ou homolog) | `COALESCE(L.ANCHOR_END_DATE, R.ANCHOR_END_DATE)` | — |
| **status (dashboard)** | R04: RETORNADA→Retornada; não-FINALIZADA→Andamento; FINALIZADA→Pontual se end≤limite+tol OU minutos≤limite; senão Atrasado | `LMPBusinessRules` | KPI R09 conta `≠Atrasado` ⇒ **Andamento e Retornada entram no "no prazo"** — semântica sutil, fixture dedicada e decisão de produto a confirmar |
| **data_limite** | start + SLA(nível) dias úteis (+1 útil tolerância no teste pontual) | R03 | — |
| **lead_time_util** | dias úteis start→end (inclusive); fds excluídos; **feriados: TO_INVENTORY** | R05 | Ausência de feriados é comportamento vigente, não confirmado como regra |
| **competência/período** | `period_policy` default `work_month_lmp` | S06 | Virada de mês: OV conta no período da política — fixture de borda |
| **revisões** | reference_revision (AD1_REVISA corrente), measurement_revision (última rev. de medição eng), homolog_revision, cycle_index | projeção | múltiplas revisões → prioridade S05 |
| **não conformidade** | registro operacional DELPI (Postgres) ligado por `sale_number`/`lmp_number`; status open/in_progress/done | `postgres_lmp_nonconformity_repository.py` | Sem FK física para OV — integridade por aplicação |
| **cancelada** | **não evidenciada** no código — `TO_INVENTORY` | — | — |
| **contagem/dedup** | eventos ordenados por ROW_NUMBER (revisão, data, hora, stage, recno) | view | — |

---

## 6. Modelo de autorização unificado

### 6.1 Matriz funcional (proposta, alinhada à C-3)

| Operação (eng-api) | Permissão |
|---|---|
| Dashboard, listagem, detalhe, históricos, charts, exportações, indicadores | `engineering.access` |
| NC — leitura (list/detail/history/streak/tags/export) | `engineering.access` |
| NC — escrita (create/update/delete/import) | `engineering.access` **+ controles de write** (validação, auditoria `_current_actor`, idempotency-key no import, versionamento otimista no update) |
| Configuração/admin do Portal (futuros endpoints admin) | `engineering.manage` |

**`engineering.manage`: NÃO existe no repo** — permissão nova a registrar no Core (DECISIONS_PENDING_OWNER-2). Nenhuma operação LMP atual a exige; fica reservada a futuros endpoints de configuração (ex.: metas operacionais, preferências do Portal).

**Writes:** exigem `principal_type=="user"` (humano), `engineering.access` efetivo, auditoria (ator = principal), `Idempotency-Key` em import, `If-Match`/version em update para concorrência, e resposta com postcondition. Negado → 403 com reason estruturada.

### 6.2 Interservice — contrato de confiança (sem nova autoridade)

Mecanismos aprovados existentes:

1. **Delegação humana** — `Authorization: Bearer <JWT humano>` repassado de ponta a ponta; cada API resolve AuthZ efetiva via Core `/me`. Usar quando o dado é personalizado (Portal→eng-api→api-delpi facts **com contexto humano**). `X-Delpi-Caller-App` identifica consumer (nunca autorização); `X-Request-Id` propaga correlação.
2. **S2S técnico** — `delpi_auth.service_token_validator`: JWT client-credentials Keycloak, `azp`/`client_id` em `S2S_ALLOWED_CLIENTS`, escopos obrigatórios, audience dedicada. Usar quando não há humano (SI batch/snapshot, jobs). **Proposto:** escopo `engineering-facts:read` para F-LMP-01..04; api-delpi valida S2S **sem** exigir permissão funcional — o fato é técnico; a autorização funcional ficou na eng-api.
3. **Legado `X-Delpi-Service-Token`** (segredo compartilhado): sinal de composição (skip-goal-enrichment), **não autoridade** — manter comportamento atual durante transição; plano de desligamento pós-migração S2S (pendência registrada).

**Anti-ciclo por contrato:** eng-api → api-delpi facts (unidirecional). api-delpi **nunca** chama eng-api. eng-api **nunca** chama SI dentro de E-LMP-03 (realized-only). SI → eng-api usa S2S ou Bearer delegado — o contrato não enriquece metas, logo não há chamada de retorno a SI.

### 6.3 Transição de permissões legadas

| Permissão | Papel hoje | Destino |
|---|---|---|
| `dashboard-lmps.view` | read LMP legado | Manter até G9; novos grants congelam |
| `dashboard-lmps.nc.write` | write NC legado | Manter até trilha NC; substituída por `engineering.access`+controles |
| `dashboard-engineering.view` | read LMP no dashboard-eng | Manter até cutover do MFE |
| `api-delpi.access` | módulo genérico — **concede NC write hoje** | Manter (fora do escopo LMP remover); achado §8.3 |

Nenhum grant alterado nesta missão.

---

## 7. Strategic Indicators — contrato realizado-only

**Estratégia C → A** formalizada:

- **Fase C (transição):** api-delpi mantém `/engineering/lmps/dashboard/summary` congelado para SI (`listing_type=LMP`, `summary_mode=kpi` → `{total_lmps, percent_dentro_prazo, avg_lead_time}`). Enriquecimento de metas já é suprimido para chamadas SI (caller_app+token — otimização, não autorização).
- **Fase A (alvo):** SI → `GET /v1/lmps/summary` (eng-api).

### E-LMP-03 (SI-facing) — especificação

```
GET /v1/lmps/summary?start_date&end_date&branch&listing_type&period_policy
→ { total_lmps, total_items, percent_dentro_prazo, avg_lead_time,
    period: {start,end}, scope: {branch|consolidado}, listing_type,
    provenance: {rules:"engineering-api", facts:"api-delpi", source:"TOTVS"},
    generated_at }
```

- **Sem `goal_*`** — realized-only por construção (não existe código de enrich no caminho); metas ficam no SI que compõe.
- **AuthZ:** Bearer humano c/ `engineering.access` **ou** S2S `azp:strategic-indicators-api` allowlisted + escopo `engineering-indicators:read` (escopo técnico — não presume `engineering.access` no principal de serviço; DECISION_PENDING_OWNER: registro de client/escopo no Keycloak).
- **Paridade exigida:** mesmo universo (period_policy), mesma R09/R10 ⇒ resultado idêntico ao legado dentro de tolerância 0 (valores são determinísticos).
- **Sem ciclo:** eng-api não consulta SI neste caminho; documentado no contrato.

---

## 8. Não conformidades — domínio e achado AuthZ

### 8.1 Opções de persistência

| Opção | Descrição | Avaliação |
|---|---|---|
| **A — api-delpi store transitório** | eng-api chama contrato NC da api-delpi | Viável incremental; mantém owner de dados errado por mais tempo; contrato extra a manter |
| **B — schema migra para eng-api** | `engineering.lmp_nonconformities` (+history/tags) passa a ser gerido por eng-api (mesmo cluster Postgres plugins ou base própria) | **Recomendada** — dado é criado pelo fluxo Engenharia; exige: decisão formal de owner de dados, migration de dados verificada, dual-read janela, rollback (schema de origem intacto até G9) |
| **C — outra solução plataforma** | — | Nenhuma comprovada |

Trilha NC separada: **B após decisão; A como fase transitória** se B for adiada. Requisitos de migração de dados: snapshot → copy verificada (counts + checksums por registro) → dual-write opcional curto → switch.

### 8.2 Achado `api-delpi.access → NC write` (PROVEN, doc 32 §8.1)

`ENGINEERING_LMP_NC_WRITE = [api-delpi.access, dashboard-lmps.nc.write]` (`api_delpi_permissions.py:234-237`). O aceite do código genérico do módulo torna o write mais amplo que a intenção do frontend (`dashboard-lmps.nc.write`).

**Proposta de transição (não implementada — requer decisão Core/Coordenação):**
1. Contrato NC da eng-api exige `engineering.access` (funcional, não genérico).
2. Rota legada api-delpi: restringir a `[dashboard-lmps.nc.write]` somente após (a) inventariar grants reais no Core e (b) confirmar que nenhum consumer legítimo depende de `api-delpi.access` para write — **PENDING em owner Core**.
3. Testes negativos G2: `api-delpi.access`-only → 403 no novo contrato; `engineering.access` → permitido com auditoria.

---

## 9. Consumidores transversais — matriz revalidada

| Consumer | Contrato atual | Estratégia | Etapa | Critério cutover |
|---|---|---|---|---|
| dashboard-lmps | 19 rotas + products + dept-idd | Migrar p/ eng-api (E-LMP-01..06) + products/dept-idd permanecem owners atuais | G5/G8 | paridade total + zero chamadas |
| dashboard-engineering | 4 rotas dashboard + dept-idd | Idem read-only; produtos/idd inalterados | G7/G8 | paridade summary/charts/items |
| Portal Engenharia | navegação legada + overview/home via eng-api | home/overview passam a consumir módulo interno LMP (não api-delpi summary) | G4 | KPIs idênticos |
| SI | api-delpi summary (kpi) | Fase A: `GET /v1/lmps/summary` | G7 | realizado idêntico por janela dual |
| eng-api interno | api-delpi `/lmps` e `/summary` | trocar gateway por facts+regras internas | G3/G4 | paridade home/overview |
| DÉLIA | paths/opIds (`list_lmps` etc.) | remap registry para novos contratos; manter actionIds | G7 | actions resolvem e retornam igual |
| TV Dashboard | catálogo OpenAPI api-delpi | regenerar catálogo pós-mudança; rotas legadas permanecem até G9 | G8 | catálogo consistente |
| api-delpi-console | smoke summary | atualizar suite | G8 | smoke verde |
| Externos não comprovados | ? | **Gate:** extrair `caller_request_stats`/`app_usage` (Core) janela 30–60d — mecanismo existe (`caller_request_stats_service.py`, `app_usage_tracker.py`); extração = TEST_NOT_RUN (sem acesso Core nesta missão) | antes de G8 | zero consumers não migrados |

---

## 10. Contratos-alvo engineering-api (E-LMP-01..07)

Convenções verificadas: `/v1/*` em eng-api (`/v1/home`, `/v1/overview`), envelope próprio, `require_any_permission`, erros estruturados.

| ID | Método/Path | Propósito | AuthZ | Notas |
|---|---|---|---|---|
| E-LMP-01 | GET `/v1/lmps` | lista paginada (filtros: start/end/branch/listing_type/status/page/page_size) | `engineering.access` | consome F-LMP-01; aplica reclassificação+filtro status em Python |
| E-LMP-02 | GET `/v1/lmps/dashboard` | summary+charts+items composto | `engineering.access` | agregação sobre E-LMP-01 internamente; `goal_*` via contrato SI oficial (pendente owner) ou omitido honestamente |
| E-LMP-03 | GET `/v1/lmps/summary` | KPIs realized-only | `engineering.access` OU S2S `engineering-indicators:read` | §7 — sem enrich SI |
| E-LMP-04 | GET `/v1/lmps/{sale_number}` | detalhe OV+LMP | `engineering.access` | F-LMP-02 |
| E-LMP-05 | GET `/v1/lmps/{sale_number}/history` | eventos+flow (flags `?view=events|flow`) | `engineering.access` | F-LMP-03 + R15/R16 |
| E-LMP-06 | CRUD `/v1/lmp-nonconformities` (+`/{id}`,`/{id}/history`,`/streak`,`/problem-tags`,`/export`,`/import`) | NC completo | `engineering.access` (+controles write §6.1) | trilha separada; E-LMP-06b = import c/ Idempotency-Key |
| E-LMP-07 | (api-delpi) `GET /engineering/lmps/facts*` | extração (§3) | §6.2 | não é contrato eng-api — fica aqui por rastreabilidade |

Todos: datas ISO, `branch` opcional, envelope eng-api, `request_id` propagado, `source_endpoint` em provenance, timeouts 30s, versionamento por path `/v1`.

---

## 11. Plano de paridade (executável)

Fixtures do doc 32 §11 + específicos G1: OV com `residence_minutes` 29/30/31; `has_sample_anchor` combinado com LMP-finalizado; `period_policy` virada de mês; revisão dupla LMP+AMOSTRA; item com `listing_kind` divergente entre SQL e domain-service (instrumentar); SI summary igualdade exata; NC com 20+ campos + history diff.

Execução: **shadow read** — eng-api computa e compara com resposta legada para amostra N=200 OVs e N=12 janelas de período; relatório de divergências por campo. Métricas: exatidão de valores (tolerância 0 — determinístico), latência P50/P95 vs baseline legado, volume facts, taxa erro.

## 12. Benchmark — TEST_NOT_RUN + protocolo

Sem acesso autorizado a ambiente/dados reais nesta missão → **TEST_NOT_RUN**.

Protocolo reproduzível (G2):
1. Dataset: 3 janelas (30d, 90d, 365d) × filiais {01,02,consolidado} × listing {LMP,Todos}.
2. Braços: (a) legado `dashboard/summary` end-to-end; (b) facts + reclassificação eng-api; (c) facts com push-down `min_residence_minutes`.
3. Medir: latência P50/P95/P99 (n=30/braço), linhas facts transferidas, bytes, tempo de query SQL (log api-delpi), memória worker (aprox.), divergência de resultado (esperado 0).
4. Critério de decisão S03/S04/S06/S08: se (b) transferir >3× linhas de (a) ou P95 >2× baseline → adotar push-down/fatos derivados declarados (default recomendado §4).

## 13. Roadmap G2→G9

- **G2:** F-LMP-01..04 (facts) + spec semântica YAML única + fixtures de paridade + benchmark protocolo §12 executado.
- **G3:** portar R01–R18 para módulo LMP eng-api (domínio puro, sem I/O) + testes contra fixtures; shadow read instrumentado.
- **G4:** E-LMP-01..05; eng-api home/overview passam a usar módulo interno; paridade backend PASS.
- **G5:** Dashboard LMPs no Portal (read→detail→history); NC read.
- **G6:** EVA `get_lmp_dashboard/search_lmps/get_lmp_detail/get_lmp_history` (READ) sobre contratos provados.
- **G7:** SI migra p/ E-LMP-03 (janela dual); DÉLIA/TV/console remap; trilha NC (E-LMP-06 + decisão persistência + migração dados).
- **G8:** cutover navegação oficial após paridade + gate de consumers externos (stats 30–60d).
- **G9:** retirada do legado; remoção de grants legados; desligamento `X-Delpi-Service-Token` residual.

## 14. EVA

Tools READ somente após contratos provados (C-6). `get_lmp_*` em G6 sobre E-LMP-01..05 — sem recalcular regra (consome saída oficial). Nenhuma tool de write sem PREPARE/ACT aprovado.

## 15. ADRs propostas

- **ADR-LMP-01:** ownership LMP → eng-api; api-delpi=facts (C-1/C-2). *Status: aprovada por diretriz; formalizar.*
- **ADR-LMP-02:** fatos derivados declarados (`residence_minutes`, `has_*`, `period_anchor`, `stage_path`) + spec YAML única para S03–S08/S12. *Proposta.*
- **ADR-LMP-03:** S2S `engineering-facts:read` / `engineering-indicators:read` via client-credentials allowlisted. *Proposta — depende Keycloak.*
- **ADR-LMP-04:** permissões `engineering.access`/`engineering.manage` (nova no Core). *Proposta — depende Core.*
- **ADR-LMP-05:** NC persistência opção B (schema migra com owner) após A transitório. *Proposta — depende owner de dados.*
- **ADR-LMP-06:** SI realized-only E-LMP-03, estratégia C→A, sem enrich no caminho. *Proposta — depende SI.*
- **ADR-LMP-07:** endurecer NC write legado removendo `api-delpi.access` após inventário de grants. *Proposta — depende Core.*

## 16. Questões pendentes / dependentes de owner

1. Feriados no cálculo de dias úteis — negócio Engenharia (TO_INVENTORY).
2. `engineering.manage` registro Core + perfis (líder Engenharia).
3. Client/escopo S2S no Keycloak para eng-api/SI.
4. Grants reais de `api-delpi.access` p/ avaliar endurecimento NC (§8.2).
5. Owner formal do schema Postgres `engineering.*`.
6. Extração de stats de uso 30–60d (acesso Core) antes do gate G8.
7. `goal_*` em E-LMP-02: quem enriquece (contrato SI oficial vs composição no frontend/eng-api) — decisão com SI.

## 17. Índice de evidências

Doc 32 (baseline); `api-delpi/.../lmp_query_repository.py` :118-218,:535-600,:825-836,:2750-2790,:3655-4216; `lmp_query_settings.py`; `LMPS_VIEWS.SQL`; `lmp_business_rules.py`; `list_lmp_dashboard_use_case.py`; `get_lmp_dashboard_summary_use_case.py`; domain `lmp/*`, `lmp_*semantics*`, `lmp_history_*`; `lmp_nonconformity_router.py`:215-641; `postgres_lmp_nonconformity_repository.py`; `api_delpi_permissions.py`:229-239; `dashboard_goals_service.py` (`_is_internal_request_declared_by_si`); `dashboard_router.py`:100; `delpi_auth/{service_token.py, service_token_validator.py, authorization.py, authz_core.py}`; `api-delpi/app/middleware/auth_middleware.py`:75-95; `caller_request_stats_service.py`, `app_usage_tracker.py`; `engineering-api/.../{downstream_client.py, api_delpi_gateway.py, overview_api_delpi.py:148-175}`; `home_routes.py`:42,76 e `overview_routes.py`:42,76 (`ENGINEERING_ACCESS`); `tool_bridge.py`:45-89; `strategic-indicators-api/.../delpi_engineering_gateway.py`; `shared/delpi_api_client/client.py`:385-395; `tv_data_routes.json`:10325-11111; DÉLIA `assistant_capabilities_catalog_generator.py`:100-102.

## 18. Próxima missão executável

**ENGINEERING.LMP.G2 — Facts contract + spec semântica única:** implementar F-LMP-01..04 na api-delpi (fatos + sinalizadores declarados), materializar a spec YAML de semântica (S03–S08/S12 + R01–R05 constants), fixtures de paridade, executar protocolo de benchmark §12, e ADR-LMP-03 (S2S) se aprovada pela Coordenação. Pré-requisitos bloqueantes: ADR-LMP-02 aprovada; `engineering-facts:read` definido.

---
*Documento de desenho — nenhum contrato implementado; decisões pendentes de owners externos estão explícitas.*
