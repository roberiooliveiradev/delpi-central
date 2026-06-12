# Playbook 18 — Instâncias operacionais, filiais, departamentos e escopo híbrido

**Status:** roadmap (jun/2026)  
**Decisões fechadas:**  
- **Opção C** — cada unidade `(filial × setor)` possui **sua própria timeline de revisões**; processo-mestre agrupa instâncias; dashboard **por unidade** ou **consolidado**.  
- **PK UUID** — toda entidade cadastral usa **`uuid` como chave primária**; códigos legíveis (`codigo_*`) ficam em colunas separadas, nunca como PK.  
**Parent:** [`PLAYBOOK-MODELAGEM.md`](./PLAYBOOK-MODELAGEM.md) · [`ARCHITECTURE.md`](./ARCHITECTURE.md)  
**Relacionado:** [`regras-de-calculo.md`](../../../transformometro-api/docs/regras-de-calculo.md) · Strategic Indicators (`goal_scope_branch`, visão consolidado/filial)

---

## 1. Problema observado

| Sintoma | Impacto |
|---------|---------|
| `filial_id` e `setor_id` fixos em `processos` | Um processo = um recorte; rollout multi-unidade exige **duplicar** processo |
| Filiais hardcoded em `catalogs.py` | Sem entidade cadastral; sem FK; diverge de `setor_filiais` |
| Rateio de recurso **global** (empresa) | Visão por filial/dept mostra fatia ambígua ou mistura unidades |
| Dashboard filtra por `filial_id` / `setor_id` | Filtro ≠ modelo de domínio; consolidado não é first-class |
| `codigo_processo` único global | Impede mesmo código lógico em duas filiais |
| `POST /processos/{id}/duplicar` | Workaround para multi-unidade, não modelo canônico |
| `setor_id` / `filial_id` como slug ou código TOTVS | Mistura identificador técnico com código de negócio; URLs e FK frágeis |
| `dashboard_calculo_id` VARCHAR(80) composto | Não é UUID; dificulta joins e auditoria |

**Princípio:** **processo-mestre** descreve a iniciativa; **instância operacional** `(filial, setor)` possui baseline → melhorias → cálculo; **recursos compartilhados** com escopo híbrido (`empresa` \| `filial` \| `setor`); **visões analíticas** consolidado / filial / departamento com a **mesma regra** no live, cache e export; **identificadores técnicos** sempre UUID — **códigos de negócio** (`codigo_filial`, `codigo_setor`, `codigo_processo`, `codigo_recurso`) só para exibição, filtros externos e integração TOTVS/SI.

---

## 2. Modelo de domínio alvo

### 2.1 Grafo de entidades

```text
filiais (PK uuid) ──┬── setor_filiais ── setores (PK uuid)
                    │
                    └── processo_instancias (PK uuid; FK filial_id, setor_id uuid)
                              │
                              └── revisoes (PK uuid; timeline própria)
                                    ├── medicoes
                                    ├── investimentos
                                    └── revisao_recursos_compartilhados → recursos (PK uuid)

processos (PK uuid; mestre: codigo_processo, nome, familia…)
      │
      └── 1:N processo_instancias
```

### 2.2 Papéis e chaves (UUID + código de negócio)

| Entidade | PK (UUID) | Código de negócio (UNIQUE, não-PK) | Papel |
|----------|-----------|-----------------------------------|-------|
| **Filial** | `filial_id` | `codigo_filial` (`01`, `02`, …) | Unidade TOTVS |
| **Setor** | `setor_id` | `codigo_setor` (`engenharia`, …) | Departamento |
| **Processo mestre** | `processo_id` | `codigo_processo` | Iniciativa corporativa |
| **Instância** | `instancia_id` | — (opcional `rotulo_instancia`) | Unidade `(processo, filial, setor)` |
| **Revisão** | `revisao_id` | `versao_revisao`, `chave_unica_*` | Cenário calculável; FK `instancia_id` |
| **Medição** | `medicao_id` | — | 1:1 revisão |
| **Investimento** | `investimento_id` | — | Custo da revisão |
| **Recurso** | `recurso_compartilhado_id` | `codigo_recurso` | + `escopo_recurso` |
| **Vínculo** | `vinculo_id` | — | Revisão ↔ recurso |
| **Custo recurso** | `recurso_custo_id` | — | Histórico mensal |
| **Dashboard cache** | `dashboard_calculo_id` | — | Linha materializada |
| **Auditoria** | `audit_id` | — | Já UUID |

