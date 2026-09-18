# Portal Transforma+ — blueprint técnico e de UX

> **Status:** desenho implementado no MFE; runtime visual = TEST_NOT_RUN. Classificação: **IMPLEMENTED_NOT_RUNTIME_PROVEN**.
> Pacote de escopo: [WAVE-1-IMPLEMENTATION-PACKET.md](./WAVE-1-IMPLEMENTATION-PACKET.md). Ordem: [ARCHITECTURE-RUNWAY.md](./ARCHITECTURE-RUNWAY.md).
> Wave 1 design foi aprovada e a fatia foi implementada. Browser smoke não foi executado neste passe.

## Navegação — IA congelada

TopBar funcional: Início, Visão geral, Meus processos, Administração, Ajuda. Busca da TopBar usa `CommandPalette` e `TopBarSearchTrigger` de `@delpi/plugin-ui` e indexa só caminhos do portal, não entidades. Favoritos continuam fora: não há contrato público de favorito de rota.

Target oculto, não PROVEN: Sala de interação, Minhas tarefas. Utility oculta: Usuário. Favoritos de rota deste portal são preferência local do MFE (`localStorage` `transformometro.portal.favorites.v1`), com estrela no `SectionRouteCard` e gatilho ao lado de Buscar. Não usam `commercial-api` nem a tabela de app da Core. Ajuda é página `/apps/transformometro/help`, conteúdo em `userManualContent.ts`, permission herdada do prefixo `transformometro.access`.

Launcher do Início: Gestão, Processos, Registros, Administração, Ajuda. Configurações não é card nem item da TopBar. Fica em Administração → Configurações. Exportar/Importar fica em Registros e exige `transformometro.access`. Administração exige `transformometro.manage`. Ajuda é rota interna `/apps/transformometro/help` (alias `/ajuda`). Não entra no `manifest.routes` e não cria permission. O guard do portal resolve pelo prefixo `/apps/transformometro` = `transformometro.access`. `HELP_ROUTE_MANIFEST_ENTRY = NOT_REQUIRED`. Favoritos = `TO_INVENTORY`. Sem Keycloak novo e sem terceira permission.

## 1. Stack provada

Frontend (`plugins/transformometro/package.json`): React 19.2.7, Vite 7, Module Federation (`@originjs/vite-plugin-federation`), TypeScript, Vitest, ESLint, lucide-react, recharts, mermaid, xyflow. Sem React Router, TanStack Query, Redux, Zustand, React Hook Form, Formik, Zod, Yup ou Axios. Cliente HTTP: `fetch` + `parseApiEnvelope` em `transformometroHttp.ts`. Estado: `useState` / `useEffect` / `useCallback`. Roteamento: `parseTransformometroPath` + `onNavigate`. CSS: `index.css` e CSS de página, breakpoints já usados (540, 720, 760, 768, 900, 980, 1100). Confirmação: `useConfirm`. Aviso: `useFloatingNotice`. Não há Error Boundary nem feature flag no MFE. Não há Playwright no `package.json`. Teste de UI: Vitest.

Backend: FastAPI, repositórios `PluginBaseRepository` com psycopg (não SQLAlchemy no repositório de processo), migrations SQL versionadas no schema `transformometro`, pytest. AuthZ de lista: `filter_rows_for_access` em `list_processos`. Envelope `{success, message, data}`. MCP e GPT Actions são adapters. `ProcessContextService` continua `OPEN_NON_BLOCKING` e **não entra** neste desenho.

## 2. Padrões

| Concern | Padrão atual | Usar no portal? |
|---|---|---|
| Routing | parser manual, paths em `routes.ts` | PROVEN_USE |
| Fetch | `fetch` + envelope | PROVEN_USE |
| Cache de servidor no MFE | nenhum cliente de cache; dashboard tem cache no backend | PROVEN_USE. Não introduzir Query nesta wave |
| Forms | estado local + validação no submit | PROVEN_USE. Wave 1 quase não escreve |
| Tabela / filtro | `ProcessFolderBrowser`, `status` + `q` | PROVEN_USE |
| Modal / toast | `ConfirmDialogProvider`, `FloatingNoticeProvider` | PROVEN_USE |
| Ícone | lucide-react | PROVEN_USE |
| i18n | textos em pt-BR no componente. Sem biblioteca | PROVEN_USE |
| E2E | não há framework no plugin | TO_INVENTORY. Aceite da wave pode ser Vitest + smoke manual até existir runner |
| ORM | não é o padrão do repositório TM | PROVEN_AVOID para esta wave |

