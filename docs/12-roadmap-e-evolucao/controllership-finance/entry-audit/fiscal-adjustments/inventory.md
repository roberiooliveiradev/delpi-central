# T14 — Inventário dos ajustes do Fiscal (somente leitura)

| Campo | Valor |
|---|---|
| Data | 2026-11-18 |
| HEAD | `784d7047a6` (plano lido em `a6a7dedc88`; `git diff` entre eles = **zero** nos arquivos da auditoria) |
| Fontes | código api-delpi + BFF; Protheus DELPI (leitura, `ENTRY_AUDIT_DB`/`TOTVS_DB`); banco da BFF em PROD (leitura) |
| Regra de dado | só estrutura e contagens — nenhum CNPJ, fornecedor, número ou valor de nota |

## 1. Premissas da seção 1 do plano — verificação no HEAD

| # | Premissa | Estado | Evidência |
|---|---|---|---|
| P1 | api-delpi devolve `invoice_type` (`F1_TIPO`) em `documents` e `documents_by_access_keys`; a BFF não usa | **PROVEN** | `api-delpi/.../financeiro_entry_audit/entry_audit_sql.py:34` (documents) e `:82` (by-access-keys) projetam `F1_TIPO AS invoice_type`; `list_entry_audit_use_case.py:19-36` repassa a linha sem filtrar. Na BFF, `domain/entry_audit/models.py:9-35` (`ProtheusHeader`) não tem o campo, `application/entry_audit/service.py:813-840` (`_header`) não o mapeia e `domain/entry_audit/engine.py:743-754` (`_view`) não o carrega |
| P2 | `key.supplier_mismatch` e `coherence.cfop_vs_state` usam SA2; heurística «seen» de `_supplier_keys` agrupa por código/loja sem o tipo do participante | **PROVEN** | `entry_audit_sql.py:30-32` e `:78-81` — nome/CNPJ/UF vêm só de `SA2010` (`A2_COD`/`A2_LOJA`); nenhum join com `SA1010`. `engine.py:321-343` — `seen[(supplier, store)]` acumula CNPJ de emitente por código/loja; `engine.py:580-581` — `cfop_vs_state` usa `row["state"]` (= `A2_EST`) |
| P3 | `coherence.ipi_on_consumption` por `F4_CONSUMO`/CFOP; existem regras de IPI acima do XML e de IPI sem destaque | **PROVEN** | `engine.py:583` — `consumption = record.consumption_material == "Sim" or suffix in CONSUMPTION_OR_ASSET[:3]`; `:584-588` dispara pela SFT (`line["ipi"]`) ou TES creditando IPI + item com IPI. IPI acima/sem destaque: `item.ipi_credit_mismatch` e `item.ipi_without_tes_decision` (`engine.py:556-573`), `header.ipi_not_booked` (`:184-192`), `item.ipi_base_mismatch` (`:572-573`) |
| P4 | `stable_occurrence_key` com `item` e `field`; `header.icms_base_mismatch` «Acompanha…» como ocorrência própria; `summary.clean`/`divergent` sem olhar status; nenhuma fila entre análises | **PROVEN** | `application/entry_audit/vocabulary.py:83-101` — chave `branch\|key\|rule_id\|field_code\|item`. `engine.py:177` — «Acompanha a divergência de ICMS acima.» vira ocorrência própria quando `not amounts_match and len(hits) > before`. `service.py:278-279,298-299` — `clean`/`divergent` contam documento com qualquer ocorrência, sem filtrar status (status só entra em pending/resolved, `:282-283`). `startup/entry_audit_worker.py:11-23` — laço só faz `claim_and_execute` de runs `queued` + `recover_orphans`; nada agenda re-análise |
| P5 | `xml_reader` sem grupo IBSCBS; `TesRecord` sem IBS/CBS; worker sem job periódico | **PROVEN** | `infrastructure/entry_audit/xml_reader.py:140-205` (`_nfe`: ICMS, IPI, ST, Simples) e `:208-283` (`_cte`) — nenhuma referência a IBS/CBS. `models.py:61-72` — `TesRecord` termina em `fiscal_code`. `models.py:75-97`/`99-136` — `XmlItem`/`XmlDocument` sem IBS/CBS. Worker: só o laço de fila (`entry_audit_worker.py:11-23`) |