**Regra UUID:** toda rota REST `{id}` e todo FK referenciam **UUID**. Filtros de dashboard e integração SI aceitam **`codigo_filial`** / **`codigo_setor`** como alias de query (resolvidos server-side para UUID).

**Unidade de cálculo:** continua **`revisao_id` (UUID)**; `filial_id` / `setor_id` (UUID) denormalizados em `dashboard_calculos` para índice e export.

### 2.3 Regras de negócio

1. **Uma instância** = par único `(processo_id, filial_id, setor_id)` — todos UUID — entre registros não deletados.
2. **`setor_id` (UUID)** da instância deve existir em `setor_filiais` para a **`filial_id` (UUID)**.
3. **Revisão ativa:** no máximo **uma** `revisao_ativa = true` **por instância** (não por processo inteiro).
4. **Baseline + melhorias** formam timeline **por instância** (como hoje por processo).
5. **Data de implementação** da instância: primeira revisão não-baseline **da instância** (mesma regra atual, escopo local).
6. **Processo mestre `codigo_processo`:** único **global** (identificador da iniciativa).
7. **Instância** pode ter rótulo opcional (`rotulo_instancia`) para UI — ex.: «PCP Matriz».
8. **Consolidado processo:** soma KPIs de **todas as instâncias** do mestre; ROI = totais líquidos / totais investimento (não média de percentuais).
9. **Consolidado empresa:** soma instâncias (ou agregação equivalente no calculador); recursos `empresa` rateiam no pool global.

### 2.4 Escopo híbrido de recurso (`escopo_recurso`)

| Valor | Pool de rateio (vínculos elegíveis na competência) |
|-------|-----------------------------------------------------|
| **`empresa`** | Todos os vínculos da empresa (comportamento atual) |
| **`filial`** | Vínculos cuja instância tem a **mesma `filial_id`** |
| **`setor`** | Vínculos cuja instância tem **mesma `filial_id` + `setor_id`** |

- `criterio_rateio` (`igualitario`, `por_revisoes_ativas`, `por_peso`) aplica **dentro do pool**.
- Migração: recursos existentes → **`empresa`** (sem mudança numérica imediata).
- Em visão **filial** ou **departamento**, recurso `empresa` exibe **fatia rateada**, nunca custo integral.

### 2.5 Visões analíticas (contrato dashboard)

| Modo | Parâmetros | Semântica |
|------|------------|-----------|
| **Consolidado** | sem `filial_id` | Empresa ou processo-mestre (todas instâncias) |
| **Filial** | `filial_id` (UUID) ou `codigo_filial` (query alias) | Só instâncias da filial |
| **Departamento** | `filial_id` + `setor_id` (UUID ou alias `codigo_*`) | Só instâncias do par |

Espelhar padrão SI: token consolidado explícito (`consolidated` / ausência de filial) documentado na API.

---

## 2.6 Identificadores UUID — inventário e migração

### 2.6.1 Situação hoje (jun/2026)

| Entidade | PK hoje | Migração |
|----------|---------|----------|
| processo, revisão, medição, investimento, recurso, vínculo, custo, audit | ✅ UUID | Manter |
| setor | ❌ `VARCHAR(64)` slug | Nova coluna UUID + `codigo_setor` |
| filial | ❌ não existe (código solto em `processos`) | Criar tabela com UUID + `codigo_filial` |
| dashboard_calculos | ❌ `VARCHAR(80)` | UUID + unique `(revisao_id, competencia)` |
| processo_instancia | — (nova) | UUID desde o início |

### 2.6.2 Convenção de nomenclatura

