# Transformômetro — Portal Transformation Playbook

> **Status:** CONTRACT FREEZE / DOCUMENTAÇÃO (sem implementação nesta entrega)  
> **BASE HEAD inventário:** `841637c3e95d18b8bd4b5667b2743ca8a9fc8248` (`main`)  
> **Data do inventário:** 2026-09-17  
> **Adendo de produto (2026-09-18):** a experiência passa a se chamar **Portal Transforma+**. O bounded context continua Transformômetro. Decisão e inventário de reuso: [PORTAL-TRANSFORMA-PLUS.md](./PORTAL-TRANSFORMA-PLUS.md). Este playbook não foi reescrito; onde ele diz «Portal Transformômetro», leia experiência de produto, não rename técnico.
> **Tipo:** playbook técnico + produto + contrato de evolução  
> **Owner documental:** Transformômetro (produto) · handoffs por fase

---

## 1. Propósito

Evoluir o Transformômetro de uma experiência **page-centric** (dashboard, processos, atas, configurações como páginas com nav no header) para um **portal interno de Gestão da Transformação e Melhoria de Processos** dentro da Minha DELPI — no mesmo *padrão de experiência* já comprovado no Portal Comercial / Suprimentos, **sem** criar nova autoridade arquitetural e **sem** copiar semântica comercial.

Cadeia operacional do produto (norte de informação):

```text
PROCESSO → EVIDÊNCIA → DIAGNÓSTICO → REDESENHO → REGISTRO → MEDIÇÃO → APRENDIZADO
```

Este documento congela:

- inventário **PROVEN** do estado atual;
- visão **TARGET** do portal;
- fases incrementais;
- handoffs;
- critérios de aceite;
- o que **não** fazer.

**Não implementar shell/código nesta tarefa.**

---

## 2. Estado e classificação da evidência

### PROVEN

| Item | Evidência |
|---|---|
| MFE federado `basePath=/apps/transformometro` | `plugins/transformometro/transformometro.manifest.json` |
| `remoteEntry` + `renderMode=federated` | mesmo manifesto |
| Roteamento manual (sem React Router) | `src/App.tsx`, `src/utils/routeParser.ts`, `src/constants/routes.ts` |
| Home atual = Dashboard | `routeParser` resolve `/apps/transformometro` → `dashboard` |
| Shell atual = `TransformometroShell` + nav no `PageHeader` | `TransformometroShell.tsx`, `TransformometroNav.tsx` |
| **Não** existe `PluginShell` no MFE TM | grep zero no plugin |
| Workspaces Processos + Configurações | `ProcessWorkspaceShell`, `SettingsWorkspaceShell` |
| Capabilities: dashboard, processos/instâncias/revisões, diagramas BPMN-lite, WBS, matriz, atas, assinatura, data transfer, recursos compartilhados | páginas + API + playbooks 18–23 |
| AuthZ backend-first; MFE trata 401/403 | manifesto permissions; `jwt.ts` só `sub`; `apiErrorMessage` |
| APIs dashboard: summary, evolution, processes, alerts, due-dates, by-family, export | `transformometroApi.ts` |
| Atas: list + pending-signatures | `transformometroMeetingMinutesApi.ts` |
| TÉO = Custom GPT Actions OAuth (não shell MFE) | `transformometro-api/docs/gpt-actions/` |
| Portal Comercial / Supplies = padrão `PluginShell` + TopBar kit | `plugins/commercial/src/app/PluginShell.tsx`, `plugins/supplies/...` |
| Primitivos shell no `plugin-ui` (TopBar, PageHero, CommandPalette, …) | `plugins/plugin-ui/src/components/layout/` |
| Deep-link bridge portal | `useDelpiPortalBridge.ts` (`DELPI_NAVIGATE` / `DELPI_EMBEDDED_ROUTE`) |
| Aliases PT→EN de path | `canonicalizeTransformometroPath` |
| Docs canônicas do produto | `docs/12-roadmap-e-evolucao/transformometro-app/` |

### TO_INVENTORY

