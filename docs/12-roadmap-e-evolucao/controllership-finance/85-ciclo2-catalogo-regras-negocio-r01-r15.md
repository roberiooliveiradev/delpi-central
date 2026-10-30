# Catálogo de regras de negócio R01–R15 — fechamento set/2026 (Ciclo 2)

**Documento:** `85-ciclo2-catalogo-regras-negocio-r01-r15.md`
**Execução:** CF-C2-PARITY-001 complemento — consolidação de conhecimento · 2026-10-23 · Devin
**Finalidade:** preservar, em forma verificável e versionada, as regras de
negócio **atualmente descobertas** para reproduzir os resultados oficiais
observados e para subsidiar a futura implementação das rotas do Portal
Controladoria & Finanças (PROC-0072). O catálogo consolida o conhecimento
desta investigação — **não pretende conter todas as regras necessárias para
concluir os 15 relatórios** (itens com binding/pendência declarada seguem em
`PENDING`/`TO_INVENTORY`). Nenhuma regra descoberta fica apenas em script
temporário, mensagem de execução ou memória da investigação.
**Referências cruzadas:** docs 47 (gates), 80 (rodadas §17–§30), 82 (owners E1–E6),
83 (crosswalk), 84 (paridade monetária).

---

## §0 — Legenda e disciplina de classificação

### Estados de prova (por regra)

| Estado | Significado |
|---|---|
| `PROVEN` | comportamento reproduzido contra artefato oficial e/ou banco, com evidência citada |
| `AS-IS` | comportamento real observado no processo/sistema (vídeo, artefato, execução) |
| `TO_INVENTORY` | conhecida a existência; binding/regra interna não demonstrada |
| `TARGET` | comportamento desejado aprovado para o Portal (decisão registrada) |
| `PENDING` | hipótese ou dependência de fonte/decisão/homologação |
| `STALE_EVIDENCE` | evidência superada por drift documentado (preservada como histórico) |

### Disciplina

- **Hipótese inferida nunca vira regra oficial.** Regras `PENDING`/`TO_INVENTORY`
  não entram em implementação sem promoção.
- Onde a regra vale apenas para a emissão observada (competência 09/2026), o
  escopo é declarado — não se generaliza o que não foi reexecutado.
- Campos/tabelas seguem nomenclatura TOTVS física (`SE5010.E5_*` etc.).

### Destino de implementação (regra de ouro)

```text
regra PROVEN/AS-IS
→ implementar na camada TOTVS provider da api-delpi (fonte canônica única)
→ controllership-finance-api (BFF) agrega/expõe contrato
→ controllership-finance (MFE) renderiza — sem regra duplicada
```

Nenhum contrato, endpoint, migration ou runtime foi criado nesta rodada.

---

## §1 — R01 · Baixas a pagar (FINR190 + `DLP06R01.prt`/`nat.prt`)

Fonte de autoridade: `FINR190_DLP.PRX` no acervo — commit `0df96daafe`,
blob `92bcae1c` (SHA do objeto no repositório de fontes, doc 80 §17).
Artefatos: `Pagos por dt.pdf` (33p), `Pagos por nat.pdf` (35p),
`pagos 09 26.xlsb` (948 linhas de dados). Paridade: doc 84 §1.

### BR-R01-001 — População base do relatório — `PROVEN`

- **Descrição:** relação dos títulos pagos (baixas) da competência, eixo de
  data = data da baixa.
- **Finalidade PROC-0072:** alimentar a visão "baixas a pagar" do fechamento.
- **Tabelas:** `SE5010` (movimentos), eixo principal.
- **Condições de inclusão:** `E5_RECPAG='P'`; `E5_DATA` dentro do período
  informado (parâmetros `MV_PAR` de datas — 01/09–30/09/2026 na emissão);
  `E5_TIPODOC` restrito à lista fixa do fonte (observado no artefato:
  `VL`, `PA`, `BA`, `CP`); `E5_FILORIG` conforme filial solicitada (SX1).
- **Condições de exclusão:** tipodoc fora da lista fixa; pares de estorno
  (BR-R01-002); linhas segregadas no log de inconsistências somente no PDF
  (BR-R01-009).
- **Validação:** WHERE fiel do fonte reproduz **948/948** chaves do XLSB —
  multiset exato (doc 84 §1). Distribuição motivo×tipodoc: CMP/BA 93 ·
  CMP/CP 93 · DAC/BA 14 · DEB/VL 600 · FAT/BA 83 · NOR/PA 65.
- **Teste negativo:** WHERE com chave de estorno incompleta retorna 937 —
  reproduz e explica o "drift" histórico 950×948.

### BR-R01-002 — Pareamento de estornos — `PROVEN`

- **Descrição:** baixas estornadas saem do relatório em par (baixa + estorno).
- **Chave exata do par (do fonte `Fr190TstCond`):**
  `FILIAL + PREFIXO + NUMERO + PARCELA + TIPO + CLIFOR + LOJA + SEQ + BANCO +
  AGENCIA + CONTA + MOVCX` — **sem data e sem valor**.
- **Regra auxiliar:** tratamento de `CD` (crédito/débito) conforme fonte.
- **Evidência:** 948/948 com a chave completa; 937 com chave restrita por
  data/valor (doc 80 §17.B/C + doc 84 §1).
- **Nota de implementação:** o par deve ser removido por multiset de chaves,
  não por anti-join 1:1 (chaves duplicadas com valores trocados existem).

### BR-R01-003 — `Total Baixado` — `PROVEN` (emissão observada)

- **Regra:** `Total Baixado = SE5.E5_VALOR` por linha — **comprovado para a
  emissão observada** (competência 09/2026).
- **Detalhe do fonte:** existe campo calculado `nVlMovFin` (movimentação via
  cadeia FK quando presente) que toma precedência; nesta competência
  `FK6_TPDOC='VA'` retornou **0 em todas as 948 linhas** — valor efetivo =
  `E5_VALOR` para toda a emissão.
- **Validação:** multiset TB×chave sem divergência (948/948, doc 84 §1).
- **Pendência:** quando `nVlMovFin` assumir precedência com valor diferente
  de `E5_VALOR`, o comportamento do `Total Baixado` permanece **`PENDING`** —
  cenário não observado, **sem expectativa de teste inventada**.

### BR-R01-004 — `Valor Original` — `PROVEN` (3 regras físicas)

| Caso | Regra | Cobertura |
|---|---|---|
| Título comum | `SE2.E2_VALOR` do título referenciado | 942/948 |
| Movimento aglutinado `INV` | `SE5.E5_VALOR` da própria linha | 5/948 |
| Grupo NF + componentes `TX UNIAO` | soma do grupo (NF 923,53 + 4×TX 105,99 = 1.029,52) | 1/948 |

- **Validação:** VO explicado em 100% das linhas; ΣVO 6.410.923,67.

### BR-R01-005 — Relacionamentos físicos — `PROVEN`

- `SE5→SE2`: busca do título pela chave
  `FILIAL(xFilial de E5_FILORIG — SE2 compartilhada, filial vazia) + PREFIXO +
  NUMERO + PARCELA + TIPO + FORNECE + LOJA` (`MsSeek` no fonte).
- `SE5→SED`: natureza via `E5_NATUREZ` (descrição exibida).
- `SE5→FK1/FK2/FK6`: cadeia de movimentação via `E5_IDORIG`; campo `SE5VA` =
  Σ`FK6_VALMOV` assinado (`FK6_TPDOC='VA'`) — presente no fonte, **=0 nesta
  competência**.
- **Nota:** SE1/SE2 são compartilhadas entre filiais (filial em branco) — o
  vínculo correto é pela chave do título, não pela filial da SE5.

### BR-R01-006 — Resumos impressos — `PROVEN`

- `Baixados` = Σ`E5_VALOR` das linhas não-CMP e não-FAT → 5.650.845,55 exato.
- `Compens.` = lado `CP` dos pares `CMP` (93 linhas espelhadas BA+CP) →
  96.992,53 exato.
- `Bx.Fatura` = linhas `FAT` → 174.995,31 exato.
- Subtotais por data/natureza = particionamento do mesmo universo.

### BR-R01-007 — Componentes monetários — `PROVEN`

- `Jur/Multa` = `E5_VLJUROS + E5_VLMULTA` → 244,07 exato.
- `Correção` = `E5_VLCORRE` → −39.365,10 exato (negativo no período).
- `Descontos` → 0,01 exato; `Abatim./Impostos` conforme colunas do layout.

### BR-R01-008 — Coluna `Orig` (filial origem) — `PROVEN`

- `Orig` = `E5_FILORIG` da linha — 532 linhas filial 01, 416 filial 02.
- A filial do relatório filtra por `E5_FILORIG` (origem da baixa), não pela
  filial do título (SE2 compartilhada).

### BR-R01-009 — XLSB × PDF × log de inconsistências — `PROVEN` (agregado) / `PENDING` (linhas)

- `ΣTB do PDF = ΣTB do XLSB − 387.629,64` — diferença = **total impresso do
  log de inconsistências** do próprio relatório. Relação exata documentada.
- **Identidade das linhas do log: `PENDING`** — não reconstruída linha-a-linha
  (hipóteses testadas e descartadas: CMP lado BA, FK6-VA, linhas `E5≠E2`,
  grupos `ΣE5>E2`). Provável validação por linha do fonte; exige o arquivo de
  log emitido com o relatório.
- `ΣVO PDF − ΣVO XLSB = −213.914,66` (VO das linhas segregadas).

### BR-R01-010 — Parâmetros e disposição — `AS-IS`

- Parâmetros observados: período (Dt.Ref 30/09/2026), disposição por **data**
  (`DLP06R01.prt`) ou por **natureza** (`nat.prt`) — mesmo produtor FINR190,
  layouts distintos.
- Competência = `E5_DATA` (data da baixa), não emissão/vencimento.
- Moeda: relatório emitido "em REAL" (movimentos moeda 01).

### BR-R01-011 — Layout ≠ produtor — `PROVEN`

- `DLP06R01.prt` e `nat.prt` são layouts `.prt` compartilhados. Para pagar, o
  produtor é **FINR190** (menu "Relação de Baixas DLP" + roster + fonte).
- Não inferir identidade de produtor a partir do `.prt` impresso.

---

## §2 — R02 · Baixas a receber (`DLP06R01` custom — fonte ausente)

Artefatos: `Recebidos.pdf` (36p), `Recebidos.xlsb` (657 linhas de dados).
Paridade: doc 84 §2 · errata: doc 80 §30 · produtor: doc 83 §2, E1 (TI/ERP).
**G4 PENDING — o fonte não está no acervo; toda regra abaixo provém de
paridade com o artefato, não de leitura de código.**

### BR-R02-001 — População do artefato — `PROVEN`

