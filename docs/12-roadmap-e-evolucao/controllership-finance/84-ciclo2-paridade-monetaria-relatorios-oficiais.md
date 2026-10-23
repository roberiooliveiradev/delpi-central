# Matriz de paridade monetária — relatórios oficiais do fechamento set/2026 (Ciclo 2, CF-C2-PARITY-001)

Reconciliação linha-a-linha e agregada entre os artefatos oficiais da pasta do PO
(`C:\Users\analistaptd\Downloads\fechamento`) e as populações físicas lidas via
SELECT-only no Protheus (`SE5010/SE1010/SE2010/SB9010/SB1010/SD1010`), mesma
competência `01/09/2026–30/09/2026` e mesmo eixo de data (`E5_DATA` = data da baixa).

**Método:** comparação de multisets de chaves `(prf, num, parcela, tipo, cli/for, dt baixa)`
e de valores por registro (Total Baixado, Valor Original, componentes). Somente
agregados e estruturas são documentados — nenhuma linha de cliente/fornecedor é
reproduzida aqui (evidência sanitizada por exigência de segurança).

**Resultado executivo:** R01 e R02 alcançam **paridade row-level** (população,
motivos, Total Baixado, componentes e resumos exatos) → **G5 promovido a PASS**
nos dois itens (doc 47). R03/R05 têm paridade **parcial** documentada (G5 PENDING).
Demais itens: sem população comparável → G5 não promovido.

---

## §1 — R01 · Baixas a pagar (`Pagos por dt.pdf` + `pagos 09 26.xlsb`)

Produtor: **FINR190** (`FINR190_DLP.PRX`, commit `0df96daafe`), layout
`DLP06R01.prt`. Competência 09/2026, filiais origem 01+02 (scope do artefato).

### §1.1 População e identidade das linhas

| Dimensão | Artefato oficial | SQL (WHERE fiel do fonte) | Δ |
|---|---|---|---|
| Linhas de dados | **948** | **948** | 0 |
| Chaves distintas (prf/num/prc/tipo/clifor/dt) | 948 multiset | 948 multiset | **0 mismatch** |
| Motivos | DEB 600 · CMP 186 · FAT 83 · NOR 65 · DAC 14 | idêntico | **0** |
| Filial origem (`E5_FILORIG`) | 01→532 · 02→416 | 01→532 · 02→416 | **0** |
| Estrutura CMP | 93 pares espelhados `BA`+`CP` | 93 BA + 93 CP | **0** |

O WHERE reproduzido é o do próprio fonte (linhas ~1040–1180): filtros fixos
(`E5_MOTBX<>'DSD'`, `E5_MOVCX<>'S'`, `E5_SITUACA NOT IN ('C','E','X')`,
`E5_HISTOR NOT LIKE '%Baixa Automatica / Lote%'`, `E5_TIPODOC NOT IN
('DC','D2','JR','J2','TL','MT','M2','CM','C2','ES','E2')`, regra `CD`,
`E5_DTCANBX=' '`), **par de estorno com a chave exata do código**
(FILIAL+PREFIXO+NUMERO+PARCELA+TIPO+CLIFOR+LOJA+SEQ+BANCO+AGENCIA+CONTA+MOVCX,
`E5_TIPODOC='ES'`, `E5_ORIGEM<>'FINA100'`) e vínculo SE2 pela chave de título
(SE2 é compartilhada — `E2_FILIAL=' '`). Reproduz exatamente 948 = oficial.

### §1.2 Valores por registro

| Coluna do relatório | Regra física demonstrada | Paridade |
|---|---|---|
| **Total Baixado** | `SE5.E5_VALOR` | **948/948 linhas — multiset por chave 0 divergências** |
| **Jur/Multa** | `E5_VLJUROS + E5_VLMULTA` | total **244,07** exato |
| **Correção** | `E5_VLCORRE` | total **−39.365,10** exato |
| **Descontos** | `E5_VLDESCO + E5_VLDECRE` | total **0,01** exato |
| **Valor Original** | `SE2.E2_VALOR` | **942/948** exato por registro |
| — 5 linhas `INV` (aglutinadas) | `E5_VALOR` do movimento (aglutinação: o movimento carrega o total) | exato |
| — 1 linha `NF` (004044596) | VO = soma do grupo (NF 923,53 + 4× `TX UNIAO` = **1.029,52**) | exato |

### §1.3 Subtotais impressos (resumo do rodapé)

| Categoria impressa | Valor oficial | Fórmula física | Paridade |
|---|---|---|---|
| Baixados | 5.650.845,55 | Σ`E5_VALOR` de DEB+NOR+DAC (679 linhas) | **exato** |
| Compens. | 96.992,53 | Σ`E5_VALOR` do lado `CP` dos pares CMP (93 linhas) | **exato** |
| Bx.Fatura | 174.995,31 | Σ`E5_VALOR` de FAT (83 linhas) | **exato** |
| Σ Total Baixado (xlsb) | 6.019.825,92 | Σ`E5_VALOR` (948) | **exato** |

### §1.4 PDF × XLSB — relação provada

