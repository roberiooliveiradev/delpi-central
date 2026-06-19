# Comercial — taxa de conversão, status e estágios do funil (TOTVS)

**Última atualização:** jun/2026  
**Rota analisada:** `GET /commercial/closing-rate` (`operationId`: `get_sales_conversion_rate`)  
**Caso de referência:** dashboard comercial com filtro `start_date=2026-05-01` e `end_date=2026-05-31` (maio/2026, todas as filiais).

---

## 1. Resumo executivo

No período filtrado, o dashboard exibe **1 ganha / 41 propostas (2,44%)** porque a API considera **convertida** apenas a oportunidade com **`AD1_STATUS = '9'`** (status TOTVS **Ganha**).

No mesmo período existem **10 propostas no estágio `000013` (ENCERRADO)**, mas **9 delas continuam com status `1` (Aberta)** — ou seja, chegaram ao fim do fluxo no funil, porém **não** estão marcadas como ganhas no Protheus.

**Conclusão:** estágio 13 (`000013`) **não é sinônimo** de conversão comercial. O indicador correto de «ganhou o negócio» no TOTVS é o **status `9`**, não o estágio isolado.

---

## 2. Regra implementada hoje na api-delpi

Implementação: `SalesConversionRateRepository` → tabela `AD1010`.

| Conceito | Campo / critério |
|----------|------------------|
| Base | `AD1010` (cabeçalho da oportunidade / OV no CRM) |
| Período | `AD1_DATA` entre `start_date` e `end_date` |
| Total (`qtd_proposals`) | Revisões com `AD1_DATA` no período (cada revisão conta; não colapsa na última da proposta) |
| Ganha (`qtd_won`) | Revisões do período com `AD1_STATUS = '9'` (Ganha) — **não** exige estágio `000013` |
| Taxa | `qtd_won / qtd_proposals × 100` |

Constante de domínio: `WON_STATUS_CODE = "9"` em `commercial_proposal_status.py`.

A listagem `GET /commercial/proposals?status=won` usa a **mesma** regra (`AD1_STATUS = '9'`).

**Não usa histórico (`AIJ010`).** O campo `AIJ_STATUS` existe na tabela de eventos, mas é outro domínio (ver § 2.1).

---

## 2.1 Status `9`: cabeçalho (`AD1010`) vs histórico (`AIJ010`)

São **dois campos diferentes** no Protheus:

| Origem | Campo | Descrição (SX3) | Significado do código `9` na api-delpi |
|--------|-------|-----------------|----------------------------------------|
| **Cabeçalho** | `AD1010.AD1_STATUS` | Status da Oportunidade | **Ganha** (`commercial_proposal_status.py`) |
| **Histórico** | `AIJ010.AIJ_STATUS` | Status do Est. Encerrado | **Concluído** (`lmp_history_event_enrichment.py` → `AIJ_STATUS_LABELS`) |

A rota `/commercial/closing-rate` lê **somente `AD1_STATUS` no cabeçalho** da revisão retornada pela query — **não** percorre `AIJ010` nem verifica se houve evento com `AIJ_STATUS = '9'`.

### Mapeamento `AIJ_STATUS` (histórico de estágios)

| Código | Rótulo no histórico |
|--------|---------------------|
| `1` | Em andamento |
| `2` | Encerrado |
| `3` | Cancelado |
| `4` | Suspenso |
| `5` | Aguardando |
| `6` | Reprovado |
| **`7`** | **Aprovado** |
| `8` | Finalizado |
| **`9`** | **Concluído** |

Ou seja: **`AIJ_STATUS = '9'` ≠ `AD1_STATUS = '9'`**. Confundir os dois subcampos levaria a regra errada.

---

## 2.2 Avaliação no período filtrado (mai/2026) — propostas com status `9`

Filtro do dashboard: `AD1_DATA` entre `2026-05-01` e `2026-05-31`.

### Cabeçalho `AD1_STATUS = '9'` (regra da API)

| Critério | Quantidade |
|----------|----------:|
| Última revisão com `AD1_STATUS = '9'` | **1** |
| Qualquer revisão no período com `AD1_STATUS = '9'` | **1** |
| Última revisão ganha com `AD1_DTFIM` no período | **1** |

**Única proposta:**

| Filial | OV | Revisão | `AD1_STATUS` | Estágio | Processo | `AD1_DATA` | `AD1_DTFIM` |
|--------|-----|---------|--------------|---------|----------|------------|-------------|
| `02` | `000102` | `04` | `9` Ganha | `000013` ENCERRADO | MODIFICACAO | 2026-05-07 | 2026-05-08 |

### Histórico `AIJ010` no mesmo período

