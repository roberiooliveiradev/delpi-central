# Playbook de Correção — Estoque Suprimentos vs. Registro de Inventário

**Data:** jun/2026  
**Escopo:** `GET /supplies/stock-value`, consumidores (`dashboard-supplies`, Strategic Indicators, IDD, chat)  
**Referências:** [supplies-estoque-historico.md](../api/supplies-estoque-historico.md), regra `sql-query-development.mdc`, checklist `new-api-route-checklist.mdc` (se nova rota de diagnóstico)

---

## 1. Objetivo

Alinhar o **valor de estoque exibido no dashboard Suprimentos** com a expectativa do usuário ao comparar com o **Registro de Inventário TOTVS** (MATR460 / fechamento SB9), sem perder o modo analítico SB9+SD3 quando não houver fechamento oficial na data.

**Resultado esperado ao concluir o playbook:**

| Cenário | Comportamento |
|---------|---------------|
| Período com fechamento SB9 na `end_date` | Dashboard usa **fechamento oficial** (ou declara explicitamente qual método foi escolhido) |
| Período sem fechamento na `end_date` | Mantém **estimativa SB9+SD3** com breakdown auditável |
| Comparação com inventário | Usuário entende diferença **EM ESTOQUE** vs **EM PROCESSO** vs **estimativa** |
| Filial 01 / 02 maio/2026 | Gap explicado (dados + método) ou corrigido dentro de tolerância acordada com Suprimentos |

---

## 2. Sintoma validado (maio/2026)

Comparativo **01/05/2026 – 31/05/2026** (modo histórico — `start_date` + `end_date`):

| Filial | Dashboard (`/supplies/stock-value`) | Registro oficial **TOTAL GERAL** | **EM ESTOQUE** | **EM PROCESSO** | % do oficial (total) |
|--------|-------------------------------------|----------------------------------|----------------|-----------------|----------------------|
| **01 — Matriz** | R$ 281.491,39 | R$ 3.862.102,97 | R$ 3.598.312,40 | R$ 263.790,57 | ~7% |
| **02 — UES** | R$ 4.911.291,59 | R$ 10.048.509,51 | R$ 9.737.043,62 | R$ 311.465,89 | ~49% |

**Conclusão:** não é apenas “falta EM PROCESSO”. A estimativa SB9+SD3 diverge estruturalmente do inventário oficial, principalmente na Matriz.

---

## 3. Arquitetura atual (baseline)

### 3.1 Rotas e consumidores

| Consumidor | Chamada | Observação |
|------------|---------|------------|
| `dashboard-supplies` — home KPI | `GET /supplies/stock-value?summary_only=true` | Com datas do filtro de estoque |
| `dashboard-supplies` — aba Estoque | `GET /supplies/stock-value` | Bundle completo |
| Strategic Indicators | `summary_only=true` | Mesmo KPI |
| `GET /supplies/inventory-turnover` | Reutiliza stock-value | IDD herda o mesmo total |
| Chat (`get_supplies_stock_value`) | OpenAPI action | Apresentação schema-first |

### 3.2 Dois modos na mesma rota

| Modo | Condição | Fonte SQL |
|------|----------|-----------|
| **Atual** | Sem `start_date` e sem `end_date` | `SB2010` (`B2_VATU1`, `B2_QATU`) |
| **Histórico estimado** | `start_date` **e** `end_date` | `SB9010` + `SD3010` |

Com datas preenchidas (como no MFE), **sempre** entra o modo histórico estimado.

### 3.3 Fórmula histórica (implementação)

```text
Estoque_fim =
  SUM(SB9 na MAX(B9_DATA) onde B9_DATA < start_date)
+ SD3 líquido (fechamento → start_date)          -- ponte
+ SD3 líquido [start_date, end_date]              -- período
```

Entrada/saída SD3: `D3_TM < '500'` → entrada; caso contrário → saída.

**Arquivos canônicos:**

| Artefato | Caminho |
|----------|---------|
| SQL histórico | `app/infrastructure/persistence/totvs/supplies_repositories/stock_value_historical_sql.py` |
| Repositório | `stock_value_query_repository.py` |
| Use case | `app/application/use_cases/supplies/get_stock_value_use_case.py` |
| Cache | `app/application/services/supplies/stock_value_cache.py` |
| MFE | `plugins/dashboard-supplies/src/pages/StockPage.tsx` |