| Item | Motivo |
|---|---|
| Como o Portal host lista o app se **todas** as `routes[].showInMenu=false` | Entrada de menu Core/Portal vs `basePath` — wiring runtime não inventariado a fundo |
| Matriz completa AuthZ API × codes do manifesto | Guards/decorators por rota API |
| Uso real de `transformometro.view.consolidated` / branch scopes no dashboard MFE | `dashboardViewScope.ts` candidato |
| Realtime no TM (se houver SSE/WS) | Não inventariado nesta passagem |
| Telemetria de navegação existente | Ausente no inventário médio |
| Deploy Cloudflare/cache `remoteEntry` do TM | Ver `docs/06-portal-frontend/portal-deploy-cache-cloudflare.md` + OPERATIONS TM |
| DÉLIA × Transformômetro | Relação futura; não há binding runtime inventariado aqui |

### TARGET

| Item | Nota |
|---|---|
| Portal Transformômetro (experiência) com Home operacional + shell persistente | Este playbook |
| Menu global único «Transformômetro» → `/apps/transformometro` | Espelhar Comercial |
| Agrupamento IA: Início / Processos / Melhorias / Resultados / Governança / TÉO / Admin | Ajustar às capabilities reais |
| Integração BPMN Modeler (BC próprio) | Contrato explícito futuro |
| Command palette / busca global no shell | Após shell Fase 1–2 |
| Endpoint agregador `portal-home` | **Não** na Fase 1; só se gap comprovado |

### PLANNED

| Item | Nota |
|---|---|
| Fases 0–6 deste playbook | Seção 20 |
| Handoffs 05 / 01 / 02 / 06 / 07 / 08 | Seção 27 |

### EXECUTION_DRIFT (premissas do pedido vs HEAD)

| Premissa do pedido | Realidade no HEAD | Classificação |
|---|---|---|
| «Portal Transformômetro» como app | Experiência TARGET; app continua `transformometro` | OK / clarificado |
| BPMN Modeler BC no monorepo | **Não encontrado** path/nome dedicado; diagramas atuais são BPMN-lite **dentro** do TM | TO_INVENTORY / TARGET |
| Home ≠ dashboard | Hoje home **é** dashboard | PROVEN drift a corrigir no TARGET |
| Copiar Comercial | Supplies é espelho mais limpo do mesmo padrão; Financial **não** | PROVEN |

---

## 3. Ownership e boundaries

```text
Keycloak          → identidade / SSO / JWT
Core              → apps, rotas, RBAC, manifesto, governança transversal
Portal / Minha DELPI → host, navegação global, contexto publicado
Transformômetro   → domínio: processos, melhorias, revisões, medições,
                    custos, diagramas, atas, capabilities comprovadas
TÉO               → especialista conversacional governado (GPT Actions)
DÉLIA             → inteligência operacional futura (não autoridade)
BPMN Modeler      → BC próprio (quando existir) — integração por contrato
Automation Hub    → execução técnica quando aplicável
```

**Portal Transformômetro ≠ novo Portal host.**  
É a **experiência do produto** no MFE `transformometro`, hospedado pelo Portal Minha DELPI.

Proibido nesta evolução:

- segunda fonte de AuthZ no frontend;
- BFF «portal-home» sem gap comprovado;
- import de domain/application entre BCs;
- absorver BPMN Modeler no schema/banco do TM;
- duplicar primitives do kit em CSS local se `plugin-ui` já resolve.

---

## 4. Estado atual do Transformômetro

### Runtime / hosting

```text
Portal host (federated)
  → /apps/transformometro (+ deep paths)
  → plugins/transformometro remoteEntry.js
  → JWT → transformometro-api (/apps/transformometro-api/transformometro)
  → Postgres schema transformometro
```

URLs ops: [OPERATIONS.md](./OPERATIONS.md).

### Rotas

Constantes: `TRANSFORMOMETRO_ROUTES` (`src/constants/routes.ts`).

| Path | Função atual | Manifest route? |
|---|---|---|
| `/apps/transformometro` | → Dashboard | implícito (home) |
| `/apps/transformometro/dashboard` | Dashboard | sim |
| `/apps/transformometro/processes` (+ deep process/instance/revision) | Workspace processos | sim (lista) |
| `/apps/transformometro/settings/*` | Unidades, departamentos, recursos | sim (units) |
| `/apps/transformometro/meeting-minutes` (+ detail/sign/pending) | Atas | sim |
| `/apps/transformometro/my-signature` | Assinatura pessoal | sim |
| `/apps/transformometro/data` | Export/import JSON | sim |
| Diagram editor paths | Editor BPMN-lite | deep interno |

