# CF-PROC0072 — Decisões do PO para R09 e direção do Gate 038

Data: 2026-11-01. Autoridade: manifestação explícita do PO nesta conversa. Escopo: R09 Faturamento × MOD (DLP204); resíduo IAM do Ciclo 3.

## Decisões confirmadas

- **D2 — APPROVED**: preparar R09 como `OPERATIONAL_VIEW`, com `official_parity=PENDING` até paridade informacional item a item com TOTVS/artefato. Não equiparar cobertura de linhas a paridade de informação; não declarar valores oficiais sem homologação funcional.
- **D3 — APPROVED (boundary)**: cálculos e SQL canônicos TOTVS na `api-delpi`; BFF `controllership-finance-api` orquestra, governa AuthZ e projeta; CLARA/MFE consomem contrato governado, sem cálculo paralelo e sem browser → api-delpi. Permissões existentes somente, com effective permissions fail-closed.
- **D4 — APPROVED**: aceitar encerramento técnico do Ciclo 3 com negativo sem `controllership-finance.access` ainda `INCONCLUSIVE`, owner IAM, ação de provisionamento e teste obrigatórios; não converter em PASS e não usar como dispensa de segurança para a próxima publicação.
- **D1 — DIRECTION APPROVED; DESIGN/IMPLEMENTATION CONDITIONAL**: estudar primeiro recuperação da SP `STP_DELPI_FORMA_PRECO_<empresa>` em RPO, backups e acervos autorizados; estudar as rotas atuais da `api-delpi` de estrutura e onde-usado, a viabilidade de combinação/reuso e pequenos ajustes compatíveis para maximizar a **paridade informacional** com relatórios TOTVS e a realidade operacional DELPI, **não paridade visual**. Se o reuso resultar em alteração material de semântica, custo/performance/consumidores, ou for inadequado, propor rota específica `/financeiro/billing-mod-breakdown` na `api-delpi` e integração pela BFF. O PO autoriza o estudo e a direção de avanço incremental, **não aprova automaticamente breaking change, algoritmo de formação de custo sem prova, contrato definitivo, escrita ERP ou deploy**. Apresentar opções, impacto, diff e teste antes da implementação material.

## Fatos e invariantes

- Fonte: `docs/13-fontes-totvs-protheus/06. Financeiro/DLP204.prw`; chama `STP_DELPI_FORMA_PRECO_<emp>` e consome `TRBMOD`. SP interna não localizada nos bancos acessíveis: `SOURCE_MISSING_WITH_SEARCH_SCOPE`, não ausência universal.
- Referência histórica `Fat x MOD.xlsb`: 2.459 linhas filial 01 + 2.017 filial 02 = 4.476; 1.767 PA âncoras. Trata-se de cobertura de artefato, não paridade oficial.
- `Qtd Fat.` propagada da âncora; investigar fallback `TRBMOD->QTDFAT == 0` no PRW e distinguir zero legítimo, fallback legado e fonte ausente.
- Campos da SP incluem `PA`, `COMP`, `QTDFAT`, `G2_TEMPAD`, `CUSTO_UNIT`, `CUSTO_TOTAL`, `CUSTOPROD`, `HORAS`; SG1 puro não demonstra equivalência aos cálculos SP.
- `OPERATIONAL_VIEW != OFFICIAL_PARITY`; `SOURCE_MISSING != ZERO`; sem inferência de homologação humana.

## Gate 038 — Estudo de viabilidade e início condicionado

1. Confirmar HEAD/status, instruções oficiais, .cursor, ADRs, ficha R09, contrato atual, owners e consumidores.
2. Inventariar endpoints de estrutura/onde-usado da api-delpi, parâmetros, producers/consumers, semântica, performance e segurança.
3. Investigar SP em fontes autorizadas e registrar escopo negativo; analisar chamadas e schema TRBMOD.
4. Fazer matriz de paridade **informacional** campo a campo com `Fat x MOD.xlsb` e dados reais TOTVS (grão, quantidades, horas, custos, níveis, nulos, competência/filial, filtros).
5. Comparar estratégias: A reuso/composição sem alteração de semântica; B pequenas extensões compatíveis; C nova rota específica. Medir gaps, riscos, performance, efeitos em consumidores e testes de não regressão.
6. Elaborar design e contratos completos, RQ/AC e plano de slices; **gate transversal explícito** antes de código/runtime. Alteração material de API/ownership/contrato/depreciação/persistência exige `DECISION_REQUIRED` específico e aprovação do PO.
7. Após autorização explícita da opção contratual, executar apenas o slice mínimo aprovado, primeiro em homologação, com testes comparativos e negativos; deploy produtivo requer gate de release separado e autorização.
8. Atualizar ledger e Help no mesmo gate de feature; registrar owners IAM e Controladoria (homologação informacional).

## Estado

Decisões D2, D3 e D4: **APPROVED pelo PO**. D1: **diretriz aprovada; escolha final da arquitetura e implementação material ainda sujeitas ao estudo/gate**. Nenhuma alteração de runtime por este documento.
