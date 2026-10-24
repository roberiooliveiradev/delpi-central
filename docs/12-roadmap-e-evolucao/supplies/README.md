# Portal Suprimentos — documentação mestra

> **Status (2026-10-23 — rebaseline R1):** implementação incremental em andamento · **E1–E9 concluídas** · **E10 / WF-15 GATE PASS_DEPLOYED** (bundle federado verificado contém a página; residual `VISUAL_AUTHENTICATED=INCONCLUSIVE`) · **E13/E14 fornecedores implementadas** (writes ERP OFF — X4.PROD-C1 aguardando TOTVS) · **USERS.PROFILE.S1–S3** fechadas
> **Readiness:** **GATE-E1 + GATE-ARCH + GATE-AUTHZ + GATE-RBAC PASS (local)** · E9/E10 fechadas c/ residual visual · **E11 READY_WITH_RESIDUAL** (contratos api-delpi completos; falta BFF+MFE)
> **Modo de entrega:** **uma página por vez até DoD** — a próxima página só pode ser promovida a foco após fechamento da atual
> **Página em foco:** **E11 / WF-16 Estoque de Segurança** — `E11.S1`–`E11.S9` executadas: BFF+MFE publicados em produção (`PASS_DEPLOYED`); detalhe migrado para página própria com seleção de filial no consolidado — ver [E11-S7](./E11-S7-DETAIL-PAGE-IMPLEMENTATION.md); indicadores do hero interativos filtram a lista (fonte única com Status/toggle, `PageHeroHighlight.onSelect` no kit) — ver [E11-S9](./E11-S9-INTERACTIVE-SUMMARY-CARDS.md); `GATE-FEATURE E11 = INCONCLUSIVE` — falta smoke federado autenticado
> **Últimas páginas fechadas:** **Início (WF-01)**, **Visão geral (WF-02/WF-02R)**, **OTD analytics (WF-OTD-A)**, **Solicitações de compras (WF-04)**, **Pedidos de compra (WF-05)**, **Detalhe do pedido (WF-06)**, **Entregas / atrasos (WF-07)**, **Controle de Estoques (WF-15)**, **Fornecedores/360 (WF-09/WF-10)** e **Perfil de usuário (`/users/:userId`)**
> **Próxima receita:** E11.P0 contract freeze (read-only) → E11.S1 BFF — **writes ERP permanecem OFF**
> **Id técnico:** `supplies` · **basePath:** `/apps/supplies` · **API:** `supplies-api` · gateway `/apps/supplies-api/` · **CSS root:** `.dashboard-supplies-portal`

O Portal Suprimentos é o hub operacional, analítico e gerencial do domínio de Suprimentos na Minha DELPI. Ele substitui progressivamente experiências fragmentadas por jornadas coesas, preservando bounded contexts, RBAC central, paridade mensurável e rollback.

**Esta pasta é contrato de produto/arquitetura e roadmap. Ela não autoriza implementação, cutover, remoção de legados, mudança de RBAC real ou migration produtiva sem pedido explícito do Product Owner.**

> **Complemento de evolução (2026-10-20):** [Gestão cadastral de fornecedores — roadmap kit-first](./FORNECEDORES-GESTAO-CADASTRAL-ROADMAP.md) detalha E13/WF-09 e E14/WF-10 (busca, ficha, POST/PUT controlados e CNPJ futuro), com componentes visuais reutilizados de `@delpi/plugin-ui` via Module Federation. **Não altera o status bloqueado nem a página em foco da fila.**

---

## 1. Fonte de verdade e regra de execução

A documentação desta pasta deve obedecer à hierarquia vigente das regras `.cursor`: instruções oficiais → regras transversais → ADRs/contratos/código atual → testes → documentação/roadmap. Se um documento histórico divergir do runtime atual, registrar e corrigir o drift; não adaptar o código para cumprir um plano obsoleto.

`IMPLEMENTATION-PLAN.md` é o plano executável da **página em foco** e o grafo de dependências do programa. Nós futuros podem existir como fila, mas **não são receita autorizada de execução** enquanto estiverem bloqueados. Ao promover uma página, aplicar `plan-construction.mdc`, revalidar código/contratos e preencher a receita completa `E*.S*` antes de implementar.