| Tipo | Coluna | Exemplo |
|------|--------|---------|
| PK técnica | `{entidade}_id UUID` | `filial_id`, `setor_id`, `instancia_id` |
| Código negócio | `codigo_{entidade}` | `codigo_filial = '01'`, `codigo_setor = 'engenharia'` |
| Rótulo UI | `nome_*` | `nome_filial`, `nome_setor` |

**Proibido:** usar `codigo_*` ou slug como PK ou como FK. **Proibido:** converter `01` → inteiro `1`.

### 2.6.3 Contrato API (breaking controlado)

**Resposta JSON (padrão novo):**

```json
{
  "filial_id": "550e8400-e29b-41d4-a716-446655440000",
  "codigo_filial": "01",
  "nome_filial": "Matriz",
  "setor_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "codigo_setor": "engenharia",
  "nome_setor": "Engenharia"
}
```

**Query params (compatibilidade):**

| Param | Aceita | Resolução |
|-------|--------|-----------|
| `filial_id` | UUID **ou** `codigo_filial` (`01`) | UUID canônico internamente |
| `setor_id` | UUID **ou** `codigo_setor` | idem |
| Integração SI | manter `filial_id: "01"` no payload legado | mapper `codigo_filial` → UUID no serviço de integração |

**URLs MFE:** passam a usar UUID (`/processos/{uuid}/instancias/{uuid}`). Redirect 301 de rotas legadas que usavam slug de setor (se existirem).

### 2.6.4 Backfill UUID (setores e filiais)

1. **`filiais`:** INSERT com `gen_random_uuid()`, `codigo_filial` = `01`/`02`, copiar labels de `catalogs.py`.
2. **`setores`:** ADD `setor_id_new UUID`; ADD `codigo_setor` = valor atual de `setor_id`; PK migra para UUID; views/repos passam a usar UUID.
3. **`setor_filiais`:** substituir colunas por FKs UUID.
4. **`processos`:** backfill instância usa UUIDs resolvidos; remover colunas string `filial_id`/`setor_id` após instâncias criadas.
5. **`dashboard_calculos`:** TRUNCATE + recalcular com `dashboard_calculo_id UUID` (aceitável — cache derivado).

---

## 3. Estado atual vs. alvo (migrations)

### 3.1 Tabelas novas / alteradas

| Migration | Ação |
|-----------|------|
| **V011** | `CREATE TABLE filiais` (`filial_id UUID PK`, `codigo_filial UNIQUE`, …) — **sem seed de conteúdo** |
| **V012** | `setores`: migrar PK → UUID; ADD `codigo_setor UNIQUE`; rebuild `setor_filiais` com FKs UUID |
| **V013** | `CREATE TABLE processo_instancias` (`instancia_id UUID PK`, FKs UUID) + unique `(processo_id, filial_id, setor_id)` |
| **V014** | `revisoes.instancia_id UUID NOT NULL` (backfill) + índice; manter `processo_id` denormalizado opcional |
| **V015** | `processos`: remover `filial_id`/`setor_id` string; mestre só metadados + `codigo_processo` |
| **V016** | `recursos_compartilhados.escopo_recurso` DEFAULT `empresa` |
| **V017** | `dashboard_calculos`: `dashboard_calculo_id UUID PK`; FKs `instancia_id`, `filial_id`, `setor_id` UUID; TRUNCATE + recalc |

### 3.2 Conteúdo cadastral — export/import (sem seed em migration)

**Decisão:** migrations V011+ alteram **somente schema**. Dados operacionais vêm de **JSON exportado do ambiente atual**, reaplicados via script — **não** `INSERT` de seed em SQL.

| Passo | Ação |
|-------|------|
| **0 — Baseline** | Exportar cadastro de produção/staging **antes** da refatoração |
| **1 — Schema** | `migrations_runner up` (V011–V017) em ambiente limpo ou evolutivo |
| **2 — Transform** | (fase Playbook 18) script/migration de dados converte JSON 1.1 → 2.0 se necessário |
| **3 — Import** | `scripts/import_cadastro_json.py apply --mode replace --yes` |
| **4 — Validar** | `preview` + testes I3/I15 + recalc dashboard |