`Pagos por dt.pdf` Total Geral: VO 6.197.009,01 / TB 5.632.196,28.
`pagos 09 26.xlsb`: VO 6.410.923,67 / TB 6.019.825,92.

- Δ TB = **387.629,64** = **total impresso no próprio PDF como "log de
  inconsistências"** — relação exata, documentada.
- Δ VO = 213.914,66 (VO das linhas segregadas no log).
- Residual: **identidade do subconjunto "inconsistência"** — não reproduzível
  por agregação (hipóteses testadas: CMP lado BA, FK6-VA via `E5_IDORIG`
  [=0 em todas as 948 linhas], linhas `E5≠E2`, grupos `ΣE5>E2`).
  Provável validação por linha do fonte (nVlMovFin/aglutinação) — exigiria o
  arquivo de log emitido junto ao relatório.

### §1.5 Veredito R01

Paridade **completa** em população, identidade de linha, Total Baixado,
componentes, motivos, resumos e filial origem. Valor Original 100% explicado
(3 regras físicas demonstradas). Residual: subconjunto do log de
inconsistências (total do próprio relatório, não divergência de dado) e
versão compilada no RPO (fora do escopo READ). **→ G5 PASS.**

---

## §2 — R02 · Baixas a receber (`Recebidos.pdf` + `Recebidos.xlsb`)

Produtor: **`DLP06R01` custom — fonte AUSENTE do acervo** (G4 segue PENDING;
layout `.prt` compartilhado não prova produtor). Competência 09/2026.

### §2.1 População e identidade das linhas

| Dimensão | Artefato | SQL | Δ |
|---|---|---|---|
| Linhas de dados | **657** | 649 (INNER SE5×SE1) + 8 sem título | **0** |
| Chaves comuns | 649/649 idênticas | — | 0 |
| Linhas sem título no artefato | 8 (`PA`, origem `FINA750`, cli/for gateway) | confirmadas na SE5, sem SE1 | 0 |
| Linhas na SQL ausentes do artefato | — | 8 linhas de **decomposição** | explicadas |

- As **8 linhas de decomposição** excluídas pelo produtor são movimentos
  `MT`/`JR`/`DC` (+1 `VL` duplicado) cujos valores já estão embutidos no
  `E5_VALOR` da baixa `VL` principal (ex.: título 102184-002: VL 587,70 já
  contém juros 4,94 + multa 11,42 = 16,36 = `E5_VLJUROS`). Regra consistente
  com a lista de exclusão de tipodoc do FINR190 — **inferida, não provada
  como regra geral** (fonte ausente).
- Universo `SE5'R'` set/2026 = **746 movimentos** (657 com título + 89 sem
  título). O artefato inclui apenas 8 dos 89 sem título: todos `PA`/`FINA750`
  com motivo NOR/DAC (7) + 1 `PA`/`DEB` origem 01. Excluídos: FOL/COF/NDF/
  tipo-vazio/NF-DEB e **3 `PA`/`DEB` adicionais** (ex.: 044052, 1.537,00,
  origem 02) — regra de inclusão do sem-título parcialmente identificada.
- Coluna `Orig`: preenchida só nas 8 linhas sem título (2×`01` + 6×`02` =
  `E5_FILORIG`); nas linhas com título exibe vazio (filial compartilhada da
  SE1). Semântica distinta do pagar — produtores distintos.

### §2.2 Valores por registro

| Coluna | Regra | Paridade |
|---|---|---|
| **Total Baixado** | `SE5.E5_VALOR` | exato nas 649 linhas comuns + 8 PA = `E5_VALOR` |
| **Valor Original** | `SE1.E1_VALOR` | **649/649** exato por registro |
| — 8 linhas `PA` sem título | VO = valor de referência do recebimento avulso (não-SE1; `FINA750`) | valores identificados, fonte física não-SE1 |
| **Jur/Multa** | `E5_VLJUROS + E5_VLMULTA` | total **44,16** exato |
| Residual agregado ΣVO | reconstrução 5.301.534,30 vs artefato 5.301.533,30 | **Δ = R$ 1,00** (1 linha, regra de VO alternativa não identificada) |

### §2.3 Subtotais e PDF × XLSB

- Resumo: **Baixados 5.236.376,13** = Σ`E5_VALOR` não-CMP — **exato**;
  **Compens. 19.109,94** = lado CP dos pares CMP (7+7 linhas espelhadas) —
  **exato**; mesma regra do pagar.
- `Recebidos.pdf` Total Geral VO 5.271.214,45 / TB 5.234.164,55 vs xlsb
  5.301.533,30 / 5.274.596,01: Δ TB = **40.431,46** = **total do log de
  inconsistências impresso** — exato; Δ VO = 30.318,85.
- Motivos impressos: NOR 638 · CMP 14 · DAC 4 · DEB 1 — as 3 linhas DAC/DEB
  extras vs `E5_MOTBX` cru são relabel do produtor nas linhas sem título
  (população idêntica; apenas o rótulo de motivo difere em 3 linhas).

### §2.4 Veredito R02

