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
| Período (denominador) | `AD1_DATA` entre `start_date` e `end_date` — propostas **abertas** no período |
| Total (`qtd_proposals`) | Revisões com `AD1_DATA` no período (cada revisão conta; não colapsa na última da proposta) |
| Ganha (`qtd_won`) | Última revisão por OV com `AD1_STATUS = '9'` e data de aceite (`AD1_DTASSI`, fallback `AD1_DTFIM`) no intervalo — **independente** da data de abertura |
| Taxa | `qtd_won / qtd_proposals × 100` (ganhas com aceite no período ÷ revisões abertas no período) |

Constante de domínio: `WON_STATUS_CODE = "9"` em `commercial_proposal_status.py`.

A listagem `GET /commercial/proposals?status=won` filtra por **aceite** (`AD1_DTASSI`, fallback `AD1_DTFIM`) no período. A coluna **Fim** exibe essa mesma data. Filtro «todas» / «em aberto» continua por abertura (`AD1_DATA`).

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
| Revisões no período com `AD1_STATUS = '9'` | **1** |
| Revisões no período com `AD1_STAGE = '000009'` (Relatório Qualidade) | **0** |
| Revisões ganhas com `AD1_DTFIM` no período (qualquer data de abertura) | **5** (fora do denominador se `AD1_DATA` não estiver no mês) |

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

### 2.3 Por que o indicador «não pega o 9» nas outras propostas em estágio 13

Três confusões recorrentes na leitura do KPI:

| O que se imagina | O que o sistema usa | Entra na taxa? |
|------------------|---------------------|:--------------:|
| «Está no estágio **13** (Encerrado)» | `AD1_STAGE = '000013'` | Não |
| «Passou pelo estágio **9** do funil» (Relatório de Qualidade) | `AD1_STAGE = '000009'` em algum evento | Não |
| «Status **Ganha** no cabeçalho» | `AD1_STATUS = '9'` | **Sim** |

No período de referência:

- **0** revisões com `AD1_STAGE = '000009'` (nenhuma proposta *parada* nesse estágio na data de abertura filtrada).
- **10** revisões com `AD1_STAGE = '000013'`, mas **9** mantêm `AD1_STATUS = '1'` (Aberta).
- O Protheus **não preenche automaticamente** `AD1_STATUS = '9'` ao mover para ENCERRADO — o flag Ganha é independente do estágio.

**Caso ilustrativo:** `02/000120` tem `AD1_DTFIM = 20260527` (data de encerramento preenchida) e estágio `000013`, porém `AD1_STATUS` continua `1` (Aberta). Por isso **não entra** no numerador, embora visualmente pareça «encerrada».

**Decisão de negócio (jun/2026):** manter conversão = `AD1_STATUS = '9'`; não usar estágio 13 como proxy de vitória.

---

## 3. Análise do período de referência (mai/2026)

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

### 3.4 Cadastro detalhado — as 10 propostas em estágio `000013` (ENCERRADO)

Dados do cabeçalho `AD1010` (revisão com `AD1_DATA` no período). Útil para alinhamento com o time comercial.

| # | Filial | OV | Rev. | Descrição (`AD1_DESCRI`) | Processo | Abertura (`AD1_DATA`) | Fim (`AD1_DTFIM`) | `AD1_STATUS` | Conta na taxa? |
|---|--------|-----|------|--------------------------|----------|----------------------|-------------------|--------------|:--------------:|
| 1 | `01` | `003567` | `05` | BUHLER - 1 ITEM | OPORTUNIDADE | 2026-05-08 | — | `1` Aberta | Não |
| 2 | `01` | `003568` | `03` | WEG MOTORES | MODIFICACAO | 2026-05-08 | — | `1` Aberta | Não |
| 3 | `01` | `003571` | `03` | WEG MOTORES | MODIFICACAO | 2026-05-14 | — | `1` Aberta | Não |
| 4 | `01` | `003572` | `06` | WEG ENERGIA | MODIFICACAO | 2026-05-14 | — | `1` Aberta | Não |
| 5 | `01` | `003573` | `04` | WEG ENERGIA | MODIFICACAO | 2026-05-14 | — | `1` Aberta | Não |
| 6 | `01` | `003574` | `05` | WEG ENERGIA | MODIFICACAO | 2026-05-15 | — | `1` Aberta | Não |
| 7 | `01` | `003578` | `14` | BUHLER - 1 ITEM | MODIFICACAO | 2026-05-08 | — | `1` Aberta | Não |
| 8 | `02` | `000102` | `04` | REV. DES. WANKE-SECADORA | MODIFICACAO | 2026-05-07 | 2026-05-08 | **`9` Ganha** | **Sim** |
| 9 | `02` | `000111` | `03` | WEG LINHARES | MODIFICACAO | 2026-05-12 | — | `1` Aberta | Não |
| 10 | `02` | `000120` | `07` | WEG LINHARES | MODIFICACAO | 2026-05-27 | 2026-05-27 | `1` Aberta | Não |