Aliases PT preservados (`/processos`, `/atas`, `/dados`, …).

### Shell

- `TransformometroShell` = wrapper visual (`ds-app-shell`).
- Nav de primeiro nível no **PageHeader** (não TopBar kit Comercial).
- Workspaces com sidebar própria (Processos / Configurações).
- Sem command palette / PageHero de produto.

### Capabilities (mapa CURRENT)

| Área | Capability | Superfície |
|---|---|---|
| Resultados | Dashboard (resumo, evolução, ranking, alertas, famílias, export) | `DashboardPage` |
| Processos | Lista + workspace (processo / melhoria / revisão) | `ProcessesPage`, `ProcessWorkspacePage` |
| Diagramas | Macro + escopo + overlay + Mermaid | `DiagramEditorPage` |
| WBS | Decomposição / mapeamento | workspace processo |
| Matriz | Impacto × esforço | revisão |
| Governança | Atas Transforma+ + assinatura | meeting-minutes pages |
| Admin | Administração → Configurações: filiais, departamentos, catálogo de recursos | settings. Data transfer é uso normal |
| Conversacional | TÉO (ChatGPT Actions) | fora do MFE |

### AuthZ

Permissions canônicas no manifesto (amostra):

- `transformometro.view`
- `transformometro.processes.manage`
- `transformometro.revisions.manage`
- `transformometro.measurements.manage`
- `transformometro.investments.manage`
- `transformometro.shared-resources.manage`
- `transformometro.dashboard.recalculate`
- `transformometro.view.consolidated`
- `transformometro.branch.filial-01|02` (+ aliases legado)
- `transformometro.data.transfer`
- `transformometro.meeting-minutes.view|manage|sign` (+ aliases `atas.*`)

Regra: **visibility ≠ authorization**. Backend continua autoridade.

### Backend

API dedicada `transformometro-api`: CRUD, dashboard, diagramas, decomposição, atas, GPT Actions, notificações portal.  
Consumidores: MFE TM, TÉO, api-delpi (Transforma+ gateway), Strategic Indicators (via api-delpi).

---

## 5. Referências internas do monorepo

### Portal Comercial

| Reutilizar | Não copiar |
|---|---|
| Padrão 1 rota `showInMenu: true` + deep routes `false` | Carteiras, sellers, pedidos, faturamento, SLAs |
| Trio `PluginShell` + `pluginRoutes` + `pluginNavigation` + `shellNav` | Badges TOTVS / worklist comercial |
| Factories `createDashboard*` (prefix próprio) | Semântica de «Portal Comercial» no hero |
| Ctrl/Cmd+K + CommandPalette do kit | Conteúdo de catálogo comercial |
| Home hub (cards de caminhos) como *ideia* | Métricas hero comerciais |

Evidência: `plugins/commercial/src/app/PluginShell.tsx`, `commercial.manifest.json`.

### Outros portais

| Fonte | Lição |
|---|---|
| **Supplies** | Melhor espelho estrutural do Comercial (mesmo esqueleto) — preferir como template de *wiring* |
| **Financial** | `FinAppShell`/`FinRail` — **não** usar como modelo do TM |
| **Maintenance** | TopBar kit simples — útil só se TM quiser chrome mínimo (não hub) |

### plugin-ui

Reuse **DIRECTLY** (via factories no MFE):

- `TopBar` / collapse hamburger+overflow
- `PageHero`
- `CommandPalette` + `TopBarSearchTrigger`
- `CatalogSearchBar`, `SectionRouteCard`, `HubChipRow`, `NavigationCard`

**Não existe** `PluginShell` no kit — shell é composição local do MFE.

Abstraction Gate: extrair para `plugin-ui` só se 2+ portais compartilham semântica estável **e** owner claro; hoje Comercial/Supplies já compartilham o kit — o shell permanece no plugin.

---

