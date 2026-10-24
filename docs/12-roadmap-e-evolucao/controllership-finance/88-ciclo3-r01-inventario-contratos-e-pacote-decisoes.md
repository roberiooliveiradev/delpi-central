# Documento 88 — Ciclo 3 · R01 — Inventário de contratos, escopo read-only e pacote de decisões

**Rodada:** `CF-C3-01-READONLY-CLOSING-INVENTORY-AND-DECISION-PACK-001`
(rodada 30 — 2026-10-24)
**Modalidade:** READ → VERIFY → INVENTORY → CLASSIFY → PROPOSE →
DOCUMENT → REPORT. `IMPLEMENTATION_AUTHORIZED=NO` — nada criado, nenhuma
rota/componente/migration proposta como aprovada.
**Baseline:** `d9c7f5f56c` (após doc 86). Authority: doc 87 (abertura
C3), doc 86 (encerramento C2), docs 48/49 (contratos-target settlements e
stock-inventory), docs 50–53 (UX das páginas de fechamento), doc 24
(páginas comuns), doc 30 (reuse map UI).

> Resultado: inventário verificável + pacote `C3-D01..D06` para o PO.
> Nenhuma opção aqui é decisão tomada nem contrato autorizado.

---

## 1. Inventário da plataforma — estado real no HEAD

### 1.1 Superfície já implementada (descoberta material da rodada)

Contrariando a hipótese implícita de "scaffold ainda não autorizado", o
HEAD já contém uma fatia funcional read-only, construída nas rodadas de
documentação/UX dos docs 48–53:

**BFF `controllership-finance-api`** (`controllership_finance_app/`):

| Rota BFF | Upstream api-delpi | operation_id |
|---|---|---|
| `GET /viewer-context` | Core `/me` (via middleware) | `get_viewer_context` |
| `GET /closing/financial-settlements` | `/financeiro/settlements/payables` \| `/receivables` | `get_closing_financial_settlements` |
| `GET /closing/financial-settlements/summary` | `/financeiro/settlements/summary` | `get_closing_financial_settlements_summary` |
| `GET /closing/stock-inventory` | `/financeiro/stock-inventory` | `get_closing_stock_inventory` |
| `GET /health` | — | health |

Segurança já vigente (lido no código, `closing_routes.py`,
`api_delpi_gateway.py`, `viewer_context_routes.py`):
- `principal_type == "user"` obrigatório; service token rejeitado;
- `controllership-finance.access` via **effective permissions do Core**
  (middleware popula; `rbac_unavailable` → 503 fail-closed);
- delegação do Bearer humano + credencial S2S própria do cliente
  `controllership-finance-api` (`X-Delpi-Service-Authorization`), ADR-010;
- escopo de dataset fail-closed no producer — `scope_unavailable` é
  retransmitido como 403 tipado, nunca convertido em autorização;
- envelope `{success,message,data,meta}` preservado sem fabricar totais.

**api-delpi** (contexto owner das regras TOTVS):

| Rota | Fonte física | Guarda |
|---|---|---|
| `/financeiro/stock-inventory` | `SB9010`+`SB1010` (snapshot por `B9_DATA`) | S2S `stock-inventory.read`, cliente allow-listed `controllership-finance-api`; `require_stock_inventory_scope` fail-closed |
| `/financeiro/settlements/payables\|receivables\|summary` | `SE5` (baixas) | S2S + Bearer delegado |
| `/financeiro/despesas-centro-custo/*` | view Financeiro | superfície existente (`REUSE_PARTIAL` p/ R10) |
| `/supplies/cpv` | SD2 vivo | `REUSE_PARTIAL` (sem `as_of`) |
| Suprimentos: `inventory_accuracy_sql`, `non_moving_stock_sql`, `stock_value_*` | SB9/SD3/SB2 | leem `MAX(B9_DATA)` como `last_closing` internamente — capacidade existe, não exposta como contrato de competência |