**Resumo:** 9 propostas precisariam de **revisão de cadastro no Protheus** (marcar Ganha ou Perdida conforme o desfecho real) se a expectativa operacional for que ENCERRADO implique conversão.

### 3.5 Trilhas do funil (histórico `AIJ010`) até o estágio 13

Consulta por **revisão atual** da proposta (`AIJ_REVISA` = revisão do período). Estágios resolvidos via `AC2010`.

**Padrão dominante (9 de 10):** percurso completo `000001` → `000012` → `000013`, com estágio imediatamente anterior ao 13 = **`000012` (LANÇAMENTO / HOMOLOGAÇÃO)**.

| Filial / OV | Rev. | Status cabeçalho | Trilha até o 13 (estágios distintos, em ordem) | Antes do 13 |
|-------------|------|------------------|--------------------------------------------------|-------------|
| `01/003567` | `05` | Aberta | 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 → 13 | 12 |
| `01/003568` | `03` | Aberta | 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 → 13 | 12 |
| `01/003571` | `03` | Aberta | 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 → 13 | 12 |
| `01/003572` | `06` | Aberta | 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 → 13 | 12 |
| `01/003573` | `04` | Aberta | 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 → 13 | 12 |
| `01/003574` | `05` | Aberta | 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 → 13 | 12 |
| `01/003578` | `14` | Aberta | 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 → 13 | 12 |
| `02/000102` | `04` | **Ganha** | 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 → 13 | 12 |
| `02/000111` | `03` | Aberta | Histórico atípico: primeiro evento já em `000013`; demais estágios registrados depois, sem sequência clara 1→12→13 | — |
| `02/000120` | `07` | Aberta | 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 → 13 | 12 |

Legenda dos códigos (processos OPORTUNIDADE / MODIFICACAO):

| Código | Descrição (AC2010) |
|--------|-------------------|
| `000001` | ANÁLISE CRÍTICA |
| `000002` | COTAÇÃO |
| `000003` | ENGENHARIA |
| `000004` | FINALIZAÇÃO DE COTAÇÃO |
| `000005` | PROPOSTA CONCLUÍDA |
| `000006` | PROPOSTA ENVIADA / AGUARD. RETORNO |
| `000007` | AMOSTRA PCP |
| `000008` | AMOSTRA ENGENHARIA |
| `000009` | RELATÓRIO QUALIDADE |
| `000010` | AMOSTRA ENVIADA A VENDAS |
| `000011` | HOMOLOGAÇÃO DE PRODUTO |
| `000012` | LANÇAMENTO / HOMOLOGAÇÃO |
| `000013` | ENCERRADO |

**Leitura:** as propostas **passaram pelo estágio 9 do funil** (Relatório de Qualidade) no histórico — isso **não** equivale ao **status 9 (Ganha)** do cabeçalho.

Query de reprodução (exemplo `02/000102`, revisão `04`):

```sql
SELECT AIJ_REVISA, AIJ_STAGE, AIJ_PROVEN, AIJ_STATUS, AIJ_DTINIC, AIJ_DTENCE
FROM AIJ010
WHERE D_E_L_E_T_ <> '*'
  AND AIJ_FILIAL = '02'
  AND AIJ_NROPOR = '000102'
  AND AIJ_REVISA = '04'
ORDER BY AIJ_DTINIC, AIJ_DTENCE;
```

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
| Teste regressão SQL | `api-delpi/tests/test_sales_conversion_rate_repository.py` |

---

## 11. Regra acordada (jun/2026)