## 6. Visão TARGET do Portal Transformômetro

```text
Minha DELPI / Portal Host
    |
    +-- Portal Comercial
    +-- Portal Suprimentos
    +-- Portal Transformômetro          ← EXPERIÊNCIA (mesmo app id)
            |
            +-- Início (Home operacional)
            +-- Processos
            +-- Melhorias                 ← agrupamento de capabilities existentes
            +-- Resultados
            +-- Governança
            +-- TÉO (entrada + contexto)
            +-- Administração
            |
            +-- [futuro] Diagrama → BPMN Modeler (contrato)
```

Diagrama ASCII de boundaries:

```text
┌─────────────────────────────────────────────────────────────┐
│ Portal Host (Core routes + JWT + menu global)               │
├─────────────────────────────────────────────────────────────┤
│ MFE transformometro                                         │
│  ┌────────────── PluginShell (TARGET) ───────────────────┐  │
│  │ TopBar | Nav | Search/Palette | TÉO entry | User ctx   │  │
│  ├────────────────────────────────────────────────────────┤  │
│  │ Home | Process Workspace | Resultados | Atas | Admin   │  │
│  └────────────────────────────────────────────────────────┘  │
│                         │ JWT                                 │
│                         ▼                                     │
│              transformometro-api (owner domínio)              │
└─────────────────────────────────────────────────────────────┘
        │                              │
        ▼                              ▼
   TÉO (GPT Actions)            BPMN Modeler (futuro BC)
   capability ≤ user            contrato explícito only
```

---

## 7. Arquitetura de informação TARGET

Validar categorias contra capabilities **reais** (sem categoria vazia):

| Nav TARGET | Conteúdo PROVEN a abrigar | Status |
|---|---|---|
| **Início** | Home operacional (nova) | TARGET |
| **Processos** | Lista + workspace + diagramas + WBS | PROVEN (reorganizar) |
| **Melhorias** | Instâncias/melhorias + priorização (matriz) + revisões no contexto | PROVEN parcial — hoje vive no workspace de processo |
| **Resultados** | Dashboard atual (métricas, alertas, famílias, export) | PROVEN (renomear/reposicionar) |
| **Governança** | Atas, pendências de assinatura, minha assinatura, timeline/audit quando exposto | PROVEN (atas) |
| **TÉO** | Entrada conversacional + deep links contextuais | TARGET (TÉO já existe fora do MFE) |
| **Administração** | Settings (unidades/depts/recursos) + data transfer | PROVEN |

**Macroprocessos** como item de menu: só se capability distinta for inventariada — hoje WBS/decomposição vive no processo → **não** criar nav vazia.

---

## 8. Home

Pergunta norte: *«O que está acontecendo na transformação e o que precisa da minha atenção?»*

### Wireframe ASCII (TARGET)

```text
┌──────────────────────────────────────────────────────────────┐
│ Transformômetro                    Buscar    TÉO    Conta    │
├──────────────────────────────────────────────────────────────┤
│ Início | Processos | Melhorias | Resultados | Governança | … │
├──────────────────────────────────────────────────────────────┤
│ Gestão da Transformação e Melhoria de Processos              │
│                                                              │
│ [Processos] [Melhorias] [Ganhos] [Pendências atas]           │
│                                                              │
│ Precisa da sua atenção                                       │
│  · Atas aguardando assinatura                                │
│  · Alertas de economia negativa                              │
│  · Datas alvo / due-dates                                    │
│                                                              │
│ Resultados recentes          │  Atalhos                      │
│  economia líquida / horas    │  Novo processo · Abrir atas   │
│  ROI / investimento          │  Trabalhar com TÉO            │
└──────────────────────────────────────────────────────────────┘
```

### Cards propostos

