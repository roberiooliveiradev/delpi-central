# CF-PROC0072 — Gate 039: R09 Faturamento × MOD — Engenharia reversa por triangulação XLSB × ADVPL × SQL live

Data: 2026-11-01. Escopo: read-only; nenhum runtime alterado. Baseline: doc 139 (`a3afc2ec7e`).

## 1. Artefato `Fat x MOD.xlsb` — estrutura real (PROVEN)

Arquivo: `Downloads/fechamento/Fat x MOD.xlsb` (anexos do fechamento mensal).

| Fato | Evidência |
|---|---|
| Abas | `1-Fl01` (2.459 linhas de dados) + `2-Fl02` (2.017) = 4.476 |
| Header | `PA · Seq Comp · Cod Produto · Desc Produto · Qtd Fat. · UM · Quantidade · Custo Unitario · Custo Total · Custo Produto · Horas` |
| `Cod Produto` | **itens SB1 com prefixo `MOD*`** — `MOD393` "MAQUINA DE CORTE WL603", `MOD399` "MAO DE OBRA DE EMBALAGEM CT-99" — 143 itens `MOD*` existem no SB1 |
| `UM` | `HR` — MOD precificado em horas |
| `Seq Comp` | `02/04/06` — nível de expansão (raiz/intermediário 1/intermediário 2), não tipo |
| PAs distintos (col 0) | f01=752, f02=1.017 (≈1.767 da ficha) — inclui **intermediários**, não só âncoras faturadas |
| `Qtd Fat.` | qty da âncora propagada; intermediários carregam qty acumulada |
| `Horas` | **= `Qtd Fat.` × `Quantidade`** — verificado 0,27×14,22=3,8394 |
| `Custo Total` | **= `Horas` × `Custo Unitario`** — verificado 271,8679 |

## 2. Cadeia MOD decodificada (PROVEN por match exato)

| PA | `Quantidade` artefato | `G2_TEMPAD` SG2 live | Recurso SG2 | Match |
|---|---|---|---|---|
| 90260054 | 14,22 | **14,22** | CT-33A | ✓ |
| 90260205 | 6,58 | **6,58** | CT-33A | ✓ |
| 90260027 | 0,02 | **0,02** | CT-99 | ✓ |
| 50220221 | 3,24 | **3,24** | CT-33A | ✓ |

**Modelo:** para cada PA âncora faturada → explode SG1 → para **cada produto da explosão** (âncora + intermediários) → suas **operações SG2** → recurso `G2_RECURSO` (CT-xx) → item `MOD*` correspondente → linha do relatório. `Quantidade` = `G2_TEMPAD` do par produto×operação; filiais via `G2_FILIAL`.

**Correção de ficha:** "PA" ≠ produto faturado. `50220221` tem **zero** linhas de faturamento (SD2 2026-09) mas aparece como PA — é intermediário da explosão. Os 1.767 "âncoras" = produtos distintos em todas as árvores; âncoras faturadas reais = 521 (299+222).

## 3. Fórmulas comprovadas

| Campo | Regra | Estado |
|---|---|---|
| Âncora | `SD2.D2_EMISSAO ∈ period` ∧ `TES.F4_DUPLIC='S'` ∧ `SB1` ranges SX1 | `PROVEN` (literal PRW + live) |
| Explosão | recursão SG1/SGG (`lPreEstru` escolhe) | `PROVEN` mecanismo (PRW:337-343) |
| MOD | `SG2` ops × `G2_RECURSO` → `MOD*` | `PROVEN` por match exato (4/4) |
| `Quantidade` | `G2_TEMPAD` | `PROVEN` |
| `Horas` | `QtdFat × G2_TEMPAD` | `PROVEN` (identity) |
| `Qtd Fat.` | qty âncora propagada × fator estrutural | `PROVEN` semântica / exata por nível `TO_INVENTORY` |
| `Custo Unitario` | **não** `B1_CUSTD` (MOD393: custd=0 mas artefato=70,81) — rate mensal/cenário da SP | `SOURCE_MISSING` |
| `Custo Produto` | 0,0 em amostras | `TO_INVENTORY` |
| `Seq Comp` | nível 02/04/06 da posição na explosão | `PROVEN` semântica (hipótese confirmada por classe 9xx→02, 5xx→04) |
| `QTDFAT==0` fallback | `aModPar[4]` = qty propagada do pai | `PROVEN` (PRW:410) |

## 4. Paridade informacional — status

| Métrica | Artefato | Reconstruído | Estado |
|---|---|---|---|
| Âncoras faturadas 2026-09 | — | 521 (299+222) | `PROVEN` |
| Produtos na col PA | 1.767+ | depende de explosão SG1 (testável) | `TO_INVENTORY` |
| Linhas MOD | 4.476 | = Σ ops SG2 com MOD-mapping por produto em árvore | `PLANNED` — conta exata requer motor |
| Custos | preenchidos | **sem fonte de taxa** | `SOURCE_MISSING` |

## 5. Vídeo

`TEST_NOT_RUN` — `Acompanhamento do Processo…mp4` (126MB) presente; sem ffmpeg/decoder no ambiente do executor. Nenhuma evidência inventada.

## 6. Contrato TARGET (revisado — mais forte que doc 139)

`GET /financeiro/billing-mod-breakdown?period&branch`

```
{ report: "billing-mod-breakdown", period, branch, officiality: "operational_view",
  official_parity: "pending",
  anchors: [{ product, billedQty,
    modLines: [{ level: "02|04|06", explodedProduct, modItem, description,
                 operation, resource, stdTime, propagatedQty, hours,
                 costUnit: <field|null>, costTotal: <derived|null> }],
    sourceMissing: ["cost_rate_basis"] }],
  limitations: [...], provenance: {sd2, sf4, sg1, sg2}, absent-state typing }
```

Campos com fonte comprovada: PA, produto explodido, nível, operação, recurso, `stdTime`, `propagatedQty`, `hours`. Campo de taxa: `SOURCE_MISSING` tipado até localizar a base de rate (SP/RPO/tabela de cenário).

## 7. DECISION_REQUIRED

| D | Tópico | Recomendação |
|---|---|---|
| DR-1 | Implementar motor de expansão+MOD na api-delpi (Alt C, doc 139) com campos comprovados + `costUnit` tipado `source_missing` | **Sim** — modelo agora PROVEN por match exato |
| DR-2 | Tratamento de `costUnit`/`costTotal` sem fonte de taxa | (a) omitir com lacuna tipada (recomendado) (b) aguardar rate source |
| DR-3 | Homologação informacional contra `.xlsb` item-a-item quando Slice 1 construído | Controladoria valida correspondência (âncora×MOD×horas; custos sinalizados) |

**Readiness Slice 1: `READY-CONDITIONAL`** — aguarda aprovação DR-1/DR-2 do PO. Comparação completa XLSB×reconstruído depende do motor (Slice 1); amostra manual 4/4 já provou a regra.
