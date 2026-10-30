# R06 — Kardex / CPV (MATR910)

Versão da ficha: 1.0 · 31/10/2026 · doc 127 Etapa 4.

## Identificação

- Código/nome: **R06 — Kardex de movimentação (MATR910)**, com a medida
  gerencial irmã **CPV** (`/supplies/cpv` → `/closing/cpv`).
- Finalidade: extrato analítico por produto — cada movimento
  elegível do mês com quantidade, custo e cadeia de saldo desde o
  fechamento anterior; o CPV mede o custo das saídas de venda (CFOP
  5101/5124/6101/6124) com regra própria de API.
- Processo: PROC-0072, P3 — `PROVEN` (doc 118 §6).
- Owner funcional: Controladoria (conferência interna).
- Owner técnico: `api-delpi` + `controllership-finance-api`.
- Produtor oficial: `MATR910` — fonte `matr910_dlp.prx` **no acervo**
  (variante Delpi); `CODE_DEPLOYED` pendente (E7 — versão RPO não
  inspecionada). CPV: `CpvQueryRepository` (canônico existente).
- Implementação: **`IMPLEMENTED`** (IMPLEMENTATION-015) —
  `/closing/kardex` + `/closing/cpv` operacionais; paridade oficial ×
  MATR910 `PENDING` (E8/G6).
- Homologação: G1–G5 `PASS` técnico; G6 `PENDING`.

## Fonte e dados

- Artefato: `cpv 09 26 matriz.xlsb` (filial 02 / loc 01, 09/2026 —
  9.357 movimentos / 1.544 blocos).
- Tabelas: UNION SD1 (entradas NF) + SD2 (saídas NF) + SD3 (internas/
  produção/inventário); cabeçalho SB1; SF4 por `D*_TES=F4_CODIGO`;
  SX1 grupo `MTR910` (22 perguntas catalogadas).
- Grão: **linha de movimento** por produto.
- **Eixo de datas por tabela — `PROVEN`:** SD1 usa `D1_DTDIGIT`
  (digitação), SD2 usa `D2_EMISSAO`, SD3 usa `D3_EMISSAO` — a mesma
  competência pode receber documento emitido em mês anterior.
- Custos: `D1_CUSTO`/`D2_CUSTO1`/`D3_CUSTO1`, moeda 1 — valores
  **as_of da emissão** (9.357/9.357 vinculados; 1.981 via `TTAT_OLD`
  de revalorização posterior).
- Filial/armazém: `D*_LOCAL=mv_par08` (loc 01 observado).
- Capabilities CLARA: `read(report.kardex)`, `read(report.cpv)`.

## Regras de negócio (doc 85 §6)

- BR-R06-001 produtor/modelo UNION + SB1 — `PROVEN`.
- BR-R06-002 filtros: `F4_ESTOQUE='S'` (SD1/SD2), `D3_ESTORNO<>'S'`,
  `D*_ORIGLAN<>'LF'`, `D1_REMITO=''`, `D3_SERVIC`/CQ — `PROVEN`.
- BR-R06-003 eixos de data por tabela — `PROVEN`.
- BR-R06-004 ordenação por data + `*_NUMSEQ` — `PROVEN`.
- BR-R06-005 coluna REF (F-fornecedor / P-pedido / OP / CC) — `PROVEN`.
- BR-R06-006 custos as_of — `PROVEN`.
- BR-R06-007 cadeia de saldo = `CalcEst` ≡ `B9_QINI`/`B9_VINI1` do
  fechamento anterior — `PROVEN` (1.544/1.544).
- BR-R06-008 devoluções: sinal − na coluna oposta (`MV_LISTDEV`) —
  `PROVEN` (11 linhas observadas).
- BR-R06-009 população = produtos **com movimento elegível** — `PROVEN`
  (1.426 produtos com SB9 sem movimento ficam fora — o kardex cobre
  movimento, não posição).
- BR-R06-010 semântica CPV: `SUM(D2_CUSTO1)` em `D2_CF∈{5101,5124,6101,
  6124}`, `D2_EMISSAO` no período — `PROVEN`; **CPV é consulta viva**
  (errata PO 23/10): correção retroativa + recálculo altera o CPV de
  consultas futuras — `D2_CUSTO1` corrente é compatível, não lacuna.

## Interpretação

- **Saídas do Kardex ≠ CPV**: as saídas agregadas incluem requisições,
  transferências e ajustes SD3 + CFOPs fora do conjunto de venda; o CPV
  restringe-se a `D2_CUSTO1` dos CFOPs de venda com custo **corrente**.
  Diferença é esperada e explicável — nunca divergência comprovada.
- `STALE_EVIDENCE` conhecida: 354 produtos divergem em valor (Δqtd=0)
  entre o impresso e a SB9 corrente — revalorização pós-emissão
  (MATA330); o impresso é as_of.
- A cadeia de saldo parte do fechamento anterior — competência sem
  virada não sustenta saldo inicial confiável.
- Medidas: `entryValue`, `outputValue`, `netValue`, `entryQuantity`,
  `outputQuantity`, `netQuantity`, `movementCount`; CPV: `cpvTotal`,
  `cpvPercentage`, `totalQuantity`, `movementCount`.

## Operação

- Uso: conferência interna por produto; investigação de custo.
- Não automatizável: emissão oficial MATR910; recálculo MATA330.
- Comparações: `COMPARABLE` mesma medida/universo entre competências
  (ex.: jul × ago × set) e filiais; R06×R07 `RELATED_REQUIRES_EXPLANATION`
  (INVENT é subconjunto SD3); R06×CPV `RELATED_REQUIRES_EXPLANATION`;
  grãos `product_type`, `warehouse` sobre agregações completas.

## Governança

- Evidências: docs 61/80/84/85 §6/122; fonte no acervo; paridade física
  9.357/9.357.
- Pendências: E7 (RPO); E8/G6 paridade oficial; poder3 (`F4_PODER3`);
  parâmetros efetivos da emissão.
- Limitações: ranking agregado somente sobre conjunto completo —
  top-N de produto nunca é totalização.
- Comparação transversal: suportado; CPV é sujeito próprio (`CPV`),
  não uma medida do R06.
- Referências: doc 85 §6; doc 84; doc 118 §6; doc 122; doc 126 §§6–8.
