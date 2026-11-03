# R09 — Faturamento × MOD (DLP204)

Versão da ficha: 2.0 · 03/11/2026 · doc 152 + Gate 073.

Estado operacional: `IMPLEMENTED` (`billing-mod-breakdown`); paridade oficial DLP204 pendente.

## Identificação

- Código/nome: **R09 — Faturamento × MOD** (explosão do produto
  acabado faturado em mão de obra direta por estrutura).
- Finalidade: relacionar o faturamento de PA à MOD consumida
  (roteiro/estrutura) — apoio a custos e margem.
- Processo: PROC-0072 — `PROVEN` no catálogo (doc 118 §6).
- Owner funcional: Custos/Controladoria.
- Owner técnico: **api-delpi** (contexto financeiro) — produtor
  `billing-mod-breakdown`.
- Produtor oficial: `DLP204.prw` (acervo, autor Gabriel, 2019) +
  SP `STP_DELPI_FORMA_PRECO_<empresa>` — SP **ausente dos bancos
  acessíveis** (E9); recursão SG1 por nível.
- Implementação: **IMPLEMENTED** — Portal → BFF
  `controllership-finance-api` → api-delpi → TOTVS (read-only).
- CLARA: `read(report.billing_mod_breakdown)` — consulta real
  positiva registrada (doc 152 §6: 2026-09 filial 01, 299 âncoras).
- Homologação: `officialParity=pending` — nunca declarar equivalência
  oficial DLP204.

## Fonte e dados

- Artefato histórico: `Fat x MOD.xlsb` — abas `1-Fl01` e `2-Fl02`.
- Motor operacional vigente (api-delpi): seleção de âncoras PA
  faturado via `SD2010`/`SF4010` com `F4_DUPLIC='S'` e `D2_EMISSAO`
  na competência; expansão SG1 por nível (`COMP` 02/04/06);
  operações/recursos via roteiro congelado SHY (última OP com
  roteiro) com fallback SG2; `Quantidade=G2_TEMPAD`/`HY_TEMPAD`;
  `Horas=quantidade×tempo`; pré-carregamento por filial
  (`_build_branch_anchors`).
- Custos: **tipados** — `source_missing` quando a taxa oficial
  dependente da SP ausente não existe; nunca substituída por zero
  ou inferida.
- Grão: linha MOD por PA-âncora.

## Regras de negócio (doc 85 §9 + implementação)

- BR-R09-001 produtor/variante — `PROVEN`.
- BR-R09-002 parâmetros SX1 `DLP204` — `PROVEN` catálogo.
- BR-R09-003 seleção do PA-âncora: SB1 × ∃ SD2 `F4_DUPLIC='S'` —
  `PROVEN`.
- BR-R09-004 motor de expansão — SP `SOURCE_MISSING`; motor
  operacional reconstituído na api-delpi (G040–G042).
- BR-R09-005 `Seq Comp` = nível da expansão — `PROVEN`.
- BR-R09-006 `Qtd Fat.` = faturamento do PA-âncora propagado —
  `PROVEN`.

## Interpretação

- A CLARA **pode consultar** os dados operacionais via
  `read(report.billing_mod_breakdown)` e **explicar** o modelo
  (âncora PA → MOD por nível de estrutura).
- `Qtd Fat.` repete a quantidade do PA em cada linha MOD — não é
  consumo unitário.
- `source_missing` na taxa de custo é ausência tipada de fonte
  oficial — não é valor zero nem erro do usuário.
- Comparação R09×R10 é par relacionado curado
  (`RELATED_REQUIRES_EXPLANATION`).

## Operação

- Portal: página «Faturamento × MOD» (visão operacional).
- CLARA: `read(report.billing_mod_breakdown)`.
- Comparações: paridade oficial `pending` — divergências medidas são
  drift temporal de revisão de roteiro, não erro.

## Governança

- Evidências: docs 142–144, 152; gates G040–G042.
- Pendências: **E9** — SP `STP_DELPI_FORMA_PRECO_*` não localizada;
  DR-3 homologação oficial pendente.
- Limitações: taxas MOD `source_missing`; paridade não homologada;
  divergências de roteiro por revisão temporal.
- Referências: doc 85 §9; doc 118 §6; docs 120, 142–144, 152.

## Histórico de implementação — não representa o estado atual

As notas abaixo são a trilha de construção (31/10–01/11/2026) e
permanecem por rastreabilidade. Afirmações como «sem endpoint» ou
«report_not_implemented» referem-se ao estado **anterior** à
publicação do produtor e estão superadas.

### Atualização — Gate 040 (01/11/2026)

- `GET /financeiro/billing-mod-breakdown` implementado na api-delpi
  (Slice 1, DR-1/DR-2 APPROVED): âncoras SD2+SF4, explosão SG1
  02/04/06, ops SG2 cadastrais → `SH1.H1_CCUSTO` → `MOD*`,
  `Quantidade=G2_TEMPAD`, `Horas=qtd×tempo`, custos em ausência tipada.
- `officiality=operational_view`, `official_parity=PENDING` (DR-3).
- Paridade live 2026-09: 521 âncoras; 1.395 chaves MOD; QtdFat 100%;
  Quantidade/Horas 84,5% (lacuna SHY roteiro-OP documentada); 3.081
  ausentes / 70 excedentes com causa e owner (doc 142).

### Atualização — Gate 041 (01/11/2026)

- Correções: SG1 compartilhada (G1_FILIAL=''), coluna PA = produto
  explodido, roteiro congelado SHY primário com fallback SG2 —
  `Quantidade=HY_TEMPAD`.
- Paridade 2026-09: 4.659 linhas; 3.694/4.476 chaves (82,5%);
  QtdFat 99,5%; divergência = drift temporal de revisão de roteiro.
- BZ_CUSTD rejeitado como fonte da taxa (SBZ só tem corrente).

### Atualização — Gate 042 (01/11/2026)

- Temporal SHY/OP adotada; bound rejeitado (3.493<3.694).
- Paridade final 2026-09: 4.659 linhas; 3.694/4.476 chaves (82,5%);
  QtdFat 99,6%; Quantidade 82,2%; Horas 81,9%.
- Taxa MOD: SBZ/SB9/custom exauridas — `SOURCE_MISSING` mantido;
  DR-3 pacote de homologação preparado (doc 144).

### Registro anterior (ficha 1.0, 31/10/2026 — SUPERADO)

- Declarava «sem contrato operacional», «CLARA não pode consultar»,
  `report_not_implemented`, «owner técnico nenhum» — **informação
  histórica superada** pela implementação e pela consulta real
  positiva (doc 152 §6).