## 3. Onde cada tela vive

| Tela | Dono | Raiz atual |
|---|---|---|
| Shell | MFE TM | `TransformometroShell` + `TransformometroNav` |
| Início / visão geral | MFE TM | `DashboardPage` |
| Lista | MFE TM | `ProcessesPage` |
| Workspace | MFE TM | `ProcessWorkspaceShell` / `processWorkspaceNav.ts` |
| Atas | MFE TM | `MeetingMinutesPage` e rotas de ata |
| Configurações | MFE TM | Administração → `settingsWorkspaceNav.ts` — unidades, departamentos, recursos |
| Exportar | MFE TM | `DataTransferPage` |

Kit em `@delpi/plugin-ui`. O MFE compõe `TopBar`, `PageHero`, `NavigationCard`, `SectionCard`, `KpiCard`, `FiltersRow` e `CommandPalette` pelo shell atual. Não importa internals do Comercial e não cria `PluginShell`.

Decisão vigente: `TransformometroShell` + `PageHeader`. Sala, tarefas, favoritos e usuário continuam `TO_INVENTORY`. Ajuda é a página do manual.

## 4. Informação — Wave 1

```text
Início            launcher. Não repete o dashboard inteiro.
Visão geral       o dashboard que já existe.
Meus processos    lista autorizada. Não é "processos de que sou dono".
Atas              fluxo atual.
Administração     container. Exige manage.
  Configurações   catálogos do domínio. Não é área principal nem admin de Keycloak/Core.
Exportar/Importar fluxo atual, com confirmação de replace. Fica em Registros.
```

Fora da nav: Sala, Tarefas, Portfólio, Diagnóstico, definição de KPI, plano, arquitetura corporativa, Favoritos. Ajuda é item da TopBar e página do manual.

## 5. Wireframes Wave 1

Cada tela: propósito, dado, ação, estados, contrato. Responsivo: abaixo de 900px a nav do workspace já empilha (`index.css`). Tabela larga rola; não virar card nesta wave. Filtro permanece na página, sem drawer novo. Foco e rótulos seguem o que a página já faz (`StatusAlerts`, `aria-label` no modo de importação). Status não depende só de cor onde já existe texto.

### Início

Propósito: orientar. Dado: nenhuma lista "recentes" (não há fonte). Ação: navegar.

```text
┌──────────────────────────────────────────────────┐
│ Transformômetro          [nav do shell atual]    │
├──────────────────────────────────────────────────┤
│ Portal Transforma+                               │
│ Transformação e melhoria de processos            │
│                                                  │
│ [Meus processos] [Visão geral] [Atas]            │
│ [Exportar / Importar]                            │
│ [Administração] só com manage                    │
└──────────────────────────────────────────────────┘
```

Nome do usuário só se o token já expuser nome nesta tela. Sem fonte, o hero não inventa "Bom dia". Loading: shell. Erro: não há fetch próprio. 403: a rota seguinte responde.

### Visão geral

Propósito: gestão à vista. Dado: `fetchDashboardResumo`, evolução, processos, alertas, família, vencimentos — o que `DashboardPage` já busca. Ação: filtrar com os params atuais. Sem métrica nova.

```text
┌──────────────────────────────────────────────────┐
│ Visão geral                          [atualizar] │
│ [filtros já existentes]                          │
│ [KPI] [KPI] [KPI] [KPI]                          │
│ [evolução]                                       │
│ [alertas de economia] [revisões a vencer]        │
└──────────────────────────────────────────────────┘
```

Loading / erro / vazio: os de `DashboardPage`. 403 ≠ gráfico vazio.

### Meus processos