- 657 linhas = **649 chaves com título** (SE5'R' × SE1 pela chave do título)
  + **8 movimentos `PA` sem título** (origem `FINA750`, histórico "Valor
  pago s/ Titulo").
- Universo `SE5'R'` set/2026 = 746 movimentos; 89 sem título — apenas os 8
  entram no artefato.

### BR-R02-002 — Exclusões observadas — `AS-IS` (regra geral `PENDING`)

- **8 linhas de decomposição** (`MT`/`JR`/`DC` + 1 `VL` duplicado) suprimidas:
  seus valores já estão embutidos no `E5_VALOR` da baixa `VL` principal
  (ex.: VL 587,70 contém juros 4,94 + multa 11,42 = 16,36).
- **3 `PA`/`DEB` sem título excluídos, identificados por linha lógica**
  (docs sanitizados): `<RECEBIMENTO-SEM-TITULO-A>` (118,27, `FINA090`, f01) · `<RECEBIMENTO-SEM-TITULO-B>`
  (1.000,00, `FINA090`, f01) · `<RECEBIMENTO-SEM-TITULO-C>` (1.537,00, `FINA750`, f02).
- **Regra geral que inclui 8 e exclui 3: `PENDING`** — dependente do fonte.
- Demais sem-título (FOL/COF/NDF/vazio/NF-DEB) corretamente fora.

### BR-R02-003 — `Total Baixado` — `PROVEN`

- `Total Baixado = SE5.E5_VALOR` — 657/657 exato.

### BR-R02-004 — `Valor Original` — `PROVEN` (2 regras físicas)

| Caso | Regra | Cobertura |
|---|---|---|
| Linha com título | `SE1.E1_VALOR` | 649/649 exato |
| Linha `PA` sem título | **provisão `'P'` espelhada** na própria SE5 — mesmo numero/clifor, motivo NOR, origem `MATA121`/`FINA050` | 8/8 exato |

- Fluxo conferido integralmente (ex.: numero <MOV-PROV-A>: provisão 1.571,60 =
  recebimentos 877,00+119,96 + compensação 'P' 574,64).
- **Errata:** o "residual de R$1,00" da rodada anterior era erro de soma na
  consolidação manual (15.836,71 transcrito como 15.837,71) — Δ real =
  **R$0,00** (doc 80 §30.A). ΣVO = 5.301.533,30 exato.

### BR-R02-005 — Resumos e componentes — `PROVEN`

- `Baixados` = Σ`E5_VALOR` não-CMP → 5.236.376,13 exato.
- `Compens.` = lado `CP` dos pares `CMP` (7+7 espelhadas) → 19.109,94 exato.
- `Jur/Multa` = `E5_VLJUROS + E5_VLMULTA` → 44,16 exato.
- Mesma regra de composição do pagar — layouts compartilhados.

### BR-R02-006 — XLSB × PDF — `PROVEN` (agregado)

- `ΣTB PDF = ΣTB XLSB − 40.431,46` = total do log de inconsistências impresso;
  identidade das linhas do log `PENDING` (mesma natureza do residual R01).

### BR-R02-007 — Coluna `Orig` — `PROVEN` (semântica distinta do pagar)

- Preenchida **somente** nas 8 linhas sem título (= `E5_FILORIG`: 2×`01` +
  6×`02`); linhas com título exibem vazio (SE1 compartilhada).
- **Diferença de semântica vs R01 documentada** — coerente com produtor
  distinto.

### BR-R02-008 — Produtor — `PENDING` (E1, TI/ERP)

- WHERE do FINR190 (`'R'`) reproduz 649/690 ≠ 657 oficial → **FINR190
  descartado** como produtor do receber (doc 80 §17.D).
- Produtor = custom `DLP06R01`; fonte ausente do acervo (`DLP06P01/F01/F02/
  F03` verificados = utilitários não relacionados).
- Todas as regras de seleção acima são **parity-proven para a emissão
  09/2026**; a forma geral (filtros fixos, parâmetros, demais competências)
  permanece `PENDING`.

---

## §3 — R03 · P7 / Registro de Inventário (MATR460 candidato)

Artefatos: `Estoque.pdf` (completo, 3.946.431,87), `Resumo Estoque.pdf`
(MP/PA/PI, 2.976.967,56); vídeo 35:00/37:00; `Material em processo.xlsb`.
Paridade parcial: doc 84 §3.

### BR-R03-001 — Identidade e finalidade — `AS-IS`

- Rotina observada: **"Registro de Inventário Modelo P7"**; roster oficial
  vincula "Estoque P7" → `MATR460` (variante a confirmar — E2).
- Saída: CLASSIFICAÇÃO FISCAL, DISCRIMINAÇÃO, UNID, QUANTIDADE, UNITÁRIO,
  PARCIAL, TOTAL + RESUMO por tipo em EM ESTOQUE / EM PROCESSO + TOTAL GERAL.
- Alimenta SPED Bloco H (roster).

### BR-R03-002 — Fechamento iterativo / versionamento — `PROVEN`

- O P7 foi reemitido ≥4× no dia 30/09 com totais distintos (3.776.994,69 →
  ~2.756.1xx → 3.946.431,87 / 2.976.967,56): **o fechamento é iterativo** e
  emissões sucessivas variam — cada versão precisa ser rastreável.
- A **versão homologada depende de aceite funcional** — não é
  automaticamente a última emissão.
- **Implicação TARGET:** todo indicador derivado exige `as_of`/versão
  (coerente com AC-E6-02/08, doc 81/82).

### BR-R03-003 — EM PROCESSO = relatório MATR989 — `PROVEN`

- Seção EM PROCESSO do P7 = `Material em processo.xlsb` — **355.240,51
  exato** (MP 354.938,50 + PI 254,44).

### BR-R03-004 — EM ESTOQUE — `PROVEN` (totalização; parâmetros `PENDING`)

- PA/PI do P7 = Saldo Atual do MATR320 **exato** (190.511,24 / 24.528,60).
- Total EM ESTOQUE reproduzido **ao centavo** (rodada 15, doc 80 §33.D):
  `EM ESTOQUE = SA_emissão − estoque loc99_emissão = 3.884.464,444 −
  293.273,084 = 3.591.191,36` (Δ residual 0,004 float).
- loc99 no estado de emissão reconstruído: `B9_VINI1@0831[99] +
  RE3-in(TransfProc) + SD3[loc99] = 215.673,929 + 940.599,335 −
  863.000,176 = 293.273,088`.
- Parâmetros por emissão seguem `PENDING` — E2; rodada 17 (doc 80
  §35): `Resumo Estoque.pdf` (folha 74) usa a **mesma data-base e o
  mesmo estado de custo** do completo (PA/PI bit a bit) — diverge por
  **escopo de tipos (MP/PA/PI) + exclusão poder3-MP**, não por
  `as_of` (BR-R03-007).

### BR-R03-005 — Origem física — `PROVEN` (totalização) / `TO_INVENTORY` (produtor)

- Binding de totalização provado: `EM ESTOQUE` = saldo físico ex-99 no
  `as_of` da emissão (compatível com SB9/`VINI1` no estado de emissão) e
  `EM PROCESSO` = MATR989 (doc 80 §33.D). O `as_of` da medida é da
  emissão, **não** do snapshot corrente — dado corrente contém o drift
  de repricing.
- Mecanismo produtor `TO_INVENTORY`: fonte `matr460.prx`/SP ausente;
  hook `A460UNIT.prw` ajusta `TOTAL/VALOR_UNIT/QUANTIDADE` por produto
  na tabela `MP7GDA`; arquivos de trabalho `MP7_*`
  (PRODUTO/ARMAZEM/DATAFECHAMENTO/TIPOMOV[`aSalAtu`·`QtCus`·
  `aDadosCF9`]/QUANTIDADE/TOTAL) persistem até ~04/2024; `MV_ALMTERC`
  exposto no hook. `EM ESTOQUE + EM PROCESSO = TOTAL P7` (exato ao
  centavo).

### BR-R03-006 — EM ESTOQUE exclui armazém de processo — `PROVEN`

- Hipótese anterior (Δ −293.273,08 ≈ armazém 99) **confirmada
  centesimalmente** (doc 80 §33.D): EM ESTOQUE P7 = saldo físico ex-
  `MV_LOCPROC='99'`. O armazém de processo não entra em EM ESTOQUE;
  EM PROCESSO é medida MATR989 (saldo alocado a OPs), **diferente** do
  saldo físico de loc 99 (355.240,51 ≠ 293.273,08) — não confundir.
- Resta `PENDING`: extensão da exclusão a outros armazéns especiais
  (`MV_CQ='98'`, `MV_ALMTERC`) em outras parametrizações — depende de
  parâmetros de emissão (E2).

### BR-R03-007 — Emissão resumida P7: escopo MP/PA/PI e divergência MP — fatos `PROVEN` / causa `PENDING`

**Fatos observados — `PROVEN`:**

- `Resumo Estoque.pdf` (folha 74) é emissão **distinta** do completo
  (folha 101), mesmo layout "REGISTRO DE INVENTÁRIO" e mesma
  data-base 30/09/2026 — prova: PA/PI idênticos bit a bit nas duas
  (EM ESTOQUE 190.511,24/24.528,60; EM PROCESSO PI 254,44) → mesmo
  estado de custo (doc 80 §35.A).
- A emissão resumida apresenta **somente** as classificações
  MP/PA/PI; a divergência monetária entre as emissões concentra-se
  **exclusivamente em MP**: EM ESTOQUE −587.698,28 (3.071.684,80 →
  2.483.986,52); EM PROCESSO −77.251,73 (354.938,50 → 277.686,77).
- Existe no SX1 o grupo `MTR460`, pergunta 02 **`Saldo em Poder
  3º ?`** com opções Sim/Não/De Terceiros/Em Terceiros (BR-R03-008) —
  mecanismo candidato oficial para exclusão de material de terceiros.

**Hipótese empiricamente sustentada — `PENDING` (não é regra oficial):**

- Modelo `QTNP@emissão`: excluir do universo ex-99 os produtos com
  `B2_QTNP>0` no estado de emissão (QTNP corrente revertido por
  `SD1`/`SD2` com `F4_PODER3='R'/'D'` inseridos pós-01/10 16:16:27)
  → estoque **587.621,85** vs alvo 587.698,28 — **residual 76,43**
  (99,987 %) — e processo **79.194,35** vs alvo 77.251,73 —
  **residual +1.942,62** (tipo '' 64.388,66 + RE9 12.410,84 + RE2
  2.394,85). Melhor ajuste entre ~10 hipóteses testadas; **não
  classificável como regra oficial** — é aproximação empírica.
- Hipóteses descartadas com evidência (doc 80 §35.C): filtro de
  armazém; `as_of` temporal; faixa/prefixo de produto; sem-movimento;
  poder3 por quantidade/posição SB6; emissão intermediária.

**Não demonstrado — `PENDING` (pacote E2, doc 82 §2.1):**

- Qual opção de `Saldo em Poder 3º ?` foi efetivamente selecionada em
  cada emissão e se ela explica a exclusão observada.
- População exata de produtos/valores excluídos (QTNP × SB6 ×
  workfile `aDadosCF9` × outra medida) e o instante do conjunto —
  direções opostas dos residuais (estoque +76,43 / processo
  −1.942,62) indicam diferença de **medida**, não só de `as_of`.
- Mecanismo do escopo de tipos MP/PA/PI: `MTR460` **não** possui
  parâmetro de tipo — exige seleção externa ao SX1 ou variante
  custom; semântica interna do MATR460 compilado indisponível.
- **Não generalizar:** nada demonstrado fora da emissão resumida de
  09/2026 filial 01.

### BR-R03-008 — Mapa de parâmetros MTR460 — `PROVEN` (catálogo SX1)

- Grupo SX1 `MTR460` extraído integralmente (25 perguntas, filial
  '  '): `01 Saldo em Processo?`(Sim/Não) · `02 Saldo em Poder 3º?`
  (Sim/Não/**De Terceiros**/**Em Terceiros**) · `03/04 Armazem
  Inicial/Final` · `05/06 Produto Inicial/Final` · `07–09 Sem
  Movim/Saldo Neg/Saldo Zera` · `10 Página` · `11 Nº Livro` ·
  `12 Imprime`(Livro/Termos) · `13 Data de Fechamento` · `14
  Descricao` · `15 Custo Zerado` · `16 Lista Custo`(Medio/FIFO/PEPS)
  · `17 Verif Sld Processo`(Data Emissao/Seq CM) · `18 Quebra
  aliquota` · `19 Lista MOD` · `20 Filiais` · `21 Sit. Trib.` · `22
  Arq. Exportação` · `23 Arq. Sped` · `24 Aglutina CNPJ+IE` · `25
  Saldo em Fabricação`.
- **Não existe parâmetro de tipo de produto** — o escopo MP/PA/PI da
  folha 74 exige mecanismo fora do SX1 (multi-seleção de tipos na UI
  ou variante custom) → `PENDING` E2.
- SX6 vigente: `MV_LOCPROC='99'`, `MV_CQ='98'`, `MV_CQREJEI='50'`,
  `MV_ALMTERC` vazio.
- **Addendum (P7-EVIDENCE-REUSE-003, 2026-10-28):** fonte
  `04. Estoque/A460UNIT.prw` **localizada no acervo** — ponto de
  entrada custom do MATR460 que, por produto, executa
  `UPDATE MP7GDA SET VALOR += <workfile>.TOTAL` (parâmetros: código,
  `MV_ALMTERC`, data de fechamento, workfile `MP7_*`). Confirma a
  cadeia `MATR460→MP7_*→MP7GDA→A460UNIT` (doc 80 §35.B) como
  `CODE_PRESENT`; o hook ajusta valor/custo, **não** implementa o
  recorte de escopo — o mecanismo MP/PA/PI permanece `PENDING` (E2).
  Fonte `matr460.prx` continua ausente. Decisão funcional do PO:
  dois escopos `all_products`/`mp_pi_pa` (doc 118 DEC-12).

### BR-R03-009 — Filtro de tipos × emissão oficial MP/PA/PI — `PROVEN` (fronteira negativa)

- O exploratório `GET /financeiro/stock-inventory` implementa
  `report_scope=mp_pi_pa` como `B1_TIPO IN ('MP','PI','PA')`
  (`constantes.MP_PI_PA_PRODUCT_TYPES`; owner canônico de tipos
  `domain/totvs/protheus_product_types.py`).
- Equivalência medida (doc 80 §35): PA/PI **idênticos** ao oficial;
  MP diverge — o recorte oficial exclui produtos com poder3 no
  `as_of` (Δ estoque 587.698,28 — modelo `QTNP@emissão>0` residual
  76,43; Δ processo 77.251,73 — modelo residual +1.942,62).
- **Regra de reúso:** o contrato oficial reusa a classificação
  canônica e adiciona a exclusão poder3
  (`third_party_materials=exclude` — candidato ao parâmetro `02`
  `Saldo em Poder 3º?` do `MTR460`, `PENDING` E2). O endpoint
  evoluiu ao motor P7 (IMPLEMENTATION-006, 29/10): `mp_pi_pa`
  permanece **tipo-only** com `parity_state` não verificado
  declarado até E2 — exclusão poder3 oficial não ativada;
  `officialP7:false` preservado (doc 119 §11).

---

## §4 — R04 · Consumo por OP — `BLOQUEADO`

- Sem artefato de consumo por OP na pasta; `matr860` candidato (papel
  decodificado rodada 7: MOD via SD3 RE1/TM999) — **não confirmado como o
  relatório em uso**. Toda regra `TO_INVENTORY`; próxima ação com
  Controladoria (doc 83 §4).

---

## §5 — R05 · Entradas e Saídas (MATR320)

Artefato: `Entradas e saidas.pdf` = `MATR320.prt` — "Resumo das Entradas e
Saidas EM R$", 01/09–30/09/2026, Matriz. Fonte:
`docs/13-fontes-totvs-protheus/04. Estoque/MATR320/matr320.prx` (padrão
TOTVS; execução via SP `MAT056` — a variante Delpi `Dmatr320.prx`/
`DLPR320` zera poder de terceiros e **não** foi a usada). Paridade:
doc 84 §4; evidência doc 80 §31.

### BR-R05-001 — Eixos do relatório — `PROVEN` (fonte)

- Colunas por tipo de produto: Saldo Inicial, Compras, Movimentações
  Internas, Requisições p/ Produção, Transferências, Produção, Vendas,
  Transf. p/ Processo, Devoluções, Poder de Terceiros, Saldo Atual + Total.
- Parâmetros `MTR320`: armazém de/até, tipo de/até, produto de/até,
  **emissão de/até**, moeda, **saldo Atual/Fechamento/CalcEst**, MOD,
  OPs SIGAMNT.

### BR-R05-002 — Saldo Atual = SB9 no recorte — `PROVEN` (10/10 tipos explicados)

- `SB9@30/09 f01` × `Saldo Atual` MATR320: **8/10 tipos exatos** (EM/GG/
  II/MC/MH/MS/MX/PA); PI −0,001 e MP +8.631,73 — ambos drift pós-emissão,
  MP **decomposto ao centavo** (doc 80 §34.C)
  (rodada 15, doc 80 §33.B): revalorização de custo médio pós-emissão em
  5 produtos (`<PRODUTO-CUSTO-A/B>` +98% do delta; 3 micro-revalorizações).
- `SA` impresso = saldo no `as_of` da emissão (01/10 16:16:27), não o
  snapshot corrente — ponte por produto em doc 80 §33.B / doc 84 §4.3.

### BR-R05-003 — Seleção física por tabela — `PROVEN` (fonte + dados)

- `SD1`: `F4_ESTOQUE='S'` (join SF4) · período por **`D1_DTDIGIT`** ·
  `D1_ORIGLAN<>'LF'` · `D1_LOCAL` no range · valor `D1_CUSTO`.
- `SD2`: `F4_ESTOQUE='S'` · período por `D2_EMISSAO` · `D2_ORIGLAN<>'LF'` ·
  valor `D2_CUSTO1`.
- `SD3`: `D3_EMISSAO` ∈ período · `D3_LOCAL` range · `D3_ESTORNO<>'S'` ·
  valor `D3_CUSTO1` **com sinal − quando `D3_TM > '500'`**.

### BR-R05-004 — Classificação SD1/SD2 — `PROVEN` (fonte + matches exatos)

- `F4_PODER3='N'` + `TIPO≠'D'` → **Compras** (SD1) / **Vendas** (SD2).
- `F4_PODER3='N'` + `TIPO='D'` → **Devolução de Vendas** (SD1) /
  **Devolução de Compras** (SD2).
- `F4_PODER3≠'N'` → **Entrada Poder Terceiros** (SD1) /
  **Saída Poder Terceiros** (SD2).

### BR-R05-005 — Classificação SD3 — `PROVEN` (fonte + matches exatos)

- `D3_CF` iniciando 'PR' → **Produção**.
- `D3_CF ∈ {RE4,DE4}` → **Transferências** (espelhadas → net ≈ 0).
- `D3_OP` vazio ∧ `D3_CF[3]≠'3'` → **Movimentações Internas**.
- `D3_OP` preenchido → **Requisições para Produção**.
- demais → **Transf. p/ Processo** (coluna **memo** — fora da equação
  do saldo).

### BR-R05-006 — Saldo Atual e Saldo Inicial — `PROVEN` (fonte)

- `nSaldoAtu` = Σ `B2_VATU<n>` (par10=1) / `B2_VFIM<n>` (par10=2) /
  `CalcEst` (par10=3) sobre `SB2` nos armazéns do range.
- **`nSalant` é derivado**: `SaldoAtu − Σ colunas de movimento` — não é
  saldo inicial cadastrado. Equação validada ao centavo na linha MP:
  `SA = SI + Compras + MovInt + Requis + Transf + Produção − Vendas
  + DevV − DevC + EntPT − SaiPT`.

### BR-R05-007 — Reconciliação coluna a coluna — `PROVEN` (ao centavo, escopo completo)

- **13/13 colunas exatas em estado de emissão** para MP (reconstrução
  via `TTAT_COLD` com corte `TTAT_DTIME > timestamp_de_emissão`);
  residual MovInt ~R$0,48 de §31 **resolvido** (rodada 15, doc 80
  §33.A — era artefato de sobre-reversão).
- Expandida a **todos os 10 tipos** (doc 80 §33.C, verificada §34.B):
  120/120 colunas de fluxo exatas e **130/130 células oficiais Δ=0,000**
  (SA via equação de fluxo no `as_of` da emissão); Δ MP +8.631,73 é
  contra o snapshot posterior — decomposto ao centavo (§34.C)
  (decomposto, BR-R05-002). Matriz em doc 84 §4.2.

### BR-R05-011 — Reconstrução `as_of` de custos via TTAT — `PROVEN`

- Custos regravados in-place por `MATA330`/`MATA241`/`MATA460A`/`RPC`
  são recuperados de `SD*_TTAT_LOG.TTAT_COLD` **somente** para updates
  com `TTAT_DTIME > timestamp_de_emissão`. Reverter updates anteriores
  à emissão introduz erro artificial (causa do ex-residual R$0,48).
- Inserções pós-emissão com datas retroativas são detectadas por bloco
  `R_E_C_N_O_`/TTAT-insert e excluídas da leitura `as_of`; linhas
  deletadas são pares espelhados líquido-zero (BR-R05-008).

### BR-R05-012 — Ponte emissão→snapshot por produto — `PROVEN`

- `Δ SA↔SB9` por produto: `residual_p = B9_VINI1@0930_p −
  (B9_VINI1@0831_p + SD1_p − SD2_p + SD3_exTransfProc_p)` no estado de
  emissão. Para MP set/2026: Σ = **+8.631,731 = oficial, Δ 0,000**
  (doc 80 §34.C) — 5 produtos de revalorização (+8.631,741) +
  `<PRODUTO-REVAL-D>` −0,010 (linha RE0 RECNO `4817031` repriced
  60,760→60,770 por `MATA330` 21/10) + 4 micro-ajustes TTAT líquido
  0,000. Mecanismo = revalorização de custo médio pós-emissão.
- **Precisão:** `B9_VINI1`/`D*_CUSTO*` são `float(53)` — agregar com
  `CAST(... AS DECIMAL(30,9))` por linha antes do SUM; somar floats e
  converter depois mascara micro-ajustes reais (erro ~1e-2 observado).
- `TransfProc` (CF `RE3`) é excluído do fluxo de valor porque
  **permanece no estoque da filial** (armazém 99) — coerente com a
  coluna memo.

### BR-R05-008 — Retificações retroativas alteram a leitura histórica — `PROVEN`

- Doc `<NF-RETIF-A>` (sanitizado): itens reclassificados TES `001`→`085`
  em ~20-21/10 com datas retroativas (RECNO vizinho datado 20-21/10) — na
  emissão contavam como Compras (+94.018,81); hoje contam como EntPT
  (+103.602).
- **Regra TARGET:** todo histórico reproduzível exige `as_of` de linha
  (linha viva/emission-time) ou snapshot — dados correntes NÃO
  reproduzem relatórios emitidos antes de retificações.

### BR-R05-009 — Armazéns especiais — `AS-IS` (constantes)

- `MV_LOCPROC` (armazém de processo, default `'99'`) e `MV_CQ`
  (qualidade, default `'98'`) entram na SP e na flag `lLocProc`
  (sinalização de TransfProc na equação derivada).

### BR-R05-010 — Identidade da SP e janela SD1 — `TO_INVENTORY`

- O fonte mostra a janela SD1 por **`D1_DTDIGIT`** (digitação), não
  emissão — os matches centesimais confirmam DTDIGIT na prática. A SP
  `MAT056` é binária (fonte indisponível); assumir lógica do `.prx`
  como espelho — validada empiricamente coluna a coluna.

---

## §6 — R06 · CPV / Kardex (MATR910) — `PROVEN` (escopo filial 02 / loc 01, 09/2026)

**Fonte no acervo:** `docs/13-fontes-totvs-protheus/04. Estoque/matr910_dlp.prx`
— `SOURCE_AVAILABLE` (variante Delpi). `CODE_DEPLOYED` **pendente** (versão
compilada no RPO não inspecionada — E7, doc 82 §2.1). Todos os pontos
testados do comportamento observado são compatíveis com o fonte.

- `BR-R06-001` (produtor/modelo — `PROVEN`): cada bloco de produto =
  UNION de três fontes — SD1 (entradas NF), SD2 (saídas NF), SD3
  (internas/produção/inventário) — com cabeçalho SB1
  (cod/desc/UM/tipo/grupo/POSIPI/armazém). Joins:
  `SB1.B1_COD=D*_COD`; SD1/SD2 fazem join SF4 por `D*_TES=F4_CODIGO`.
  Grupo SX1 `MTR910` — 22 perguntas (mv_par01..22), catálogo extraído.
- `BR-R06-002` (filtros — `PROVEN` fonte + empírico): `SF4.F4_ESTOQUE='S'`
  (SD1/SD2); `SD3.D3_ESTORNO<>'S'` — pares de estorno excluídos
  (verificado: doc com trio DE6-limpo + DE6/RE6 `ESTORNO=S`/deletado
  imprime só a linha limpa); `D1_ORIGLAN<>'LF'` e `D2_ORIGLAN<>'LF'`;
  `D*_LOCAL=mv_par08` (loc 01 observado); `D1_REMITO=''`; cláusula
  `D3_SERVIC` (CQ/`MV_CQ`); SB1 limitado por produto mv_par01/02, tipo
  mv_par03/04, grupo mv_par18/19 e `B1_COD<>MV_PRODIMP`.
- `BR-R06-003` (data de competência por tabela — `PROVEN`): SD1 usa
  **`D1_DTDIGIT`** (digitação — 281 linhas impressas na data de digitação
  com digitação≠emissão; docs emitidos em out/digitados em set entram na
  competência); SD2 usa **`D2_EMISSAO`** (590/590); SD3 usa
  **`D3_EMISSAO`**. Reflete o fonte (queries literais).
- `BR-R06-004` (ordenação — `PROVEN`): por data do movimento; dentro da
  mesma data por `*_NUMSEQ` — mv_par16=Digitação ordena pela coluna
  SEQUENCIA (D1/D2/D3_NUMSEQ). Verificado: 1.971/1.971 grupos de mesma
  data consistentes com `D3_NUMSEQ`.
- `BR-R06-005` (coluna REF "P.V.,FOR, CC, PJ, OP ou OS" — `PROVEN`):
  SD1 → `F-`+`D1_FORNECE` (260/260); SD2 → `P-`+`D2_PEDIDO` (594/594);
  SD3 → `OP`+`D3_OP` (6.060/6.060) ou `CC`+`D3_CC` (~2.443, zero
  divergência).
- `BR-R06-006` (custos — `PROVEN`): SD1 → `D1_CUSTO`, SD2 → `D2_CUSTO1`,
  SD3 → `D3_CUSTO1`, moeda mv_par11=1. Valores impressos são **as_of da
  emissão** (01/10 16:58, pré-recálculo MATA330 ~17:5x): **9.357/9.357
  (100%)** com vínculo — 7.376 `CUR` + 1.981 `TTAT_OLD` de revalorização
  posterior; binding de identidade linha-a-linha verificado por blocos
  (9.357 movimentos / 1.544 blocos). Errata r20 (doc 80 §38): o
  "99,88%" anterior era artefato do roteamento estrito da reconciliação
  inicial.
- `BR-R06-007` (cadeia de saldo — `PROVEN`): saldo inicial do cabeçalho =
  `CalcEst(produto, local, mv_par05)` ≡ `B9_QINI`/`B9_VINI1` @2026-08-31
  (1.544/1.544 exato); saldo acumulado linha a linha = saldo impresso —
  1.544/1.544 blocos contínuos (qtd e valor).
- `BR-R06-008` (sinais/devoluções — `PROVEN` no fonte): com `MV_LISTDEV`
  ativo, `zMTR910Dev` marca linhas `TIPONF='D'` (dbSeek `SF1`/`SF2`) e
  o relatório imprime a devolução **na coluna oposta com sinal −**:
  SD1 tipo `D` (devolução de venda, ex. TES 120/CF 2201) → coluna
  **saídas** ×−1 e `aSalAtu += QUANTIDADE` (mercadoria retorna); SD2
  tipo `D` (devolução de compra, ex. TES 561/530, CF 6201/5201) →
  coluna **entradas** ×−1 e `aSalAtu −= QUANTIDADE` (devolução sai).
  Observadas 11 linhas (4 entrada− SD2 + 7 saída− SD1), todas com custo
  `CUR` exato — doc 80 §38.
- `BR-R06-009` (população — `PROVEN` no escopo observado): produtos com
  ≥1 movimento elegível (mv_par07 "Lista Prods S/Movim" = Não — 0 blocos
  sem movimento); 26 produtos `MOD*` (tipo `MO`) fora — nenhum tem SB9;
  1.426 produtos com SB9 fora do kardex (1.023 com saldo ≠0 @30/09) —
  o relatório cobre **movimento**, não posição.
- `BR-R06-010` (semântica CPV — `PROVEN`, regra existente verificada —
  rodada 21, doc 80 §39): **o CPV já existe implementado e canônico** —
  `GET /supplies/cpv` na api-delpi (`supplies_router.py` op
  `get_supplies_cpv`, auth `KPI_SUPPLIES_ACCESS`):
  `CpvQueryRepository` → `SUM(SD2.D2_CUSTO1)` com `D2.D_E_L_E_T_=''`,
  `D2_EMISSAO` no período, `D2_FILIAL` opcional e
  `D2_CF IN (5101,5124,6101,6124)` (CFOPs fixos no contrato — o campo
  `cfops` do DTO não é exposto na rota); o use case
  `GetCPVUseCase` compõe ROL (`FinancialRepository.get_rol` — SD2 vendas
  elegíveis `F4_DUPLIC='S'` + exceções MI/5927/5911-6911, menos devoluções
  de venda SD1) e devolve `cpv_total`, `cpv_percentage`, cortes
  `by_cfop`/`by_tm`/`top_products`/`top_documents`. Docstring do repo:
  "CPV alinhado ao relatório Kardex" (commit `4bd217a3ae` — realinhamento
  deliberado SD2010 + CFOPs padrão). Consumidores verificados:
  `dashboard-supplies` `CpvPage.tsx` (via `/apps/api-delpi/supplies/cpv`),
  `supplies-api` `OverviewCompositionService` KPI-CPV → `cpv_percentage`
  (`SuppliesDelpiReads.get_cpv`), `strategic_indicators_gateway`
  `"KPI-CPV"→"supplies-cpv"`, chat/DAVI `SUPPLIES_CPV` agent_route.
  **Crosswalk R06:** CPV implementado = subconjunto das saídas SD2 do
  kardex restrito aos CFOPs de venda — as saídas agregadas do MATR910
  continuam **não** sendo CPV (incluem SD3 requisições/transferências/
  INVENT e CFOPs fora do conjunto) — a observação física da versão
  anterior se mantém; o que muda é que a "medida CPV" **existe** fora
  do relatório, como regra de API própria. **Lacunas para evidência de
  fechamento (`REUSE_PARTIAL`):** (a) `D2_CUSTO1` é custo **corrente**,
  não `as_of` — revalorização MATA330 posterior altera o valor medido
  (mesma natureza do saldo final `STALE_EVIDENCE`); (b) sem filtro
  `D2_ORIGLAN<>'LF'` nem `F4_ESTOQUE='S'` no WHERE (o conjunto CFOP já
  delimita vendas); (c) branch único opcional — sem consolidado multi-
  unidade explícito nem recorte produto/tipo; (d) cobertura de testes
  limitada a contrato/registro de rota (sem teste unitário do SQL, ao
  contrário de outros repositórios SD2). Para PROC-0072 o contrato
  existente atende a medida "CPV de vendas por emissão"; a cadeia de
  evidência `as_of` de fechamento exige decisão do owner sobre custo
  histórico (TTAT) ou snapshot — `DECISION_REQUIRED` se a medida de
  fechamento exigir imutabilidade temporal.
  **ERRATA/DECISÃO PO 23/10/2026 (supersede a exigência de `as_of`/snapshot e o `DECISION_REQUIRED` acima apenas para CPV corrente):** CPV mensal é consulta **viva** por competência; correção retroativa na competência de origem seguida de recálculo autorizado Protheus altera o CPV apresentado em consultas futuras àquele mês. `D2_CUSTO1` corrente é compatível com essa regra, não uma lacuna temporal. Valores/evidências anteriormente homologados têm rastreabilidade separada, sem afirmar snapshot implementado. E6=C versa especificamente sobre MOD e não estabelece solução técnica para CPV. Permanecem possíveis lacunas independentes (granularidade, CFOPs, testes), sujeitas a requisitos comprovados.

- `PENDING`: versão compilada no RPO (E7); parâmetros efetivos da emissão
  além dos inferidos (mv_par09=`D`, mv_par16=Digitação pela ordenação,
  mv_par10 `Saldo a considerar` — provável Fechamento dado o as_of);
  classificação poder3 (`F4_PODER3`) no escopo kardex.
- `STALE_EVIDENCE` (saldo final vs SB9 corrente): 354 produtos divergem
  **só em valor** (Δqtd=0 em todos) — SB9@0930 reconstruído em 21/10 após
  recálculo; o saldo impresso é o as_of da emissão. 227 < R$1; 127 ≥ R$1.

---

## §7 — R07 · Inventários (MATR910 filtrado) — `PROVEN` (filial 02 / loc 01+99)

- `BR-R07-001` (artefato — `PROVEN`): `Invent.xlsb` (1 aba, 50 linhas, 45
  movimentos efetivos) = mesmo layout kardex filtrado a
  `D3_DOC='INVENT'` — TES **999/RE0** (saída) e **499/DE0** (entrada);
  cobre loc 01 e loc 99 da filial 02.
- `BR-R07-002` (semântica — `PROVEN`): ajuste de inventário = SD3 com doc
  `INVENT`; entrada DE0 soma qtd/valor ao saldo; saída RE0 subtrai; custo
  = `D3_CUSTO1` as_of emissão; saldo resultante impresso na linha —
  mesma cadeia de BR-R06-007.
- `BR-R07-003` (reconciliação — `PROVEN`): 45/45 linhas vinculadas ao SD3
  — 35 match direto + 10 via `TTAT_OLD` de `D3_CUSTO1` (revalorização
  pós-emissão; ex.: 1.330,650 impresso vs 1.331,299 corrente). Totais
  oficiais: entradas 2.348,108 / R$185.103 · saídas 30.808,206 · líquido
  −28.460,098. População física INVENT do escopo coberta pelo artefato.
- `PENDING`: versão RPO do produtor (E7, compartilhada com R06);
  confirmação do parâmetro de armazém da emissão (loc 01+99 observados).

---

## §8 — R08 · Material em Processo (MATR989) — `PROVEN` (paridade física rodada 22)

`Material em processo.xlsb` = "Saldo em Processo (Ana)" (aba única `01-01`,
57.359 linhas, 8 colunas, Dt.Ref 01/10/2026 · Hora 16:15:58 · Emissão
01/10/2026): `CODIGO, DESCRICAO, UM, LOCAL, ORDEM PRODUCAO, TIPO RE/DE,
QTDE EM PROCESSO, VALOR EM PROCESSO`. Fonte `matr989.prx` ausente do
acervo (`SOURCE_MISSING` — classe DLP06R01); produtor = rotina oficial
MATR989 variante analítica **inferida** por roster + título da aba
(`PRODUCER_INFERRED_BY_ARTIFACT`; relatório emitido prova
`EXECUTION_OBSERVED`, não identidade do código implantado — versão RPO
pendente, E8). População e valores reproduzidos 100% no físico
(doc 80 §41/§42).

### BR-R08-001 — Grão da linha = linha física SD3 `RE*` — `PROVEN`

Cada linha com OP do relatório corresponde 1:1 a uma linha `SD3010` com
`D3_CF LIKE 'RE%'`: **1.501 linhas impressas = 1.501 linhas SD3** (uma
única ocorrência de 2 linhas SD3 no mesmo `D3_DOC` gera 2 linhas no
relatório — grão é a linha de movimento, não o documento). Chaves
exibidas: `CODIGO`=`D3_COD`, `ORDEM PRODUCAO`=`D3_OP`, `TIPO RE/DE`=`D3_CF`,
`LOCAL`=`D3_LOCAL`. Não há coluna de documento; duplicatas aparentes de
(produto, OP, tipo) são linhas de docs distintos (93 chaves).

### BR-R08-002 — Quantidade/valor = `D3_QUANT`/`D3_CUSTO1` — `PROVEN`

`QTDE EM PROCESSO` = `D3_QUANT`; `VALOR EM PROCESSO` = `D3_CUSTO1`
(custo do movimento a moeda 1, gravado na emissão — custo médio da época:
ex. 9,16/u ↔ `B2_CM1`=9,16).

### BR-R08-003 — População do bloco com OP — `PROVEN`

`SD3010` filial 01, `D3_OP<>''`, `D_E_L_E_T_<>'*'`, `D3_ESTORNO<>'S'`,
`D3_EMISSAO<='20260930'` (corte de competência), `D3_CF` em `RE0/RE1/RE2/RE9`.
Movimentos `RE*` datados de 01/10+ são excluídos (provado: 4 linhas RE9 de
01/10 na mesma OP não impressas). Devoluções `DE*` subtraem o par — ver
BR-R08-006.

### BR-R08-004 — Escopo da OP avaliado no instante da emissão — `PROVEN`

O par (produto, OP) é impresso somente se a OP estiver **aberta na data de
referência/emissão**: sem apontamento de produção (`SD3 D3_CF LIKE 'PR%'`)
e não encerrada. Evidência: **0 das 650** pares impressas tem `PR0` da OP;
**33 OPs excluídas** têm primeiro `PR0` exatamente em 01/10 (dia da
emissão); as OPs impressas com produção têm `PR0` só a partir de 02/10 ou
nenhum. **3 OPs excluídas nunca produziram** (`C2_QUJE=0` mas `C2_DATRF`
preenchido = encerradas/canceladas); zero OPs impressas têm esse perfil.
Discriminação intra-dia (PR0 de 01/10 antes vs depois das 16:15) não é
observável por data — fronteira registrada como `as_of` do dia Dt.Ref.

### BR-R08-005 — Saldo por par = Σ`RE*` − Σ`DE*` ≤ corte — `PROVEN` (estrutura)

Para os **650/650 pares** impressos: Σ qtde e valor `RE*−DE*` ≤30/09 =
impresso, Δ 0,000 exato. Nenhum par impresso contém `DE*` — o mecanismo de
neteo é estrutural (inferido da seleção), não exercido dentro das pares
vivas desta competência. `DE*` observados (752 movs.) pertencem a pares de
OPs já produzidas/excluídas.

### BR-R08-006 — Bloco sem OP = posição do armazém 99 no `as_of` da emissão — `PROVEN`

Linhas sem `ORDEM PRODUCAO` = saldo físico do armazém 99 na data-base de
fechamento **no estado vigente na emissão** — reconciliável com `SB9010`
`B9_DATA='20260930'`, `B9_LOCAL='99'`, filial 01 (`QTDE`=`B9_QINI`,
`VALOR`=`B9_VINI1`). As 753 linhas dessa faixa foram **regravadas em
21/10 19:13** (`I_N_S_D_T_`, todas) — 20 dias após a emissão; o impresso
carrega o custo do instante do relatório, a SB9 vigente carrega o custo
pós-recálculo. **569/573 exato**; 4 diferenças temporais (aliases — doc 80
§42.D): `<PRODUTO-WIP-A>` ΔR$449,16 e `<PRODUTO-WIP-B>` Δ0,144
(revalorização `B9_VINI1` — mesma classe `STALE_EVIDENCE` do drift R05/R06),
`<PRODUTO-WIP-C>` Δ0,01 e `<PRODUTO-WIP-D>` Δ−0,001 (resíduo de centavo).
Zero produtos SB9-loc99 ≠ 0 ausentes do artefato. ΣΔ = +449,294 =
SB9 corrente (293.722,382) − impresso (293.273,088), decomposto 100%.

### BR-R08-007 — EM PROCESSO do P7 = total do MATR989 — `PROVEN`

Total do artefato = **R$355.240,51**, exato com EM PROCESSO do P7 completo
(BR-R03-003). Decomposição em precisão original (3 dec): loc-99 sem OP
293.273,088 + `RE0` 588,500 + `RE1`(loc 01) 254,437 + `RE2` 48.713,642 +
`RE9` 12.410,845 = **355.240,512** → exibição 355.240,51 (half-up 2 dec).
Somar componentes já arredondados dá 355.240,52 — artefato de
arredondamento, não divergência (doc 80 §42.A). O bloco `RE1`
em `LOCAL='01'` corresponde à fatia **PI** do EM PROCESSO (254,44 — doc 80
§33.D). EM PROCESSO **não é** o saldo físico do armazém 99: é estoque do
armazém de processo (293.273,088) **+ material alocado a OPs abertas**
(61.967,424).

### BR-R08-008 — Linhas de apresentação / catálogo — `AS-IS`

Das 57.355 linhas de dados, ~54.600 são produtos sem saldo (qtde=0,
valor=0, sem OP) e 141 são códigos `MOD*` (mão de obra, qtde/valor 0) —
linhas de catálogo sem efeito nos totais. Linhas efetivas: 1.501 com OP +
573/555 produtos sem OP com saldo ≠ 0.

### BR-R08-009 — Reuso transversal existente — `REUSE_PARTIAL`

- `api-delpi` `stock_value_historical_sql.py` (`supplies_repositories`):
  engine canônico SB9@data + ponte SD3 (mesma reconstrução usada aqui) —
  **reutilizável** para o bloco sem-OP e para saldos `as_of`.
- `stock_value_query_repository._fetch_wip_proxy_rows` expõe
  `em_processo_proxy_value` = `SUM(SB2.B2_VATU1)` nos armazéns de processo
  (`WORK_IN_PROCESS_WAREHOUSES=('50','98','99')`, método
  `sb2_process_locations`): cobre **apenas** o bloco sem-OP corrente
  (~293k), não o alocado a OP (61.967,42) nem `as_of` — **parcial**.
- `pedidos_venda_abertos/ops_abertas_sql.py` codifica o predicado canônico
  de OP aberta (`C2_QUANT>C2_QUJE AND C2_DATRF=''`) — semântica adjacente:
  o MATR989 exige `C2_QUJE=0` (nenhuma produção), não só saldo pendente.
- Não existe serviço que materialize o saldo `RE*−DE*` por OP — lacuna
  real para a Central de Fechamento (`TARGET` futuro).

### T-R08-01..05 — testes executados (rodada 22, SELECT-only, `as_of` 01/10 16:15)

| Teste | Regra | Resultado |
|---|---|---|
| T-R08-01 | BR-R08-001/002/003 | positive · 1.501/1.501 linhas com OP = linhas SD3 `RE*`; 650/650 pares (produto,OP) qtde+valor exatos |
| T-R08-02 | BR-R08-006 | positive · 569/573 exato vs `SB9010`@20260930 loc 99; 4 Δ temporais explicados (revalorização/centavo) |
| T-R08-03 | BR-R08-004 | sibling/negative · 33 OPs com `PR0` em 01/10 excluídas; 3 OPs encerradas-sem-produção excluídas; 15 pares filial 02 excluídos; 118 OPs sem `PR0` impressas |
| T-R08-04 | BR-R08-007 | positive · total artefato = EM PROCESSO P7 = 355.240,51 exato |
| T-R08-05 | BR-R08-003 | negative · movimentos `RE*` de 01/10 na mesma OP não impressos (corte 30/09) |

**Pendente (E8):** fonte `matr989.prx`/versão RPO implantada
(`TO_INVENTORY` — mesma classe E7 de R06/R07); semântica intra-dia do
corte de OP (`as_of`-dia vs timestamp 16:15); neteo `DE*` dentro de par
impresso
(não exercido nesta competência).

---

## §9 — R09 · Faturamento × MOD (DLP204) — modelo físico `PROVEN` (rodada 24)

Artefato `Fat x MOD.xlsb`: abas `1-Fl01` (2.459 linhas) e `2-Fl02` (2.017),
título `Estrutura Filial NN`, colunas `PA, Seq Comp, Cod Produto, Desc
Produto, Qtd Fat., UM, Quantidade, Custo Unitario, Custo Total, Custo
Produto, Horas` — 4.476 linhas de detalhe, sem linhas de total persistidas.

### BR-R09-001 — Produtor e variante — `PROVEN`

`DLP204.prw` **presente no acervo** (`docs/13-fontes-totvs-protheus/06.
Financeiro/DLP204.prw`, autor Gabriel, 03/07/2019) — `SOURCE_AVAILABLE` +
`EXECUTION_OBSERVED` (artefato). Emissor `FWMSEXCEL`: uma aba `FlNN` por
filial, tabela `Estrutura Filial NN`, colunas exatamente as observadas;
linha `Total Produto ---->` existe apenas na sessão Excel interativa
(`oExcel:AddRow` por PA com `nThrs`) — não persistida no XLSB.
`CODE_DEPLOYED` não declarado (versão RPO não vinculada — E9).

### BR-R09-002 — Parâmetros (SX1 grupo `DLP204`) — `PROVEN` (catálogo) / inferido (emissão)

`MV_PAR01` Data de · `MV_PAR02` Data até · `MV_PAR03/04` Produto Acabado
de/até · `MV_PAR05/06` Grupo de/até · `MV_PAR07/08` Tipo de/até ·
`MV_PAR09` Roteiro de Operações (default `01`) · `MV_PAR10` Seleciona
Filiais (combo) · `MV_PAR11` "Exibir MP?" (combo). Artefato: competência
inferida **2026-09-01→2026-09-30** (`PROVEN` por reprodução integral de
`Qtd Fat.`), ambas filiais (par10=Sim), par11=**Não** (ausência das
linhas `03/05/07` de componentes não-MOD — ver BR-R09-005).

### BR-R09-003 — Seleção do PA-âncora (por filial) — `PROVEN`

`SB1` na faixa produto/grupo/tipo (par03..08) **e** ∃ `SD2010` da filial
com `D2_EMISSAO` ∈ [par01,par02] cujo TES (`SF4010` via
`D2_TES=F4_CODIGO`) tem **`F4_DUPLIC='S'`** — WHERE literal do fonte. A
fonte **não** filtra `D2_TIPO` — as 7 NFs tipo `D` de set/2026 com TES
duplic-S são de MPs fora do escopo PA (ramo não exercido pelo artefato —
`UNEXERCISED`). População âncora+descendentes: 1.767 (filial,PA).

### BR-R09-004 — Motor da expansão PA→MOD — `SOURCE_MISSING` (SP) / contrato `PROVEN`

Cada linha MOD sai de `EXEC STP_DELPI_FORMA_PRECO_<empresa> (produto,
filial, roteiro(par09), dataDe, dataAte, nivel, pa_ancora)` — a SP
retorna `PA, COMP, B1_COD, B1_DESC, QTDFAT, B1_UM, G2_TEMPAD, CUSTO_UNIT,
CUSTO_TOTAL, CUSTOPROD, HORAS`. A procedure **não existe em nenhum banco
acessível** (produção/testes) — objeto legado de 2019; internos
inferidos por artefato (`PRODUCER_INFERRED_BY_ARTIFACT` para a semântica
interna) → E9. O `Estrut()` ADVPL faz a recursão SG1 por nível (chamadas
SP com nível `0`,`1`,`2`).

### BR-R09-005 — `Seq Comp` = nível da expansão — `PROVEN`

`COMP` retornado pela SP: `02` = PA faturado (nível 0), `04` = componente
direto (nível 1), `06` = subcomponente (nível 2) — conferido por
distância estrutural SG1 (0/1/2). Com par11=Sim a rotina emitiria linhas
`03/05/07` (produtos componentes com `qty×BZ_CUSTD`) — **ausentes no
artefato** → par11=Não.

### BR-R09-006 — `Qtd Fat.` = faturamento do PA-âncora propagado — `PROVEN`

`QTDFAT` (SP) = Σ `D2_QUANT` do PA-âncora no período (TES duplic-S);
quando a SP retorna `QTDFAT=0` o ADVPL propaga a quantidade do chamador
(`aModPar[4]`) — explica a propagação pai→componente (seriais
compartilham o `Qtd Fat.` do PA faturado). **4.476/4.476 linhas
explicadas** (TES `F4_DUPLIC='S'` + `D2_TIPO<>'D'`; ramo tipo-D não
exercido — ver BR-R09-003).

### BR-R09-007 — Vínculo PA→MOD via roteiro da OP — `PROVEN` (99,4%)

O MOD de cada linha vem do **recurso da operação do roteiro congelado da
OP** — `SHY010` (`HY_OP` = `C2_NUM+C2_ITEM+C2_SEQUEN`; OPs de
desdobramento carregam item-pai + seriais como sequências da mesma OP) —
ou, em fallback, do roteiro cadastral `SG2010`. Ponte recurso→MOD:
`SH1010.H1_CCUSTO` (código do centro de custo espelha o sufixo `MOD*` —
mesma ponte já documentada no doc 80 §22 e usada pela
`vw_Apontamentos_Eficiencia`; `SHB010.HB_CC` concordante exceto `CT-01C`
f02, onde a regra correta é SH1 → `MOD345`). Cobertura linha a linha:
**4.311 via `HY_TEMPAD` + 138 via `G2_TEMPAD` = 4.449/4.476 (99,4%)**;
27 residuais (tempos zerados e roteiros de OP não localizados —
`PENDING` E9).

### BR-R09-008 — `Quantidade` = tempo padrão da operação (`HY_TEMPAD`/`G2_TEMPAD`) — `PROVEN` (99,4%)

A coluna `G2_TEMPAD` no contrato da SP carrega o **tempo padrão vigente
no roteiro da OP** (`SHY010.HY_TEMPAD`) — não o cadastro corrente
(prova: seriais com OP-roteiro CT-01A exibem `MOD20101` e tempos
distintos do SG2 cadastro CT-23A). Fator `÷2`/÷`C2_QUANT` observado em
itens de desdobramento (par de seriais — semântica do divisor `PENDING`,
E9). As divergências antes lidas como "revisão de roteiro" eram
`HY_TEMPAD` histórico ≠ `G2_TEMPAD` corrente (`STALE_EVIDENCE` do lado
do cadastro — a fonte correta é a OP).

### BR-R09-009 — Fórmulas das colunas — `PROVEN`

`Horas = Qtd Fat. × Quantidade`; `Custo Total = Horas × Custo Unitario` —
identidades verificadas nas 4.476 linhas (precisão ~4 dec). `Custo
Produto` = `CUSTOPROD` da SP = **0 em todas as linhas** (semântica não
exercida — provável opção de custo calculado desligada; `PENDING` baixo
impacto).

### BR-R09-010 — `Custo Unitario` = `SBZ010.BZ_CUSTD` (filial,MOD) vigente na emissão — `PROVEN`

Reconstrução `as_of` via `SBZ010_TTAT_LOG` (regra: último valor ≤ corte;
na ausência, `COLD` da primeira alteração posterior): **4.469/4.469**
linhas com MOD portador de rate conferem com cutoff ~06-07/10/2026 —
anterior às revalorizações `MATA019` de 07-08/10 (doc 80 §23). **7
linhas** cujo MOD não tem registro SBZ na filial (rate blank/zero — não
é "falta": é ausência de cadastro; falta ≠ zero — E6). Totais derivados:
f01 ΣCustoTotal=164.985,66 · f02 ΣCustoTotal=579.268,58 · f01
ΣHoras=2.472,5805 · f02 ΣHoras=7.089,3959.

### BR-R09-011 — `UM` e metadados MOD — `PROVEN`

`UM` = `B1_UM` do produto MOD (`HR` 4.025 linhas, `H` 421, `PC` 30 — MODs
de máquina em peças). `Cod Produto` = `B1_COD` (`B1_TIPO='MO'`);
`Desc Produto` = `B1_DESC`.

### BR-R09-012 — Reuso transversal — `REUSE_PARTIAL`

- **Predicado de venda** `F4_DUPLIC='S'`: idêntico à regra canônica de
  faturamento — `REUSE_CONFIRMED` de predicado (implementação do filtro
  literal no fonte; ver doc 85 §15).
- **`vw_Apontamentos_Eficiencia`**: mesmo domínio (CT→MOD, rate MOD) mas
  semântica divergente — a view usa horas **reais/previstas por
  apontamento** e aplica `BZ_CUSTD` **corrente retroativamente** (doc 80
  §23.E); o relatório usa **tempo padrão do roteiro da OP × quantidade
  faturada × rate `as_of` emissão** → `REUSE_PARTIAL`, **não
  transplantar fórmula**.
- Nenhum serviço Minha DELPI reproduz a cadeia
  SD2→estrutura→roteiro-OP→rate-as_of → `TARGET` futuro (§15).

### BR-R09-013 — E6 (decisão) — `PRODUCT_DIRECTION_ONLY`

Histórico homologado + recalculado corrente, opção **C** (doc 81/82) —
`IMPLEMENTATION_AUTHORIZED=NO`. O comportamento do artefato (rate
`as_of`) é compatível com a leitura histórica homologada; a divergência
de semântica com a view (BR-R09-012) permanece registrada — falta ≠ zero
(7 linhas sem SBZ; 224 linhas f02 com rate zero cadastrado).

---

## §10 — R10/R11 · Consultas EDAPP (SD1/SD2)

> **Gate contratual:** inventário, reuso, contratos TARGET e decisões E10/E11
> consolidados em [doc 126](126-gate-contratual-r10-r11-comparacao-clara-2026-10-30.md)
> (`CF-PROC0072-R10-R11-CLARA-COMPARISON-CONTRACT-GATE-019`). **Gate-020**
> (30/10): decisões PO formalizadas + catálogo de divergências
> DV-R10-01..06 / DV-R11-01..04 + contratos revisados no [doc 126 §14–§19](126-gate-contratual-r10-r11-comparacao-clara-2026-10-30.md).

### R10 · `CC matriz.xlsb` — seleção reconstruída e corroborada pelo owner (rodada 25)

Artefato: aba `SCAGQGA0.XML`, linha 0 literal `SD1`, headers = títulos
SX3 `D1_*`, **353 linhas**, filial 01, 139 documentos, 46 centros de
custo, Σ `Vlr.Total` = **169.704,12**. Grão = item SD1 (linha física).

#### BR-R10-001 — Binding SD1 — `PROVEN`

Export EDAPP monotabela: headers são títulos SX3 de `D1_*`; chave de
vínculo `(D1_DOC, D1_ITEM, D1_COD, D1_TOTAL)` une 353/353 linhas ao
SD1 físico sem ambiguidade (doc 47 §11.1). `Vlr.Unitario`=`D1_VUNIT`,
`Quantidade`=`D1_QUANT`, `Tipo Produto`=`D1_TP` (tipo gravado na linha —
pode divergir de `B1_TIPO` corrente), `Tipo Entrada`=`D1_TES`,
`Cod. Fiscal`=`D1_CF`, `C Custo`=`D1_CC`, `DT Digitacao`=`D1_DTDIGIT`,
`No do Pedido`=`D1_PEDIDO`, `Armazem`=`D1_LOCAL`.

#### BR-R10-002 — Competência = data de digitação — `PROVEN`

Eixo `D1_DTDIGIT` ∈ [2026-09-01, 2026-09-30] (universo 686 linhas f01):
80 linhas incluídas têm `D1_EMISSAO` fora de setembro (mín 08-03) —
eixo digitação, não emissão. `OWNER_REPORTED_VIA_PO` (doc 56 Reg.17:
"filtro de data de digitação no mês") + prova física.

#### BR-R10-003 — Exclusão por tipo de entrada — `PROVEN` (lista exata `PENDING`)

Procedimento relatado: excluir "12 tipos de entrada" — lista narrada
`{01,02,03,04,030,040,083,080,085,120,204,318}` (doc 56 §Reg.17 —
transcrição 2/3 dígitos). Conjunto **fisicamente excluído** (13 TES,
zero falso-positivo/negativo): `001,003,016,020,030,040,080,083,085,
120,159,204,318` = COMPRAS MP (001/003), CONTA ORDEM (016), ENERGIA
(020), COMUNICAÇÃO (030), TRANSP. (040), ENTRADA IND/VASILHAME
(080/083/085), DEVOL. VENDAS (120), REMESSA INDUSTR. (159), TRANSF. MP
(204), IMPORT. (318). `016`/`159` observados além da lista narrada —
ambos `F4_DUPLIC='N'` (coerente com análise de despesas); mapeamento
exato da transcrição → E10.

#### BR-R10-004 — Exclusão de matéria-prima — `PROVEN`

"D1_TP='MP' fora" (owner: "ordena por produto e exclui MP — não compõe
esta análise específica"): **302/302** linhas MP excluídas (sem
exceção); não revoga uso de MP em outros relatórios (P7/CPV).

#### BR-R10-005 — Coparticipação plano de saúde fora — `PROVEN`

Regra relatada: parcela do plano de saúde que é despesa do colaborador
fica fora da apuração (não exige CC). Única classe não coberta pelas
regras anteriores: **6 linhas** TES 046, tipo GG, **sem CC**, produtos
do grupo de benefícios saúde/odonto (`<PRODUTO-BENEFICIO-*>`) — R$
6.990,44 excluídos. Nota do owner: não extrapolar para "toda
coparticipação" — discriminar parcela colaborador × empresa (regra
contábil → E10).

