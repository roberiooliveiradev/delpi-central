# R09 — Faturamento × MOD (DLP204)

Versão da ficha: 1.0 · 31/10/2026 · doc 127 Etapa 4.

## Identificação

- Código/nome: **R09 — Faturamento × MOD** (explosão de produto acabado
  faturado em mão de obra direta por estrutura).
- Finalidade: relacionar o faturamento de PA à MOD consumida (roteiro/
  estrutura) — apoio a custos e margem.
- Processo: PROC-0072 — `PROVEN` no catálogo (doc 118 §6).
- Owner funcional: Custos/Controladoria.
- Owner técnico: nenhum implementado (candidato `api-delpi`).
- Produtor oficial: `DLP204.prw` — `SOURCE_AVAILABLE` no acervo
  (autor Gabriel, 2019); `CODE_DEPLOYED` não vinculado (E9).
- Implementação: **`TARGET_ONLY`** — modelo físico `PROVEN` (rodada 24),
  **sem contrato implementado** (doc 118 §6; E9/G5).
- Homologação: G4 `PASS`, G5 `INCONCLUSIVE`.

## Fonte e dados

- Artefato: `Fat x MOD.xlsb` — abas `1-Fl01` (2.459) e `2-Fl02` (2.017);
  4.476 linhas, sem totais persistidos.
- Motor: `DLP204.prw` (FWMSEXCEL, uma aba por filial) + SP
  `STP_DELPI_FORMA_PRECO_<empresa>` — **SP ausente de todos os bancos
  acessíveis** (objeto legado 2019 — E9); recursão SG1 por nível.
- Grão: linha MOD por PA-âncora (nível 0/1/2 → `COMP` 02/04/06).
- Eixo: `D2_EMISSAO` ∈ competência; TES com `F4_DUPLIC='S'`; ambas
  filiais; `Exibir MP?=Não` (sem linhas 03/05/07).
- Capability CLARA: **nenhuma** — relatório sem contrato.

## Regras de negócio (doc 85 §9)

- BR-R09-001 produtor/variante — `PROVEN` (fonte + artefato).
- BR-R09-002 parâmetros SX1 `DLP204` — `PROVEN` catálogo / inferido
  emissão (competência 09/2026, ambas filiais, MP=Não).
- BR-R09-003 seleção do PA-âncora: SB1 na faixa **e** ∃ SD2 com TES
  `F4_DUPLIC='S'` — `PROVEN` (WHERE literal; 1.767 âncoras).
- BR-R09-004 motor de expansão — `SOURCE_MISSING` (SP) / contrato de
  saída `PROVEN` por artefato.
- BR-R09-005 `Seq Comp` = nível da expansão — `PROVEN`.
- BR-R09-006 `Qtd Fat.` = faturamento do PA-âncora propagado — `PROVEN`.

## Interpretação

- A CLARA pode **explicar** o modelo (âncora PA faturada → MOD por
  nível de estrutura) mas **não pode consultar** dados — sem endpoint.
- `Qtd Fat.` repete a quantidade do PA em cada linha MOD — não é
  consumo unitário; interpretar junto de `Quantidade`/`Custo Unitario`.
- Comparação R09×R10 é par relacionado curado
  (`RELATED_REQUIRES_EXPLANATION`) **quando o R09 tiver contrato** —
  hoje o sujeito retorna `report_not_implemented` e a comparação sai
  parcial/honesta, nunca com valor inventado.

## Operação

- Sem operação Portal/CLARA disponível — conhecimento documental apenas.
- Comparações: `INSUFFICIENT_EVIDENCE`/parcial — motor stage-03 marca
  `report_not_implemented`.

## Governança

- Evidências: docs 65/85 §9; fonte `DLP204.prw` no acervo.
- Pendências: **E9** — localizar/reconstruir `STP_DELPI_FORMA_PRECO_*`;
  versão RPO; G5; decisão de contrato (doc 120 pacote 016).
- Limitações: não afirmar totais de MOD como apuração oficial — SP
  interna não verificada.
- Referências: doc 85 §9; doc 118 §6; doc 120; doc 121.