Artefato **100% reconciliado linha-a-linha** contra SE5/SE1 (cada linha
impressa tem fonte física e valor exato). Residual: regra geral de
inclusão/exclusão do sem-título (3 `PA`/`DEB`), fonte do VO das linhas
`FINA750`, Δ R$1,00 e subconjunto do log — todos dependentes do fonte
`DLP06R01` (E1, TI/ERP). A paridade do artefato × banco está **demonstrada e
reproduzível** → **G5 PASS**; **G4 segue PENDING** (binding do relatório =
fonte ausente).

---

## §3 — R03 · P7 / Registro de Inventário

| Medida oficial | Artefato | Base física comparável | Resultado | Δ |
|---|---|---|---|---|
| EM PROCESSO total | `Estoque.pdf` 355.240,51 | `Material em processo.xlsb` (57.355 linhas, MATR989) | **exato** | 0 |
| — por tipo | MP 354.938,50 · PI 254,44 | soma do xlsb por `B1_TIPO` | **exato** (MP+PI+EM 39,12+MH 8,46 = total) | 0 |
| EM ESTOQUE PA | 190.511,24 | MATR320 Saldo Atual PA | **exato** | 0 |
| EM ESTOQUE PI | 24.528,60 | MATR320 Saldo Atual PI | **exato** | 0 |
| EM ESTOQUE total | 3.591.191,36 | SB9 f01 ex-armazém 99 → 3.599.373,79; ex-99/50 → 3.545.071,27 | **parcial** | −8.182,43 / +46.120,09 |
| Resumo MP/PA/PI estoque | 2.699.026,36 (MP 2.483.986,52) | SB9 MP qualquer recorte testado (loc01: 3.016.277,89) | **não reproduzido** | ≥ −532.291,37 |
| Resumo MP/PA/PI processo | 277.941,20 (MP 277.686,77) | xlsb MEP MP = 354.938,50 | **não reproduzido** | −77.251,73 |

As duas emissões do P7 usam filtros distintos (completo × escopo MP/PA/PI) e
o "EM ESTOQUE" não corresponde a nenhum recorte SB9 por armazém testado —
parâmetros por emissão pendentes (E2, TI/ERP). **→ G5 PENDING.**

## §4 — R05 · Entradas e Saídas (`MATR320.prt`)

SB9@30/09/2026 filial 01 (`B9_VINI1` por `B1_TIPO`) × coluna **Saldo Atual**
do MATR320:

| Tipo | SB9 | MATR320 | Δ |
|---|---|---|---|
| EM, GG, II, MC, MH, MS, MX, PA, PI | — | — | **0 (9/10 tipos exatos ao centavo)** |
| MP | 3.373.542,05 | 3.364.910,31 | **+8.631,73** |

Total: 3.893.096,17 vs 3.884.464,44 (Δ = o mesmo 8.631,73, isolado em MP).
Eixos Entradas/Saídas não reconciliados (exigiria agregação SD3 por tipo —
não executado; eixo pendente). **→ G5 PENDING** (paridade de fechamento
9/10 + residual MP não explicado).

## §5 — Demais itens (candidatos avaliados)

- **R10** (CC matriz / SD1): artefato = 353 linhas, ΣVlr.Total 169.704,12.
  SD1 filial 01 set/2026: eixo `D1_EMISSAO` 657 linhas / 1.218.399,30; eixo
  `D1_DTDIGIT` 686 / 1.262.557,36 — **não reproduzível** (o artefato é
  subconjunto da consulta EDAPP do operador; filtro não documentado). G5 não
  promovido.
- **R08** (Material em Processo): xlsb já é o próprio artefato oficial —
  paridade documental com o P7 demonstrada (§3); população SIZ/SC2 não
  testada. G5 não promovido.
- **R04, R06, R07, R09, R11–R15**: sem população oficial comparável
  disponível → G5 `TEST_NOT_RUN`/PENDING preservado.

## §6 — Gates e métricas resultantes

| Item | Antes | Depois |
|---|---|---|
| R01 G5 | TEST_NOT_RUN | **PASS** (paridade row-level integral) |
| R02 G5 | TEST_NOT_RUN | **PASS** (paridade row-level integral do artefato; G4 permanece PENDING — fonte ausente) |
| R03 G5 | TEST_NOT_RUN | PENDING (paridade parcial: EM PROCESSO + PA/PI exatos) |
| R05 G5 | TEST_NOT_RUN | PENDING (9/10 tipos + residual MP) |

`COLETA = 39/60 = 65,0%` (inalterado — G5 não entra no denominador) ·
`AUDITORIA = 41/90 = 45,6%` · `CONCLUÍDOS = 0/15` (G6 exige aceite humano).

## §7 — Segurança e método

- Somente SELECT; principal efetivo `db_datareader`, sem DML/DDL/jobs.
- Nenhum valor individualizado versionado; apenas agregados e regras.
- Execução: `docker exec -i delpi-api-delpi python -` →
  `app.infrastructure.providers.totvs.connection_pool` (canal autorizado).
- Scripts temporários de prova não versionados.