**Export (origem):**

```bash
cd transformometro-api
set -a && source ../infra/.env && set +a
python scripts/import_cadastro_json.py export \
  -o fixtures/cadastro/transformometro-cadastro-$(date +%Y%m%d).json
```

**Import (destino pós-schema):**

```bash
python scripts/import_cadastro_json.py preview -i fixtures/cadastro/transformometro-cadastro-YYYYMMDD.json --mode replace
python scripts/import_cadastro_json.py apply -i fixtures/cadastro/transformometro-cadastro-YYYYMMDD.json --mode replace --yes
```

Arquivo de referência: [`transformometro-api/fixtures/cadastro/README.md`](../../../transformometro-api/fixtures/cadastro/README.md) · serviço canônico `JsonBackupService` (mesma regra que UI `/data/export`).

### 3.3 Backfill estrutural (pós-import ou inline na migration de dados)

Para cada processo legado no JSON 1.1 (`filial_id` + `setor_id` string):

1. Resolver `filial_id UUID` via `filiais.codigo_filial`.
2. Resolver `setor_id UUID` via `setores.codigo_setor`.
3. Garantir vínculo em `setor_filiais` (UUID, UUID).
4. Criar **uma** `processo_instancia` com par UUID.
5. Atualizar `revisoes` → `instancia_id`.
6. TRUNCATE `dashboard_calculos` + recalcular full.

Processos duplicados manualmente (mesmo nome, filiais diferentes) **permanecem processos mestre distintos** até merge manual — fora do escopo automático.

---

## 4. Arquitetura API

### 4.1 Módulos canônicos

| Módulo | Camada | Responsabilidade |
|--------|--------|------------------|
| `FilialCatalogService` | domain | Validação de filial ativa |
| `ProcessoInstanciaService` | domain | Regras de par único, setor ∈ filial |
| `SharedResourceScopeService` | domain | Pool de rateio por `escopo_recurso` |
| `DashboardCalculatorService` | domain | Estender contexto com `instancias_by_id`; rateio via scope service |
| `ProcessoInstanciaRepository` | infrastructure | CRUD instâncias |
| `DashboardViewScopeService` | application | Resolve consolidado / filial / dept → filtros no raw |
| `ProcessoDuplicateService` | application | **Nova semântica:** duplicar instância ou criar instância em outra filial/setor |

**Proibido:** regra de rateio ou filtro de visão só no MFE ou só em rota SQL legada.

### 4.2 Rotas HTTP (evolução)

| Grupo | Rotas novas / alteradas |
|-------|-------------------------|
| Filiais | `GET/POST /filiais`, `GET/PUT/DELETE /filiais/{id}` |
| Instâncias | `GET /processos/{id}/instancias`, `POST /processos/{id}/instancias`, `GET /instancias/{id}` |
| Revisões | `POST /instancias/{id}/revisoes` (preferencial); manter compat `POST /revisoes` com `instancia_id` |
| Ativar | `POST /revisoes/{id}/ativar` — escopo **instância** |
| Duplicar | `POST /processos/{id}/duplicar` → **`POST /instancias/{id}/duplicar`** (copia timeline para nova filial/setor) |
| Dashboard | Query `view=consolidated\|filial\|department` + `filial_id` / `setor_id` |
| Options | `GET /options` inclui `filiais` do banco |
| Integração S2S (interna) | TM `…/integrations/engineering/transforma-mais/*` — espelho para **api-delpi**; SI/MFE **não** consomem direto |

Envelope resposta TM nativo: `{ success, message, data }`. Contrato **público** para outras apps: api-delpi (§4.4).

### 4.3 Contrato instância (exemplo)

```json
{
  "instancia_id": "6fa459ea-ee8a-3ca4-894e-db77e160455e",
  "processo_id": "550e8400-e29b-41d4-a716-446655440000",
  "filial_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "codigo_filial": "01",
  "nome_filial": "Matriz",
  "setor_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "codigo_setor": "engenharia",
  "nome_setor": "Engenharia",
  "rotulo_instancia": "Engenharia — Matriz",
  "status_instancia": "ativo",
  "revisao_ativa_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
  "data_implantacao": "2025-03-15"
}
```

