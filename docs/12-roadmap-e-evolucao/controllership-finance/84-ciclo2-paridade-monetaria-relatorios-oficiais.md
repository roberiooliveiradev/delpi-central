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
| — 1 linha `NF` (`<NF-GRUPO-A>`) | VO = soma do grupo (NF 923,53 + 4× `TX UNIAO` = **1.029,52**) | exato |

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
- Residual: **identidade do subconjunto "inconsistência"** — o total do log
  está reconstruído **em agregado** (ΔTB exata); as linhas individuais do
  log **não foram reconstruídas linha-a-linha** — não reproduzível por
  agregação (hipóteses testadas: CMP lado BA, FK6-VA via `E5_IDORIG`
  [=0 em todas as 948 linhas], linhas `E5≠E2`, grupos `ΣE5>E2`).
  Provável validação por linha do fonte (nVlMovFin/aglutinação) — exigiria o
  arquivo de log emitido junto ao relatório.

### §1.5 Veredito R01

Paridade **completa** em população, identidade de linha, Total Baixado,
componentes, motivos, resumos e filial origem. Valor Original 100% explicado
(3 regras físicas demonstradas). **O que está provado:** as 948 linhas do
XLSB reconciliam 1:1 com a população física — a paridade é do **artefato**,
não do PDF impresso (este segrega um log de inconsistências cujo
**subconjunto de linhas não foi reconstruído linha-a-linha**; seu total é
reconstruído em agregado). Residual: identidade do subconjunto do log +
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
  `E5_VALOR` da baixa `VL` principal (ex.: título <TITULO-VL-A>: VL 587,70 já
  contém juros 4,94 + multa 11,42 = 16,36 = `E5_VLJUROS`). Regra consistente
  com a lista de exclusão de tipodoc do FINR190 — **inferida, não provada
  como regra geral** (fonte ausente).
- Universo `SE5'R'` set/2026 = **746 movimentos** (657 com título + 89 sem
  título). O artefato inclui apenas 8 dos 89 sem título: todos `PA`/`FINA750`
  com motivo NOR/DAC (7) + 1 `PA`/`DEB` origem 01. Excluídos: FOL/COF/NDF/
  tipo-vazio/NF-DEB e **3 `PA`/`DEB` adicionais**, todos identificados por
  linha lógica (sem expor partes): `<RECEBIMENTO-SEM-TITULO-A>` 118,27 `FINA090` f01 ·
  `<RECEBIMENTO-SEM-TITULO-B>` 1.000,00 `FINA090` f01 · `<RECEBIMENTO-SEM-TITULO-C>` 1.537,00 `FINA750` f02. A
  regra geral que seleciona 8 e exclui 3 segue **hipótese não demonstrada**
  (fonte ausente — G4); a população impressa, porém, é 100% reproduzida.
- Coluna `Orig`: preenchida só nas 8 linhas sem título (2×`01` + 6×`02` =
  `E5_FILORIG`); nas linhas com título exibe vazio (filial compartilhada da
  SE1). Semântica distinta do pagar — produtores distintos.

### §2.2 Valores por registro

| Coluna | Regra | Paridade |
|---|---|---|
| **Total Baixado** | `SE5.E5_VALOR` | exato nas 649 linhas comuns + 8 PA = `E5_VALOR` |
| **Valor Original** | `SE1.E1_VALOR` | **649/649** exato por registro |
| — 8 linhas `PA` sem título | VO = **valor da provisão `'P'` espelhada** (mesmo numero/clifor, motivo NOR, origem `MATA121`/`FINA050`) | **8/8 exato** — ex.: numero <MOV-PROV-A>: provisão 1.571,60 = recebimentos 877,00+119,96 + compensação 'P' 574,64 |
| **Jur/Multa** | `E5_VLJUROS + E5_VLMULTA` | total **44,16** exato |
| ΣVO agregado | 649×`E1_VALOR` + 8×provisão 'P' | **5.301.533,30 = artefato — exato, Δ R$ 0,00** (rework: a divergência de R$ 1,00 reportada na rodada anterior era erro de soma na consolidação manual — 15.836,71 registrado como 15.837,71 — não divergência de dado) |

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
impressa tem fonte física e valor exato — incluindo os 8 VOs de provisão
espelhada). **Reproduzidos integralmente:** população 657, chaves, TB, VO,
componentes, resumos e PDF−xlsb. **Hipóteses ainda não demonstradas
(escopo G4, não G5):** regra geral de inclusão/exclusão do sem-título (3
linhas identificadas fora do artefato), regra de supressão das 8 linhas de
decomposição e identidade do subconjunto do log impresso — todas
dependentes do fonte `DLP06R01` (E1, TI/ERP). Paridade monetária do
artefato × banco **demonstrada e reproduzível, Δ R$ 0,00** →
**G5 PASS**; **G4 segue PENDING** (binding do relatório = fonte ausente);
**G6 exige aceite humano do owner.**

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