Semântica do stock-inventory (lida em `get_stock_inventory_use_case.py`):
presença do snapshot **antes** dos filtros → `source_missing` nunca se
disfarça de total zero; `branchesAvailable`/`branchesMissing` por filial;
status `available|incomplete|no_matching_items|source_missing`. Isso já
materializa a distinção "snapshot ausente ≠ valor zero" do PROC-0072.

**MFE `plugins/controllership-finance`** (`src/`):
- `PluginShell` + `SHELL_NAV_ITEMS` (hoje: apenas **Início**; ordem
  canônica doc 24 reservada), `ViewerContext`, busca Ctrl+K no conteúdo;
- `features/home/HomePage` + recentes;
- `features/closing/FinancialSettlementsPage` (R01/R02) e
  `StockInventoryPage` (P7/SB9) com `ClosingHero`, filtros, tabela de
  dados com densidade/resize, tooltips de ajuda (`helpTooltips.ts`);
- rotas no manifest: `/`, `/closing/financial-settlements`,
  `/closing/stock-inventory` (`showInMenu:false` — páginas de fundo);
- testes: `manifestContract.structural.test.mjs`, suites das páginas e
  do BFF (`test_closing_*`, `test_viewer_context`, `test_api_delpi_s2s_gateway`).

### 1.2 Padrão dos demais Portais

Manifest `supplies` (referência): `/apps/supplies`, `/overview`,
`/my-tasks`, rotas de domínio, `/administration`, `/help` — confirma a
convenção doc 24 (Início, Visão geral, Sala de interação, Minhas tarefas,
Administração, Ajuda; usuário como deep route). O MFE CF já está alinhado
estruturalmente; as páginas comuns restantes são **rotas futuras**, não
duplicações.

### 1.3 Componentes `@delpi/plugin-ui`

Categorias exportadas (HEAD): `actions, activity, bpmn, charts,
collaboration, composer, conversation, data, deck, diagram, directory,
displayFormat, document, feedback, forms, help, layout, markdown, menu,
navigation, org, preview, ribbon, rich-text, shape, signature, tasks`.
O MFE já consome `data` (tabela), `feedback`, `forms` (filtros),
`help`, `layout`, `navigation` — padrão confirmado; nenhum componente
novo necessário para a jornada candidata §6.

## 2. Inventário de dados da Central de Fechamento

| Necessidade | Owner | Fonte física | Contrato hoje | Classe |
|---|---|---|---|---|
| Última competência fechada (`MV_ULMES`) | api-delpi | `SX6` por filial | **não existe** | `TARGET` — ver C3-D04 |
| Competências disponíveis p/ consulta | api-delpi | `SB9010.B9_DATA` distintas (`MAX(B9_DATA)` já usado internamente em supplies) | não existe como contrato | `TARGET` |
| Snapshot mensal (produto×armazém×qtd×valor) | api-delpi | `SB9010`+`SB1010` | `get_financeiro_stock_inventory` | `REUSE_CONFIRMED` |
| Baixas a pagar/receber (R01/R02) | api-delpi | `SE5` | `settlements/payables|receivables|summary` | `REUSE_CONFIRMED` |
| Histórico/status do wizard Acompanha Custos | TI/ERP→api-delpi | **tabela física não identificada** (lista `Fechamentos` existe na UI Protheus; writer E5) | não existe | `PENDING_EVIDENCE` → `TARGET` |
| Estado técnico do fechamento (etapas/andamento) | api-delpi | nenhuma persistência de estado do processo identificada | não existe | `TARGET` |
| Homologação funcional | Controladoria | **processo humano — sem fonte sistêmica** | nunca será sistêmico sem decisão | `DECISION_REQUIRED` (C3-D05) |
| CPV mensal vivo | api-delpi/Suprimentos | `SD2` | `GET /supplies/cpv` | `REUSE_PARTIAL` (corrente, sem `as_of`) |
| Reconciliações oficiais (R05–R11) | api-delpi | SD1/SD2/SD3/SC2/SB9 | parcial (despesas-CC, cpv) | `REUSE_PARTIAL`/`TARGET` |
| Notas por centro de custo (R10) | Financeiro/api-delpi | `vw_fin_despesas_centro_custo` (SD1) | existe | `REUSE_PARTIAL` (448 linhas ≠ 353 oficiais — taxonomia E10) |