---

## 2. Readiness atual

| Item | Estado |
|---|---|
| Baseline de produto | concluída |
| Arquitetura alvo | concluída |
| **E1 — descoberta + freeze** | **concluída 2026-09-08** |
| **E2 — supplies-api foundation** | **concluída 2026-09-08** — Flask, authz Core-first, schema `supplies`, gateway api-delpi, `/me/capabilities` |
| **E3 — MFE + RBAC coexistência** | **concluída 2026-09-08** — `plugins/supplies`, BFF-only, shell capability-driven, manifest Core, papéis canônicos |
| **E4 — Home + Ajuda + perfil** | **concluída** — hub do Início (Atenção removida no P3), Manual/Quero→onde/FAQ/glossário, perfil `/users/:userId`, preferências e avatar Core |
| **E5 — Overview + OTD analytics** | **concluída** — WF-02/WF-02R + WF-OTD-A; tríade de meta SI, filtros/URL, charts e gauges |
| **E6 — SC C1 + GATE-FEATURE WF-04** | **concluída 2026-09-11** — BFF C1, lista/detalhe/export, kit-first, Help, testes; smoke federado `INCONCLUSIVE` |
| **E7 — Pedidos lista + GATE-FEATURE WF-05** | **concluída 2026-09-11** — api-delpi SC7 aberto, BFF operations+unit, MFE kit-first |
| **E8 — Detalhe do Pedido + GATE-FEATURE WF-06** | **concluída 2026-09-16** — ficha `/purchase-orders/:branch/:number`; smoke federado **PASS** em 2026-09-21 |
| **E9 — Entregas / atrasos + P0 freeze** | **FECHADA** — **GATE-FEATURE WF-07 PASS** após redeploy BFF; FAIL inicial preservado na [evidência](./evidence/e9-wf07-federated-runtime-gate.md); [freeze](./evidence/e9-wf07-p0-contract-freeze.md) |
| **E10 — Controle de Estoques (WF-15)** | **FECHADA (residual visual)** — S1–S4 PASS; bundle federado verificado com a página (R1, 2026-10-23); `VISUAL_AUTHENTICATED=INCONCLUSIVE` ([evidência](./evidence/e10-wf15-s4-final-acceptance.md), [R1](./ROADMAP-REBASELINE-R1-20261023.md)) |
| RBAC alvo | revisado; menor catálogo suficiente (ADR-007) |
| Authz Core-first | **GATE-AUTHZ PASS** — fail-closed na fronteira; permissions efetivas do Core, não claims JWT |
| BIs externos | dump **local** 0/6 documentado; dump Core **produção** obrigatório antes do cutover |
| KPIs Overview P0 | **7 confirmados**; `KPI-PO-LATE` e cobertura fora do Overview P0 |
| Manifest | `schemaVersion 1.0.0` registrado no Core local |
| Identificador de usuário | Core `/me.id` UUID; P-13 fechado |

### Gates

| Gate | Estado atual |
|---|---|
| **GATE-E1** | **PASS** |
| **GATE-ARCH** | **PASS** |
| **GATE-AUTHZ** | **PASS** |
| **GATE-RBAC** | **PASS local**; persona negativa real/HML continua dependente de usuário não-superadmin |
| **GATE-API** | **PASS parcial** — fundação + Overview/OTD + SC C1; demais operações entram página a página |
| **GATE-MFE** | **PASS nas páginas fechadas**; revalidar por página nova |
| **GATE-FEATURE WF-04** | **PASS** — smoke federado `INCONCLUSIVE` (não inferido) |
| **GATE-FEATURE WF-05** | **PASS** — smoke federado `INCONCLUSIVE` (não inferido) |
| **GATE-FEATURE WF-06** | **PASS** — smoke federado em `https://minhadelpi.com.br` em 2026-09-21; residual: 403 de unidade não executado ([evidência](./evidence/e8-wf06-federated-runtime-gate.md)) |
| **GATE-FEATURE WF-07** | **PASS** — recovery 2026-09-21: redeploy `supplies-api` em `srv-api` + re-smoke 200 ([evidência](./evidence/e9-wf07-federated-runtime-gate.md)) |
| **GATE-FEATURE E10** | **PASS_DEPLOYED** — bundle federado `App-SSmBJjdj.js` contém `stock-balances`; rotas 401 protegidas em runtime; residual `VISUAL_AUTHENTICATED=INCONCLUSIVE` ([evidência](./evidence/e10-wf15-s4-final-acceptance.md), [R1](./ROADMAP-REBASELINE-R1-20261023.md)) |
| **GATE-C2** | futuro; não autorizado enquanto prerequisites não forem provados |
| **GATE-PARITY** | futuro; evidência quantitativa obrigatória |
| **GATE-CUTOVER** | futuro; nenhum legado/BI pode permanecer `LEGADO_A_VALIDAR` |