#### BR-R10-006 — Classificação Direto/Indireto/Adm — `AS-IS` (manual, pós-exportação)

Coluna **sem título** entre `C Custo` e `C Contabil` com valores
`Direto`(122+2 minúsc.), `Indireto`(128), `Adm`(101): **não é campo
SD1 nem CTT** (CTT sem campo de classe análogo) — classificação manual
da operadora sobre a exportação, guiada pelo CC: `Direto` = CCs de
máquina/produção (275, 223, 393, CT-## — mesmos CCs dos MOD###) +
insumos sem CC marcados manualmente; `Indireto` = CCs de apoio
(0301–0504); `Adm` = CCs administrativos (01xx–02xx, 0501). Subtotais
derivados: Adm 99.297,81 · Indireto 38.554,82 · Direto 31.851,49.
Regra de classificação **não automatizada** — `TARGET` exige fonte de
classe homologada (não inferir de prefixo de CC sem owner).

#### BR-R10-007 — Reuso transversal — `REUSE_PARTIAL` (seleção não equivalente)

`GET /financeiro/despesas-centro-custo/*` (api-delpi, plugin
`financeiro-centro-custo`) + `vw_fin_despesas_centro_custo`: **mesmo
domínio** (SD1 por CC) mas seleção diferente — view usa
`data_emissao`=`D1_EMISSAO`, exige `D1_CC<>''`, **não** exclui MP nem
os 13 TES (448 linhas set/26 f01 = escopo próprio; 269/353 do artefato
cobertos; as 84 faltantes = 80 eixo-digitação + 4 sem-CC). A regra do
artefato (digitação + TES-exclusão + MP-out + benefícios-out) é a
seleção do procedimento Controladoria — `TARGET` se homologada como
consulta distinta; **não transplantar a seleção da view**.

#### IMPLEMENTAÇÃO (stage-01, 2026-10-31) — `PROVEN` operacional

Execução `CF-PROC0072-R10-IMPLEMENTATION-STAGE-01` materializou
BR-R10-001..005 como engine novo na api-delpi
(`GET /financeiro/cost-center-expenses`, módulo
`financeiro_cost_center_expenses`): universo SD1 f01 por
`D1_DTDIGIT` ∈ competência, classificado por linha em
`calculation` (−13 TES BR-R10-003, −MP BR-R10-004, −6 benefícios
BR-R10-005) ou `investigation` (demais linhas em competência). Paridade
live 2026-09 f01: **353 linhas / R$ 169.704,12 / 139 docs / 46 buckets
de CC** (45 nomeados + grupo sem-CC — forma de contagem do artefato).
CTT resolvido via `TOP 1 OUTER APPLY` (filial específica, fallback
filial-branca) — snapshot **vigente**, não comprova validade histórica.
BR-R10-006 permanece manual/`UNCLASSIFIED` por D-01 (E10a pendente);
findings DV-R10-01/02/04 implementados, DV-R10-03/06 declarados e
bloqueados por E10a (`rulesCatalog.implemented=false`). View legada
`vw_fin_despesas_centro_custo` não foi reutilizada (BR-R10-007
`REUSE_PARTIAL` confirmado).

### R11 · `NF a desconsiderar.xlsb` — seleção reconstruída (rodada 26)

Artefato: aba `Planilha2`, linha 0 literal `SD2`, headers = títulos SX3
`D2_*` (184 colunas exportadas; sem `Emissao`/`Cliente`/`Serie`/
`Custo`), **11 linhas**, filial 01, **11 documentos distintos**,
Σ `Vlr.Total` = **R$ 97.462,71**. Grão = item SD2. Errata doc 47
§11.1: `Tipo Saida` exportado = `D2_TES` (`D2_TIPO`='N' nas linhas).

#### BR-R11-001 — Binding SD2 — `PROVEN`

Chave `(D2_DOC, D2_ITEM, D2_COD, D2_TOTAL)` une 11/11 linhas ao SD2
físico sem ambiguidade. `Num. Docto.`=`D2_DOC`, `Quantidade`=
`D2_QUANT`, `Vlr.Unitario`=`D2_PRCVEN`, `Vlr.Total`=`D2_TOTAL`,
`Tipo Saida`=`D2_TES`, `Cod. Fiscal`=`D2_CF`, `Grupo`=`D2_GRUPO`,
`C Contabil`=`D2_CONTA`, `Loja`=`D2_LOJA`, `MD5`/`Campo UUID` = campos
de auditoria Protheus.

#### BR-R11-002 — Seleção = grupo 9035 ∩ TES 594, competência set/2026 — `PROVEN`

População física `D2_FILIAL='01'` + `D2_EMISSAO`∈[20260901..20260930] +
`D2_GRUPO='9035'` = **11 linhas** — conjunto **idêntico** ao artefato
(identidade, não cardinalidade). `D2_TES='594'` produz o mesmo conjunto
em set/2026 (equivalência bidirecional nesta competência: todo 594 é
9035 e vice-versa); all-time 9035 aparece com outros TES (511/505/610…)
— o predicado **não** é "grupo 9035 sempre" nem "TES 594 sempre"; é a
interseção observada na competência. Qual dos dois o operador filtrou
(grupo vs TES) é indistinguível pelo artefato → E11.

#### BR-R11-003 — CPV zero = propriedade estrutural do TES 594 — `PROVEN`

As 11 linhas têm `D2_CUSTO1 = 0` **desde a criação** (TTAT
`SD2010_TTAT_LOG`: insert MATA460A na data da emissão, `COLD`=`CNEW`=
0.000, zero alterações posteriores). Causa: `SF4.F4_ESTOQUE='N'` — TES
que não movimenta estoque não gera custo de saída. `F4_DUPLIC='S'`
(gera duplicata/receita). Portanto: "CPV zero" **não** é custo faltante
nem erro de cálculo — é venda sem baixa de estoque (faturamento de
serviço/insumo de industrialização).

#### BR-R11-004 — Semântica do conjunto: industrialização para terceiros — `PROVEN`

Produtos 9035 = itens de serviço/insumo de industrialização
(descrições "INDUSTR./RESINAGEM/INSUMOS UTILIZADOS", `B1_TIPO`='PA' na
linha `D2_TP`). NFs típicas têm 2 itens: item 01 = produto físico
`9026*` com TES **510** "INDUSTRIALIZACAO EFET. P/ OUTRA EMPRESA"
(`F4_ESTOQUE='S'`, `D2_CUSTO1`>0, CFOP 5124) + item 02 = faturamento
da industrialização com TES 594 (`F4_ESTOQUE='N'`, custo 0, CFOP 5101).
3 NFs têm só o item 594. Clientes = terceiros (não intercompany) —
industrialização efetuada para outra empresa. 8 das 11 notas casam
item-custo(510)+item-faturamento(594) no mesmo documento.

#### BR-R11-005 — Efeito no CPV canônico — `PROVEN` (impacto nulo no numerador)

`GET /supplies/cpv` (`CpvQueryRepository`) = `SUM(D2_CUSTO1)` em
`D2_CF∈{5101,5124,6101,6124}`: as 11 linhas (CFOP 5101) **contribuem
R$ 0,00** ao CPV — a inclusão no conjunto não altera o custo; sua
receita (97.462,71) integra faturamento/ROL. O arquivo é lista de
conferência da Controladoria (receita sem custo associado), não regra
do contrato CPV — **nenhuma alteração contratual necessária**; os
itens-irmão (510/5124) entram normalmente no kardex (`F4_ESTOQUE='S'`)
e no CPV. Qual apuração efetivamente desconsidera estas NFs (numerador
CPV, denominador ROL, conferência DRE) = `OWNER_REPORTED` → E11.

#### BR-R11-006 — Reuso — `REUSE_PARTIAL`

`GET /supplies/cpv` = `REUSE_PARTIAL`: semântica verificada (custo por
CFOP de venda) e **coerente** com o artefato (contribuição zero — sem
contradição); o "desconsiderar" é camada de conferência manual, não
predicado da API. Regra kardex `F4_ESTOQUE='S'` (R06) =
`REUSE_CONFIRMED` por predicado: explica a ausência destas linhas no
MATR910. Nenhum consumidor implementa "lista de exceções de
faturamento" — `TARGET` se homologada (doc 56 §Reg.18: estados
`excluded_from_analysis` etc. são `TARGET_DECISION_REQUIRED`).