### 3.4 Lacunas conhecidas do contrato

- Doc de exemplo mostra `closing_base_date`, `bridge_value`, `period_net_value` em `by_branch`, mas **a API não expõe** esses campos hoje.
- `estimation.method` é fixo: `sb9_last_closure_plus_sd3_movements`.
- Não existe modo **fechamento SB9 na `end_date`**.
- **EM PROCESSO** (WIP fabril) não entra no escopo SB9+SD3 por local/produto.

---

## 4. Diagnóstico — causas prováveis (ordenadas)

### 4.1 Metodologia diferente (causa principal)

O Registro de Inventário consolida por **família contábil** (MP, PA, insumos, etc.) e inclui **EM ESTOQUE + EM PROCESSO**.  
A API reconstrói saldo via Kardex — **não replica MATR460**.

### 4.2 Fechamento SB9 na data do inventário ignorado

Para maio/2026, se existir `B9_DATA = 20260531`, o inventário oficial usa esse fechamento.  
A API usa `MAX(B9_DATA) < start_date` (ex.: fev/2026) + SD3 até maio — **não lê o fechamento de 31/05**.

### 4.3 Ponte SD3 negativa / incompleta

Documentação interna (abril/2026, filial 01): base SB9 ~R$ 3,47M com ponte e período **negativos** → estimativa ~R$ 1,7M vs ~R$ 3,6M “em estoque” no oficial.  
Em maio/2026 a Matriz cai para ~R$ 281k → investigar ponte mar–abr–mai e consistência SD3.

### 4.4 EM PROCESSO fora do escopo

Gap parcial (~264k filial 01, ~311k filial 02). Não explica o total.

### 4.5 O que **não** é a causa

- Filtro intencional por tipo de produto no SQL histórico — **não há**.
- Exclusão de localização quando filtro = “Todas” — agrega todos os `B9_LOCAL` / `D3_LOCAL`.

---

## 5. Decisões de negócio (bloqueantes)

Registrar resposta de **Suprimentos / Controladoria** antes da onda W2:

| # | Pergunta | Opções | Impacto |
|---|----------|--------|---------|
| D1 | Qual número o dashboard deve mostrar com período fechado? | A) Total geral inventário · B) Só EM ESTOQUE · C) Estimativa SB9+SD3 | Define `estimation.method` default |
| D2 | Incluir **EM PROCESSO** no KPI? | Sim (nova fonte) / Não (banner) | Escopo W3 |
| D3 | Tolerância vs. oficial quando usar estimativa | Ex.: ±2% / apenas explicar gap | Critério de aceite |
| D4 | Meta de estoque (goals) continua “quanto menor melhor”? | Manter / Revisar por filial | `dashboard_goal_enrichment` |

**Recomendação técnica (default se D1 não responder):**

```text
Se existir fechamento SB9 com B9_DATA <= end_date na filial → usar sb9_closure_on_end_date
Senão → manter sb9_last_closure_plus_sd3_movements com breakdown exposto
EM PROCESSO → seção opcional / fase posterior, nunca somar silenciosamente sem D2=Sim
```

---

## 6. Plano de correção por ondas

```text
W0 Validação TOTVS     → provar gap com SQL (sem mudar produção)
W1 Transparência       → expor breakdown + método na API e MFE
W2 Fechamento oficial  → novo modo quando SB9 na end_date existir
W3 EM PROCESSO         → escopo ampliado (se D2=Sim)
W4 Chat / SI / testes  → contrato, regressão, documentação
```

---

## 7. Onda W0 — Validação no TOTVS (obrigatória)

**Objetivo:** separar problema de **dados** vs **regra**.

### 7.1 Script de reconciliação

**Artefatos (jun/2026):**

| Artefato | Caminho |
|----------|---------|
| SQL | `api-delpi/scripts/sql/reconcile_stock_value_period.sql` |
| Runner | `api-delpi/scripts/reconcile_stock_value.py` |
| Evidências | `api-delpi/docs/roadmaps/evidencias/estoque-reconciliacao-<end_date>.{json,md}` |