### §4.1 — Saldo Atual × SB9

SB9@30/09/2026 filial 01 (`B9_VINI1` por `B1_TIPO`) × coluna **Saldo Atual**
do MATR320:

| Tipo | SB9 | MATR320 | Δ |
|---|---|---|---|
| EM, GG, II, MC, MH, MS, MX, PA, PI | — | — | **0 (9/10 tipos exatos ao centavo)** |
| MP | 3.373.542,05 | 3.364.910,31 | **+8.631,73** |

Total: 3.893.096,17 vs 3.884.464,44 (Δ = o mesmo 8.631,73, isolado em MP).

### §4.2 — Reconciliação completa das colunas (linha MP) — rodada 23/10

Fonte oficial localizada: `docs/13-fontes-totvs-protheus/04. Estoque/
MATR320/matr320.prx` (padrão TOTVS, execução via SP `MAT056` — a variante
Delpi `Dmatr320.prx`/`DLPR320` tem poder de terceiros comentado e **não**
foi a usada, pois o PDF traz EntPT/SaiPT não zeradas). Regras por coluna
em doc 80 §31.B e catálogo doc 85 §5 (BR-R05-003…010).

| Coluna MP | Impresso | Reconstruído (origem física) | Δ |
|---|---|---|---|
| Saldo Inicial | 3.315.659,021 | derivado; = ΣSB9@0831 | **0** |
| Compras | 642.670,88 | SD1 poder3=N/est=S/tipo≠'D' `D1_CUSTO` DTDIGIT-Set + itens 001 do doc `<NF-RETIF-A>` (sanitizado) ainda vivos na emissão | **0** |
| Movimentações Internas | −40.957,818 | SD3 OP-vazio CF[3]≠'3' (INV + DE6/RE6 + RE0-503) | ~0,48 (precisão TTAT_COLD) |
| Requisições p/ Produção | −666.114,374 | SD3 OP-preenchido não-PR a custos de emissão | **0** |
| Transferências | 0,000 | RE4/DE4 espelhadas | **0** |
| Produção | 0,000 | — | **0** |
| Vendas | 164.330,717 | SD2 poder3=N/est=S/tipo≠'D' `D2_CUSTO1` | **0** |
| Transf. p/ Processo | 940.599,335 | SD3 CF[3]='3' OP-vazio (RE3) — **memo, fora da equação** | **0** |
| Devolução de Vendas | 264,681 | SD1 poder3=N/est=S/tipo='D' (TES 168/1949) | **0** |
| Devolução de Compras | 4.732,694 | SD2 poder3=N/est=S/tipo='D' (CFOP 6201) | **0** |
| Entrada Poder Terceiros | 319.258,140 | SD1 poder3≠'N'/est=S `D1_CUSTO` DTDIGIT-Set − itens 085 do doc `<NF-RETIF-A>` (inseridos ~20-21/10 retroativos) | **0** |
| Saída Poder Terceiros | 36.806,805 | SD2 poder3≠'N'/est=S `D2_CUSTO1` (TES 524/x903) | **0** |
| Saldo Atual | 3.364.910,314 | saldo no estado de custo da emissão (01/10 16:16) | +8.631,73 vs SB9@21/10 |

Equação validada ao centavo: `SA = SI + Compras + MovInt + Requis +
Transf + Produção − Vendas + DevV − DevC + EntPT − SaiPT` (TransfProc
memo).

### §4.3 — Divergência MP +8.631,73 — decomposição (doc 80 §31.E)

| Componente | Valor |
|---|---|
| Repricing da retificação doc `<NF-RETIF-A>` (001→085, ~20-21/10) | +9.583,19 |
| Movimentos INVENT retroativos (insert 01/10 ~19h) | −24,95 |
| Recálculo de custo médio pós-emissão (MATA330 c/ 25.995 updates `D3_CUSTO1`; `Analise.xlsx` ΣQ×ΔCM ≈ +10,7k agregado) | incluído |
| Residual não decomposto | ≈ −950 |

**DIFERENÇA EXPLICADA**: SA impresso = estado de custo da emissão; SB9 =
snapshot reconstruído 21/10 pós-retificação. Não é erro de fórmula nem
de filtro — é diferença temporal de estado. **→ G5 PENDING** até
paridade `as_of` demonstrada nas três medidas canônicas (E/S × P7 × H02).

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