1. **Conversão = `AD1_STATUS = '9'`** (Ganha) nas revisões com `AD1_DATA` no período — alinhado ao flag TOTVS.
2. **Não** usar estágio `000013` (ENCERRADO) como critério de ganha; estágio 13 pode existir com status Aberta.
3. Dashboard/funil: «ganha» = **status 9**, não estágio 13.
4. Métrica de «chegou ao fim do funil» (`000013`) deve ser **indicador separado**, se necessário.
5. `closing-rate`: denominador = revisões **abertas** no período (`AD1_DATA`); numerador = ganhas com **fechamento** no período (`AD1_DTFIM` + `AD1_STATUS = '9'`).

---

## 12. Alinhamento comercial e próximos passos

### 12.1 Mensagem para o time comercial (resumo)

Pontos comunicados à liderança comercial (jun/2026):

1. O dashboard de maio/2026 mostra **2,44%** porque só **1 de 41** propostas tem **status Ganha (`9`)** no TOTVS.
2. **10 propostas** estão em **estágio Encerrado (13)**, mas **9** seguem com **status Aberta** — o funil terminou sem marcar vitória comercial.
3. Se a regra de negócio for «estágio 13 = convertida», o cadastro atual **não reflete** isso; a taxa subiria para ~**24%** só em maio/2026, sem garantir que o negócio foi ganho.
4. Ações possíveis: (a) corrigir status no Protheus ao encerrar com vitória; (b) criar indicador separado de «chegou ao fim do funil»; (c) redefinir a regra do KPI (decisão explícita de negócio).

### 12.2 Propostas candidatas a revisão de status no Protheus

As OVs abaixo estão em `000013` com `AD1_STATUS = 1` — validar desfecho real (Ganha `9` ou Perdida `8`) com o responsável comercial:

- `01/003567` — BUHLER - 1 ITEM  
- `01/003568` — WEG MOTORES  
- `01/003571` — WEG MOTORES  
- `01/003572` — WEG ENERGIA  
- `01/003573` — WEG ENERGIA  
- `01/003574` — WEG ENERGIA  
- `01/003578` — BUHLER - 1 ITEM  
- `02/000111` — WEG LINHARES  
- `02/000120` — WEG LINHARES (tem `AD1_DTFIM` preenchido, mas status ainda Aberta)

---

## 13. Histórico da investigação

| Data | Descoberta |
|------|------------|
| jun/2026 | KPI usa `AD1_STATUS = '9'`, não estágio `000013`. |
| jun/2026 | `AIJ_STATUS = '9'` (histórico) ≠ `AD1_STATUS = '9'` (Ganha). |
| jun/2026 | 10 em estágio 13 em mai/2026; 9 com status Aberta no cabeçalho. |
| jun/2026 | Trilha típica até o 13: estágios 1–12 completos; antecessor imediato = 12. |
| jun/2026 | Regra do `closing-rate` ajustada: revisões do período (`AD1_DATA`), não última revisão global. |
| jun/2026 | Constante `WON_STATUS_CODE` centralizada; teste `test_sales_conversion_rate_repository.py`. |
| jun/2026 | **Filtro de conversão:** denominador permanece `AD1_DATA` (abertura); numerador passa a exigir `AD1_DTFIM` no período + `AD1_STATUS = '9'`. Listagem `proposals?status=won` alinhada. Script `scripts/validate_commercial_closing_rate_dtfim.py`. |

### Validação em produção (TOTVS, jun/2026)

Comando:

```bash
docker exec delpi-api-delpi python scripts/validate_commercial_closing_rate_dtfim.py \
  --start 2026-01-01 --end 2026-06-23
```

| Período | Abertas (`AD1_DATA`) | Ganhas legado (só status 9 na cohort) | Ganhas nova (`AD1_DTFIM` + status 9) | Taxa % |
|---------|---------------------:|--------------------------------------:|-------------------------------------:|-------:|
| 2026-01-01 → 2026-06-23 | 331 | 46 | 46 | 13,90 |
| 2026-05-01 → 2026-05-31 | 41 | 5 | 2 | 4,88 |

**OV003446** (caso reportado pelo comercial): abertura `20260130`, fechamento `20260623`, `AD1_STATUS = 9` — entra como ganha no YTD/2026 com a nova regra; no recorte de **maio/2026** não entra no numerador (fechamento em 23/06).

**Observação:** filtro «só hoje» com denominador por abertura retorna 0 propostas se nenhuma OV foi aberta na data — comportamento esperado da regra acordada (cohort aberta no período).