```bash
# Container com TOTVS
docker exec -w /app delpi-api-delpi env PYTHONPATH=/app python scripts/reconcile_stock_value.py \
  --start-date 2026-05-01 --end-date 2026-05-31

# Alternativa: SQL via console interno
API_DELPI_INTERNAL_SERVICE_TOKEN=... python scripts/run_sql_investigation.py \
  reconcile_stock_value_period.sql
```

O SQL executa cinco blocos por filial (`01`, `02`):

```sql
-- (1) Estimativa atual — espelha CTE ultima_data_sb9 + fechamento_base + movimentos_sd3
-- (2) Fechamento oficial MAX(B9_DATA) <= end_date
-- (3) Fechamento exato B9_DATA = end_date (inventário)
-- (4) Saldo atual SB2
-- (5) Últimas datas SB9 por filial (auditoria)
```

Trecho legado (referência manual):

### 7.2 Checklist W0

- [ ] Confirmar se existe `B9_DATA = 20260531` por filial
- [ ] Comparar (2) com Registro de Inventário **EM ESTOQUE**
- [ ] Comparar (1) com resposta atual da API (`curl` autenticado)
- [ ] Se (2) ≈ oficial e (1) ≪ oficial → **W2 é a correção principal**
- [ ] Se (2) também diverge do oficial → problema **TOTVS/fechamento**, escalar DBA/Protheus
- [ ] Registrar `closing_base_date`, `bridge_value`, `period_net_value` por filial na planilha de reconciliação

### 7.3 Saída W0

Documento gerado automaticamente:

`docs/roadmaps/evidencias/estoque-reconciliacao-<end_date>.md` (+ `.json`)

**Resultado maio/2026 (jun/2026 — ambiente TOTVS):**

| Achado | Detalhe |
|--------|---------|
| API = SQL | Estimativa bate com o repositório (sem bug de código) |
| SB9 em `20260531` | **Inexistente** em `SB9010` |
| Último fechamento SB9 | `20260228` (mar/abr/mai ausentes) |
| Filial 01 estimada | R$ 281k (base R$ 3,47M + ponte/período SD3 **−R$ 3,19M**) |
| Filial 02 estimada | R$ 4,91M (base R$ 9,64M + ponte/período SD3 **−R$ 4,72M**) |
| SB2 atual | ~R$ 3,55M (01) e ~R$ 10,17M (02) — **próximo do inventário oficial** |

**Implicação:** W2 só resolve quando houver fechamento SB9 na `end_date` (ou mensal até o período). Enquanto SB9 parar em fev/2026, a estimativa SD3 **subestima** o estoque. Próximo passo operacional: Controladoria (fechamentos SB9) + decisão D1 sobre fallback (SB2 / aviso forte na UI).

---

## 8. Onda W1 — Transparência e auditoria ✅ (jun/2026)

**Entregue:** breakdown na API (`estimation` + `by_branch`) e painel no MFE `StockPage`.

**Objetivo:** usuário e console conseguem ver **por que** o número é o que é, sem alterar ainda a regra principal.

### 8.1 API — enriquecer `by_branch` e `estimation`

| Campo novo | Onde | Descrição |
|------------|------|-----------|
| `closing_base_date` | `by_branch[]` | `MAX(B9_DATA) < start_date` |
| `closing_base_value` | `by_branch[]` | Soma SB9 na data base |
| `bridge_value` | `by_branch[]` | SD3 entre fechamento e `start_date` |
| `period_net_value` | `by_branch[]` | SD3 no período |
| `official_closure_available` | `estimation` | `true` se existe SB9 com `B9_DATA <= end_date` |
| `official_closure_date` | `estimation` | Data do fechamento disponível (se houver) |
| `official_closure_value` | `estimation` | Soma SB9 nessa data (filial ou consolidado) |

**Implementação:**

1. Estender CTE `ultima_data_sb9` ou adicionar CTE `fechamento_oficial_fim` em `stock_value_historical_sql.py`.
2. Agregar breakdown no `HISTORICAL_STOCK_BY_BRANCH_SQL` (ou query auxiliar no repositório).
3. Use case monta `estimation` com flags — **sem strings PT novas em Python** (notas em JSON de conteúdo se necessário para chat; ver `assistant-content-json` no pacote chat).

### 8.2 MFE — `StockPage.tsx`

