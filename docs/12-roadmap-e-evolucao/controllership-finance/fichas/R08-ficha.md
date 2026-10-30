# R08 — Material em Processo (MATR989 / H02)

Versão da ficha: 1.0 · 31/10/2026 · doc 127 Etapa 4.

Publicação: **release produtivo stage-05** (30/10/2026, srv-api, SHA `297068f1b7`) — serviço reconstruído e paridade verificada em produção; corpus `5bebf07f-a66a-479f-aa2b-e7d0e6c7ea00` (88 fontes / 2.186 itens).

## Identificação

- Código/nome: **R08 — Material/Saldo em Processo** (analítico; bloco
  H02 do fechamento; alimenta "EM PROCESSO" do P7).
- Finalidade: saldo de material em processo por produto/OP na data de
  referência — físico do armazém de processo + material alocado a OPs
  abertas.
- Processo: PROC-0072, P3 — `PROVEN` (doc 118 §6).
- Owner funcional: Controladoria (conciliação tripla + P7).
- Owner técnico: `api-delpi` + `controllership-finance-api`.
- Produtor oficial: `MATR989` variante analítica — **fonte ausente**
  (`SOURCE_MISSING`, E8); produtor inferido por artefato
  (`PRODUCER_INFERRED_BY_ARTIFACT`).
- Implementação: **`IMPLEMENTED`** (IMPLEMENTATION-009, 29/10) —
  `/closing/work-in-process` + export: motor MATR989 compartilhado com
  o P7 (físico loc-99 + alocado `RE−DE`); `officialMatr989=false`,
  `parityStatus=PENDING` (doc 119 §12). Paridade física rodada 22.
- Homologação: G1–G5 `PASS` empírico; fonte E8 `PENDING`; G6 `PENDING`.

## Fonte e dados

- Artefato: `Material em processo.xlsb` (aba `01-01`, 57.359 linhas,
  Dt.Ref 01/10/2026 16:15).
- Tabelas: SD3 (`RE*`/`DE*` com `D3_OP`), SC2 (estado da OP), SB9 loc 99.
- Grão: **linha física SD3 `RE*`** (não documento); bloco sem OP =
  saldo SB9 do armazém de processo no as_of.
- Eixo: `D3_EMISSAO` ≤ corte; data de referência = competência.
- Capability CLARA: `read(report.work_in_process)`.

## Regras de negócio (doc 85 §8)

- BR-R08-001 grão = linha SD3 `RE*` 1:1 — `PROVEN` (1.501/1.501).
- BR-R08-002 qtde/valor = `D3_QUANT`/`D3_CUSTO1` — `PROVEN`.
- BR-R08-003 população com OP: filial, `D3_OP<>''`, não estornada,
  emissão ≤ corte, `D3_CF ∈ RE0/RE1/RE2/RE9` — `PROVEN`.
- BR-R08-004 OP impressa só se **aberta na data de referência** (sem
  `PR0`, não encerrada) — `PROVEN` (33 OPs com produção no dia excluídas).
- BR-R08-005 saldo por par = Σ`RE*` − Σ`DE*` ≤ corte — `PROVEN`
  (650/650 pares exatos).
- BR-R08-006 bloco sem OP = posição SB9 loc 99 as_of — `PROVEN`
  (569/573 exato; 4 Δ temporais de revalorização explicadas).
- BR-R08-007 **EM PROCESSO do P7 = total MATR989** — `PROVEN`
  (R$355.240,51; loc-99 293.273,088 + alocado 61.967,424).
- BR-R08-009 reuso: `stock_value_historical_sql` `REUSE_PARTIAL`;
  `em_processo_proxy_value` (SB2 corrente) não cobre alocado nem as_of.

## Interpretação

- **EM PROCESSO ≠ armazém 99**: soma físico do armazém de processo
  + material alocado a OPs abertas — decomposição provada.
- Total do artefato = total "EM PROCESSO" do P7 — conciliação exata;
  somar componentes arredondados gera centavo de diferença (artefato de
  arredondamento, não divergência).
- `STALE_EVIDENCE`: linhas sem-OP carregam custo do instante da emissão;
  a SB9 vigente já reflete recálculo posterior — Δ de valor com Δqtd=0
  é revalorização, não erro.
- Medidas: `grandTotal`, `physicalTotal`, `allocatedTotal`; grão
  `product_type` (agregação completa).

## Operação

- Uso: conciliação com P7/R05; investigação de OP aberta antiga.
- Não automatizável: emissão MATR989 oficial; encerramento de OP.
- Comparações: `COMPARABLE` mesma medida entre competências; R03×R08
  `RELATED_REQUIRES_EXPLANATION` (universos SB9 disjuntos); R08×R05
  `INSUFFICIENT_EVIDENCE`.

## Governança

- Evidências: docs 63/64/80 §§41-42/84/85 §8; T-R08-01..05.
- Pendências: E8 (fonte/RPO); semântica intra-dia do corte de OP;
  neteo `DE*` dentro de par vivo (não exercido).
- Limitações: `officialMatr989=false`; proxy SB2 ≠ motor.
- Comparação transversal: suportado (measures/grão registrados no
  catálogo stage-03).
- Referências: doc 85 §8; doc 84; doc 118 §6; doc 119 §12.
