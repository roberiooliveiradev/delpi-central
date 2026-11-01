# R09 — Faturamento × MOD (DLP204)

Versão da ficha: 1.0 · 31/10/2026 · doc 127 Etapa 4.

Publicação: ficha **publicada no corpus produtivo** `5bebf07f-a66a-479f-aa2b-e7d0e6c7ea00` (release stage-05, 30/10/2026) — **sem contrato operacional**; estado PENDING_CONTRACT/EXTERNAL inalterado.

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

## Atualização — Gate 040 (01/11/2026)

- `GET /financeiro/billing-mod-breakdown` implementado na api-delpi
  (Slice 1, DR-1/DR-2 APPROVED): âncoras SD2+SF4, explosão SG1
  02/04/06, ops SG2 cadastrais → `SH1.H1_CCUSTO` → `MOD*`,
  `Quantidade=G2_TEMPAD`, `Horas=qtd×tempo`, custos em ausência tipada.
- `officiality=operational_view`, `official_parity=PENDING` (DR-3).
- Paridade live 2026-09: 521 âncoras; 1.395 chaves MOD; QtdFat 100%;
  Quantidade/Horas 84,5% (lacuna SHY roteiro-OP documentada); 3.081
  ausentes / 70 excedentes com causa e owner (doc 142).
- Owner técnico: `api-delpi` (financeiro). Evidências: doc 142.

## Atualização — Gate 041 (01/11/2026)

- Slice 1 já estava publicado em main (7ca041a19b); push SSH segue
  bloqueado nesta estação (publickey) — novos commits locais pendentes.
- Correções comprovadas: SG1 compartilhada (G1_FILIAL=''), coluna PA
  = produto explodido, roteiro congelado SHY (última OP com roteiro)
  primário com fallback SG2 — `Quantidade=HY_TEMPAD`.
- Nova paridade 2026-09: 4.659 linhas; 3.694/4.476 chaves (82,5%);
  QtdFat 99,5%; 983 ausentes/1.165 excedentes por drift temporal de
  revisão de roteiro (medido, com owner).
- BZ_CUSTD REJEITADO como fonte da taxa (0/120; SBZ só tem corrente).
- Custos continuam source_missing (DR-2); DR-3 pendente. Evid.: doc 143.

## Atualização — Gate 042 (01/11/2026)

- Git: G041 já publicado em main (0acdf32b6a); SSH `publickey`
  bloqueia novos pushes desta estação (bloqueio formal, sem perda).
- Temporal SHY/OP: última OP com roteiro congelado (run_date=hoje)
  adotada; bound ≤07/10 rejeitado (3.493<3.694). Fallback SG2 por linha.
- Paridade final 2026-09: 4.659 linhas; 3.694/4.476 chaves (82,5%);
  QtdFat 99,6%; Quantidade 82,2%; Horas 81,9%; 782 aus./965 exc. —
  divergência = drift temporal de revisão de roteiro.
- Taxa MOD: SBZ/SB9/custom exauridas — SOURCE_MISSING mantido (DR-2);
  próximo: RPO/backups + Controladoria.
- DR-3: pacote de homologação preparado (doc 144). BFF: NOT_READY.

## Atualização — Gates 043/044 (01/11/2026)

- BFF R09: GET /closing/competences/{period}/billing-mod-breakdown na
  controllership-finance-api — passthrough S2S governado, officiality
  operational_view + officialParity pending, evidência histórica de
  paridade (G042, escopo 2026-09), ausência tipada preservada. 10/10
  testes; regressão 33 pass.
- CLARA: capability read(report.billing_mod_breakdown) registrada no
  semantic bridge (paridade 1:1 com a rota BFF, sem recálculo).
- Integração live BFF→api-delpi e deploy produtivo: NÃO executados —
  SSH público indisponível na estação (publickey GitHub); WSL/Docker
  fora na sessão (mock ≠ integração). Canal credenciado publica.
- Portal MFE: pendente para gate dedicado (não implementado).
- DR-3 segue pendente; custos source_missing. Verdict: ACCEPT_WITH_RESIDUAL.

## Atualização — Gate 045 (01/11/2026)

- Portal MFE: página R09 «Faturamento × MOD» implementada na rota
  contextual monthly-closing/{period}/reports/billing-mod-breakdown —
  filtro de filial, banner de visão operacional/paridade pendente,
  evidência histórica, limitações e âncoras com linhas MOD (ausências
  tipadas renderizadas, nunca zero). API client billingModBreakdownApi
  espelha o padrão de costClosingStateApi.
- Build/typecheck do plugin: ENV-BLOCKED (caminho UNC impede npx/tsc
  nesta estação; WSL/Docker fora). Código segue o padrão dos irmãos;
  validação pendente em ambiente funcional.
- Deploy produtivo e validação CLARA/Portal live: NÃO executados —
  SSH público indisponível na estação (publickey). Canal credenciado.
- DR-3 pendente; custos source_missing. Verdict: ACCEPT_WITH_RESIDUAL.

## Atualização — Gate 046 (01/11/2026) — DEPLOY PRODUTIVO EXECUTADO

- Publicação: todo o código R09 confirmado em origin/main (producer
  7ca041a19b, G041 0acdf32b6a, G042 92c2ee44f8, BFF dd6552526d, CLARA
  d1987532fa, MFE 8607173b56 + fix 586073e9b5). SSH GitHub funcional.
- Typecheck MFE real (WSL): corrigidos variant/props/REPORT_META; 1 erro
  PRÉ-EXISTENTE em CostClosingStatePage (contrato legado ClosingHero —
  fora do escopo R09, owner plugins).
- Homologação live local: api-delpi rebuildado com produtor R09
  (healthy); 401 sem/com token inválido; BFF 401 noauth; READ_ACTIONS
  contém report.billing_mod_breakdown.
- DEPLOY PRODUTIVO (srv-api): git pull --no-rebase → ae8c587c; rebuild
  api-delpi + controllership-finance-api + controllership-finance via
  up-prod-sequential.sh. Verificado em prod: producer file presente,
  health 200, BFF módulo + registry OK, gateway 401 noauth, serviços
  compartilhados sem regressão.
- Cadeia positiva (usuário autenticado) e validação CLARA via ChatGPT:
  aguardam credencial de usuário/execução do PO — NÃO classificadas.
- DR-3 pendente; custos source_missing. Verdict: ACCEPT_WITH_RESIDUAL.

## Atualização — Gate 047 (01/11/2026) — 503 corrigido em produção

- Causa raiz PROVEN: DELPI_API_TIMEOUT=30 (BFF→api-delpi) < ~150-210s
  do produtor (logs: status=200 duration_ms=149157/212481). Classe:
  configuração/timeout.
- Fix: timeout_seconds=300 dedicado na rota R09 (proxy nginx 300s);
  produtor e regras inalterados. 10/10 testes. Deploy rebuild BFF —
  healthy, fix verificado no container.
- Consulta positiva real pendente de credencial de usuário (PO/ChatGPT).