| Critério | Quantidade |
|----------|----------:|
| Eventos com `AIJ_STATUS = '9'` (Concluído) e data no período | **0** |
| Eventos com `AIJ_STATUS = '7'` (Aprovado) e data no período | **0** |
| Propostas do período com **algum** evento `AIJ_STATUS = '9'` | **0** |
| Propostas do período com **algum** evento `AIJ_STATUS = '7'` | **0** |

### Cabeçalho vs histórico na OV ganha (`02` / `000102`)

Na revisão `04`, o cabeçalho está **Ganha (`AD1_STATUS = 9`)**, mas o evento de histórico no estágio `000013` ENCERRADO registra **`AIJ_STATUS = 1` (Em andamento)** — não `9` nem `7` (Aprovado):

```
AIJ rev.04 → estágio 000013 ENCERRADO → AIJ_STATUS = 1 (Em andamento)
AD1 rev.04 → AD1_STATUS = 9 (Ganha)
```

Isso confirma que a conversão **não** é derivada do histórico; o flag «ganha» está **apenas no cabeçalho** `AD1010`.

### As outras 9 propostas em estágio `000013` (ENCERRADO)

Todas com **`AD1_STATUS = 1` (Aberta)** no cabeçalho. Na maioria **não há** evento correspondente em `AIJ010` na última revisão (histórico incompleto ou estágio gravado só no cabeçalho). **Nenhuma** delas tem `AD1_STATUS = '9'`.

| Filial | OV | Revisão | `AD1_STATUS` | `AD1_DTFIM` |
|--------|-----|---------|--------------|-------------|
| 01 | 003567 | 05 | 1 Aberta | — |
| 01 | 003568 | 03 | 1 Aberta | — |
| 01 | 003571 | 03 | 1 Aberta | — |
| 01 | 003572 | 06 | 1 Aberta | — |
| 01 | 003573 | 04 | 1 Aberta | — |
| 01 | 003574 | 05 | 1 Aberta | — |
| 01 | 003578 | 14 | 1 Aberta | — |
| 02 | 000111 | 03 | 1 Aberta | — |
| 02 | 000120 | 07 | 1 Aberta | 2026-05-27 |

**Resposta direta:** no período filtrado, **só 1 proposta tem `AD1_STATUS = 9` no cabeçalho** — e **nenhuma** tem status `9` no histórico `AIJ010`. Por isso o KPI mostra 1 ganha.


### 3.1 Números do período (revisões com `AD1_DATA` no filtro)

Consulta equivalente à regra da API: **cada revisão** cuja `AD1_DATA` cai entre `start_date` e `end_date` (sem colapsar na última revisão global da proposta).

| Métrica | Valor |
|---------|------:|
| Total de propostas | **41** |
| Status **Ganha** (`9`) | **1** |
| Estágio **ENCERRADO** (`000013`) | **10** |
| Ganha **e** ENCERRADO | **1** |
| ENCERRADO com status **Aberta** (`1`) | **9** |

Taxa com regra atual: **1 ÷ 41 = 2,44%**.

### 3.2 A única proposta «ganha»

| Campo | Valor |
|-------|-------|
| Filial | `02` |
| Oportunidade | `000102` |
| Processo | `000003` — MODIFICACAO |
| Estágio | `000013` — ENCERRADO |
| Status | `9` — Ganha |

### 3.3 Por que as outras 40 não entram como convertidas

| Situação | Qtd | Motivo |
|----------|----:|--------|
| Em andamento (status Aberta, estágios intermediários) | 31 | Ainda não marcadas como Ganha (`9`) |
| ENCERRADO com status Aberta | 9 | Funil encerrado, mas **sem** flag de vitória comercial |
| **Total não convertido pela regra atual** | **40** | Nenhuma tem `AD1_STATUS = '9'` |

As **9** em ENCERRADO com status Aberta são o principal motivo de confusão: visualmente estão no «estágio 13», mas o TOTVS **não** as classifica como ganhas.

---

## 4. Distribuição por estágio em maio/2026

Contagem por **processo + estágio + status** (última revisão, `AD1_DATA` no período):

| Processo | Estágio | Descrição (AC2010) | Status | Qtd | % do total |
|----------|---------|-------------------|--------|----:|----------:|
| OPORTUNIDADE (`000002`) | `000006` | PROPOSTA ENVIADA/AGUARD RETORN | Aberta (`1`) | **17** | 41,5% |
| OPORTUNIDADE (`000002`) | `000002` | COTACAO | Aberta (`1`) | **8** | 19,5% |
| MODIFICACAO (`000003`) | `000013` | ENCERRADO | Aberta (`1`) | **8** | 19,5% |
| OPORTUNIDADE (`000002`) | `000005` | PROPOSTA CONCLUIDA | Aberta (`1`) | **3** | 7,3% |
| OPORTUNIDADE (`000002`) | `000001` | ANALISE CRITICA | Aberta (`1`) | **1** | 2,4% |
| OPORTUNIDADE (`000002`) | `000007` | AMOSTRA PCP | Aberta (`1`) | **1** | 2,4% |
| OPORTUNIDADE (`000002`) | `000013` | ENCERRADO | Aberta (`1`) | **1** | 2,4% |
| MODIFICACAO (`000003`) | `000002` | COTACAO | Aberta (`1`) | **1** | 2,4% |
| MODIFICACAO (`000003`) | `000013` | ENCERRADO | **Ganha (`9`)** | **1** | 2,4% |
| | | | **Total** | **41** | 100% |