### 4.4 Contrato público — api-delpi (SI, dashboard-engineering, chat)

**Fronteira externa:** **api-delpi** entrega Transforma+ para o resto da plataforma. transformometro-api é backend interno (S2S).

Documento: [`transformometro-api/docs/integration-contracts.md`](../../../transformometro-api/docs/integration-contracts.md).

#### Cadeia

```text
transformometro-api (cadastro + cálculo + rotas S2S internas)
        │  TransformometroApiClient + service token
        ▼
api-delpi  GET /engineering/transforma-mais/processes
           GET /engineering/transforma-mais/processes/summary
        │
        ├── strategic-indicators-api  (delpi_api_client)
        ├── plugins/dashboard-engineering
        └── demais consumidores REST/OpenAPI api-delpi
```

#### O que congelar (contrato api-delpi `data`)

| Rota | Congelado |
|------|-----------|
| `list_transforma_mais_processes` | `total`, `items[]` com `id`, `name_process`, `filial_id`, `sector_name`, `daily_savings`, `payback_months`, `status`, `implementetion_date` |
| `get_transforma_mais_summary` | `total_gross_savings_in_period`, `monthly_breakdown`, `implemented_solutions_count`, `average_roi`, … + metas de `enrich_dashboard_metric` se já usadas |

Query pública: `filial_id` = **`codigo_filial`** (`01`/`02`); `sector_name` = **`codigo_setor`**.

#### Regras Playbook 18

1. **Dono do shape externo:** DTOs + rotas **api-delpi** (`Process`, `ProcessSummaryResponse`, `engineering_router.py`).
2. **TM → api-delpi:** mapper `engineering_transforma_mais.py` + gateway `TransformometroTransformaMaisGateway` mantêm paridade.
3. **`filial_id` / `sector_name` em `data`:** códigos de negócio, **nunca** UUID interno.
4. **Campos novos:** aditivos em `items[]` até bump OpenAPI; coordenar api-delpi + SI + MFE.
5. **SI nunca** passa a chamar transformometro-api direto na refatoração.

#### Testes / aceite

| Camada | Teste |
|--------|-------|
| TM S2S | `tests/test_engineering_transforma_mais.py` |
| api-delpi | smoke `transforma-mais-summary`; contrato `list_transforma_mais_processes` / `get_transforma_mais_summary` |
| SI | KPI engenharia (`total_gross_savings_in_period`) — caso **I11**, **I17** |
| MFE engenharia | `engineeringApi.ts` + TransformaPage |

#### Breaking change

PR coordenado **api-delpi + transformometro-api + consumidores**; bump OpenAPI/`operationId` — não alterar só o backend TM.

---

## 5. Microfrontend (`plugins/transformometro`)

| Superfície | Mudança |
|------------|---------|
| **Lista processos** | Coluna mestre; badge «N instâncias»; filtro por filial/setor na lista de instâncias |
| **Detalhe processo** | Abas: **Visão geral (mestre)** · **Instâncias** (grid filial × setor) · **Consolidado** (KPIs somados) |
| **Detalhe instância** | Timeline revisões (substitui detalhe monolítico filial+setor no processo) |
| **Dashboard** | Toggle **Consolidado / Filial / Departamento** (como SI); setor disabled até filial |
| **Cadastro processo** | Mestre sem filial/setor; wizard «Adicionar instância» pós-criação |
| **Duplicar** | «Replicar instância em outra filial/setor» |
| **Recursos** | Campo `escopo_recurso` no formulário |

**Regra:** KPIs consolidados do processo-mestre vêm da API — MFE não soma client-side.

---

## 6. Cálculo e cache

### 6.1 Pipeline (inalterado em espírito)

```text
load_raw() → build_context(instancias + revisoes + recursos)
  → SharedResourceScopeService.resolve_pool(recurso, escopo, visão)
  → DashboardCalculatorService._calculate_shared_resource_cost_for_review
  → dashboard_calculos (denormaliza filial_id, setor_id, instancia_id, processo_id)
```