- Card ou tooltip: “Base SB9: {data} · Ponte: R$ … · Período: R$ …”
- Se `official_closure_available` e valor divergente da estimativa: banner **informativo** (não alarmista) sugerindo fechamento oficial disponível (prepara W2).
- Manter subtítulo atual; adicionar link para doc interna.

### 8.3 Console Saúde SQL

- Incluir no metadata da operação `get_supplies_stock_value` os campos de breakdown quando existirem (facilita suporte).

### 8.4 Testes W1

| Teste | Arquivo |
|-------|---------|
| SQL contém agregação de breakdown | `tests/test_stock_value_query_repository_sql.py` |
| Payload `by_branch` com novos campos | `tests/test_get_stock_value_use_case.py` |
| Snapshot JSON OpenAPI / golden | Atualizar se contrato público mudar |

---

## 9. Onda W2 — Modo fechamento oficial na `end_date` ✅ (jun/2026)

**Entregue:** `stock_method=auto|estimated|official_closure`, SQL SB9 na `end_date`, fan-out consolidado histórico, MFE com banner oficial.

**Objetivo:** quando o inventário já foi fechado na SB9 na data fim do período, o dashboard mostra esse valor.

### 9.1 Regra proposta

```text
closure_end = MAX(B9_DATA) WHERE B9_DATA <= end_date AND B9_DATA <> ''

SE closure_end existe E usuário não forçou estimativa:
  method = sb9_closure_on_end_date
  total = SUM(B9_VINI1) WHERE B9_DATA = closure_end
SENÃO:
  method = sb9_last_closure_plus_sd3_movements  (atual)
```

### 9.2 Parâmetro opcional (query)

| Query | Valores | Default |
|-------|---------|---------|
| `stock_method` | `auto` \| `estimated` \| `official_closure` | `auto` |

- `auto`: W2 acima.
- `estimated`: força SB9+SD3 (comportamento atual).
- `official_closure`: exige fechamento; erro amigável se ausente.

### 9.3 Implementação SQL

Nova variante em `stock_value_historical_sql.py`:

- `HISTORICAL_STOCK_OFFICIAL_CLOSURE_SQL` — leitura direta SB9 em `closure_end`, agregação por filial/local/produto (mesma forma do bundle).
- Reutilizar paths de cache com sufixo `|method=official` vs `|method=estimated`.

### 9.4 Impacto em consumidores

| Consumidor | Ação |
|------------|------|
| `dashboard-supplies` | `stock_method=auto` implícito; UI mostra badge “Fechamento SB9 em 31/05/2026” |
| IDD | Documentar que estoque do IDD passa a seguir `auto` |
| Chat | `estimation.method` no metadata; presenter genérico — sem `if` por rota |
| Metas | Validar se meta compara com mesmo método |

### 9.5 Critério de aceite W2

Para `branch=01`, `start_date=2026-05-01`, `end_date=2026-05-31`:

- Se SB9 em `20260531` existir: `total_stock_value` ≈ **EM ESTOQUE** do Registro (tolerância D3).
- `estimation.method` = `sb9_closure_on_end_date`.
- Regressão: cenário abril/2026 **sem** fechamento em `end_date` mantém totais atuais da estimativa.

---

## 10. Onda W3 — EM PROCESSO (opcional)

**Somente se D2 = Sim.**

### 10.1 Escopo

O Registro separa **EM ESTOQUE** (SB9 por família) e **EM PROCESSO** (WIP — MP/PA/PI em ordens abertas).

Fontes candidatas (validar com Protheus local):

| Fonte | Uso típico | Risco |
|-------|------------|-------|
| Relatório / view já usada pelo MATR460 | Paridade máxima | Pode não existir como view SQL |
| `SC2010` + estrutura de OP | WIP por ordem | Regra de custo médio |
| Movimentos SD3 tipos específicos | Parcial | Pode duplicar com SB9 |

### 10.2 Contrato API (separado do KPI principal)

Opção A (recomendada): segundo bloco no payload, não misturado silenciosamente:

```json
{
  "summary": { "total_stock_value": 3598312.40 },
  "wip": {
    "enabled": true,
    "total_wip_value": 263790.57,
    "method": "protheus_wip_snapshot",
    "note": "..."
  },
  "grand_total": { "total_stock_value": 3862102.97 }
}
```

Opção B: query `include_wip=true` soma ao total — **só com opt-in explícito**.

