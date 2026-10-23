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

## §6 — R06 · CPV / Kardex (MATR910) — `AS-IS`/`TO_INVENTORY`

- `cpv 09 26 matriz.xlsb` = "Kardex Fisico-Financeiro" por produto
  (14.382 linhas): sequência de movimentos (DATA, TES, C.F, DOC,
  entradas/saídas qtd+custo, saldo, CM do movimento) + cabeçalho do produto.
- Roster: MATR910 "Kardex diario — CPV e Inventarios". Bindings SD3/D1/D2
  `TO_INVENTORY`.

---

## §7 — R07 · Inventários (MATR910 filtrado) — `AS-IS`

- `Invent.xlsb` = mesmo kardex filtrado a docs `INVENT` — TES **999 (RE0)** /
  **499 (DE0)**: ajustes de inventário com saldo resultante.
- Regra derivável: ajuste de inventário = movimento SD3 com TES de ajuste
  (`TO_INVENTORY` para binding físico).

---

## §8 — R08 · Material em Processo (MATR989) — `AS-IS`

- `Material em processo.xlsb` = "Saldo em Processo" (57.359 linhas):
  produto, UM, LOCAL, **ORDEM PRODUCAO**, TIPO RE/DE (RE2…), QTDE e VALOR EM
  PROCESSO — Dt.Ref 01/10/2026 16:15.
- Soma fecha com EM PROCESSO do P7 (BR-R03-003). Binding físico (SC2/SD3
  saldo por OP) `TO_INVENTORY`.

---

## §9 — R09 · Faturamento × MOD (DLP204) — `AS-IS` + taxa `PROVEN`

- `Fat x MOD.xlsb` (abas filial 01/02): explosão PA → componentes MOD:
  PA, Seq Comp, Cod MOD, Descrição, Qtd Fat, UM=`HR`, Quantidade (horas),
  Custo Unitário, Custo Total, Custo Produto, Horas.
- **Custo Unitário MOD = rate por produto/filial `SBZ010.BZ_CUSTD`** —
  `PROVEN` (MOD393 = 70,81 confere, doc 80 §22–§25).
- Vínculo DLP204↔view/SGZ/estruturas `TO_INVENTORY`.
- **E6 (decisão):** histórico homologado + recalculado corrente, opção **C**
  — `PRODUCT_DIRECTION_ONLY`, `IMPLEMENTATION_AUTHORIZED=NO` (doc 81/82);
  histórico incompleto deve ter tratamento explícito (falta ≠ zero).

---

## §10 — R10/R11 · Consultas EDAPP (SD1/SD2) — binding `PROVEN`

- Export EDAPP grava o literal da tabela na linha 0 (`SD1`/`SD2`) e headers =
  títulos SX3 `D1_*`/`D2_*` — **binding 1:1 monotabela** (doc 47 §11.1).
- R10 `CC matriz.xlsb` (SD1: NF entrada × centro de custo, IPI/ICMS);
  R11 `NF a desconsiderar.xlsb` (SD2: Tipo Saida 594, CF 5101).
- **Regra de negócio:** filtros são da consulta do usuário (operacional,
  sem WHERE fixo de relatório) — no Portal, o equivalente é consulta
  parametrizada sobre SD1/SD2, não reprodução de filtro ad hoc.

---

## §11 — R12 · Fechamento de custo / Reposição / Refaz Saldos — `AS-IS`

### BR-R12-001 — Recálculo do Custo de Reposição — `AS-IS` (parâmetros íntegros)

Vídeo 04:00: Utilizar Qual Moeda?=Nenhuma · Utilizar Taxa?=Diaria · Calcular
os Custos Por?=Estrutura · Considerar Ult. Preco Compra?=Sim · Dt Final Ref
Taxa?=30/09/2026 · Tipo de produto até=MP · Considera Mão de Obra?=Ambos ·
Tempo Setup?=Som Tempo Propo.

### BR-R12-002 — Wizard "Novo fechamento de custo" — `AS-IS`

Etapas observadas: Predefinição de cálculo → Cálculo de custo → Análise e
revisão → Fechamento; checkpoints: níveis validados, arquivo de trabalho,
transferências entre filiais, movimentações. Execução real 30/09 14:47
(JOICI, Matriz).

### BR-R12-003 — Refaz Saldos (DEL100) — `PROVEN` (reconstrução)

- `DEL100.PRW` decodificado: reconstrói posição a partir de SD3/SD1/SD2 e
  compara com SB9; query vigente sanitizada **3.058/421/242** (doc 80 §24.E,
  reproduzida 2×; SF4 compartilhada ≡ `xFilial`).
- `STALE_EVIDENCE`: contagens antigas 724/672 superadas — preservado como
  `EXECUTION_DRIFT` (doc 80 §23.A).

---

## §12 — R13 · Extratos e aplicações — `BLOQUEADO` (fonte externa)