### 6.2 Paridade obrigatória

- `DashboardLiveService` e `DashboardRecalcService` usam **mesmo** calculador e **mesmo** scope service.
- Após mudança de regra: recálculo full + query de validação (ver PLAYBOOK-MODELAGEM § cache).

### 6.3 `_filter_raw_preserving_resource_rateio`

Substituir por **`DashboardViewScopeService`**: ao filtrar visão filial/dept, manter vínculos necessários para rateio conforme `escopo_recurso` (não truncar pool de recurso `empresa`).

---

## 7. Testes de regressão

Arquivo alvo: `transformometro-api/tests/fixtures/instancia_escopo_cases.py` (+ testes unitários existentes).

| ID | Caso | Visão |
|----|------|-------|
| **I1** | Processo mestre + 2 instâncias (01/eng, 02/prod) timelines independentes | consolidado processo |
| **I2** | Ativar revisão instância A não altera instância B | por instância |
| **I3** | Backfill: processo legado vira 1 instância + N revisões intactas | migração |
| **I4** | Recurso `empresa`, vínculos 01 e 02 → filial 01 vê 50% (igualitário) | filial |
| **I5** | Recurso `filial` só em 01 → filial 02 = 0 | filial |
| **I6** | Recurso `setor` PCP@01 → dept eng@01 = 0; PCP@01 = rateio local | departamento |
| **I7** | Consolidado empresa = soma fatias (sem double-count) | consolidado |
| **I8** | ROI consolidado processo = líquida total / investimento total | consolidado |
| **I9** | Instância rejeita setor não vinculado à filial | CRUD |
| **I10** | Export CSV/XLS reflete visão filial/dept | export |
| **I11** | Integração transforma-mais com filtro filial | integração |
| **I12** | JSON backup inclui `filiais`, `processo_instancias` | backup |
| **I13** | CRUD setor/filial: API retorna UUID + `codigo_*`; FK válida | UUID |
| **I14** | Query `filial_id=01` (codigo) resolve igual a UUID | compat query |
| **I15** | JSON backup export/import preserva UUIDs; merge por PK | backup |
| **I16** | `dashboard_calculo_id` UUID; unique `(revisao_id, competencia)` | cache |

---

## 8. Roadmap por sprint

| Sprint | Entrega | Critério de pronto |
|--------|---------|-------------------|
| **S0 — Design lock** | Este playbook aprovado; ADR curto em `transformometro-api/docs/` | Decisões §2 fechadas |
| **S1 — Filiais UUID** | V011 (schema only), CRUD filiais, options do banco | Sem seed SQL; filiais vêm do import ou CRUD |
| **S2 — Setores UUID** | V012, migrar PK setor, `setor_filiais` UUID, MFE/API por UUID | I13; remover slug como PK |
| **S3 — Instâncias + backfill** | V013–V014, repos, backfill script, testes I1–I3, I15 | Revisões com `instancia_id` UUID |
| **S4 — Processo mestre** | V015, API cadastro mestre + instância na criação | ✅ API (MFE pendente) |
| **S5 — Escopo híbrido** | V016, `SharedResourceScopeService`, testes I4–I7 | Paridade live/cache |
| **S6 — Dashboard cache UUID** | V017, `dashboard_calculos` UUID, recalc full, I16 | Cache alinhado |
| **S7 — Dashboard visões** | `DashboardViewScopeService`, toggle MFE, query alias I14, export I10 | Consolidado / filial / dept |
| **S8 — Duplicar instância** | Novo endpoint, deprecar duplicar processo | Rollout multi-unidade |
| **S9 — Integração via api-delpi + backup** | Paridade TM S2S + gateway/DTO api-delpi; smoke; I11/I17; JSON I12 | Contrato público = `/engineering/transforma-mais/*`; SI/MFE só api-delpi |
| **S10 — RBAC filial** (opcional) | Filtro server-side por filial do usuário | Permissão escopada |

**Dependências:** S1 → S2 → S3 bloqueia S4–S9; S5–S6 após S3; S7 após S5–S6.