### 10.3 Nova rota?

Preferir estender `/supplies/stock-value` com `include_wip` antes de criar rota nova. Se rota nova for necessária → seguir `new-api-route-checklist.mdc` completo (api-delpi + registry chat + perfil).

---

## 11. Onda W4 — Chat, SI, documentação e gates

### 11.1 Documentação

- Atualizar [supplies-estoque-historico.md](../api/supplies-estoque-historico.md) com modos `auto` / `official_closure` / `estimated`.
- Atualizar [06-modulos-departamentais.md](../api/06-modulos-departamentais.md) § Suprimentos.
- Changelog: `api-delpi/docs/changelog/2026-06-estoque-supplies-reconciliacao.md`.

### 11.2 Chat (`minha-delpi-ai-api`)

- Se comportamento mudar: caso em `chat_intelligence_regression_cases.py` ou `operational_presentation_quality_cases.py`.
- Textos de `reason` / notas → `assistant/*.json` (`assistant-content-json.mdc`).
- Apresentação: perfil existente de KPI/série — **sem presenter por rota**.

### 11.3 Gates CI

```bash
cd api-delpi
pytest tests/test_stock_value_query_repository_sql.py tests/test_get_stock_value_use_case.py -q
pytest tests/test_get_inventory_turnover_use_case.py -q   # herda estoque
# Após W2 com contrato novo:
pytest tests/ -q -k "get_supplies_stock_value or stock_value"
```

Medir no container TOTVS (regra `sql-query-development.mdc`):

- Latência `get_supplies_stock_value` summary consolidado (cache frio vs quente).
- Plano de execução SB9/SD3 se novo CTE de fechamento oficial.

---

## 12. Matriz de riscos

| Risco | Mitigação |
|-------|-----------|
| Fechamento SB9 parcial (só alguns locais) | Validar cobertura por `B9_LOCAL`; aviso `dataCoverage` se incompleto |
| Cache servir método errado após deploy | Incluir `stock_method` na chave `stock_value_cache_key` |
| IDD e CPV desalinhados temporalmente | Documentar; IDD já exige mesmo período |
| Usuário acha que SB2 atual = inventário de maio | UI: sem datas = SB2; com datas = histórico/fechamento |
| Duplicar WIP com SB9 | W3 só após mapeamento com Controladoria |

---

## 13. Ordem de execução recomendada

```text
1. W0 — SQL reconciliação (1–2 dias, Suprimentos + dev)
2. Decisão D1–D4 (reunião curta)
3. W1 — breakdown na API + MFE (entrega rápida, baixo risco)
4. W2 — modo official_closure / auto (correção principal se W0 confirmar hipótese)
5. W3 — só se necessário para paridade TOTAL GERAL
6. W4 — chat, docs, regressão
```

**Não pular W0.** Implementar W2 sem evidência repete o risco de “corrigir” o número errado.

---

## 14. Definição de pronto (DoD)

- [ ] Planilha W0 arquivada com gap explicado por filial
- [ ] D1–D4 respondidas por stakeholder
- [ ] API expõe método usado e breakdown (`estimation` + `by_branch`)
- [ ] Com fechamento em `end_date`, total ≈ EM ESTOQUE oficial (tolerância acordada)
- [ ] MFE deixa claro: estimativa vs fechamento vs EM PROCESSO (se W3)
- [ ] Testes unitários verdes nos pacotes tocados
- [ ] Doc `supplies-estoque-historico.md` atualizada
- [ ] Sem `slow_sql` novo sem medição (cache / índices)

---

## 15. Referências rápidas

| Item | Local |
|------|-------|
| SQL histórico | `stock_value_historical_sql.py` |
| `operation_id` | `get_supplies_stock_value` |
| MFE Estoque | `plugins/dashboard-supplies/src/pages/StockPage.tsx` |
| Tabela SB9 | `allowed_tables.json` — inventário / MATR460 |
| Performance estoque | `supplies-estoque-historico.md` § Implementação SQL |
| Regra SQL | `.cursor/rules/sql-query-development.mdc` |

---

## Histórico

| Data | Autor | Nota |
|------|-------|------|
| jun/2026 | — | Playbook inicial — gap maio/2026 filiais 01 e 02 vs Registro de Inventário |