---

## 3. Protocolo obrigatório — uma página por vez

```text
selecionar página em foco
→ revalidar regras + código + contratos + working tree
→ ledger RQ-* e baseline
→ BFF/contrato no owner correto
→ UI kit-first
→ AuthZ + unit/resource scope
→ loading/empty/partial/error/403/404
→ Ajuda sincronizada
→ positive + sibling + negative
→ docs + smoke + tema + responsividade
→ GATE-FEATURE fechado
→ somente então promover a próxima página
```

### Fila canônica

| Ordem | Página | Rota | Estado |
|---:|---|---|---|
| 1 | Início | `/apps/supplies` | **FECHADA (DoD)** |
| 2 | Visão geral | `/overview` | **FECHADA (DoD)** · WF-02R |
| — | OTD analytics | `/analytics/otd` | **FECHADA (DoD)** · satélite WF-OTD-A |
| **3** | **Solicitações de compras** | `/purchase-requests` | **FECHADA (DoD)** · WF-04 |
| 4 | Pedidos de compra | `/purchase-orders` | **FECHADA (DoD)** · WF-05 |
| 5 | Detalhe do pedido | `/purchase-orders/:branch/:number` | **FECHADA (DoD)** · WF-06 |
| 6 | Entregas / atrasos | `/deliveries` | **FECHADA (DoD)** · WF-07 |
| 7 | Controle de estoques | `/inventory` | **FECHADA** (E10, residual visual) · WF-15 |
| 8 | Estoque de segurança | `/safety-stock` + detalhe `/safety-stock/{filial}/{material}` | **DEPLOYED (S1–S7)** — detalhe em página própria com seleção de filial no consolidado; `GATE-FEATURE = INCONCLUSIVE` (falta smoke autenticado/visual) |
| 9 | Análise de consumo | `/safety-stock/consumption-analysis` | fila (satélite E12; contrato produtor existe) |
| 10 | Fornecedores | `/suppliers` | **FECHADA** (E13) — lista/busca/filtros; cadastro/edição em TST |
| 11 | Fornecedor 360 | `/suppliers/:code/:store` | **FECHADA** (E14) — avatar/nome navegáveis nas listas/fichas de PC e Entregas (SUPPLIERS.NAV.S1). Ver [DIRECTORY-OBJECTS.md](./DIRECTORY-OBJECTS.md) |
| 11b | Perfil de usuário | `/users/:userId` | **FECHADA** (USERS.PROFILE.S1) — ficha Minha DELPI reusada; avatar/nome do solicitante navegáveis nas listas/fichas de SC/PC quando `user_id` Core + acesso; seção de SCs relacionadas. `/people/:code` descartada |
| 12 | OTD fornecedores | `/suppliers/otd` | fila |
| 13 | Produtos / MP | `/products` | fila |
| 14 | Produto / MP 360 | `/products/:code` | fila |
| 15 | Onde o item é usado | `/products/:code/where-used` | fila |
| 16 | Histórico de preços | `/products/:code/price-history` ou seção do 360, conforme contrato promovido | fila |
| 17 | Savings / Negociações | `/negotiations` | fila |
| 18 | Indicadores | `/indicators` | fila |
| 19 | Minhas Atividades | `/my-tasks` | fila |
| 20 | Administração | `/administration` | fila |

**Regra:** a tabela acima é uma fila de produto, não autorização para o Cursor implementar várias páginas em paralelo. O próximo plano executável contém somente a página promovida e seus satélites inevitáveis (Ajuda, contrato, testes, docs).

### DoD de página — GATE-FEATURE