## 3. Mapa de bounded contexts

`consumer → owner → contrato → dado → regra → segurança` já implementado
na cadeia existente e a preservar:

```
MFE controllership-finance
→ BFF controllership-finance-api   (human Bearer + effective access via Core)
→ api-delpi                        (S2S client-credentials próprio + Bearer delegado;
                                    scope de dataset fail-closed)
→ Protheus (SB9/SE5/SB1)           (somente leitura)
→ Core API                         (effective permissions — nunca do JWT)
```

`strategic-indicators-api`: metas/indicadores — nenhuma necessidade do
MVP de fechamento mapeada (`NOT_EQUIVALENT` por ora). `controllership-
finance-api` é orquestradora de contratos do Portal; **não** é owner de
regra TOTVS — novas leituras (ex.: `MV_ULMES`) pertencem à api-delpi
(Frente D, C3-D04).

## 4. Estados do fechamento — modelagem candidata (C3-D02)

O Ciclo 2 separou cinco estados; a plataforma já expõe três deles com
fonte verificável:

| Estado | Fonte de verdade | Condição verificável | Disponível? |
|---|---|---|---|
| Cálculo executado | TTAT `MATA330`/`MATA280` + lista `Fechamentos` | execução datada | parcial — TTAT não é contrato |
| Resultado produzido | artefatos/valores calculados | `Analise.xlsx`↔SB9 (histórico) | indireto |
| Fechamento persistido | `SB9010` por `B9_DATA`+filial | `branchesAvailable`/`source_missing` | **sim** (contrato vigente) |
| Cutoff avançado | `SX6.MV_ULMES` | valor por filial | dados provados, contrato ausente |
| Conferido/homologado | **aceite humano da Controladoria** | registro de aceite | **não é dado sistêmico** |

Opções para a UI (detalhadas em §7, C3-D02):
- **A (recomendada):** trilha separada `calculo → persistencia →
  conferencia → homologacao`, cada nó com fonte própria e estado
  `indisponivel|parcial|nao_verificado`. Nunca colapsar em `fechado`.
- **B:** estado único derivado — rejeitada como semântica pública porque
  equipararia `MV_ULMES`/SB9 a G6.

## 5. RQ/AC candidatos — primeira jornada read-only

Jornada hipótese (não aprovada): selecionar competência → filial/escopo
autorizado → consultar estado disponível → evidências e pendências.

| RQ | Objetivo | Dado/contrato | Estado | AC principal |
|---|---|---|---|---|
| RQ-C3-01 | Selecionar competência dentre as disponíveis | `B9_DATA` distintas (contrato novo na api-delpi) ou período livre | `TARGET` | AC: lista ≥1 competência; ausência → `source_missing` explícito |
| RQ-C3-02 | Selecionar filial dentro do escopo autorizado | `branch` `all\|01\|02` (já vigente) | `PROVEN` | AC: filial fora de escopo → 403 `scope_unavailable` |
| RQ-C3-03 | Visão do snapshot da competência | `stock-inventory` | `PROVEN` | AC: totais do universo completo; `branchesMissing` visível |
| RQ-C3-04 | Exibir marcador de último fechamento | `MV_ULMES` | `TARGET` | AC: marcador rotulado "técnico", nunca "homologado" |
| RQ-C3-05 | Distinguir estado técnico de homologação | composição §4 | `DECISION_REQUIRED` | AC: UI nunca afirma aceite sem fonte |
| RQ-C3-06 | Baixas financeiras por período | `settlements` | `PROVEN` | AC: payable/receivable + summary; erros tipados |
| RQ-C3-07 | Mensagens de indisponibilidade | statuses existentes | `PROVEN` | AC: `source_missing`/`incomplete`/erro S2S com copy PT-BR |
| RQ-C3-08 | Help contextual | `helpTooltips` + página Ajuda | `PROVEN`/parcial | AC: ajuda acompanha cada superfície nova |
| RQ-C3-09 | Acessibilidade/responsivo | plugin-ui | `PROVEN` | AC: teclado/foco, claro/escuro, mobile |