Propósito: abrir um processo visível. Dado: `GET /processes` → `list_processos` (`status`, `q`; backend também aceita filial, setor, família). Sem página. Sort local já testado em `processListSort.test.ts`. Clique na linha abre o workspace.

```text
┌──────────────────────────────────────────────────┐
│ Meus processos                                   │
│ Processos visíveis no seu acesso                 │
│ [Buscar] [Status]                                │
│ Código | Processo | Status | …                   │
└──────────────────────────────────────────────────┘
```

Filtros de setor/filial na UI são alvo futuro: o endpoint aceita, a `ProcessesPage` hoje não manda. Wave 1 não é obrigada a acrescentar esses filtros. Mobile: a lista atual (`tm-processo-browser`) já quebra em 900px. Empty: mensagem atual, só quando `error` é nulo. 403: `StatusAlerts`, texto "Acesso negado".

### Workspace

Propósito: operar o processo com as seções PROVEN. Sem diagnóstico, SIPOC, plano ou definição de KPI na nav ativa.

```text
┌────────────┬─────────────────────────────────────┐
│ Visão geral│                                     │
│ Dados      │  seção atual                        │
│ Mapeamento │                                     │
│ Diagrama   │                                     │
│ Arquivos   │                                     │
│ Melhorias  │                                     │
│ Priorização│                                     │
│ Timeline   │                                     │
└────────────┴─────────────────────────────────────┘
```

Writes existentes (cadastro, diagrama, árvore, revisão, medição) continuam nos seus handlers. O shell não cria write.

### Atas

Lista, filtro e status atuais. Pendência em `/meeting-minutes/pending`. Detalhe, editor e assinatura não mudam de fluxo. Estados: loading da página, lista vazia, erro, 403.

### Configurações

Subárea de Administração, não caminho de primeiro nível. Unidades, departamentos e catálogo de recursos compartilhados. O CRUD administrativo exige `transformometro.manage`. A consulta para operar um processo continua `access`. Identidade e RBAC ficam no Keycloak e no Core. A tela não ganha gestão de usuário.

### Exportar / Importar

Export JSON/pacote e import com preview. Modo `replace` pede `useConfirm` ("Substituir"). Erro via `fail`. Permissão `transformometro.data.transfer`. Não redesenhar o contrato. O arquivo importado não é autoridade de AuthZ.

## 6. Tela → contrato

| Tela | Fonte | Write novo | Backend novo | MCP | Actions |
|---|---|---|---|---|---|
| Início | nenhuma API própria | não | não | não | não |
| Visão geral | dashboard já usado | não | não | não | não |
| Meus processos | `list_processos` | não | não | não | não |
| Workspace | APIs já do workspace | os writes atuais, sem ampliação | não | não | não |
| Atas | meeting-minutes | fluxo atual | não | não | não |
| Configurações | CRUD de catálogo, sob Administração | fluxo atual | não | não | não |
| Exportar | backup JSON | fluxo atual | não | não | não |

Cache: sem React Query. Invalidação continua a que cada página já faz no `load()`. Abort existe em algumas buscas (ata, presença), não é padrão global. N+1 do dashboard (vários `fetchDashboard*`) é CURRENT_RISK, não bloqueia a wave: não criar endpoint agregado só para o wireframe.

## 7. Estados

| Página | Loading | Empty | Error | 403 |
|---|---|---|---|---|
| Início | shell | não se aplica | não se aplica | na rota de destino |
| Visão geral | dashboard | sem linhas no período | `StatusAlerts` / equivalente da página | acesso negado |
| Meus processos | `ProcessFolderBrowser` | mensagem de lista vazia | `error` | não usar a mensagem de vazio |
| Workspace | por seção | seção vazia já existente | por seção | por seção |
| Atas / config / export | página atual | página atual | página atual | página atual |

## 8. Pastas

Wave 1 não impõe `features/portal`. O código novo de nav, se vier, fica junto de `TransformometroNav` e `App.tsx`. Backend da Wave 1: nenhuma pasta nova.

Futuro, só como padrão já usado pela API: `domain` / `application` / `infrastructure` / `interface`. Não criar ports estéticos.