1. Contrato/BFF no owner correto ou composição explícita.
2. UI kit-first: `@delpi/plugin-ui` antes de qualquer componente local reutilizável; PagePath/PageHero/SectionCard e estados conforme padrão vigente.
3. AuthZ backend-first; capability + unit + resource scope/ownership + business rule quando aplicável.
4. Estados `loading`, `empty`, `partial` quando permitido, `error`, `403`, `404` e retry/recovery quando seguro.
5. Ajuda no mesmo entregável (`feature-help-sync`): tooltip contextual, Quero→onde/FAQ/Manual quando o conceito novo exigir.
6. Testes positive + sibling + negative; contrato/wiring quando material.
7. URL/F5/back-forward preservados quando a página possui filtros/deep links.
8. Desktop/mobile, tema claro/escuro e teclado/focus validados em mudança visual material.
9. `WIREFRAMES.md`, `API-ROUTES.md`, readiness e evidências atualizados sem prometer funcionalidade inexistente.
10. Smoke federado no Portal quando a integração for material; se não executável, marcar `INCONCLUSIVE`, nunca `PASS` por inferência.

---

## 4. Páginas já fechadas

**Início (WF-01):** hub capability-driven, PageHero/kit, Favoritos TopBar, busca/recentes, AuthZ e Ajuda. Seção Atenção removida no HOME-ATTENTION.P3 (sem fonte canônica de tarefas; Home não dispara composição operacional).

**Visão geral (WF-02/WF-02R):** `/analytics/overview` + `/analytics/otd/series`; filtros por período/unidade com URL shareable; 7 KPIs; tríade SI (`goalValue`, `comparableGoal`, `referenceGoal`, `iddScore`); charts OTD/comparativo; Help sincronizado. Filtros de domínio como `location`/`stock_method` não são globais da Overview.

**OTD analytics (WF-OTD-A):** `/analytics/otd`; gauges por unidade + série; mesmos filtros do Overview; Help sincronizado.

**Solicitações de compras (WF-04):** BFF C1 `/purchase-requests*` via `purchase-requests-api` (CC fail-closed; multi-unidade `?branch=` repetido; `sort_by`/`sort_dir`; export sem fan-out paginado). MFE: MultiSelect de unidades (nome sem código), Tabela/Cards, sort server-side, Excel (`format=xlsx`, CSV legado), colunas/fonte persistidos. AuthZ access/export/unit/CC. Smoke federado: `INCONCLUSIVE` neste ambiente.

**Pedidos de compra (WF-05):** MFE → `supplies-api` → `api-delpi` `GET /supplies/purchase-orders` (SC7 aberto, filtro `01`/`02`, `sort_by`/`sort_dir`, `summary`); BFF `GET /purchase-orders` + `GET /purchase-orders/export` (XLSX; `supplies.access`). MFE: MultiSelect de unidades (nome sem código), Tabela/Cards, sort server-side, Excel, colunas/fonte persistidos. Clique na linha abre a ficha E8. Distinto do painel OTD. Smoke federado: `INCONCLUSIVE`.

**Detalhe do pedido (WF-06):** api-delpi `GET /supplies/purchase-orders/{branch}/{order_number}`; BFF `GET /purchase-orders/<branch>/<number>` (`supplies.access` + filtro `01`/`02`); MFE `/purchase-orders/:branch/:number` read-only (itens, entrega prometida, receipts, SC origem). Smoke federado: **PASS** em 2026-09-21 ([evidência](./evidence/e8-wf06-federated-runtime-gate.md)).

A manutenção transversal de UI (por exemplo, help embutido no próprio label e loading canônico do `plugin-ui`) pode corrigir componentes compartilhados, mas não reabre uma página fechada salvo regressão material do seu DoD.

---

## 5. Identidade e arquitetura congeladas

| Superfície | Valor |
|---|---|
| Plugin id | `supplies` |
| basePath MFE | `/apps/supplies` |
| API/BFF | `supplies-api` · `/apps/supplies-api` |
| Framework API | Flask |
| CSS root | `.dashboard-supplies-portal` |
| Tokens | `--sp-*` → `--delpi-ui-*` |
| Entrada | `supplies.access` |

