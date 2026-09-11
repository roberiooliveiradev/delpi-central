# Portal Suprimentos — documentação mestra

> **Status (2026-09-11):** implementação incremental em andamento · **E1–E7 concluídas** · **WF-05 GATE-FEATURE PASS** (smoke federado `INCONCLUSIVE` neste ambiente)  
> **Readiness:** **GATE-E1 + GATE-ARCH + GATE-AUTHZ + GATE-RBAC PASS (local)**  
> **Modo de entrega:** **uma página por vez até DoD** — a próxima página só pode ser promovida a foco após fechamento da atual  
> **Página em foco:** **nenhuma** — aguardando autorização explícita do Product Owner para promover **Detalhe do pedido (WF-06)**  
> **Últimas páginas fechadas:** **Início (WF-01)**, **Visão geral (WF-02/WF-02R)**, **OTD analytics (WF-OTD-A)**, **Solicitações de compras (WF-04)** e **Pedidos de compra (WF-05)**  
> **Próxima página candidata:** **Detalhe do pedido (WF-06)**, somente com autorização explícita do Product Owner  
> **Id técnico:** `supplies` · **basePath:** `/apps/supplies` · **API:** `supplies-api` · gateway `/apps/supplies-api/` · **CSS root:** `.dashboard-supplies-portal`

O Portal Suprimentos é o hub operacional, analítico e gerencial do domínio de Suprimentos na Minha DELPI. Ele substitui progressivamente experiências fragmentadas por jornadas coesas, preservando bounded contexts, RBAC central, paridade mensurável e rollback.

**Esta pasta é contrato de produto/arquitetura e roadmap. Ela não autoriza implementação, cutover, remoção de legados, mudança de RBAC real ou migration produtiva sem pedido explícito do Product Owner.**

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
| **E4 — Home + Ajuda + perfil** | **concluída** — `/home/attention`, Manual/Quero→onde/FAQ/glossário, perfil `/users/:userId`, preferências e avatar Core |
| **E5 — Overview + OTD analytics** | **concluída** — WF-02/WF-02R + WF-OTD-A; tríade de meta SI, filtros/URL, charts e gauges |
| **E6 — SC C1 + GATE-FEATURE WF-04** | **concluída 2026-09-11** — BFF C1, lista/detalhe/export, kit-first, Help, testes; smoke federado `INCONCLUSIVE` |
| **E7 — Pedidos lista + GATE-FEATURE WF-05** | **concluída 2026-09-11** — api-delpi SC7 aberto, BFF operations+unit, MFE kit-first; detalhe fora (E8) |
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
| 5 | Detalhe do pedido | `/purchase-orders/:branch/:number` | bloqueada até WF-05 fechar + autorização PO |
| 6 | Entregas / atrasos | `/deliveries` | bloqueada até WF-06 fechar |
| 7 | Controle de estoques | `/inventory` | fila |
| 8 | Estoque de segurança | `/safety-stock` | fila |
| 9 | Análise de consumo | `/safety-stock/consumption-analysis` | fila |
| 10 | Fornecedores | `/suppliers` | fila / contrato de busca a confirmar |
| 11 | Fornecedor 360 | `/suppliers/:code/:store` | fila |
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

**Início (WF-01):** BFF `/home/attention`, hub capability-driven, PageHero/kit, Favoritos TopBar, loading/error/partial/empty, AuthZ e Ajuda.

**Visão geral (WF-02/WF-02R):** `/analytics/overview` + `/analytics/otd/series`; filtros por período/unidade com URL shareable; 7 KPIs; tríade SI (`goalValue`, `comparableGoal`, `referenceGoal`, `iddScore`); charts OTD/comparativo; Help sincronizado. Filtros de domínio como `location`/`stock_method` não são globais da Overview.

**OTD analytics (WF-OTD-A):** `/analytics/otd`; gauges por unidade + série; mesmos filtros do Overview; Help sincronizado.

**Solicitações de compras (WF-04):** BFF C1 `/purchase-requests*`; PageHero + FilterBar kit + SectionCard; URL/F5 dos filtros e detalhe; AuthZ access/export/unit/CC fail-closed; estados loading/empty/error/403/404; Help + FAQ; testes MFE estruturais + BFF/security. Smoke federado: `INCONCLUSIVE` neste ambiente.

**Pedidos de compra (WF-05):** api-delpi `GET /supplies/purchase-orders` (SC7 aberto); BFF `GET /purchase-orders` (operations + unit); MFE kit-first com filtros/URL/F5; seleção de linha marca URL (detalhe completo = E8). Distinto do painel OTD. Smoke federado: `INCONCLUSIVE`.

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
| Entrada | `supplies.portal.access` |

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
- Unidade é eixo ortogonal `supplies.unit.filial-{TOTVS}`.
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
| [IMPLEMENTATION-PLAN.md](./IMPLEMENTATION-PLAN.md) | estado de execução + fila; página-a-página |
| [HOMOLOGACAO-PARIDADE.md](./HOMOLOGACAO-PARIDADE.md) | paridade mensurável |
| [CUTOVER-RUNBOOK.md](./CUTOVER-RUNBOOK.md) | target-first, redirect-last |
| [DECISOES_FUNCIONAIS_PENDENTES.md](./DECISOES_FUNCIONAIS_PENDENTES.md) | somente decisões realmente não respondidas |

### ADRs

| ADR | Decisão |
|---|---|
| ADR-001 | `supplies-api`, Flask, authz Core-first |
| ADR-002 | absorção progressiva `purchase-requests-api` C0→C3 |
| ADR-003 | coexistência/cutover |
| ADR-004 | identidade do plugin/CSS |
| ADR-005 | BIs externos precisam de dump Core antes do GO |
| ADR-006 | unidade ortogonal |
| ADR-007 | minimização de permissions |

---

## 7. Próximo passo operacional

**Único próximo passo autorizado pelo roadmap:** Product Owner autorizar a promoção de **WF-06 Detalhe do pedido**. Sem essa autorização, a fila permanece bloqueada.

Dump Core de produção dos BIs externos não bloqueia a fila de páginas; bloqueia decisões de paridade/depreciação/redirect e o `GATE-CUTOVER`.