---

## 9. Mapa de migração MFE / API (checklist)

- [ ] `processos.filial_id` / `setor_id` removidos do formulário mestre
- [ ] Rotas `/processos/{id}` listam instâncias
- [ ] URL canônica revisão: `/processos/{id}/instancias/{instanciaId}/revisoes/{revisaoId}` (redirect legado)
- [ ] `DashboardPage` — toggle visão
- [ ] `transformometroApi.ts` — tipos `ProcessoInstancia`, `Filial`, `Setor` com UUID + `codigo_*`
- [ ] Rotas MFE e forms usam UUID; exibem `codigo_*` / `nome_*` na UI
- [ ] `setorCatalogForm` / `ProcessoFormFields` — parar de usar slug como id técnico
- [ ] `PLAYBOOK-MODELAGEM.md` — § entidades atualizado (pós-S2)
- [ ] `ARCHITECTURE.md` — diagrama com instâncias (pós-S3)
- [ ] `regras-de-calculo.md` — § escopo recurso (pós-S4)

---

## 10. Riscos e mitigação

| Risco | Mitigação |
|-------|-----------|
| Backfill errado (revisão na instância errada) | Script idempotente + snapshot pré-migration + teste I3 |
| Double-count no consolidado | Testes I7/I8; ROI por totais, não média |
| Regressão integração SI | I11 + I14: resposta legado com `codigo_filial`; internamente UUID |
| Migração setor PK quebra URLs/bookmarks | Redirect + export JSON com mapa slug→UUID |
| Performance recalc multi-instância | Recalc incremental por `instancia_id` / `processo_id` |
| UX complexa | Wizard mestre → primeira instância obrigatória |

---

## 11. Fora de escopo (este playbook)

- Sincronização filiais com TOTVS/Core API (fase futura)
- Merge de dois processos mestre
- Recurso com escopo N:N custom (só os três valores fixos)
- RBAC filial (S8 opcional)

---

## 12. Referências

| Doc / módulo | Conteúdo |
|--------------|----------|
| [`PLAYBOOK-MODELAGEM.md`](./PLAYBOOK-MODELAGEM.md) | Regras vigentes de revisão/vigência (atualizar pós-S2) |
| [`ARCHITECTURE.md`](./ARCHITECTURE.md) | Camadas API/MFE |
| [`regras-de-calculo.md`](../../../transformometro-api/docs/regras-de-calculo.md) | Fórmulas oficiais |
| `tm_app/domain/services/dashboard_calculator.py` | Calculador canônico |
| `tm_app/core/catalogs.py` | Filiais hardcoded (remover em S1) |
| `migrations/V010__create_setores.sql` | Setores × filiais |
| [`integration-contracts.md`](../../../transformometro-api/docs/integration-contracts.md) | **api-delpi** como fronteira pública; TM S2S interno |

---

## 13. Resumo executivo

O Transformômetro evolui de **processo monolítico (1 filial + 1 setor)** para **processo-mestre + instâncias operacionais** `(filial × departamento)`, cada uma com **timeline própria de revisões**. Filiais e setores passam a ser entidades com **PK UUID** e **`codigo_*` de negócio**; recursos compartilhados ganham **escopo híbrido**; o dashboard passa a ter **visões consolidado / filial / departamento** com cálculo coerente no live, cache, export e integrações.

**Próximo passo:** Sprint **S4** (V015 — processo mestre sem `filial_id`/`setor_id` na tabela `processos`) · status: [`transformometro-api/docs/playbook-18-implementation-status.md`](../../../transformometro-api/docs/playbook-18-implementation-status.md).

### Progresso API (jun/2026)

| Sprint | Status |
|--------|--------|
| S1 Filiais UUID | ✅ V011, CRUD, options, bootstrap JSON |
| S2 Setores UUID | ✅ V012, `codigo_setor`, backup 1.1 |
| S3 Instâncias | ✅ V013–V014, rotas instância, `revisoes.instancia_id` |
| S4 Processo mestre | ✅ V015, create processo + instância |