## 9. Testes

Vitest no MFE (nav, parser, lista, 403). Pytest na API só se alguém tocar handler — a wave não deve. MCP/Actions: não. E2E automatizado: TO_INVENTORY. Smoke de browser entra no DoD quando houver deploy, não neste documento.

## 10. Riscos

| Risco | Classe |
|---|---|
| Lista sem paginação | CURRENT_RISK. Não bloqueia |
| Vários fetches do dashboard | CURRENT_RISK. Não bloqueia |
| Tabela no mobile | CURRENT_RISK. Scroll existente |
| Trocar o shell inteiro para TopBar | FUTURE_RISK. Proibido nesta wave |
| `ProcessContextService` | OPEN_NON_BLOCKING. Fora do desenho |

## 11. Segurança

O MFE não decide quem vê o processo. Quem tem acesso ao portal vê os processos de todas as unidades. Filial filtra a Visão geral e não autoriza. A Core API decide `access` e `manage`. Desenho em [AUTHZ-FINAL-DESIGN.md](./AUTHZ-FINAL-DESIGN.md). Não é runtime.

## 12. Alvo futuro — wireframes baixos

Não são UI ativa. Owner de plano, portfólio, tarefas e sala continua TO_INVENTORY.

**Escopo / SIPOC** — view, não tabela `sipoc`. Gatilho, fim, fornecedor, entrada, etapa, saída, cliente, sistema, regra. Ao lado do escopo organizacional, com outro nome.

**Diagnóstico** — achado, tipo, etapa, evidência, estado (`OBSERVED` / `INFERRED` / `UNKNOWN`). Causa ao lado, marcada como hipótese.

**Indicadores** — bloco Definição (nome, fórmula, unidade, direção, fonte, frequência, meta) separado do bloco Medição (valor, período). A medição atual permanece o valor.

**AS-IS × TO-BE** — duas colunas: baseline e cenário, com mantido / alterado / incluído / removido. Fonte: revisão e overlay. Sem segundo documento.

**Plano** — ação, responsável, prazo, status, dependência, evidência, resultado. Sem store até o owner existir.

**Portfólio** — projeção: processos visíveis, melhorias, pendências com fonte. Sem entidade.

**Tarefas** — só o que já tem fonte (assinatura pendente, vigência). O resto não entra no wireframe como fila.

**Sala** — caixa vazia com o rótulo "sem owner". Não desenhar chat.

**Arquitetura** — empresa → cadeia → macroprocesso → processo, fora da árvore de um mestre.

## 13. Decisões

| Decisão | Status | Bloqueia código? |
|---|---|---|
| Host = `TransformometroShell` + `PageHeader` | FROZEN | Sim, se alguém trocar o shell |
| Nav da §4 | FROZEN | Sim |
| Paths atuais | FROZEN | Sim |
| Meus processos = todos os processos de quem tem access. Unidade não filtra | SUPERSEDED_BY_BUSINESS_DECISION | A linha anterior «escopo autorizado» não vale |
| Sem backend/MCP/Action/migration/permissão nova | FROZEN | Sim |
| 403 ≠ vazio | FROZEN | Sim |
| TopBar / CommandPalette | PROVEN no código; aceite visual pendente | Não |
| Ajuda página | IMPLEMENTED_AWAITING_VISUAL_ACCEPTANCE | Não |
| Favoritos de rota | TO_INVENTORY — sem contrato público | Sim, se copiar o Comercial |
| Paginação, filtros extras de filial na lista | DEFERRED | Não |
| KPI, plano, portfólio, sala, tarefas, arquitetura | TO_INVENTORY | Não nesta wave |
| Nome no hero | TO_INVENTORY | Não. Omitir se não houver fonte |

## 14. Handoff

Trilha **05 Frontend & UX**, quando houver autorização separada. **07** no smoke de browser depois do deploy. **01** não entra: não há mudança de API. Critério de saída do desenho: este arquivo + o pacote da Wave 1. Critério de saída da implementação, no futuro: DoD do runway, com SHA e smoke. Este passe não é essa saída.