| Card | Objetivo | Fonte / API | AuthZ | Freshness | Status |
|---|---|---|---|---|---|
| Resumo ganhos | Economia líquida/bruta, horas, ROI, investimento | `GET /dashboard/summary` | `transformometro.view` (+ branch/consolidado) | sob demanda / cache dashboard | **PROVEN** |
| Alertas economia | Atenção a tendências negativas | `GET /dashboard/alerts` | view | sob demanda | **PROVEN** |
| Due dates | Compromissos/datas alvo | `GET /dashboard/due-dates` | view | sob demanda | **PROVEN** |
| Por família | Rateio consolidado | `GET /dashboard/by-family` | view | sob demanda | **PROVEN** |
| Ranking processos | Top processos no período | `GET /dashboard/processes` | view | sob demanda | **PROVEN** |
| Atas pendentes | Assinaturas do usuário | `GET .../meeting-minutes/pending-signatures` | `meeting-minutes.view|sign` | sob demanda | **PROVEN** |
| Evolução | Série temporal | `GET /dashboard/evolution` | view | sob demanda | **PROVEN** |
| Atalhos | Navegação (processos, atas, settings) | client-only | visibility por rota | — | **TARGET** (wiring) |
| «Trabalhar com TÉO» | Abrir especialista | link externo / deep-link chat GPT | capability ≤ user | — | **TARGET** |
| Fila unificada «atenção» | Merge de atas+alertas+dues | composição frontend Fase 3 | união AuthZ | — | **TARGET** (sem BFF) |
| Atividade recente / audit | Timeline | audit APIs / process timeline | manage/view | — | **TO_INVENTORY** |

**Fase 1 Home mínima:** hero + atalhos + 2–4 cards **PROVEN** (summary + pending atas + alerts), sem novo endpoint.

---

## 9. Navegação e rotas

### Rota raiz

TARGET: `/apps/transformometro` → **Home** (não mais Dashboard).

Dashboard migra para `/apps/transformometro/dashboard` **ou** grupo Resultados (preservar path atual).

### Deep links (preservar)

- Processo / instância / revisão
- Editor de diagrama
- Atas (detail, sign, pending, my-signature)
- Settings
- Data transfer
- Aliases PT
- Links emitidos por TÉO / notificações portal (`action.portal_route`)

### Redirects / aliases

| Caso | Estratégia |
|---|---|
| `/apps/transformometro` deixa de ser dashboard | Redirect **explícito** documentado **ou** Home com card «Ir ao dashboard» na Fase 1; preferir Home nova + dashboard no mesmo path antigo |
| Paths PT | Manter canonicalize |
| Bookmarks dashboard | Path `/dashboard` permanece |

### Browser navigation

Aceite Fase 1: back/forward, refresh em rota interna, `DELPI_NAVIGATE` / `DELPI_EMBEDDED_ROUTE`, unsaved-change guards existentes.

---

## 10. Shell

TARGET (inspirado Comercial/Supplies + kit):

| Peça | Decisão |
|---|---|
| Top bar | `createDashboardTopBar` prefix `tm` |
| Nav 1º nível | Itens caps-gated (Início, Processos, …) |
| Conteúdo | Outlet das páginas atuais dentro do shell |
| User context | Escopo filial / consolidado (já existe no dashboard) — **não** inventar perfil AuthZ |
| Busca | Fase 2–6: CatalogSearchBar / CommandPalette sobre catálogo de rotas TM |
| Responsive | collapse hamburger+overflow (kit) |
| Loading/error | Padrões page excellence / estados existentes |

Persistência: shell **não remonta** ao navegar entre seções (diferença vs PageHeader por página).

---

## 11. Process Workspace

O workspace atual (`ProcessWorkspaceShell`) permanece o **contexto profundo** do processo.

No portal:

```text
Nav Processos → lista
  → abre workspace (sidebar processo/melhoria/revisão)
  → diagramas / WBS / matriz / medições no contexto
```

Não achatar workspace em páginas soltas. Shell do portal **envolve** o workspace; sidebar do processo continua dona do contexto.

---

## 12. Melhorias

Hoje: melhorias = instâncias + revisões **dentro** do processo.

TARGET de informação:

- atalho «Melhorias» pode listar/filtrar instâncias abertas (**TO_INVENTORY** se API de lista global adequada);
- priorização via matriz (Playbook 21) no contexto da revisão;
- não criar domínio paralelo «oportunidade» sem contrato.

---

## 13. Resultados e medições

Dashboard atual **é** a capability de Resultados.

TARGET: item de nav «Resultados» → dashboard existente (path estável).  
Medições/investimentos/recursos continuam no contexto de revisão (não migrar para nav raiz sem necessidade).