Cada RQ amarra: R-ID de origem (R01–R03/R15), BR do doc 85, contrato,
owner e teste (BFF route test + página). Nenhum AC exige dado sem fonte
identificada.

## 6. Wireframe textual — página candidata "Central de Fechamento"

Rota candidata (não registrada): `/apps/controllership-finance/closing`
— visão consolidada que hoje só tem deep-routes.

```
[Hero: título + competência selecionada + filial + dataAsOf]
[Faixa de estado técnico: persistido(parcial/completo) | cutoff MV_ULMES |
 conferência | homologação = "não informado" até C3-D05]
[Cards KPI: total histórico, itens, filiais disponíveis/ausentes]
[Abas/links: Estoque (P7) → stock-inventory | Baixas → settlements |
 Evidências → futuro]
[Mensagens: source_missing / incomplete / 403 scope / 503 origem]
```

Reuso UI direto: `layout` (hero/stack), `data` (tabela), `feedback`
(alertas), `forms` (seletores), `help` (tooltips), `navigation`.
Capacidades ausentes: nenhuma crítica identificada para o recorte A.

## 7. Pacote de decisões C3-D01..D06

### C3-D01 — Escopo mínimo da primeira entrega read-only
- **A (recomendação):** competência/filial + dados já comprovados por
  contrato (snapshot SB9 via stock-inventory, baixas via settlements).
  Impacto: zero contrato novo obrigatório além do seletor de competência;
  cobre R01–R03/R15 parcialmente. Risco baixo.
- **B:** acrescentar trilha de estados do wizard — depende de
  `PENDING_EVIDENCE` (tabela do wizard não identificada; E5/E12).
  Recomenda-se adiar até E12.5.
- **C:** evidências/divergências detalhadas — agrega valor mas multiplica
  ACs e depende de R05–R11 (paridades provadas, sem contratos ainda).
  Candidato à segunda fatia.
- **Recomendação: A**, com seletor de competência limitado a `B9_DATA`
  observáveis (evita depender de `MV_ULMES` para V1) ou, se o PO quiser o
  marcador, incluir C3-D04-A.

### C3-D02 — Modelo de estados
- **A (recomendação):** estados separados (§4) com fonte e disponibilidade
  por nó; homologação sempre explícita "não informado" até C3-D05.
- **B:** estado único `fechado` — **não recomendado**: viola a premissa
  "SB9/`MV_ULMES` ≠ homologação".
- Impacto de A: copy/semântica no contrato de resposta (campo `status` +
  `stateDetail`), zero persistência.

### C3-D03 — Reabertura
- **B (recomendação):** fora da V1. Semântica de `Reabertura de estoque`
  ainda pendente (E12.6); read-only nunca executa — exibir histórico só
  quando a tabela do wizard estiver evidenciada (A ficaria para fatia
  posterior).

### C3-D04 — Dados não expostos (competência/`MV_ULMES`/wizard)
- **A (recomendação condicionada):** evoluir contrato no owner —
  api-delpi: `GET /financeiro/closing-context` candidato
  (`B9_DATA` distintas por filial + `MV_ULMES` SX6), guarda S2S igual à
  de stock-inventory. Impacto: rota+use case+repo novos na api-delpi e
  passthrough na BFF — requer gate de contrato antes de implementar.
- **B:** adiar o campo e usar seletor por período (V1 funciona hoje).
- **C:** nova persistência — **não recomendado**: dado já existe em SX6;
  duplicaria fonte de verdade.

### C3-D05 — Homologação
- **A (recomendação):** aceite funcional explícito da Controladoria,
  registrado fora do sistema nesta fase (G6). A UI exibe "pendente de
  homologação" como dado de processo, não de autoridade.
- **B:** inferir por `MV_ULMES`/SB9 — **rejeitado** (premissa do C2).

### C3-D06 — Dependências incompletas
- **A (recomendação):** excluir do MVP superfícies sem fonte (wizard
  `PENDING_EVIDENCE`, R03-P7-oficial, R04/R13/R14 `BLOCKED_BY_OWNER`) e
  acompanhar E1–E12 em paralelo.