```text
Browser
  → Minha DELPI Portal
    → plugins/supplies
      → supplies-api
          ├── Core API /me + /me/apps (effective permissions/rotas em apps[].routes)
          ├── PostgreSQL próprio (estado Minha DELPI)
          ├── purchase-requests-api (C1 até C2)
          ├── strategic-indicators-api
          ├── contextos irmãos quando autorizados
          └── api-delpi → TOTVS
```

Invariantes:

- MFE nunca chama `api-delpi` diretamente.
- JWT identifica/autentica; Core resolve permissions efetivas.
- Não existe dependência canônica em `/me/routes`; o Core atual entrega rotas autorizadas em `/me/apps` (`apps[].routes`).
- SQL/regra TOTVS permanecem na `api-delpi`.
- Estado do produto pertence à `supplies-api`; não espelhar TOTVS no Postgres.
- Capabilities de produto não devem espelhar CRUD.
- Unidade do Portal é filtro de dados `01`/`02` (ADR-009), não `supplies.unit.*`.
- C1 → C2 → paridade final → C3 é ordem obrigatória para Purchase Requests.
- Cutover só após paridade, classificação dos BIs/legados, target saudável e rollback conhecido.

---

## 6. Documentos canônicos da pasta

| Documento | Conteúdo |
|---|---|
| [00-DIAGNOSTICO.md](./00-DIAGNOSTICO.md) | cenário e dores |
| [INVENTARIO-ATIVOS.md](./INVENTARIO-ATIVOS.md) | ativos, owners e destino |
| [PERSONA-EXPERIENCE-MAP.md](./PERSONA-EXPERIENCE-MAP.md) | personas × apps × permissions |
| [DUPLICIDADES-E-SOBREPOSICOES.md](./DUPLICIDADES-E-SOBREPOSICOES.md) | overlaps e drifts |
| [MATRIZ-BOUNDARIES.md](./MATRIZ-BOUNDARIES.md) | ownership |
| [PLAYBOOK-MODULO-SUPRIMENTOS.md](./PLAYBOOK-MODULO-SUPRIMENTOS.md) | decisões de produto/arquitetura |
| [PLAYBOOK-01-fronteiras-api-delpi.md](./PLAYBOOK-01-fronteiras-api-delpi.md) | fronteira BFF × TOTVS |
| [DESIGN-IA-SUPRIMENTOS.md](./DESIGN-IA-SUPRIMENTOS.md) | IA/UX |
| [WIREFRAMES.md](./WIREFRAMES.md) | páginas e contratos de experiência |
| [PERFIS-E-PERMISSOES.md](./PERFIS-E-PERMISSOES.md) | RBAC mínimo + unidade + aliases |
| [MANIFEST-DRAFT.md](./MANIFEST-DRAFT.md) | contrato do plugin |
| [API-ROUTES.md](./API-ROUTES.md) | contratos e status das rotas BFF |
| [DATA-MODEL.md](./DATA-MODEL.md) | estado Postgres |
| [KPI-FICHAS.md](./KPI-FICHAS.md) | indicadores |
| [INTEGRACOES.md](./INTEGRACOES.md) | HTTP, authz, observabilidade |
| [HELP-AND-ONBOARDING.md](./HELP-AND-ONBOARDING.md) | Ajuda e onboarding |
| [DIRECTORY-OBJECTS.md](./DIRECTORY-OBJECTS.md) | avatar kit + rotas reservadas de fornecedor e pessoa |
| [IMPLEMENTATION-PLAN.md](./IMPLEMENTATION-PLAN.md) | estado de execução + fila; página-a-página |
| [HOMOLOGACAO-PARIDADE.md](./HOMOLOGACAO-PARIDADE.md) | paridade mensurável |
| [CUTOVER-RUNBOOK.md](./CUTOVER-RUNBOOK.md) | target-first, redirect-last |
| [SC-PC-DETAIL-ENRICHMENT-P0.md](./SC-PC-DETAIL-ENRICHMENT-P0.md) | discovery P0: estado atual, gaps, owners e proposta das fichas de Detalhe da SC e do PC (`DISCOVERY_COMPLETE`/`IMPLEMENTATION_NOT_AUTHORIZED`) |
| [SC-PC-DETAIL-DATA-CONTRACT-MATRIX.md](./SC-PC-DETAIL-DATA-CONTRACT-MATRIX.md) | matriz mestra de campos, endpoints, produtores e evidências das duas fichas |
| [SC-PC-DETAIL-UX-WIREFRAMES.md](./SC-PC-DETAIL-UX-WIREFRAMES.md) | wireframes desktop/mobile, estados e componentes do kit das duas fichas |
| [SC-PC-DETAIL-IMPLEMENTATION-ROADMAP.md](./SC-PC-DETAIL-IMPLEMENTATION-ROADMAP.md) | fases EN.A–EN.D, owners, gates e RQ/AC da evolução |
| [SC-PC-DETAIL-EN-A1-CONTRACT-TYPES.md](./SC-PC-DETAIL-EN-A1-CONTRACT-TYPES.md) | EN.A1: tipagem e validação do contrato SC detail (`DONE`, sem mudança visual/backend) |
| [SC-PC-DETAIL-EN-A2-SC-HERO.md](./SC-PC-DETAIL-EN-A2-SC-HERO.md) | EN.A2: hero da ficha SC em 3 níveis (`DONE`, frontend-only, sem deploy) |
| [SC-PC-DETAIL-EN-A3-A7.md](./SC-PC-DETAIL-EN-A3-A7.md) | EN.A3–A7: itens/pedidos/recebimentos/acompanhamento SC + ficha PC + links SC↔PC + D1/D2 na UI (`DONE`) |
| [DECISOES_FUNCIONAIS_PENDENTES.md](./DECISOES_FUNCIONAIS_PENDENTES.md) | somente decisões realmente não respondidas |
| [ROADMAP-TRANSFORMA-PLUS.md](./ROADMAP-TRANSFORMA-PLUS.md) | **Visão de negócio Transforma+** (SUP-*, ondas, integrações) — descoberta/backlog; **não** duplica contratos técnicos nem autoriza implementação |
| [BRANCH-AUTHZ-DOCS-R1-GLOBAL-RECONCILIATION.md](./BRANCH-AUTHZ-DOCS-R1-GLOBAL-RECONCILIATION.md) | reconciliação global: filial é filtro de dados, nunca autorização no Portal |
| [../financeiro-controladoria/ROADMAP.md](../financeiro-controladoria/ROADMAP.md) | Irmão Controladoria (custos de importação compartilhados) |

