# R10 — Notas/Despesas por Centro de Custo

Versão da ficha: 1.2 · doc 127 Etapa 5 (correção editorial §4.1:
universo `calculation` definido como 686−exclusões=353, prova doc 85
§10). Anterior: 1.1 · 31/10/2026 · doc 127 Etapa 4 (GATE C — ficha de
atenção especial).

## Identificação

- Código/nome: **R10 — Notas/Despesas por Centro de Custo** (apuração +
  investigação de despesas do fechamento).
- Finalidade: apurar despesas do mês por centro de custo para rateio/
  classificação contábil e investigar lançamentos que merecem
  conferência — **dois universos estritos, nunca somados**.
- Processo: PROC-0072 — `PROVEN` (docs 85 §10, 126).
- Owner funcional: Controladoria (operadora do artefato EDAPP).
- Owner técnico: `api-delpi` (`financeiro_cost_center_expenses`) +
  `controllership-finance-api` (BFF + CLARA).
- Produtor do artefato: `EDAPP` export SD1 monotabela
  (`SCAGQGA0.XML`, headers SX3 `D1_*`).
- Implementação: **`IMPLEMENTED`** (stage-01) —
  api-delpi `GET /financeiro/cost-center-expenses` (+export CSV/PDF),
  BFF `/closing/cost-center-expenses`, página MFE, CLARA
  `read(report.cost_center_expenses)`. Paridade live TOTVS 2026-09 f01:
  **353 linhas / R$ 169.704,12 / 139 docs / 46 buckets de CC**.
- Homologação: G1–G5 `PASS`; G6 `PENDING`; residuais E10a/E10b.

## Fonte e dados

- Tabela: `SD1010` (itens de NF de entrada) + SF4 (TES) + CTT (centro
  de custo, via `OUTER APPLY TOP 1` — filial específica, fallback
  filial-branca — snapshot **vigente**, não prova validade histórica).
- Grão: **item SD1** (linha física). Chave de vínculo do artefato:
  `(D1_DOC, D1_ITEM, D1_COD, D1_TOTAL)` — 353/353 exato.
- **Eixo de competência: `D1_DTDIGIT` (data de digitação)** — `PROVEN`:
  80 das 353 linhas têm `D1_EMISSAO` fora de setembro; filtro narrado
  pelo owner ("data de digitação no mês") + prova física.
- Filial: `D1_FILIAL` — dimensão de dado, não fronteira RBAC.
- Universos:
  - `calculation` — universo da apuração: **353 linhas** — as 686 linhas
    SD1 em competência **menos** as exclusões BR-R10-003/004/005
    (13 TES, 302 MP, 6 benefícios) — identidade exata com o artefato:
    R$ 169.704,12 / 139 documentos / 46 buckets de CC (`PROVEN` live).
  - `investigation` — demais linhas em competência (excluídas da
    apuração, mantidas para conferência).
  - **Invariante: nunca somar nem comparar totais dos dois universos.**

## Regras de negócio (doc 85 §10 + doc 126 §§14–19)

- BR-R10-001 binding SD1 — `PROVEN`.
- BR-R10-002 eixo `D1_DTDIGIT` — `PROVEN`.
- BR-R10-003 exclusão por TES — `PROVEN` conjunto físico: **13 TES**
  `{001,003,016,020,030,040,080,083,085,120,159,204,318}` excluídos,
  zero falso-positivo/negativo; lista narrada "12 tipos" → divergência
  12-vs-13 registrada (`PENDING` confirmação formal — LISTA-13).
- BR-R10-004 exclusão de matéria-prima: `D1_TP='MP'` fora — `PROVEN`
  (302/302).
- BR-R10-005 coparticipação plano de saúde fora: 6 linhas TES 046,
  tipo GG, sem CC, grupo benefícios — `PROVEN` (R$ 6.990,44; regra é a
  parcela do **colaborador**, não "toda coparticipação" → E10).
- BR-R10-006 classificação Direto/Indireto/Adm — `AS-IS` **manual**
  sobre o export (coluna sem título; não é campo SD1 nem CTT);
  implementação expõe `costClass=UNCLASSIFIED` por D-01 — **não
  inferir de prefixo de CC**; catálogo homologado = **E10a** pendente.
- BR-R10-007 view `vw_fin_despesas_centro_custo` — `REUSE_PARTIAL`
  (eixo `D1_EMISSAO`, sem exclusões: seleção diferente — **não
  transplantar**).
- Divergências DV-R10-01..06 (doc 126): DV-R10-01/02/04 implementadas
  como `POSSIBLE_DIVERGENCE` + orientação de conferência; DV-R10-03/06
  declaradas e **bloqueadas por E10a** (`rulesCatalog.implemented=false`).
- Findings nunca são `CONFIRMED_ERROR`: `affectedCalculation` honesto,
  `correctiveAction=PENDING_EVIDENCE`.

## Interpretação

- **Apuração ≠ investigação**: `calculation` é a seleção EDAPP
  reconstruída (13 TES fora + MP fora + benefícios fora);
  `investigation` é o resto da competência — linha em `investigation`
  **não é** despesa errada; é linha fora do critério do relatório.
- "Por que esta matéria-prima aparece no investigativo?" — porque
  `D1_TP='MP'` é excluída da apuração por regra (BR-R10-004), não por
  erro; a linha segue disponível para conferência. A CLARA explica a
  regra e o motivo de conferência, sem afirmar classificação errada.
- `UNCLASSIFIED` significa "sem classe homologada" (E10a), não
  "incorreto".
- CTT resolve nome vigente — um CC renomeado/excluído aparece com o
  nome atual; não prova que era válido na data do lançamento.
- Medidas: `totalValue`, `lineCount`, `findingCount`, `documentCount`;
  grãos `cost_center`, `product_type` (agregações completas); filtros
  `universe`, `cost_center`, `tes`, `document`, `product`, `view`.

## Operação

- Uso: apuração mensal de despesas para a contabilidade; investigação
  de lançamentos atípicos; findings sustentam pendências P4.
- Conferência no Protheus: localizar a NF por `filial+documento+série`
  + item (SD1010); verificar TES (SF4), CC da linha e tipo do produto.
- Não automatizável: classificação Direto/Ind/Adm (E10a), correção de
  lançamento no ERP, aceite.
- Comparações: `COMPARABLE` **dentro do mesmo universo** entre
  competências (totais, buckets de CC, contagens de findings —
  dependendo das mesmas regras ativas); `calculation`×`investigation`
  → `NOT_COMPARABLE` (`r10_universe_mismatch`); R10×R11 →
  `RELATED_REQUIRES_EXPLANATION` com cruzamento documental por chave
  completa.

## Governança

- Evidências: docs 56 Reg.17/18, 77, 85 §10, 126 §§14–19, 127 Etapa 1;
  paridade live `eb91058740`.
- Decisões: D-01 (classe manual→UNCLASSIFIED), D-08; **E10a** catálogo
  homologado CC→classe `DECISION_REQUIRED`; **E10b** persistência de
  revisão `DECISION_REQUIRED`; CTT histórico `TO_INVENTORY`; LISTA-13
  `PENDING`; G6 `PENDING`.
- Limitações: `rulesCatalog` declara quais DVs estão ativas por
  competência — comparação de findings exige mesmas regras ativas.
- Referências: doc 85 §10; doc 126; doc 121; ficha R11.