- **B:** expor parcial com proveniência — aceitável somente com AC
  verificável e aviso de limitação; não aplicar a homologação nem a
  "status do fechamento" como verdade.

## 8. Resíduos E1–E12 — classificação para o design

| Pacote | Bloqueia design do recorte A? | Classe |
|---|---|---|
| E1 (fonte DLP06R01) | não — contrato settlements já existe | acompanhamento |
| E2 (MATR460/params) | não — recorte usa SB9, não o P7 oficial | acompanhamento |
| E3 (DDL views) | não | acompanhamento |
| E4 (jobs/SPs) | não | acompanhamento (relevante p/ trilha de estados futura) |
| E5 (writer MATA280) | não para V1; **sim** para exibir "etapa de virada" com fonte | design de B/C |
| E7/E8 (RPO/params MATR910/989) | não | acompanhamento |
| E9 (SP DLP204) | não | acompanhamento (R09 fora do recorte A) |
| E10/E11 (taxonomia/finalidade) | não — afeta inclusão de R10/R11 no MVP | decisão de escopo |
| E12.5 (tabela do wizard) | **sim** para exibir status do wizard | bloqueio design B |
| E12.6 (reabertura) | **sim** para C3-D03-A | bloqueio design |
| E12.7 (critério homologação) | **sim** para qualquer rótulo de "homologado" | bloqueio design |
| G6×15 | não bloqueia design read-only; bloqueia claims | acompanhamento |

## 9. Plano page-by-page (proposta, sem implementação)

| # | Página/rota candidata | Conteúdo | Contrato | Prontidão |
|---|---|---|---|---|
| P0 | `/` Início | hero, busca, recentes (vigente) | viewer-context | `PROVEN` |
| P1 | `/closing` Central de Fechamento | competência+filial+estado técnico+cards | stock-inventory (+`closing-context` se C3-D04-A) | `READY_WITH_CONSTRAINTS` (C3-D01/D02/D04) |
| P2 | `/closing/stock-inventory` | P7 operacional SB9 (vigente) | stock-inventory | `PROVEN` |
| P3 | `/closing/financial-settlements` | baixas R01/R02 (vigente) | settlements | `PROVEN` |
| P4 | visão-geral/tarefas/admin/ajuda | convenção Portal | — | `PLANNED` (doc 24) |
| P5 | `/closing/evidence` divergências/paridades | resumo R05–R11 read-only | TARGET | `DECISION_REQUIRED` (C3-D01-C) |
| — | wizard/reabertura | — | — | `BLOCKED_BY_OWNER` (E12.5/E12.6) |

Cada página segue: permissão única `access`, filial como filtro de dados,
estados loading/error/empty/`source_missing`, help contextual, testes de
rota BFF + composição MFE.

## 10. Segurança — estado vigente (verificado no código)

- Permissions: apenas `.access`/`.manage` — nenhuma granularidade por
  página/filial; filial = filtro com `scope_unavailable` fail-closed.
- S2S por cliente (ADR-010): `controllership-finance-api` allow-listed na
  api-delpi por superfície (`stock-inventory.read`).
- `viewer-context`: `principal_type==user`, RBAC indisponível → 503,
  `manage` não implica `access`.
- Nenhum dado fiscal individualizado neste documento; sanitização mantida.

## 11. Estado e encaminhamento

- Estado da rodada: **inventário concluído, decisões pendentes do PO**.
- O próximo gate é decisão sobre C3-D01..D06 + (se A) contrato
  `closing-context` como proposta formal; **runtime permanece bloqueado**
  até gate transversal + autorização page-by-page.
- G6×15, métricas e gates do Ciclo 2: inalterados (47/60 · 55/90 · 0/15).

*Referências: doc 87 §§3–7; doc 86 §§2/5/8; doc 48 (settlements contract);
doc 49 (stock-inventory contract + §8 scope decision); docs 50–53 (UX);
doc 24 (páginas comuns); doc 30 (reuse map); doc 82 (E1–E12); doc 85
(BR/T).*