Achado lateral relevante para o ajuste 1 (participante SA1 em B/D): o módulo `invoice_posting` (LNF) **já resolve** `F1_TIPO='B'` → partido na SA1 — `infrastructure/invoice_posting/totvs_invoice_posting_sf1_sql.py:112,129`, `domain/invoice_posting/ports.py:26`, `domain/invoice_posting/reconciliation_matching.py`. Há, portanto, um conceito irmão implementado em outro bounded context: a decisão de owner/fonte canônica é parte do ajuste, não só o código novo.

## 2. I3 — Protheus (leitura, base DELPI, mesmo acesso da T0)

### 2a. `F1_TIPO` × TES, entradas recebidas 01–17/11/2026, filiais 01/02

| Filial | TES | F1_TIPO | Notas (distintas) |
|---|---|---|---|
| 01 | 085 | B | 16 |
| 01 | 159 | B | 6 |
| 01 | 120 | D | 3 |
| 01 | 201 | D | 1 |
| 02 | 120 | D | 1 |

Contexto (`F1_TIPO` no período, todas as TES): filial 01 — N 172, C 47, B 22, D 4; filial 02 — N 184, C 37, D 1.

Partido das 27 notas B/D (22 B + 5 D): código/loja (`F1_FORNECE`/`F1_LOJA`) **existe na SA1 em 27/27**
(join `SA1010`, `A1_FILIAL=''`). Comparando a SA1 com o emitente do XML (cache da BFF, 27/27 XML presente):
**CNPJ igual em 17 e diferente em 10; UF igual em 26 e diferente em 1.**

### 2b. Configurador de Tributos — F2B/F2D

- `SX2010`/`INFORMATION_SCHEMA`: `F2B010` («Regra Tributária») e `F2D010` («Tributos Genéricos Calculados») **existem** — search miss descartado.
- `F2D010`: 61.668 linhas; origem (`F2D_TABELA`): SD2 48.813 · SC7 7.862 · SD1 4.993.
- Ligação ao item da SD1: **`SD1.D1_IDTRIB = F2D.F2D_IDREL`** (GUID). No período: 1.722 de 2.083 itens de entrada com linha F2D.
- Campos por linha: `F2D_TRIB` = **código da regra** (= `F2B.F2B_REGRA`; o GUID `F2D.F2D_IDCAD` = `F2B.F2B_ID`), `F2D_BASE`, `F2D_ALIQ`, `F2D_VALOR`; `F2D_IDBASE` → `F27.F27_ID` (regra de base), `F2D_IDALIQ` → `F28.F28_ID` (regra de alíquota).
- Tributo (CBS / IBS UF / IBS Mun): via `F2B.F2B_TRIB` → `CBSFED`, `IBSEST`, `IBSMUN`.
- CST e cClassTrib: **não são colunas** — constam no texto `F2B.F2B_DESC` (padrões como «CBS FED CCLASSTRIB 000001» e «E_CBS CST 000 CLASTRIB 000001»). SD1/SF1/SFT não têm colunas próprias de CST/cClassTrib da reforma.
- Regras de IBS/CBS na F2B: 21 linhas, vigência a partir de 2026 (algumas já encerradas). No período: TES 120/201 (tipo D) usam regras `CBS001`/`IBS001`/`IBS002`; a maioria das TES usa `CBS100`/`IBS100`; itens das TES 085/159 (tipo B) **não têm** linha F2D no período.

### 2c. Livro fiscal (SFT)

`SFT010` **não tem colunas de IBS/CBS** (SX3 e INFORMATION_SCHEMA). `FT_IDTRIB` está preenchido em 858 de 1.219 linhas de entrada do período — o livro liga a linha ao cálculo de tributos genéricos, mas os valores de IBS/CBS ficam na F2D, não na SFT.