### 4.1 Agregado só por estágio (todas as propostas)

| Estágio | Descrição | Qtd |
|---------|-----------|----:|
| `000006` | PROPOSTA ENVIADA/AGUARD RETORN | 17 |
| `000002` | COTACAO | 9 |
| `000013` | ENCERRADO | 10 |
| `000005` | PROPOSTA CONCLUIDA | 3 |
| `000001` | ANALISE CRITICA | 1 |
| `000007` | AMOSTRA PCP | 1 |

Nenhuma proposta em maio/2026 usou processo **COMPONENTES** (`000001`).

---

## 5. Status da oportunidade (`AD1_STATUS`)

Campo: **Status da Oportunidade** (`AD1010.AD1_STATUS`, 1 caractere).

Mapeamento usado na api-delpi (`commercial_proposal_status.py`):

| Código | Rótulo | Categoria na API |
|--------|--------|------------------|
| `1` | Aberta | `open` |
| `2` | Em andamento | `open` |
| `3` | Em negociação | `open` |
| `4` | Aguardando cliente | `open` |
| `5` | Aguardando interno | `open` |
| `6` | Suspensa | `open` |
| `7` | Cancelada | `open` |
| `8` | Perdida | `lost` |
| **`9`** | **Ganha** | **`won`** |
| `X` | Perdida | `lost` |

**Para taxa de conversão:** somente **`9` (Ganha)** entra no numerador hoje.

---

## 6. Estágios do funil — o que cada um significa

### 6.1 Regra de leitura

- Estágio = par **`AD1_PROVEN` (processo) + `AD1_STAGE` (código)**.
- Descrição oficial: tabela **`AC2010`** (Estágios do Processo de Vendas).
- Processo: tabela **`AC1010`**.
- **O mesmo código de estágio pode ter significados diferentes em processos distintos** — sempre resolver via `AC2010`, nunca assumir que «estágio 13» é igual em todo o CRM.

Consulta canônica (rotas `/data/sql` + whitelist):

```sql
SELECT
    AC2.AC2_PROVEN AS processo,
    AC1.AC1_DESCRI AS processo_descricao,
    AC2.AC2_STAGE AS estagio,
    LTRIM(RTRIM(AC2.AC2_DESCRI)) AS estagio_descricao
FROM AC2010 AC2
LEFT JOIN AC1010 AC1
  ON AC1.AC1_PROVEN = AC2.AC2_PROVEN
 AND AC1.D_E_L_E_T_ <> '*'
WHERE AC2.D_E_L_E_T_ <> '*'
ORDER BY AC2.AC2_PROVEN, AC2.AC2_STAGE;
```

Metadados dos campos: `GET /system/tables/AD1010/columns/search?q=STAGE` e `?q=STATUS`.

---

### 6.2 Processo `000001` — COMPONENTES

Funil voltado a componentes; **não possui estágio `000013`**.

| Estágio | Significado operacional |
|---------|-------------------------|
| `000001` | Apresentação da empresa ao cliente |
| `000002` | Levantamento das necessidades |
| `000003` | Elaboração da proposta técnica |
| `000004` | Elaboração da proposta comercial |
| `000005` | Apresentação da proposta ao cliente |
| `000006` | Aguardando retorno do cliente |
| `000007` | Follow-up comercial |
| `000008` | Elaboração de amostra |
| `000009` | Revisão técnica |
| `000010` | Revisão comercial |
| `000011` | Negociação / fechamento — estágio final deste processo |

---

### 6.3 Processo `000002` — OPORTUNIDADE

Principal processo das 31 propostas «em aberto» no período de referência.

| Estágio | Significado operacional |
|---------|-------------------------|
| `000001` | Análise crítica inicial da oportunidade |
| `000002` | Cotação em elaboração |
| `000003` | Engenharia (desenvolvimento técnico) |
| `000004` | Finalização da cotação |
| `000005` | Proposta concluída (pronta, ainda sem fechamento comercial) |
| `000006` | Proposta enviada; aguardando retorno do cliente |
| `000007` | Amostra em PCP |
| `000008` | Amostra em engenharia |
| `000009` | Relatório de qualidade |
| `000010` | Amostra enviada à área de vendas |
| `000011` | Homologação de produto |
| `000012` | Lançamento / homologação (entrada em carteira técnica) |
| **`000013`** | **Encerrado** — fim do fluxo; **não implica ganha** sem `AD1_STATUS = '9'` |