- Checklist `Arquivos de envio` confirma entregáveis externos (Extratos, XP,
  BB, Aplicações): **fonte fora do Protheus** — regra de coleta = contrato de
  entrada externo, não SQL. `G1 PASS`, demais `PENDING`.

---

## §13 — R14 · Importação / câmbio — `BLOQUEADO`

- Sem evidência na pasta; nenhuma regra registrável além de `TO_INVENTORY`.

---

## §14 — R15 · Cutoff / sacramentação / SB9 — `AS-IS` + divergência preservada

- Execução do fechamento observada (wizard, 30/09 14:47) — `EXECUTION_OBSERVED`.
- **Divergência temporal preservada:** timestamps de inserção SB9
  (`B9_I_N_S_D_T_`: f02 02/10, f01 21/10) ≠ execução observada. Hipóteses:
  reexecução ("Refazer cálculo"), etapa distinta ou rotina separada —
  **identidade do passo que grava SB9: `PENDING`** (E5).
- `SB9` = snapshot mensal de SB2 (`PROVEN` no recorte, doc 80 §21) — usar como
  "estoque no fechamento" depende de provar a cadeia produtora.

---

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
| BR-R10/11 EDAPP | SD1/SD2 | `D1_*`,`D2_*` | consulta parametrizada | `fiscal-docs-query` | api-delpi | T-R10-01 | doc 47 §11.1 |
| BR-R12-003 Refaz | `DEL100.PRW` | SD3/SB9 | reconstrução→comparação | `rebuild-balances-audit` | api-delpi | T-R12-01 | doc 80 §24.E |
| BR-R15 SB9 snapshot | SB9/SB2 | `B9_*` | snapshot mensal | `month-end-stock` (**após E5**) | api-delpi | T-R15-01 | doc 80 §21 |

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
| T-R09-01 | BR-R09 | positive · reproduzido | Custo Unitário MOD = `BZ_CUSTD` por produto/filial |
| T-R10-01 | BR-R10/11 | positive · reproduzido | export = tabela literal; consulta parametrizada equivalente |
| T-R12-01 | BR-R12-003 | positive · reproduzido | query DEL100 vigente = 3.058/421/242 |
| T-R15-01 | BR-R15 | negative · reproduzido | snapshot com timestamp ≠ execução → não declarar produtor |

---

## §17 — Registro consolidado

| Classe | Regras |
|---|---|
| `PROVEN` | BR-R01-001..011 (exceto pendências internas declaradas), BR-R02-001/003/004/005/006/007 (paridade), BR-R03-002/003/004/006 (P7: EM ESTOQUE ex-99 + EM PROCESSO MATR989, totalização), BR-R03-007 (fatos do resumo `PROVEN`; causa poder3 = hipótese `PENDING`), BR-R03-008 (catálogo MTR460), BR-R05-001..008/011/012 (fonte + reconciliação **escopo completo** ao centavo + ponte de drift), BR-R09 (rate), BR-R10/11 (binding), BR-R12-003, SB9 snapshot (recorte) |
| `AS-IS` | BR-R01-010, BR-R02-002 (exclusões observadas), BR-R03-001, BR-R05-009 (armazéns especiais), R06, R07, R08, R09 (layout), BR-R12-001/002, R15 (execução) |
| `TO_INVENTORY` | R03 produtor/parâmetros por emissão (E2), BR-R05-010 (SP MAT056 binária), R04 (matr860?), R06/R07/R08 bindings físicos, R09 vínculo DLP204, R10/11 filtros, R13 contrato externo, R14 todo |
| `TARGET` | E6 opção C (histórico homologado + recalculado corrente; histórico incompleto = tratamento explícito, não zero); divisão de camadas §15; `as_of` obrigatório (BR-R05-008 reforça) |
| `PENDING` | subconjuntos dos logs (R01/R02), regra geral sem-título e decomposições (R02), `nVlMovFin`≠`E5_VALOR` (R01), parâmetros P7 (R03), paridade `as_of` do saldo R05 + generalização aos demais tipos, passo que grava SB9 (R15), fonte `DLP06R01` (E1) |
| `STALE_EVIDENCE` | contagens DEL100 antigas 724/672 (`EXECUTION_DRIFT`, doc 80 §23.A) |

**Garantia do critério essencial:** as regras **descobertas nesta
investigação** e necessárias para reproduzir os resultados oficiais
observados estão consolidadas neste documento ou em doc 84 (paridade
detalhada) — nenhuma ficou apenas em scripts temporários, mensagens ou
memória. O catálogo **não afirma completude**: itens com binding/pendência
declarada (R04, R06–R08, R13, R14 e pendências internas de R01–R03/R05/R15)
não têm ainda todas as regras necessárias para conclusão — permanecem
`PENDING`/`TO_INVENTORY`.