---

## 14. Governança / atas

PROVEN: meeting-minutes + pending + my-signature + notificações portal.

TARGET: grupo Governança no shell; deep links e magic links inalterados.

---

## 15. TÉO no Portal

### Invariantes

```text
TÉO capability <= authenticated user capability
perfil/contexto ≠ autorização
confirmação conversacional ≠ AuthZ
frontend ≠ autoridade
```

Writes: UNDERSTAND → READ → PREPARE → VALIDATE → SHOW → CONFIRM → WRITE → READ-BACK → VERIFY → REPORT.

### UX TARGET

| Entrada | Comportamento |
|---|---|
| Botão global «TÉO» | Abre especialista (URL ChatGPT / instrução) sem elevar permissão |
| Ações contextuais | «Analisar este processo», «Revisar melhoria», «Interpretar medição», «Preparar pauta» — passam **contexto** (ids/rotas), não grants |
| Home | Atalho «Trabalhar com TÉO» |

Separar **CONTEXT** (onde o usuário está) de **AUTHORITY** (o que a API permite).

Handoff: 02 TÉO / Actions — alinhar deep links e copy; sem mudar OpenAPI nesta fase documental.

---

## 16. Integração futura BPMN Modeler

Estado HEAD: editor **BPMN-lite** vive no TM (Playbook 19).  
BC «BPMN Modeler» dedicado: **não localizado** no monorepo nesta passagem → **TO_INVENTORY / TARGET**.

Reserva de integração:

```text
Portal TM → Processo → Diagrama
                 ↓ (contrato futuro)
            BPMN Modeler BC
```

Proibido até contrato aprovado: compartilhar banco, importar internals, segunda fonte de verdade, antecipar OpenAPI.

Fase 5 deste playbook.

---

## 17. AuthN / AuthZ

| Camada | Papel |
|---|---|
| Keycloak | AuthN |
| Core + manifesto | Registro permissions/routes |
| transformometro-api | AuthZ efetiva |
| Shell | Esconde nav sem capability (**visibility**) |

Não redesenhar RBAC para «ficar bonito». Agrupar nav não cria permissions novas.

Aliases legado (`atas.*`, `view.filial-*`) permanecem até depreciação documentada.

---

## 18. Contratos e APIs

Fase 1–2: **frontend-first**, contratos atuais.

| Necessidade Home | Contrato existente? | Ação |
|---|---|---|
| KPIs | `/dashboard/summary` | Reusar |
| Alertas | `/dashboard/alerts` | Reusar |
| Due dates | `/dashboard/due-dates` | Reusar |
| Pendências atas | `/meeting-minutes/pending-signatures` | Reusar |
| Fila unificada | Não | Compor no MFE; BFF só se performance/AuthZ exigir (handoff 01) |

Não criar `GET /portal-home` nesta evolução inicial.

---

## 19. Estratégia de reutilização de frontend