### ADRs

| ADR | Decisão |
|---|---|
| ADR-001 | `supplies-api`, Flask, authz Core-first |
| ADR-002 | absorção progressiva `purchase-requests-api` C0→C3 |
| ADR-003 | coexistência/cutover |
| ADR-004 | identidade do plugin/CSS |
| ADR-005 | BIs externos precisam de dump Core antes do GO |
| ADR-006 | unidade ortogonal — **SUPERSEDED por ADR-009** |
| ADR-007 | minimização de permissions (histórico; catálogo antigo superado) |
| ADR-008 | `supplies.access`/`supplies.manage` (parcialmente vigente) |
| ADR-009 | **vigente**: só `access`/`manage`; unidade = filtro de dados `01`/`02`, sem `supplies.unit.*` |

---

## 7. Próximo passo operacional

**Único próximo passo autorizado pelo roadmap:** **E11.S1 — BFF `supplies-api` safety-stock** (aguardando autorização formal do PO; contrato congelado em [E11-P0](./E11-P0-SAFETY-STOCK-CONTRACT-FREEZE.md), receita §9; `BRANCH_AUTHZ_RECONCILIATION = COMPATIBLE` — produtor já aceita chamada confiável do BFF). E10 está `PASS_DEPLOYED` — falta apenas o clique autenticado do PO para fechar `VISUAL_AUTHENTICATED=INCONCLUSIVE` ([evidência](./evidence/e10-wf15-s4-final-acceptance.md)).

Revalidação 2026-09-21 (`4f3ed59483`): GATE-FEATURE WF-06 permanece **PASS**. Autorização do Product Owner e freeze P0 de E9 estão persistidos. P-03 continua bloqueando apenas paridade/depreciação do BI, não a construção da página nativa.

Dump Core de produção dos BIs externos não bloqueia a fila de páginas; bloqueia decisões de paridade/depreciação/redirect e o `GATE-CUTOVER`.

---