#### IMPLEMENTAÇÃO (stage-02, 2026-10-31) — `PROVEN` operacional

Execução `CF-PROC0072-R11-IMPLEMENTATION-STAGE-02` materializou
BR-R11-001..006 como engine novo na api-delpi
(`GET /financeiro/billing-exclusion-roster`, módulo
`financeiro_billing_exclusion_roster`): população SD2 f01 por
`D2_EMISSAO` ∈ competência relacionada ao critério (grupo 9035 ∪
TES 594), classificada por linha em `matches_historical_criteria`
(interseção observada) ou `related_out_of_criteria`, exposta pelas
visões `candidates`/`out_of_criteria`/`all` com totalizadores separados
e nunca somados. Paridade live 2026-09 f01 via o próprio engine:
**11 linhas / R$ 97.462,71 / 11 docs / 3 docs sem item-irmão de
estoque** (103033, 103199, 103202 — identidade exata do artefato).
SF4 resolvido via `TOP 1 OUTER APPLY` (filial específica, fallback
filial-branca); SB1/SA1 por LEFT JOIN sem multiplicação; item-irmão por
correlação `D2_FILIAL+D2_DOC+D2_SERIE`. DV-R11-03 implementado como
`POSSIBLE_DIVERGENCE`; DV-R11-01 exposta como bloco `selection`;
DV-R11-02 como `costStatus=structural_zero_expected` (condição
esperada, nunca divergência); DV-R11-04 como visão separada. E11a/E11b
permanecem `TO_INVENTORY`/`PENDING_EVIDENCE`: `affectedCalculation`
honesto, nenhuma exclusão automática de CPV/faturamento/DRE, predicado
não publicado como regra oficial universal. CPV canônico não foi
alterado (BR-R11-005 `REUSE_PARTIAL` confirmado — contribuição zero no
numerador).