| Primitive | Owner atual | Consumers | Decisão | Evidência |
|---|---|---|---|---|
| TopBar | plugin-ui | Comercial, Supplies, … | **REUSE DIRECTLY** | `layout/TopBar.tsx` |
| PageHero | plugin-ui | Comercial Home | **REUSE DIRECTLY** | `PageHero.tsx` |
| CommandPalette | plugin-ui | Comercial | **REUSE DIRECTLY** (Fase 6) | `CommandPalette.tsx` |
| SectionRouteCard / HubChipRow | plugin-ui | Comercial Home | **REUSE DIRECTLY** | layout/* |
| PluginShell composição | MFE Comercial/Supplies | 2 portais | **REIMPLEMENT LOCALLY** (esqueleto Supplies) | sem PluginShell no kit |
| TransformometroNav / PageHeader nav | TM | só TM | Manter até migração; depois reduzir | `TransformometroNav.tsx` |
| ProcessWorkspaceShell | TM | só TM | **REUSE DIRECTLY** (domínio) | workspace |
| FinRail | Financial | Financial | **DO NOT USE** | outro modelo |
| ShellUserPortfolioMenu | Comercial | Comercial | **DO NOT USE** | semântica carteira |

---

## 20. Migração incremental

### Fase 0 — Inventory / Contract freeze

- Congelar este playbook + inventário rotas/permissions/APIs.
- Decidir naming Home vs Dashboard.
- Confirmar wiring menu Portal (`showInMenu`) — TO_INVENTORY.

### Fase 1 — Portal shell

- Introduzir `PluginShell`-like (wiring Supplies).
- `/apps/transformometro` → Home mínima.
- Páginas existentes dentro do shell.
- Deep links + aliases + guards preservados.
- **Sem** mudança backend obrigatória.

### Fase 2 — Information architecture

- Nav agrupada (Processos / Resultados / Governança / Admin).
- Ajustar labels; workspaces intactos.

### Fase 3 — Operational Home

- Cards PROVEN (summary, alerts, dues, pending atas).
- Atalhos; fila «atenção» composta no cliente.

### Fase 4 — TÉO integration

- Entry points + ações contextuais (CONTEXT only).
- PREPARE/ACT inalterado.

### Fase 5 — BPMN Modeler integration

- Somente após BC/contrato aprovados.

### Fase 6 — Optimization

- Command palette, busca, badges, realtime se justificado, telemetry.

---

## 21. Acceptance criteria por fase

### Fase 1 (mínimo)

- [ ] `/apps/transformometro` abre Home
- [ ] Shell persiste entre navegações
- [ ] Páginas existentes acessíveis
- [ ] Deep links (processo, ata, diagrama, settings, data) OK
- [ ] Back/forward OK
- [ ] Refresh em rota interna OK
- [ ] Permissions respeitadas (403 backend)
- [ ] Guards unsaved changes OK
- [ ] Atalhos externos / notificações portal OK
- [ ] Responsive sem regressão grave
- [ ] Nenhum backend alterado sem necessidade
- [ ] Nenhuma authority mudou

### Fases 2–6

Critérios específicos derivados dos cards/nav/TÉO/BPMN desta seção; validar no handoff 07.

---

## 22. Deploy / rollback

Inventário ops (PROVEN parcial):

| Peça | Fonte |
|---|---|
| Docker compose / gateway paths | OPERATIONS, DEPLOYMENT API |
| Rebuild MFE `transformometro` | remoteEntry |
| Rebuild API se houver contrato | só se Fase exigir |
| Manifest / Core register | `register-manifest.sh` — impacto se `showInMenu` mudar |
| Cache CDN remoteEntry | `docs/06-portal-frontend/portal-deploy-cache-cloudflare.md` (**TO_INVENTORY** aplicação ao TM) |

Rollback Fase 1: reverter MFE para build anterior (Home=dashboard); manifesto só se alterado.

---

## 23. Observabilidade / métricas

| Métrica candidata | Status |
|---|---|
| Tempo até encontrar processo | TARGET |
| Cliques até capability | TARGET |
| Uso da Home | TARGET |
| Deep-link success / 404 internos | TO_INVENTORY |
| Uso contextual TÉO | TARGET |
| Telemetry existente no MFE | TO_INVENTORY (não assumir) |

Não inventar pipeline de métricas nesta fase documental.

---

## 24. Risks

| Risco | Mitigação |
|---|---|
| Quebra de bookmarks ao mudar home | Preservar `/dashboard`; migrar raiz com aceite explícito |
| Copiar Comercial demais | Abstraction Gate + espelho Supplies |
| Nav esconde capability ≠ AuthZ | Mensagens 403; testes negativos |
| Pressão por BFF home | Compor cliente até evidência contrária |
| BPMN Modeler «absorvido» cedo | Fase 5 bloqueada sem contrato |
| Dirty tree / deploy paralelo | Isolar PRs só do MFE portal |

---

## 25. Gaps

1. Entrada de menu Portal com todas `showInMenu=false` — **TO_INVENTORY**.
2. Lista global de «melhorias abertas» para nav Melhorias — gap API possível.
3. BC BPMN Modeler ainda não materializado no repo.
4. TÉO ainda fora do chrome MFE (só Custom GPT).
5. Telemetry de produto ausente no inventário.

---

## 26. Decisions needed

1. Home na raiz **substitui** dashboard ou dashboard permanece raiz com Home em `/home`?
2. Item de menu global: criar rota manifesto `showInMenu:true` em `/apps/transformometro`?
3. «Melhorias» como nav de 1º nível agora ou só atalho no workspace (Fase 2)?
4. TÉO: deep link ChatGPT vs superfície interna futura?
5. Quando abrir inventário formal do BPMN Modeler BC?

---

## 27. Handoffs

| Trilha | Escopo |
|---|---|
| **05 Frontend & UX** | Shell, Home, nav, deep links, responsive, reuse kit |
| **01 Backend & Domain** | Só se Home exigir agregação/AuthZ impossível no cliente |
| **02 TÉO / Actions** | Entry points, contexto de rota, copy; sem relaxar AuthZ |
| **06 Security** | Revisar visibility vs permissions; manifesto `showInMenu` |
| **07 Integration & Acceptance** | Aceite Fase 1–3; regressão deep links/notificações |
| **08 Documentation** | Manter este playbook + status-atual + OPERATIONS |
| **BPMN Modeler** | Contrato de integração (Fase 5) |

---

## 28. Roadmap executivo

**Histórico (2026-09-17).** Não usar esta tabela para ordenar o Portal Transforma+. Sequência vigente: [ARCHITECTURE-RUNWAY.md](./ARCHITECTURE-RUNWAY.md).

| Fase | Objetivo | Owner | Dependências | Contract impact | Status |
|---|---|---|---|---|---|
| 0 | Freeze inventário | 08 + 05 | Este doc | NONE | **PLANNED** |
| 1 | Shell + Home mínima | 05 | Fase 0; kit plugin-ui | Manifesto possível (`showInMenu`) | **PLANNED** |
| 2 | IA / nav agrupada | 05 | Fase 1 | Baixo (rotas labels) | **PLANNED** |
| 3 | Home operacional | 05 (+01 se gap) | APIs dashboard/atas | Prefer NONE | **PLANNED** |
| 4 | TÉO no chrome | 02 + 05 | TÉO go-live | Baixo | **PLANNED** |
| 5 | BPMN Modeler | BC + 05 | Contrato BC | Contrato novo | **TARGET** |
| 6 | Palette / polish | 05 | Fases 1–3 | NONE | **TARGET** |

---

## 29. Definition of Done do Portal

O Portal Transformômetro está **Done** quando:

1. Experiência de portal (shell persistente + Home operacional) em produção.
2. Cadeia PROCESSO→…→APRENDIZADO navegável sem perder deep links.
3. AuthZ inalterada em autoridade (backend-first).
4. TÉO contextual sem elevação de privilege.
5. Dashboard/resultados e governança/atas acessíveis na IA acordada.
6. BPMN Modeler, se existir, integrado só por contrato.
7. Aceite Fase 1+3 verde; OPERATIONS/status-atual atualizados.
8. Sem BFF desnecessário; sem segunda fonte de verdade.

---

## Apêndice A — Relação com documentos existentes

Este playbook **complementa** (não substitui):

- [ROADMAP.md](./ROADMAP.md) — fases de domínio já entregues (0–7+)
- [ARCHITECTURE.md](./ARCHITECTURE.md)
- [PLAYBOOK-18…23](./) — capacidades de domínio
- [OPERATIONS.md](./OPERATIONS.md)
- GPT Actions em `transformometro-api/docs/gpt-actions/`

Atualizar [README.md](./README.md) com link canônico a este arquivo.

## Apêndice B — Residual search (2026-09-17)

Termos: Portal Comercial, PluginShell, transformometro, portal, shell, home, dashboard, command palette, plugin-ui, manifest, roadmap, bpmn modeler.

Achados materiais:

- Padrão shell = Comercial **e** Supplies; Financial diverge.
- TM sem PluginShell; home=dashboard.
- Docs TM em `docs/12-roadmap-e-evolucao/transformometro-app/`.
- Sem artefato «BPMN Modeler» BC no grep do monorepo.
- `useDelpiPortalBridge` confirma deep-link host.
- Índice global `docs/12-roadmap-e-evolucao/roadmap.md` **não** lista Transformômetro — referência produto fica no README do módulo (padrão local).