---

### 6.4 Processo `000003` — MODIFICACAO

Mesma estrutura de estágios que OPORTUNIDADE (`000001`–`000013`), com significados equivalentes na `AC2010`.

No período de referência concentra as propostas em **ENCERRADO** (`000013`): 8 abertas + 1 ganha.

---

## 7. Estágio 13 vs «proposta aprovada / convertida»

| Interpretação | O que o TOTVS mostra |
|---------------|----------------------|
| «Chegou no estágio 13» | `AD1_STAGE = '000013'` → rótulo **ENCERRADO** |
| «Proposta convertida / ganha» | `AD1_STATUS = '9'` → rótulo **Ganha** |

No cadastro consultado **não existe** estágio com descrição «Aprovada». Os estágios mais próximos de conclusão operacional são:

- `000005` — PROPOSTA CONCLUIDA (documento pronto)
- `000011` / `000012` — homologação / lançamento
- `000013` — ENCERRADO (fim do fluxo)

**ENCERRADO** pode representar encerramento **com ou sem** vitória comercial — daí as 9 propostas em `000013` com status Aberta em maio/2026.

---

## 8. Impacto se a regra mudar

| Regra hipotética | Ganhas (mai/2026) | Taxa |
|------------------|------------------:|-----:|
| Atual: `AD1_STATUS = '9'` | 1 | 2,44% |
| Só `AD1_STAGE = '000013'` | 10 | 24,39% |
| `000013` **e** `AD1_STATUS = '9'` | 1 | 2,44% |

Alterar para «estágio 13» isolado **multiplicaria por ~10** o numerador sem garantir que o negócio foi ganho.

---

## 9. Como reproduzir a análise (rotas `/system` e `/data/sql`)

1. **Metadados** (sem dados sensíveis):
   - `GET /system/tables/AD1010/columns/search?q=STAGE`
   - `GET /system/tables/AC2010/schema`
   - `GET /system/tables/search?description=estagio`

2. **Catálogo de estágios** — `POST /data/sql` com a query da seção 6.1.

3. **Contagem do período** — exemplo para maio/2026:

```sql
WITH ovs_base AS (
    SELECT DISTINCT
        AD1.AD1_FILIAL,
        AD1.AD1_NROPOR,
        AD1.AD1_REVISA,
        AD1.AD1_STATUS,
        AD1.AD1_STAGE,
        AD1.AD1_PROVEN
    FROM AD1010 AD1
    WHERE AD1.D_E_L_E_T_ <> '*'
      AND AD1.AD1_DATA >= '20260501'
      AND AD1.AD1_DATA <= '20260531'
)
SELECT
    COUNT(*) AS total,
    SUM(CASE WHEN AD1_STATUS = '9' THEN 1 ELSE 0 END) AS ganhas_status_9,
    SUM(CASE WHEN AD1_STAGE = '000013' THEN 1 ELSE 0 END) AS estagio_13
FROM ovs_base;
```

Permissão: `api-delpi.data` ou `api-delpi.access.full`. Tabelas na whitelist: `allowed_tables.json`.

---

## 10. Referências no repositório

| Artefato | Caminho |
|----------|---------|
| SQL da taxa de conversão | `app/infrastructure/persistence/totvs/commercial_repositories/sales_conversion_rate_repository.py` |
| Status ganha/perdida | `app/domain/services/commercial_proposal_status.py` |
| Listagem de propostas | `app/infrastructure/persistence/totvs/commercial_repositories/commercial_proposals_repository.py` |
| Rota HTTP | `app/interface/http/routes/commercial/commercial_router.py` (`/closing-rate`) |
| Funil LMP (processo + estágio) | `documentos/Routes/documentacao_completa_da_rota_lmp.md` § AC2010 |
| Dashboard consumidor | `plugins/dashboard-commercial` → `ConversionFunnelChart.tsx` |

---

## 11. Regra acordada (jun/2026)

1. **Conversão = `AD1_STATUS = '9'`** (Ganha) nas revisões com `AD1_DATA` no período — alinhado ao flag TOTVS.
2. **Não** usar estágio `000013` (ENCERRADO) como critério de ganha; estágio 13 pode existir com status Aberta.
3. Dashboard/funil: «ganha» = **status 9**, não estágio 13.
4. Métrica de «chegou ao fim do funil» (`000013`) deve ser **indicador separado**, se necessário.
5. `closing-rate` conta **revisões do período** (`AD1_DATA` entre `start_date` e `end_date`), não a última revisão global da proposta.