## §11 — R12 · Fechamento de custo / Reposição / Refaz Saldos — `AS-IS`→`PROVEN` (bindings)

### BR-R12-001 — Recálculo do Custo de Reposição = **MATA320** — `PROVEN` (rotina + efeito)

- **Binding físico:** grupo SX1 `MTA320` reproduz 1:1 os 16 parâmetros da
  tela (`Utilizar Qual Moeda?`, `Utilizar Taxa?`, `Calcular os Custos
  Por?`, `Considerar Ult. Preco Compra?`, `Dt.Final Ref.Taxa ?`,
  `Do/Ate o Tipo do Produto`, `Do/Ate o Grupo`, `Considerar Qtdes.
  Negativa?`, `Avisar Divergencia?`, `Seleciona filiais?`, `Considera
  Mão de Obra?`, `Considera Tipo Dec. OP?`, `Tempo Setup?`, `Cod do
  Roteiro de Operacoes?`).
- **Campo efetivo:** a própria tela declara que o cálculo grava
  `SB1.B1_CUSTD` (custo de reposição). `B1_CUSTD` já é lido pela
  api-delpi como `standard_cost` (product repositories) —
  `REUSE_CONFIRMED` (leitura).
- **Execução provada (TTAT):** `SB1010_TTAT_LOG` registra `MATA320`
  atualizando `B1_CUSTD` em rajada — usuário JOICI: **13.201 writes
  30/09 14:36–14:56** (1ª execução, produtos até MP) + **1.532 writes
  15:09–15:14** (2ª execução, PA/PI); reexecuções 01/10 16:03–17:48
  (+15.972) — `EXECUTION_OBSERVED` confirmado em dados, não só em tela.
- **Duas execuções observadas (doc 56 Reg.02 + TTAT):** 1ª ~03:11 —
  `Do Tipo`=MC, `Ate`=MP, `Calcular os Custos Por?`=**Ult Custo
  Compra**; 2ª ~03:54 — `Do Tipo`=PA, `Ate`=PI, `Calcular os Custos
  Por?`=**Estrutura**. Comuns: Moeda=Nenhuma · Taxa=Diária ·
  Ult. Preco Compra=Sim · Dt.Final Ref.Taxa=30/09/2026 · Mão de
  Obra=Ambos · `Tempo Setup?`=**Som Tempo Propo** (frame 03:20 —
  errata: doc 56 dizia "Sem Tempo Proprio").

### BR-R12-002 — Wizard "Acompanha Custos → Novo fechamento de custo" — `AS-IS` (sequência `EXECUTION_OBSERVED`)

- Tela `Fechamentos` (02:08) = **histórico de execuções** com
  status/filial/início e botão `Reabertura de estoque` — o fechamento é
  objeto persistido com ciclo de vida, não cálculo efêmero.
- Etapas 1–4: `Predefinição de cálculo` (02:40 — último fechamento
  31/08/2026, data 30/09/2026, método `Diária`, `Filial corrente`) →
  `Cálculo de custo` (14:47 — 100%, níveis validados, arquivo de
  trabalho, transferências entre filiais, movimentações; controles
  `Cancelar fechamento`/`Refazer cálculo`/`Próximo passo`; texto
  menciona EventViewer) → `Análise e revisão` (16:40/36:10 — grade
  "1991 produtos", status por moeda, CM inicial/final, Variação%,
  botão Exportar) → `Fechamento` (**não exibida** — a etapa final não
  aparece concluída no vídeo).
- Execução real 30/09 ~14:4x (JOICI, Matriz) = `EXECUTION_OBSERVED`
  das etapas 1–3; a etapa 4 e o aceite funcional ficam `PENDING`
  (G5/G6).

### BR-R12-003 — "Refaz Saldos" do vídeo = **MATA300** — `PROVEN` (binding; DEL100 é rotina distinta)

- **Errata:** a documentação anterior associava o Refaz Saldos ao
  DEL100. O grupo de perguntas da tela (frame 04:36) é `MTA300` — o
  "Refaz Saldos" do vídeo é o **MATA300** (Recálculo dos Saldos),
  rotina padrão.
- Parâmetros `MTA300` observados: `Do Armazem?` vazio · `Ate o
  Armazem?`=ZZ · `Do/Ate o Produto?` (faixa ampla) · `Zera o saldo de
  produtos MOD?`=**Recalcular** · `Zera o CM de produtos MOD?`=
  **Recalcular** (+ `Travar Registros SB2?`, `Seleciona Filiais?` no
  grupo SX1).
- Execução: janela `Recálculo dos Saldos` com `Log de processamento
  das STORED PROCEDURES` — threads `c300P0101xx - Ok` (06:46).
  Identidade dos workers `c300P*` e efeito direto em SB2:
  `PENDING_EVIDENCE` (campos `B2_*` não auditados em TTAT — sem rastro
  físico consultável).