## Atualização bounded — enriquecimento cadastral e fase de interface (2026-10-22)

A frente **SHARED-INTEGRATIONS-01 X0–X3.E2E** atingiu **ACCEPT para backend/runtime de enriquecimento**, conforme [fechamento X3.E2E e readiness X4](../shared-integrations/X3-E2E-CLOSURE-AND-X4-UI-READINESS-20261022.md) e [evidência de runtime](../shared-integrations/X3-RUNTIME-EVIDENCE-20261022.md). Consulta real BrasilAPI via `external-data-api`, BFF `supplies-api`, comparação S1, persistência/revisões S2, decisões e `prepare-update` draft-only foram exercitados em produção de forma controlada; **nenhum PUT/POST ERP foi habilitado**. Contrato `person_type` PJ e replay idempotente foram esclarecidos no rework de `72427d5017` (evidência reportada).

**X4.P0 — inventário e contract freeze da interface de fornecedores está autorizado pelo PO**, sem autorização de implementação/deploy MFE. A fila geral mantinha E10/WF-15 em foco com gate federado `INCONCLUSIVE` segundo a última evidência desta pasta **(superado em 2026-10-23: `GATE-FEATURE E10 = PASS_DEPLOYED`, residual `VISUAL_AUTHENTICATED=INCONCLUSIVE` — ver R1)**; o novo P0 precisa revalidar esse gate e reconciliar E13/WF-09 e E14/WF-10 antes de promover página. Não usar o aceite backend como `GATE-FEATURE` visual. Registro LGPD/ROPA específico permanece pendente no [backlog documentado](../shared-integrations/X3-LGPD-STATUS-AND-DEFERRED-REMEDIATION-20261022.md).


## Handoff atual — X4.PROD-C1 (2026-10-23) — aguardando Gabriel/TOTVS

**LEITURA PRIORITÁRIA AO RETOMAR A FRENTE DE CADASTRO REAL:** [X4-PROD-C1-HANDOFF-AGUARDANDO-GABRIEL-20261023.md](./X4-PROD-C1-HANDOFF-AGUARDANDO-GABRIEL-20261023.md). Homologação local POST/PUT em `DELPI_TST01` reportada com sucesso; **produção NÃO liberada**: `G8 = FAIL` (rota suppliers 404, autenticação 401 em `192.168.1.231:8061/restall`). `URL_REST@1` ainda resolve TST para preservar GET E14; guarda produtiva fixa o endpoint 231:8061 e bloqueia escrita por mismatch; CREATE/UPDATE OFF. Deploy parcial da guarda registrado como `EXECUTION_DRIFT`. **Decisão do PO: aguardar resposta do Gabriel antes de nova intervenção de cutover.** Revalidar HEAD/authorities antes de agir. Esta atualização bounded não reclassifica gates de outras páginas históricas.


## Planejamento bounded — Atenção da Home (2026-10-23)

**`HOME-ATTENTION-REFACTOR=PLANNED`; implementação e deploy NÃO autorizados.** As capturas do PO mostram sete atalhos genéricos aparentando pendências, sem quantidade/situação comprovadas. Plano exclusivo para a seção Atenção da Home: [HOME-ATTENTION-REAL-DATA-REFACTOR-PLAN-20261023.md](./HOME-ATTENTION-REAL-DATA-REFACTOR-PLAN-20261023.md). Próximo gate proposto: `A0` inventário read-only do produtor BFF `GET /home/attention`, contagens e contratos de origem, antes de congelar A1. **Não modificar hero, caminhos, favoritos, demais seções/páginas; não tocar o bloqueio de cutover produtivo C1**, que continua aguardando Gabriel.


**Autorização PO posterior (2026-10-23) — HOME-ATTENTION:** Devin autorizado a executar A0–A4, testes, commit/push e deploy canônico do componente Atenção **sem checkpoints de aprovação intermediários**, apenas com gates técnicos e de segurança PASS. O plano [HOME-ATTENTION-REAL-DATA-REFACTOR-PLAN-20261023.md](./HOME-ATTENTION-REAL-DATA-REFACTOR-PLAN-20261023.md) é a referência atual para este escopo e substitui a classificação PLANNED acima. A autorização não afeta fornecedores C1/Gabriel.
