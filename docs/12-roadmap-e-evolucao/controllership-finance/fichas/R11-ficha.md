# R11 — Notas Fiscais a Desconsiderar

Versão da ficha: 1.1 · 31/10/2026 · doc 127 Etapa 4 (GATE C — ficha de

Publicação: **release produtivo stage-05** (30/10/2026, srv-api, SHA `297068f1b7`) — serviço reconstruído e paridade verificada em produção; corpus `5bebf07f-a66a-479f-aa2b-e7d0e6c7ea00` (88 fontes / 2.186 itens).
atenção especial).

## Identificação

- Código/nome: **R11 — Notas Fiscais a Desconsiderar** (roster de
  conferência de faturamento).
- Finalidade: listar notas de saída selecionadas pelo critério
  histórico observado para conferência da Controladoria —
  **investigativo, nunca exclusão automática** de CPV/faturamento/DRE.
- Processo: PROC-0072 — `PROVEN` (docs 85 §10, 126).
- Owner funcional: Controladoria.
- Owner técnico: `api-delpi` (`financeiro_billing_exclusion_roster`) +
  `controllership-finance-api` (BFF + CLARA).
- Produtor do artefato: `EDAPP` export SD2 (`Planilha2`, headers SX3
  `D2_*`).
- Implementação: **`IMPLEMENTED`** (stage-02) —
  api-delpi `GET /financeiro/billing-exclusion-roster` (+export CSV/PDF),
  BFF `/closing/billing-exclusion-roster`, página MFE, CLARA
  `read(report.billing_exclusion_roster)`. Paridade live via o próprio
  engine: **11 linhas / R$ 97.462,71 / 11 docs / 3 docs sem item-irmão
  de estoque** (103033, 103199, 103202).
- Homologação: G1–G5 `PASS`; G6 `PENDING`; **E11a/E11b `TO_INVENTORY`**.

## Fonte e dados

- Tabela: `SD2010` (itens de NF de saída) + SF4 (via `OUTER APPLY
  TOP 1`) + SB1/SA1 (enriquecimento por LEFT JOIN).
- Grão: **item SD2**. Chave: `(D2_DOC, D2_ITEM, D2_COD, D2_TOTAL)` —
  11/11 exato. **Errata doc 47:** `Tipo Saida` = `D2_TES`.
- **Eixo: `D2_EMISSAO`** (diferente do eixo de digitação do R10).
- Filial: `D2_FILIAL='01'` na evidência.
- **Seleção histórica observada: grupo `D2_GRUPO='9035'` ∩ TES
  `D2_TES='594'`** — `PROVEN` (11/11, identidade exata com o artefato).
  Em set/2026 os dois predicados coincidem bidirecionalmente; all-time,
  grupo 9035 aparece com outros TES — **a interseção é a evidência, não
  uma regra universal** (E11b).
- Visões: `candidates` (interseção observada — default),
  `out_of_criteria` (linhas relacionadas fora do predicado —
  DV-R11-04), `all`; totalizadores separados, nunca somados.

## Regras de negócio (doc 85 §10 + doc 126 §§14–19)

- BR-R11-001 binding SD2 — `PROVEN`.
- BR-R11-002 seleção 9035∩594 na competência — `PROVEN`.
- BR-R11-003 **custo zero estrutural**: `D2_CUSTO1=0` desde a criação
  (TTAT zero alterações) porque `SF4.F4_ESTOQUE='N'` — TES 594 não
  movimenta estoque → não gera custo de saída; `F4_DUPLIC='S'` gera
  receita/duplicata. **"CPV zero" é condição estrutural esperada, não
  custo faltante nem divergência** — `PROVEN`.
- BR-R11-004 semântica do conjunto: industrialização para terceiros —
  produtos 9035 = serviço/insumo; NF típica tem item-irmão TES 510
  (`F4_ESTOQUE='S'`, custo>0, CFOP 5124) + item 594 (CFOP 5101); 8/11
  casam os dois itens; 3 docs só têm o item 594 — `PROVEN`.
- BR-R11-005 efeito no CPV canônico: contribuição **R$ 0,00** ao
  numerador (CFOP 5101 entra com custo zero) — `PROVEN`; nenhuma
  alteração contratual no CPV.
- BR-R11-006 reuso — `REUSE_PARTIAL`; "desconsiderar" é camada de
  conferência, não predicado da API.
- Divergências DV-R11-01..04: DV-R11-01 bloco `selection`;
  DV-R11-02 `costStatus=structural_zero_expected` (explicativo, nunca
  divergência); DV-R11-03 `POSSIBLE_DIVERGENCE` por documento sem
  item-irmão de estoque; DV-R11-04 visão `out_of_criteria`.
- `affectedCalculation=TO_INVENTORY`; `correctiveAction=
  PENDING_EVIDENCE`; `predicateOfficiality=TO_INVENTORY` (E11b).

## Interpretação

- "Por que esta nota aparece na lista?" — **porque atende ao critério
  histórico observado** (9035∩594 na competência). Isso **não**
  confirma correção fiscal/contábil, não afirma que a nota deve ser
  estornada nem excluída do CPV/DRE — a ficha e o relatório deixam
  explícito: investigativo até E11a/E11b serem resolvidos pelo owner.
- "Por que o custo é zero?" — TES 594 tem `F4_ESTOQUE='N'`: venda sem
  baixa de estoque (faturamento de industrialização) — estrutural,
  esperado; nunca classificar como erro.
- Aumento de notas selecionadas entre competências **não** prova
  aumento de erros fiscais — comparação R11×R11 é de contagem/valor de
  seleção com ressalva do predicado histórico.
- Medidas: `totalValue`, `lineCount`, `documentCount`; grãos `tes`,
  `product_group`; filtros `view`, `tes`, `document`, `product`,
  `product_group`, `customer`.

## Operação

- Uso: conferência mensal do faturamento de industrialização; apoio à
  decisão contábil/fiscal humana.
- Conferência no Protheus: localizar NF por `filial+documento+série`;
  verificar itens, TES (594 vs item-irmão 510), `F4_ESTOQUE`, grupo de
  produto e CFOP.
- Não automatizável: estorno/exclusão de NF, decisão de
  desconsiderar na apuração — **nenhuma** ação no ERP.
- Comparações: `COMPARABLE` entre competências na mesma visão/medida
  (com ressalva do predicado); R10×R11 `RELATED_REQUIRES_EXPLANATION` —
  cruzamento documental somente por `filial+documento+série` completos
  (eixos de data distintos: digitação × emissão — mesma NF pode cair em
  competências diferentes; número de documento isolado não comprova
  relação).

## Governança

- Evidências: docs 67, 85 §10, 126 §§14–19, 127 Etapa 2; paridade live
  `bf8f2a0d58`.
- Decisões pendente: **E11a** (apuração consumidora + ação corretiva),
  **E11b** (predicado oficial — grupo vs TES vs interseção), G6; vídeo
  54:44 não demonstra R11 (`INCONCLUSIVE` no gate-020).
- Limitações: `view=candidates` default; `out_of_criteria` vazio na
  evidência (visão testada, sem população live em 2026-09).
- Referências: doc 85 §10; doc 126; doc 121; ficha R10.