- `DEL100.PRW` (custom, acervo) = rotina **separada** de
  auditoria/correção SB9: reconstrói posição a partir de SB9-abertura
  + SD3 + SD1/SD2 (`F4_ESTOQUE='S'`), modo log-only ou `RecLock` em
  `B9_VINI1`/`B9_QINI`; query vigente sanitizada **3.058/421/242**
  (doc 80 §24.E). `STALE_EVIDENCE`: contagens antigas 724/672
  superadas — `EXECUTION_DRIFT` (doc 80 §23.A).

### BR-R12-004 — Persistência do fechamento (SB9 + `MV_ULMES`) — `PROVEN` no dado, writer `PENDING`

- `SB9010` set/2026 existe para **as duas filiais** em rajada única
  por filial: f02 02/10 17:58:01–03 (3.117 linhas) e f01 21/10
  19:13:40–42 (4.812 linhas); `MV_ULMES` = `20260930` em f01 e f02 —
  marcador de último fechamento avançado.
- O writer efetivo (etapa 4 do wizard × MATA300 × rotina separada)
  **não é byte-provado** — divergência temporal preservada (E5);
  SB2/SB9 sem auditoria TTAT dos campos de saldo/custo.

### BR-R12-005 — `Analise.xlsx` = export da etapa "Análise e revisão" — `PROVEN` (binding + reconciliação)

- Estrutura 1:1 com a grade exibida (Status moedas, Filial, Produto,
  Tipo, Grupo, Armazém, CM inicial/final + Variação% por moeda
  R$/US$/UFIR/MARCO/IENE); "1991 produtos" na tela vs 1.994 linhas de
  dados no export (Δ de contagem registrado — possível recorte/
  distinct, `PENDING` menor).
- Reconciliação contra SB9: **CM final ≡ `B9_CM1`@30/09 em
  1.966/1.994 (98,6%)**; 22 linhas sem SB9 = pseudo-produtos `MOD*`
  com custo 0 (estrutural — sem snapshot de saldo); 6 deltas = drift
  temporal entre o cálculo exibido (30/09) e a gravação f01 (21/10).
  CM inicial ≡ `B9_CM1`@31/08 em 1.689 linhas (283 chaves sem
  snapshot de agosto).
- Status×Variação consistente em **1.994/1.994** (Positivo/Negativo/
  Neutro = sinal da variação). Artefato ligado à etapa 3 do wizard —
  evidência do **resultado produzido**, não do fechamento persistido.

### BR-R12-006 — Integração pós-fechamento `MA330OK` — `SOURCE_AVAILABLE`, execução `PENDING`

- `MA330OK.PRW` (acervo) = ponto de entrada pós-MATA330: chama
  `STP_DELPI_OP_TERCEIRO_<emp>` (`@DATADE`) e
  `STP_PROTHEUS_DELPI_AJUSTA_OP` f01+f02 (`@ANOMES`), com gravação em
  EventViewer — coerente com a menção a EventViewer na tela do wizard.
- SPs `STP_DELPI_*`/`STP_PROTHEUS_*` **ausentes** nas bases
  acessíveis; `sysjobs` inacessível à permissão — implantação/
  execução: `PENDING` (E4).

## §12 — R13 · Extratos e aplicações — `BLOQUEADO` (fonte externa)

- Checklist `Arquivos de envio` confirma entregáveis externos (Extratos, XP,
  BB, Aplicações): **fonte fora do Protheus** — regra de coleta = contrato de
  entrada externo, não SQL. `G1 PASS`, demais `PENDING`.

---

## §13 — R14 · Importação / câmbio — `BLOQUEADO`

- Sem evidência na pasta; nenhuma regra registrável além de `TO_INVENTORY`.

---

## §14 — R15 · Cutoff / sacramentação / SB9 — `AS-IS`→`PROVEN` (bindings)

> Rodada 28 (doc 80 §47): cadeia produtora do fechamento reconstruída por
> TTAT + SX1 + timestamps físicos. Descoberta-chave: `I_N_S_D_T_` grava
> **UTC** (prova: SD3 recno × TTAT_DTIME local = exatamente −3h). Todas as
> rajadas SB9 caem **dentro** das janelas de execução do `MATA280`.

### BR-R15-001 — Cutoff: fechamento só em data > último fechamento — `PROVEN`

- Wizard etapa 1 (frame 02:35): campo "Data para fechamento de custo" com a
  regra literal "O processo de fechamento de custo só pode ser realizado em
  datas posteriores ao último fechamento." Último fechamento exibido:
  31/08/2026; data escolhida: 30/09/2026; método `Diária`; `Filial corrente`.
- `MV_ULMES` é **por filial** (SX6: f01=20260930, f02=20260930; global default
  `29/02/2024` defasado) — marcador por filial, não por empresa.
- Leitores de `MV_ULMES` no acervo: MATR860, DLP023, DLP04F04, MATA103
  (`dDTULMES := SuperGetMV("MV_ULMES")` para validação de OP encerrada/
  integração SIGAMNT) — evidência de consumo do marcador como cutoff; o
  bloqueio de movimento retroativo em si é comportamento padrão TOTVS
  (não auditável via TTAT — SX6 sem log).

### BR-R15-002 — Cadeia produtora: MATA330 → MATA280 → SB9 — `PROVEN` (execução+binding; atribuição interna da escrita por timing)

- **`MATA330`** (Recálculo do Custo Médio, SX1 `MTA330` 21 perguntas):
  executor **JOICI** (host 192.168.1.23) + componente de serviço
  (192.168.1.231); escreve SD3/SC2/SD2 massivamente. Execuções: 30/09
  14:34–18:00 (demo), 01/10, 02/10 14:35–14:46, 21/10 07:52–16:12.
- **`MATA280`** (Virada de Saldos — SX1 `MTA280`: "Gravar Dados Em
  Arquivos?", "**Gera Saldo Inicial** para MOD?", "Seleciona Filial?",
  "Atualiza Saldo Atual MOD?"): executa como serviço (TTAT_USER em branco)
  imediatamente após/ao fim do MATA330; escreve campos de **saldo inicial de
  OP** em SC2 (`C2_VINI1`, `C2_VINIRP1`, `C2_APRINI1/2/3` — tipo N).
- **Rajadas SB9 × janelas MATA280 (horário local = `I_N_S_D_T_`−3h):**

  | data | MATA280 (SC2 TTAT) | rajada SB9 (local) | competência/filial |
  |---|---|---|---|
  | 10/08 | 15:45–17:11 | 15:45–17:11 | jul — f01+f02 (28.839) |
  | 18/09 | 14:42–16:03 | 14:42–16:03 | ago — f01 (13.936) |
  | 01/10 | 16:29–17:45 | 17:44:46–48 | ago — f02 (3.093) |
  | 02/10 | 14:58:05–12 | 14:58:01–03 | **set — f02 (3.117)** |
  | 21/10 | 16:13:44–50 | 16:13:40–42 | **set — f01 (4.812)** |

- 5/5 rajadas dentro da janela MATA280; nenhum outro programa com atividade
  TTAT nos segundos das rajadas; MATA330 já havia encerrado em 02/10 e 21/10
  (SB9 cai 2–4s antes do início do burst MATA280-SC2, dentro da mesma execução).
- **Resíduo honesto:** SB9/SB2 não são auditados em TTAT (logs vazios
  all-time; trigger `SB9010_STAMP` existe e está habilitada mas não popula o
  log) — a atribuição "MATA280 escreve SB9" é binding temporal±4s + semântica
  SX1 ("Gera Saldo Inicial"), não prova de insert auditado. Fonte MATA280 não
  está no acervo (RPO padrão TOTVS) → E5 permanece aberto, agora **estreitado**
  para confirmação de RPO/função interna.

### BR-R15-003 — SB9 = snapshot mensal íntegro — `PROVEN`

- Cadeia mensal completa ago/2025→set/2026, ambas as filiais (30/09: f01
  4.812 linhas únicas `B9_COD+B9_LOCAL`, f02 3.117); cardinalidade 1:1 sem
  duplicados.
- `stock_value_official_closure_sql` lê `SB9010` por `B9_DATA` —
  `REUSE_CONFIRMED` na api-delpi.
- Anomalia: 2 linhas SB9 com `B9_DATA` em branco inseridas 30/09 ~16:50 local
  (durante a demo) — placeholders estruturais, não snapshots de competência.

### BR-R15-004 — `MV_ULMES` avança na virada — `PROVEN` no dado, writer `PENDING`

- Valor 20260930 f01+f02; avanço ocorreu na virada de cada filial (f02 ~02/10,
  f01 ~21/10 — posterior à demo de 30/09). Writer específico não auditável
  (SX6 sem TTAT) — candidato MATA280/etapa-4 do wizard → E5/E12.

### BR-R15-005 — Wizard persiste ciclo de vida — `EXECUTION_OBSERVED`

- Lista `Fechamentos` (frame 02:05): execuções com `Iniciado em`,
  `Iniciada na` (filial), `Status`, `Concluído em`/`Cancelado em`/`Progresso
  atual`. Evidência: f01-ago "Concluído 18/09 16:05" = 1min após fim do
  MATA280 (16:03:52) → status do wizard reflete o término da virada.
- Execuções **canceladas** não produzem SB9 (f01-ago cancelada 18/09 14:30,
  refeita 15:52); f02-ago ficou em "Análise e revisão 50%" desde 03/09 —
  virada f02-ago só ocorreu 01/10 (explica o lag entre filiais).
- Botões de ciclo de vida: `Novo fechamento`, `Configurar parâmetros`,
  `Reabertura de estoque`; etapa-2 exibe `Cancelar fechamento`,
  `Refazer cálculo`, `Próximo passo` + texto sobre EventViewer.

### BR-R15-006 — Reabertura de estoque existe; semântica `PENDING` — `AS-IS`

- Botão visível na lista; nenhum fluxo de reabertura demonstrado no vídeo.
- Efeitos de reabertura (reverter `MV_ULMES`? apagar SB9? reprocessar?)
  não comprovados → E12 (Controladoria+TI/ERP).
- Doc 56 (Complemento Reg.12): owner reporta que divergência de período
  anterior pode exigir reabertura+recálculo; `HISTORICAL_REOPEN=
  OWNER_REPORTED_VIA_PO`; não automatizar no Portal.

### BR-R15-007 — Correções retroativas precedem a virada — `PROVEN` (padrão temporal)

- f01-set: demo 30/09 executou cálculo (MATA330 14:34–18:00) mas **sem
  virada** (sem MATA280/SB9 naquele dia); reprocessamento MATA330 ocorreu
  21/10 07:52–16:12 e a virada f01-set gravou 16:13 — compatível com a onda
  retificadora ~20-21/10 (doc 80 §§anteriores). Interpretação: correções na
  competência original são absorvidas **antes** da virada que persiste o
  snapshot — consistente com "CPV vivo" (doc 80 §40).

### T-R15 — Matriz de testes

| Teste | Regra | Tipo | Resultado observado |
|---|---|---|---|
| T-R15-01 | BR-R15-002 | negative · preservado | timestamp de persistência ≠ execução demonstrada — refinado: `I_N_S_D_T_` é UTC (−3h local), provado por SD3 recno×TTAT |
| T-R15-02 | BR-R15-002 | positive | rajadas SB9 dentro da janela MATA280 em 5/5 execuções registradas (10/08, 18/09, 01/10, 02/10, 21/10) |
| T-R15-03 | BR-R15-002 | positive | `I_N_S_D_T_` (SD3) = TTAT_DTIME +3h exatos — stamp UTC |
| T-R15-04 | BR-R15-004 | negative | `SX6010` sem TTAT — writer de `MV_ULMES` não auditável por log |
| T-R15-05 | BR-R15-003 | positive | SB9@30/09: 4.812 (f01) + 3.117 (f02) linhas, `B9_COD+B9_LOCAL` únicos |
| T-R15-06 | BR-R15-005 | positive | "Concluído 18/09 16:05" do wizard ≈ fim MATA280 16:03:52 (Δ~1min) |
| T-R15-07 | BR-R15-002 | negative | `SB9010_TTAT_LOG`/`SB2010_TTAT_LOG` vazios all-time — escrita SB9 não auditável por TTAT |


## §15 — Matriz de handoff técnico (regra → implementação futura)

> `contrato candidato` = rótulo de superfície futura (`TARGET`/`PLANNED`);
> **nada foi criado**. Os rótulos **não são nomes de endpoints aprovados** —
> nome, path e payload definitivos dependem de design de contrato + gate
> transversal. Nenhuma regra muda de bounded context sem esse design.