### 2d. SF4 das TES pedidas (`F4_FILIAL` ''/01)

| TES | Descrição | F4_CONSUMO | F4_CREDIPI | F4_LFIPI | F4_IPI | F4_CREDICM | F4_TIPO | F4_CF |
|---|---|---|---|---|---|---|---|---|
| 018 | INSUMO C EST S IPI | S | N | O | N | N | E | 1556 |
| 052 | INSUMO C EST C IPI | S | S | T | S | N | E | 1556 |
| 069 | CONS ADM C EST C IPI BASE | S | N | O | S | N | E | 1556 |
| 106 | INSUMO IPI NA BASE | S | S | O | S | N | E | 1556 |
| 166 | CONS ADM S EST C IPI | S | N | O | S | N | E | 1556 |
| 169 | INSUMO C EST C IPI BASE | S | S | T | S | N | E | 1556 |
| 406 | MANUT MAQUIN COM IPI | S | S | T | S | N | E | 1556 |

Quatro TES (052, 106, 169, 406) marcam **material de consumo e creditam IPI** — a classe do ajuste 3. A regra atual (`engine.py:583-588`) só dispara quando o IPI efetivamente foi creditado (SFT ou item), não pela configuração da TES sozinha.

## 3. I4 — Grupo IBSCBS no XML (cache da BFF em PROD)

`controllership_finance.entry_audit_xml_cache` (coluna `model` guarda `nfe`/`cte`). XML emitidos em 11/2026 (AAMM `2611` na chave, sem cancelados): **343** — 270 NF-e, das quais **201 com `IBSCBS`** (~74%), e 73 CT-e, dos quais **72 com `IBSCBS`** (~99%).

Estrutura (NF-e, por item `det/imposto`; CT-e, em `imposto` — mesma forma):

```text
IBSCBS
  CST
  cClassTrib
  gIBSCBS
    vBC
    gIBSUF
      pIBSUF
      vIBSUF
    gIBSMun
      pIBSMun
      vIBSMun
    vIBS
    gCBS
      pCBS
      vCBS
```

Total da NF-e: `total/IBSCBSTot` (`vBCIBSCBS`, `gIBS`, `gCBS`, …) ao lado de `ICMSTot`. O leitor atual (`xml_reader.py`) ignora todos esses grupos (P5).

## 4. Cobertura

- I1 rebaseline: HEAD `784d7047a6`; working tree com alterações de outras frentes (delia-api, tv-dashboard, docs) — preservadas.
- I2: 5/5 premissas PROVEN com arquivo:linha; nenhum EXECUTION_DRIFT.
- I3: a–d respondidos (contagens; sem CNPJ no repositório).
- I4: contagem e estrutura do IBSCBS respondidas.
- I5 (linha de base em PROD): vai só no relatório da etapa, por conter números de notas reais.

## 5. Riscos e aberturas levantados na T14

1. SA1 não é autoridade absoluta no partido B/D: em 10/27 notas o CNPJ da SA1 difere do emitente do XML — a regra nova precisa verificar CNPJ/UF como a SA2 já faz, não assumir o cadastro.
2. CST/cClassTrib por item só existem dentro do texto `F2B.F2B_DESC` — parsear descrição é frágil; contrato precisa decidir a fonte (regra F2B × grupo `IBSCBS` do XML).
3. Itens das TES 085/159 (tipo B) não geram linhas F2D — nessas notas o IBS/CBS só existe no XML.
4. `summary.clean`/`divergent` conta documento com ocorrência **resolvida** como divergente — os «indicadores ao vivo» do ajuste 5 pedem regra nova, não só leitura.
5. Ajuste 5 (reverificação automática) contraria a decisão D10 («sob demanda, em qualquer dia; sem agendamento») — exige decisão do owner/ADR antes de implementar.
6. «B/D → SA1» já existe no `invoice_posting` (LNF): decidir o owner canônico do conceito para não nascer segunda implementação divergente (`centralized-rules-first`).