| Regra | Fonte canônica | Campos | Transformação | Contrato candidato | Owner | Testes | Evidência |
|---|---|---|---|---|---|---|---|
| BR-R01-001/002 população+estorno | `FINR190_DLP.PRX`@`92bcae1c` + SE5 | `E5_*` | WHERE fiel + anti-par por chave 12 campos | `payables-settlements` (api-delpi TOTVS provider) | api-delpi | T-R01-01/02/03 | doc 84 §1 |
| BR-R01-003/004 TB/VO | fonte + SE5/SE2 | `E5_VALOR`,`E2_VALOR` | VO condicional (E2→E5→grupo) | idem | api-delpi | T-R01-04/05 | doc 84 §1.2 |
| BR-R01-005 joins | fonte | chaves título/natureza/IDORIG | MsSeek equivalente | idem | api-delpi | T-R01-06 | doc 80 §17 |
| BR-R01-006/007 resumos/componentes | artefato+fonte | componentes `E5_VL*` | agregação por motivo/tipodoc | BFF agrega | cf-api | T-R01-07 | doc 84 §1.3 |
| BR-R01-009 log inconsistências | PDF impresso | — | total = ΣXLSB−ΣPDF | flag "reconciled_excl_log" | cf-api | T-R01-08 | doc 84 §1.4 |
| BR-R02-001..007 receber | artefato+SE5/SE1 | `E5_*`,`E1_VALOR`, provisão 'P' | população 649+8, VO dual | `receivables-settlements` | api-delpi (**após fonte DLP06R01** — E1) | T-R02-01..06 | doc 84 §2 |
| BR-R03-001..006 P7 | artefatos + saldo ex-99 (`PROVEN`) | `B9_*`, `D3_*`(loc99/RE3), MATR989, tipos, armazém | EM ESTOQUE ex-`MV_LOCPROC` + EM PROCESSO (MATR989) por `as_of` | `inventory-p7` (binding de totalização provado; parâmetros por emissão — E2) | api-delpi | T-R03-01..04 | doc 84 §3, doc 80 §33.D |
| BR-R03-007 resumo P7 | fatos: folha 74 = escopo MP/PA/PI, divergência só MP (`PROVEN`); hipótese `QTNP@emissão` (`PENDING`) | `B2_QTNP`,`D1_QUANT`,`D2_QUANT`,`F4_PODER3` | hipótese: exclusão produtos `QTNP>0` (Δ76,43/+1.942,62 — não é regra oficial; causa `PENDING` E2) | `inventory-p7` (parâmetro poder3 — E2) | api-delpi | T-R03-05 | doc 80 §35/§35.E |
| BR-R03-008 parâmetros MTR460 | SX1010 grupo `MTR460` | `X1_*` | catálogo 25 perguntas; sem parâmetro de tipo → escopo resumo fora do SX1 | — (referência de parâmetros) | api-delpi | T-R03-06 | doc 80 §35.B/E |
| BR-R05-001/002 MATR320 | artefato+SB9 | `B9_*` por tipo | Saldo Atual por tipo | `stock-movements-summary` | api-delpi | T-R05-01 | doc 84 §4 |
| BR-R05-003/004 SD1/SD2 | `matr320.prx` + SF4 | `D1_DTDIGIT`,`D2_EMISSAO`,`D*_CUSTO*`,`F4_PODER3`,`F4_ESTOQUE`,`D*_TIPO` | janela digitação/emissão + split poder3/TIPO='D' | `stock-movements-summary` (api-delpi TOTVS provider) | api-delpi | T-R05-02/03 | doc 80 §31.B-C |
| BR-R05-005 SD3 | `matr320.prx` | `D3_CF`,`D3_OP`,`D3_TM`,`D3_CUSTO1`,`D3_ESTORNO` | classificação por CF/OP + sinal TM>500 | idem | api-delpi | T-R05-04/05 | doc 80 §31.B-C |
| BR-R05-006 saldos | `matr320.prx` + SB2 | `B2_VATU<n>`,`B2_VFIM<n>` | saldo por modo par10; SI derivado | idem | api-delpi | T-R05-06 | doc 80 §31.B |
| BR-R05-008 retificações | TTAT/RECNO | `D_E_L_E_T_`,`R_E_C_N_O_` | leitura histórica exige `as_of` | `as_of` em todo contrato histórico | cf-api | T-R05-07 | doc 80 §31.D |
| BR-R05-011/012 as_of custo + ponte | `SD*_TTAT_LOG` | `TTAT_DTIME`,`TTAT_COLD`,`TTAT_FIELD` | custo no `as_of` da emissão + residual por produto | `as_of` + decomposição de drift em contrato histórico | api-delpi | T-R05-08/09 | doc 80 §33.A-B |
| BR-R09 MOD rate | `SBZ010.BZ_CUSTD` + Fat×MOD | `BZ_CUSTD`, horas | rate×horas por PA/filial | `mod-cost-rate` (E6=C) | api-delpi | T-R09-01 | doc 80 §22–§25 |
| BR-R09-003/006 população+faturamento | `DLP204.prw` + SD2/SF4/SG1 | `D2_COD`,`D2_QUANT`,`D2_EMISSAO`,`D2_TES`,`F4_DUPLIC`,`G1_*` | PA âncora = produto com SD2 TES-duplic-S no período; `Qtd Fat.` do âncora propagada aos descendentes | `billing-mod-breakdown` (`as_of` obrigatório) | api-delpi | T-R09-02/06 | doc 80 §43 |
| BR-R09-007/008 roteiro OP→MOD+tempo | `SHY010`/`SG2010` + `SH1010` | `HY_OP`,`HY_RECURSO`,`HY_TEMPAD`,`H1_CCUSTO`,`G2_TEMPAD` | `Quantidade` = tempo do roteiro congelado da OP (fallback SG2); MOD = `MOD`+`H1_CCUSTO` do recurso | idem | api-delpi | T-R09-03/04 | doc 80 §43 |
| BR-R09-009/010 horas+custo as_of | artefato + SBZ/TTAT | `BZ_CUSTD`,`TTAT_COLD`,`TTAT_DTIME` | `Horas=QtdFat×Quantidade`; `CustoTotal=Horas×rate`; rate `as_of` via TTAT | `billing-mod-breakdown` (`as_of`) | api-delpi | T-R09-01/05 | doc 84 §5.3 |
| BR-R10-002..005 seleção CC matriz | artefato + SD1/SF4/SB1 | `D1_DTDIGIT`,`D1_TES`,`D1_TP`,`D1_CC` | digitação no mês + NOT IN 13 TES + `D1_TP<>'MP'` + benefícios sem CC fora | `despesas-cc-official-scope` (owner: procedimento Controladoria, não filtro de tela genérico) | api-delpi | T-R10-01..03 | doc 80 §44 |
| BR-R10-006 classe Direto/Ind/Adm | artefato + CTT | col. sem título, `D1_CC` | classificação manual pós-exportação por CC — sem fonte física | — (manual) | — | T-R10-04 | doc 80 §44 |
| BR-R11-002/003 seleção + CPV-zero | artefato + SD2/SF4/SB1 | `D2_GRUPO`,`D2_TES`,`D2_CUSTO1`,`F4_ESTOQUE` | `D2_GRUPO='9035'`∩`D2_TES='594'`∩emissão mês; custo zero estrutural (`F4_ESTOQUE='N'`) | `billing-exceptions` (lista de conferência Controladoria — owner da finalidade) | api-delpi | T-R11-01..03 | doc 80 §45 |
| BR-R10/11 EDAPP | SD1/SD2 | `D1_*`,`D2_*` | consulta parametrizada | `fiscal-docs-query` | api-delpi | T-R10-00 | doc 47 §11.1 |
| BR-R06-001/002/003 kardex UNION | `matr910_dlp.prx` + SD1/SD2/SD3/SF4 | `D1_DTDIGIT`,`D2_EMISSAO`,`D3_EMISSAO`,`F4_ESTOQUE`,`D3_ESTORNO`,`D*_ORIGLAN`,`D*_LOCAL` | UNION SD1+SD2+SD3 por produto/armazém com datas por tabela | `stock-kardex` (contrato futuro — `DECISION_REQUIRED`) | api-delpi | T-R06-01..04 | doc 80 §37.C |
| BR-R06-004/005 ordem+REF | `matr910_dlp.prx` | `D*_NUMSEQ`,`D1_FORNECE`,`D2_PEDIDO`,`D3_OP`,`D3_CC` | data + NUMSEQ; REF por origem (F-/P-/OP/CC) | idem | api-delpi | T-R06-05/06 | doc 80 §37.C |
| BR-R06-006/007 custo+saldo | `matr910_dlp.prx` + TTAT/SB9 | `D*_CUSTO*`,`TTAT_COLD`,`B9_QINI`,`B9_VINI1` | custo as_of emissão; cadeia saldo desde `CalcEst` | `as_of` obrigatório (mesma regra de BR-R05-008) | api-delpi | T-R06-07/08 | doc 80 §37.C/E |
| BR-R06-009/010 população+CPV | artefato + SB1/SB9 + **`GET /supplies/cpv` existente** | `B1_TIPO`,`B1_COD`,mv_par07,`D2_CF`,`D2_CUSTO1` | só produtos com movimento; saídas kardex ≠ CPV — CPV = subconjunto SD2 CFOPs venda (rota api-delpi canônica) | `REUSE_PARTIAL` — endpoint cobre CPV por emissão com custo corrente; lacuna `as_of`/snapshot p/ fechamento → owner | api-delpi (regra) / cf-api (composição) | T-R06-09 | doc 80 §37.C/§39 |
| BR-R07-001..003 INVENT | artefato + SD3/TTAT | `D3_DOC='INVENT'`,`D3_TM`,`D3_CF`,`D3_CUSTO1` | ajustes 999/RE0 saída + 499/DE0 entrada, loc 01+99 | `stock-kardex` filtro doc — mesmo contrato de R06 | api-delpi | T-R07-01/02 | doc 80 §37.D |
| BR-R08-001..005 bloco OP | artefato + SD3/SC2 | `D3_COD`,`D3_OP`,`D3_CF`,`D3_LOCAL`,`D3_QUANT`,`D3_CUSTO1`,`C2_QUJE`,`C2_DATRF`,`PR0` | linha SD3 `RE*`≤corte de OP aberta na emissão; saldo = ΣRE−DE | `material-in-process` (`as_of` obrigatório — estado da OP muda no tempo) | api-delpi | T-R08-01/03/05 | doc 80 §41 |
| BR-R08-006 bloco sem OP | artefato + SB9 | `B9_DATA`,`B9_LOCAL`,`B9_QINI`,`B9_VINI1` | saldo físico `SB9`@fechamento loc99 | idem — coberto por `stock_value_historical_sql` existente | api-delpi | T-R08-02 | doc 80 §41 |
| BR-R12-001 Reposição | `MATA320` (SX1 `MTA320` 1:1) + TTAT `SB1010` | `B1_CUSTD` | recálculo custo reposição (últ. compra/estrutura) | leitura existente `standard_cost` (product repos) — `REUSE_CONFIRMED` | api-delpi | T-R12-02 | doc 80 §46 |
| BR-R12-002 Acompanha Custos | wizard (motor MATA330 custom — fonte fora do acervo) | `MV_ULMES`, SB9, workfile | etapas 1–4 ciclo de vida persistido | `cost-closing-run` (`TARGET` — orquestração/status não existem) | api-delpi | T-R12-03 | doc 80 §46 |
| BR-R12-003 Refaz Saldos | `MATA300` (SX1 `MTA300` 1:1) + `DEL100.PRW` (auditoria SB9 distinta) | SB2 (recalc); SD3/SB9 (DEL100) | reconstrução→comparação (DEL100) | `rebuild-balances-audit` | api-delpi | T-R12-01 | doc 80 §24.E/§46 |
| BR-R12-005 Análise e revisão | `Analise.xlsx` + SB9 | `B9_CM1`,`B9_QINI`,`B9_VINI1` | export da etapa 3; CM final ≡ SB9@fechamento 98,6% | `stock_value_official_closure_sql` existente — `REUSE_CONFIRMED` | api-delpi | T-R12-04 | doc 80 §46 |
| BR-R15-002 cadeia fechamento | `MATA330`+`MATA280` (TTAT/SX1) | SB9, SC2 `C2_VINI*`/`C2_APRINI*`, `MV_ULMES` | cálculo→virada→snapshot | `month-end-stock` (**após E5**) | api-delpi | T-R15-02/06 | doc 80 §47 |
| BR-R15-003 SB9 snapshot | SB9/SB2 | `B9_*` | snapshot mensal | `stock_value_official_closure_sql` existente — `REUSE_CONFIRMED` | api-delpi | T-R15-05 | doc 80 §21/§47 |

**Divisão de camadas (TARGET):** regras físicas e WHEREs vivem na
**api-delpi** (provider TOTVS — fonte única); **controllership-finance-api**
compõe competência/filial/escopo e contrato; **MFE** só apresenta. Nada se
copia para BFF/frontend.

---

## §16 — Matriz de testes derivada das regras comprovadas

> Especificação documental de cenários — **nenhum teste automatizado foi
> executado** nesta fase (READ-only). Onde o critério foi reproduzido por
> evidência na investigação, a linha marca `reproduzido`; cenários propostos
> sem execução marcam `candidato`; dependências de fonte/decisão marcam
> `pending`.

| Teste | Regra | Tipo | Critério |
|---|---|---|---|
| T-R01-01 | BR-R01-001 | positive · reproduzido | competência 09/2026 retorna 948 linhas, chaves multiset = XLSB |
| T-R01-02 | BR-R01-002 | negative · reproduzido | par de estorno por chave 12 campos é removido; sem a remoção = 950 |
| T-R01-03 | BR-R01-001 | negative · reproduzido | chave de estorno com data/valor produz 937 — regresso conhecido |
| T-R01-04 | BR-R01-003 | limit · reproduzido+pending | TB=`E5_VALOR` na emissão observada (948/948); cenário `nVlMovFin`≠`E5_VALOR` = `pending`, **sem expectativa definida** (não observado — não inventar) |
| T-R01-05 | BR-R01-004 | limit · reproduzido | VO: título comum `E2_VALOR`; INV→`E5_VALOR`; grupo NF+TX→soma |
| T-R01-06 | BR-R01-005 | positive · reproduzido | título compartilhado resolve por chave, não por filial SE5 |
| T-R01-07 | BR-R01-006/007 | positive · reproduzido | Baixados/Compens./BxFat/Jur/Correção batem subtotais impressos |
| T-R01-08 | BR-R01-009 | limit · reproduzido | PDF=XLSB−log; log ausente → expor flag, não igualar totais |
| T-R02-01 | BR-R02-001 | positive · reproduzido | 657 = 649 título + 8 PA/FINA750 |
| T-R02-02 | BR-R02-004 | limit · reproduzido | VO sem título = provisão 'P' espelhada (numero/clifor) |
| T-R02-03 | BR-R02-002 | negative · reproduzido | decomposições MT/JR/DC não viram linha; não-CMP não-CMP'd |
| T-R02-04 | BR-R02-007 | limit · reproduzido | `Orig` só preenchida em linha sem título |
| T-R02-05 | BR-R02-002 | pending | sem fonte: não generalizar inclusão de sem-título (3 excluídos) |
| T-R03-01 | BR-R03-002 | limit · reproduzido | duas emissões P7 do mesmo dia → totais distintos exigem `as_of` |
| T-R03-02 | BR-R03-003 | positive · reproduzido | EM PROCESSO = MATR989 (355.240,51) |
| T-R03-03 | BR-R03-004/006 | positive · reproduzido | EM ESTOQUE = SA_emissão − estoque loc99_emissão (3.591.191,36 exato) |
| T-R03-04 | BR-R03-006 | negative · candidato | armazéns especiais além de loc99 (`MV_CQ`, `MV_ALMTERC`) só entram na regra se parâmetros provarem exclusão |
| T-R03-05 | BR-R03-007 | positive · parcial | hipótese `QTNP@emissão>0`: estoque 587.621,85 (Δ76,43) / processo 79.194,35 (Δ+1.942,62) — reproduzido **sem** paridade centavo; classificação `PENDING`, não regra |
| T-R03-06 | BR-R03-008 | negative · candidato | escopo de tipos da emissão resumida exige mecanismo fora do grupo `MTR460` (sem parâmetro de tipo no SX1) |
| T-R05-01 | BR-R05-002 | limit · reproduzido | SB9×MATR320 8/10 tipos Δ=0,000; PI −0,001; MP +8.631,731 decomposto ao centavo por produto — revalorização CM |
| T-R05-02 | BR-R05-003 | positive · reproduzido | SD1 usa `D1_DTDIGIT` (não emissão) — doc digitação-Set/emissão-Out entra na competência |
| T-R05-03 | BR-R05-004 | negative · reproduzido | `D*_TIPO='D'` vai para Devolução, não Compras/Vendas; poder3≠'N' vai para EntPT/SaiPT |
| T-R05-04 | BR-R05-005 | positive · reproduzido | SD3 CF 'PR*'→Produção, RE4/DE4→Transferências, OP-vazio→MovInt, OP-preenchido→Requisições, resto→TransfProc |
| T-R05-05 | BR-R05-005 | negative · reproduzido | `D3_TM>'500'` sinaliza saída (valor negativo); `D3_ESTORNO='S'` excluído |
| T-R05-06 | BR-R05-006 | limit · reproduzido | SI impresso é derivado (SA − movimentos), não saldo cadastrado |
| T-R05-07 | BR-R05-008 | negative · reproduzido | linha inserida/deletada após emissão não pode entrar/sair da reprodução `as_of` |
| T-R05-08 | BR-R05-011 | negative · reproduzido | reversão TTAT_COLD limitada a `TTAT_DTIME > emissão` — sobre-reversão gera erro artificial |
| T-R05-09 | BR-R05-012 | positive · reproduzido | ponte por produto: Σ residual = +8.631,731 = oficial **exato** (agregação `CAST DECIMAL(30,9)`); TransfProc-RE3 fora do fluxo de valor |
| T-R09-01 | BR-R09-010 | positive · reproduzido | Custo Unitário MOD = `BZ_CUSTD` por produto/filial **as_of emissão** — 4.469/4.469 linhas com SBZ conferem; 7 sem registro SBZ |
| T-R09-02 | BR-R09-003/006 | positive · reproduzido | `Qtd Fat.` = Σ `D2_QUANT` TES `F4_DUPLIC='S'` do PA-âncora propagada — 4.476/4.476 explicadas |
| T-R09-03 | BR-R09-008 | boundary · reproduzido | `Quantidade` = `HY_TEMPAD` do roteiro da OP — 4.311 linhas (+138 `G2_TEMPAD` fallback); 27 residuais E9 |
| T-R09-04 | BR-R09-007 | positive · reproduzido | MOD = `MOD`+`H1_CCUSTO` do recurso da operação (SHY ou SG2); mapa 150 CTs cobre a população |
| T-R09-05 | BR-R09-009 | positive · reproduzido | `Horas=QtdFat×Quantidade`, `CustoTotal=Horas×rate` — identidade 4.476/4.476 |
| T-R09-06 | BR-R09-005 | positive · reproduzido | `Seq Comp` 02/04/06 = nível SG1 0/1/2 do âncora (distância estrutural conferida) |
| T-R09-07 | BR-R09-003/006 | negative · candidato | NF `D2_TIPO='D'` com TES duplic-S não deve compor `Qtd Fat.` — não exercido nesta competência |
| T-R10-01 | BR-R10-001/002 | positive · reproduzido | 353/353 linhas = itens SD1 f01 `D1_DTDIGIT`∈set (Σ `D1_TOTAL`=169.704,12 exato); 80 linhas provam eixo digitação |
| T-R10-02 | BR-R10-003 | positive · reproduzido | 13 TES excluídos sem exceção (303 linhas); lista narrada owner mapeia 11/13 — `016`/`159` residuais E10 |
| T-R10-03 | BR-R10-004/005 | positive · reproduzido | MP 302/302 fora; benefícios saúde/odonto sem CC 6/6 fora |
| T-R10-04 | BR-R10-006 | boundary · reproduzido | classe `Direto/Indireto/Adm` = coluna manual (não SD1/CTT); 2 entradas minúsculas evidenciam edição humana |
| T-R11-01 | BR-R11-001/002 | positive · reproduzido | 11/11 linhas = itens SD2 `D2_GRUPO='9035'`∩`D2_TES='594'`∩`D2_EMISSAO`∈set f01 — conjunto idêntico; Σ `D2_TOTAL`=97.462,71 exato |
| T-R11-02 | BR-R11-003 | positive · reproduzido | `D2_CUSTO1`=0 nas 11 linhas desde a criação (TTAT insert MATA460A, `COLD`=`CNEW`=0) — estrutural `F4_ESTOQUE='N'` |
| T-R11-03 | BR-R11-002 | negative · reproduzido | universo `D2_CUSTO1=0` do mês = 91 linhas — artefato é subconjunto 9035/594; `custo=0` sozinho NÃO é o predicado |
| T-R11-04 | BR-R11-004 | sibling · reproduzido | 8/11 docs casam item 510 (custo>0, estoque-S) + item 594 (custo 0, estoque-N) — industrialização p/ terceiros |
| T-R10-00 | BR-R10-001 | positive · reproduzido | export = tabela literal SD1; headers SX3; binding 1:1 |
| T-R06-01 | BR-R06-001/002 | positive · reproduzido | UNION SD1/SD2/SD3: 9.357 linhas vinculadas linha-a-linha por blocos (1.544 produtos) |
| T-R06-02 | BR-R06-002 | negative · reproduzido | `D3_ESTORNO='S'`/deletado fora; doc com trio limpo+par estornado imprime só a linha limpa |
| T-R06-03 | BR-R06-003 | positive · reproduzido | SD1 por `D1_DTDIGIT`: doc emitido em out/digitado em set entra na competência (281 casos dig≠emi); SD2/SD3 por `EMISSAO` |
| T-R06-04 | BR-R06-002 | negative · reproduzido | `D*_ORIGLAN='LF'` excluído; `D*_LOCAL≠mv_par08` excluído |
| T-R06-05 | BR-R06-004 | positive · reproduzido | mesma data ordena por `D3_NUMSEQ` — 1.971/1.971 grupos consistentes |
| T-R06-06 | BR-R06-005 | positive · reproduzido | REF: `F-`+fornecedor (260/260), `P-`+pedido (594/594), `OP`+`D3_OP` (6.060/6.060), `CC`+`D3_CC` |
| T-R06-07 | BR-R06-006 | positive · reproduzido | custo impresso = `D*_CUSTO*` as_of emissão; divergente do corrente resolve via `TTAT_OLD` (1.981 linhas) |
| T-R06-08 | BR-R06-007 | positive · reproduzido | saldo inicial `B9_*`@0831 + movimentos = saldo impresso — 1.544/1.544 blocos contínuos |
| T-R06-09 | BR-R06-009 | negative · reproduzido | produto sem movimento elegível não vira bloco (0/1.544); tipo `MO`/MOD* fora |
| T-R06-10 | BR-R06-008 | positive · reproduzido | devolução `TIPONF='D'` cruza coluna com sinal −: SD1 tipo D → saída− (retorna ao estoque), SD2 tipo D → entrada− (sai) — 11/11 custo `CUR` exato, `zMTR910Dev`/`MV_LISTDEV` no fonte |
| T-R07-01 | BR-R07-001/002 | positive · reproduzido | 45/45 linhas INVENT vinculadas ao SD3 (999/RE0 saída, 499/DE0 entrada), loc 01+99 |
| T-R07-02 | BR-R07-003 | positive · reproduzido | 10 divergências de custo = revalorização pós-emissão provada via `TTAT_OLD`; totais oficiais fecham |
| T-R07-03 | BR-R07-002 | negative · candidato | estorno de INVENT (par `D3_ESTORNO`) deve ficar fora — mesma regra de T-R06-02 |
| T-R07-04 | BR-R07-002 | positive · candidato | movimento retroativo INVENT digitado após emissão não entra na reprodução `as_of` |
| T-R12-01 | BR-R12-003 | positive · reproduzido | query DEL100 vigente = 3.058/421/242 |
| T-R12-02 | BR-R12-001 | positive | SX1 `MTA320` 16/16 params + TTAT `MATA320`→`B1_CUSTD` (13.201+1.532 writes 30/09 JOICI) |
| T-R12-03 | BR-R12-002 | negative | etapa 4 `Fechamento` ausente no vídeo → não classificar como concluída |
| T-R12-04 | BR-R12-005 | positive | `Analise.xlsx` CM final ≡ `B9_CM1`@30/09: 1.966/1.994 (22 MOD* estrutural + 6 drift) |
| T-R08-01 | BR-R08-001/002/003 | positive · reproduzido | 1.501/1.501 linhas com OP = linhas SD3 `RE*` (grão linha física); 650/650 pares qtde+valor exatos |
| T-R08-02 | BR-R08-006 | positive · reproduzido | 569/573 exato vs `SB9010`@0930 loc99; 4 Δ temporais explicados |
| T-R08-03 | BR-R08-004 | sibling/negative · reproduzido | OP com `PR0` no Dt.Ref (33), encerrada-sem-produção (3) e filial 02 (15) excluídas; OP aberta impressa |
| T-R08-04 | BR-R08-007 | positive · reproduzido | total = EM PROCESSO P7 = 355.240,51 exato |
| T-R08-05 | BR-R08-003 | negative · reproduzido | `RE*` de 01/10 na mesma OP fora — corte de competência 30/09 |
| T-R08-06 | BR-R08-005 | negative · candidato | par impresso com `DE*` deve ter saldo netado — não exercido nesta competência |
| T-R15-01 | BR-R15-002 | negative · refinado | timestamp de persistência ≠ execução — `I_N_S_D_T_` é UTC (−3h local), prova SD3 recno×TTAT |
| T-R15-02 | BR-R15-002 | positive | rajadas SB9 dentro da janela `MATA280` em 5/5 execuções |
| T-R15-03 | BR-R15-002 | positive | `I_N_S_D_T_` = TTAT_DTIME +3h exatos (stamp UTC) |
| T-R15-04 | BR-R15-004 | negative | `SX6010` sem TTAT — writer `MV_ULMES` não auditável |
| T-R15-05 | BR-R15-003 | positive | SB9@30/09: 4.812 f01 + 3.117 f02, chave única |
| T-R15-06 | BR-R15-005 | positive | wizard "Concluído 18/09 16:05" ≈ fim MATA280 16:03:52 |
| T-R15-07 | BR-R15-002 | negative | `SB9010_TTAT_LOG`/`SB2010_TTAT_LOG` vazios all-time |

---

## §17 — Registro consolidado

| Classe | Regras |
|---|---|
| `PROVEN` | BR-R01-001..011 (exceto pendências internas declaradas), BR-R02-001/003/004/005/006/007 (paridade), BR-R03-002/003/004/006 (P7: EM ESTOQUE ex-99 + EM PROCESSO MATR989, totalização), BR-R03-007 (fatos do resumo `PROVEN`; causa poder3 = hipótese `PENDING`), BR-R03-008 (catálogo MTR460), BR-R05-001..008/011/012 (fonte + reconciliação **escopo completo** ao centavo + ponte de drift), **BR-R06-001..010** (kardex UNION SD1/SD2/SD3: fonte+filtros+datas+ordem+REF+custo as_of+cadeia de saldo+população; BR-R06-010 = CPV existente `GET /supplies/cpv` identificado — semântica verificada, `REUSE_PARTIAL` p/ fechamento), **BR-R07-001..003** (INVENT 45/45), **BR-R09-001..011** (DLP204 fonte+parâmetros+seleção SD2-duplic-S+expansão SP+QtdFat propagado+roteiro-OP HY_TEMPAD+H1_CCUSTO+fórmulas+rate as_of; BR-R09-007/008 marcadas 99,4% com 27 residuais declarados), **BR-R10-001..005** (seleção Controladoria SD1: digitação+TES-exclusão+MP-out+benefícios-out — corroborada owner doc 56 §Reg.17), **BR-R11-001..005** (binding+seleção 9035/594+CPV-zero estrutural+industrialização-terceiros+impacto-nulo-CPV), **BR-R12-001** (MATA320 rotina+efeito TTAT `B1_CUSTD`), **BR-R12-003** (MATA300 binding SX1 + DEL100 distinto), **BR-R12-004/005** (SB9+`MV_ULMES` no dado; `Analise.xlsx`↔etapa-3↔SB9 98,6%), SB9 snapshot (recorte), **BR-R15-001/002/003/005/007** (cutoff por filial; cadeia MATA330→MATA280→SB9 por timing+SX1; snapshots íntegros; ciclo de vida do wizard; correções antes da virada) |
| `AS-IS` | BR-R01-010, BR-R02-002 (exclusões observadas), BR-R03-001, BR-R05-009 (armazéns especiais), R08, R09 (layout), BR-R12-002 (wizard: etapas 1–3 `EXECUTION_OBSERVED`, etapa 4 não exibida), BR-R15-006 (reabertura existe, semântica pendente) |
| `TO_INVENTORY` | R03 produtor/parâmetros por emissão (E2), BR-R05-010 (SP MAT056 binária), R04 (matr860?), R06/R07 versão RPO implantada (E7), R08 bindings físicos, R09 internos da `STP_DELPI_FORMA_PRECO_*` + versão RPO DLP204 + parâmetros efetivos + 27 tempos residuais + divisor desdobramento (E9), R11 finalidade da exclusão (qual apuração recebe o desconsiderar — E11), R10 mapeamento exato da lista narrada 12→13 TES + regra contábil benefícios (E10), R13 contrato externo, R14 todo |
| `TARGET` | E6 opção C (histórico homologado + recalculado corrente; histórico incompleto = tratamento explícito, não zero); divisão de camadas §15; `as_of` obrigatório (BR-R05-008 reforça) |
| `PENDING` | subconjuntos dos logs (R01/R02), regra geral sem-título e decomposições (R02), `nVlMovFin`≠`E5_VALOR` (R01), parâmetros P7 (R03), paridade `as_of` do saldo R05 + generalização aos demais tipos, fonte/RPO MATA280 e writer interno do `MV_ULMES` (R15 — E5 estreitado; atribuição SB9→MATA280 por timing+semântica SX1), fonte `DLP06R01` (E1) |
| `STALE_EVIDENCE` | contagens DEL100 antigas 724/672 (`EXECUTION_DRIFT`, doc 80 §23.A) |

**Garantia do critério essencial:** as regras **descobertas nesta
investigação** e necessárias para reproduzir os resultados oficiais
observados estão consolidadas neste documento ou em doc 84 (paridade
detalhada) — nenhuma ficou apenas em scripts temporários, mensagens ou
memória. O catálogo **não afirma completude**: itens com binding/pendência
declarada (R04, R08, R13, R14 e pendências internas de R01–R03/R05–R07/R15)
não têm ainda todas as regras necessárias para conclusão — permanecem
`PENDING`/`TO_INVENTORY`.


### BR-R03-010 — Semântica poder-de-terceiros verificada em dados (P7-READINESS-005)

Verificação SELECT-only 2026-10-28 (filial 01, fechamento 30/09/2026):

- `SB2.B2_QTNP` = material próprio **em** terceiros — só em linhas
  `B2_LOCAL='01'` (111 produtos MP, 710.034,862 u).
- `SB2.B2_QTER` = material de terceiros **conosco** — só em `B2_LOCAL='01'`
  (50 produtos MP, 6.788,40 u).
- `SF4.F4_PODER3` ∈ {N,R,D}: `SD2 R` = remessa p/ terceiro (QTNP+);
  `SD1 D` = retorno poder3 (QTNP−); `SD1 R` = entrada de material de
  terceiro (QTER+); `SD2 D` = devolução ao dono (QTER−). Catálogo SF4
  extraído integralmente.
- `SB6`/`VW_PD3_BENEF_RETORNOS` = tracking de beneficiamento (módulo
  canônico `protheus_third_party_materials.py`); 221 remessas tipo `D`
  abertas + 80 tipo `E`, filial 01.
- **Proibido** excluir genericamente `F4_PODER3<>'N'` — direção importa
  (decisão PO; doc 119 §4).
- A exclusão MP do resumo oficial atua **por produto** (conjunto
  `QTNP>0` no `as_of`), não por quantidade `QTNP×custo` — modelos de
  quantidade descartados; população exata `PENDING_EXTERNAL` (E2).
- EM PROCESSO excluído mede-se como **MATR989 por produto**
  (loc99 + RE−DE por OP viva `as_of`), não loc99+RE globais — modelo
  73.412,67 vs alvo 77.251,73 (residual −3.839,06, `PENDING_EXTERNAL`).
- QTNP@emissão = QTNP atual para MP filial 01: movimentos poder3 de
  02/10 foram direção QTER (SD1-R/SD2-D), não QTNP.
- Drift MP `STALE_EVIDENCE`: SB9 ex-99 atual diverge do estado de
  emissão em +8.182,43 (revalorização + regravação 21/10); PA/PI/II
  exatos — validação de paridade exige nova emissão controlada.

## §18 — Regras semânticas de comparação transversal (stage-03, 2026-10-31)

Execução `CF-PROC0072-CLARA-REPORT-COMPARISON-IMPLEMENTATION-STAGE-03`
materializou a camada transversal de comparação prevista no doc 126 §7:
owner `controllership-finance-api` (orquestração apenas — medidas e
seleções continuam produzidas pelos owners canônicos). Regras
semânticas agora executáveis:

### BR-CMP-001 — Mesma convenção + mesma seleção = `COMPARABLE`

O mesmo relatório entre competências/filiais é comparável somente com
mesma medida, universo e convenção de custo (ex.: R06 `outputValue`
entre competências, R07 entre filiais). O motor não inventaria delta
para pares fora dessa condição.

### BR-CMP-002 — R10 universos são partições estritas

`universe=calculation` × `universe=investigation` → `NOT_COMPARABLE`
(`r10_universe_mismatch`). Os totais dos dois universos nunca são
somados nem comparados como equivalentes.

### BR-CMP-003 — R06×CPV é relacionado, não equivalente — `PROVEN` semântico

Saída de estoque (R06, `F4_ESTOQUE='S'` + custo TTAT) ≠ CPV
(`SUM(D2_CUSTO1)` por CFOP de venda, custo corrente `live`). O delta é
exibido rotulado `related_not_equivalent` + explicação com evidência —
nunca divergência financeira comprovada. Mesma classe para
R05×R06 (fluxo × kardex valorizado), R06×R07 (INVENT é subconjunto),
R03×R05 (snapshot × fluxo), R03×R08 (universos disjuntos SB9),
R10×R11 (SD1 despesa × SD2 roster, eixos de data distintos).

### BR-CMP-004 — Identidade documental exige chave completa

Cruzamento documental (ex.: R10×R11) somente por
`filial+documento+série`; itens sem chave completa são declarados em
`incompleteKeys` e nunca participam do match — número de documento
isolado não é identidade. Eixo de data divergente (D1_DTDIGIT ×
D2_EMISSAO) é anotado por match: a mesma NF pode cair em competências
distintas.

### BR-CMP-005 — Sem medida comum = `NOT_COMPARABLE`; sem evidência = `INSUFFICIENT_EVIDENCE`

Pares fora da matriz curada respondem `INSUFFICIENT_EVIDENCE` — nunca
promovidos por semelhança de nome de coluna. Relatórios sem contrato
implementado (R04/R09/R12/R15) → `report_not_implemented`; R13/R14 são
evidência externa sem medida numérica.

### BR-CMP-006 — Ausência de dados não é zero

`EMPTY`/`denied`/`unavailable`/`truncated` são estados de sujeito
declarados — nunca convertidos em valor 0, nunca usados para completar
tendência. Sujeito negado não contribui nem existência. Percentual com
denominador zero é declarado `zero_baseline`, não calculado.

## §19 — Fichas técnicas R01–R15 (stage-04, 2026-10-31)

As regras deste catálogo foram consolidadas em fichas técnicas
versionadas para consumo da CLARA (decisão D-06 do doc 126):
`fichas/R01-ficha.md` … `fichas/R15-ficha.md` (+ `fichas/README.md`
índice e `fichas/processo-fechamento-ficha.md`). Cada ficha referencia
esta fonte e mantém a classificação por afirmação — a ficha não cria
regra nova nem rebaixa `PENDING`/`TO_INVENTORY` a fato; divergências
encontradas devem ser corrigidas **aqui** (fonte canônica) e propagadas
para a ficha.


## Adendo — Publicacao produtiva (30/10/2026)

As regras R10/R11 e o motor de comparacao publicadas em producao: release stage-05 (30/10/2026, host `srv-api`, checkout `297068f1b7` — inclui `9f66f8b8e0`) publicado por `up-prod-sequential.sh`: api-delpi `sha256:d46e307ad3e6`, BFF `sha256:7f0e7db69114`, MFE `sha256:8530bbc8f797`; corpus produtivo `5bebf07f-a66a-479f-aa2b-e7d0e6c7ea00` (88 fontes / 2.186 itens, 17 fichas, 100% `PORTAL_ACCESS`).
As regras sem contrato (R04/R09/R12/R13/R14/R15) seguem `PENDING_CONTRACT`/
`EXTERNAL` — fichas publicadas no corpus descrevem regras, nao capabilities.
