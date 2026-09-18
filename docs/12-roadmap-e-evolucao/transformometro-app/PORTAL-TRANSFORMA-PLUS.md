# Portal Transforma+ — experiência de produto

> **Status:** TARGET de experiência. **IMPLEMENTATION = NOT AUTHORIZED.**  
> **Sequência:** [ARCHITECTURE-RUNWAY.md](./ARCHITECTURE-RUNWAY.md). As fases A–I abaixo não ordenam implementação.
> **ADR:** [`adr-portal-transforma-plus.md`](../../../transformometro-api/docs/architecture/adr-portal-transforma-plus.md)  
> **Domínio:** [CICLO-INTELIGENCIA-DE-PROCESSO.md](./CICLO-INTELIGENCIA-DE-PROCESSO.md)  
> **Inventário anterior do shell:** [PLAYBOOK-PORTAL-TRANSFORMA.md](./PLAYBOOK-PORTAL-TRANSFORMA.md) (BASE `841637c3e`, 2026-09-17). Este arquivo é o adendo de produto de 2026-09-18, no HEAD `95097815d` mais o inventário abaixo. Não substitui o nome técnico Transformômetro.

```text
PORTAL TRANSFORMA+ PRODUCT TARGET = DOCUMENTED
COMMERCIAL UX REFERENCE = INVENTORIED
COMMERCIAL DOMAIN LOGIC REUSE = FORBIDDEN
SHARED UI REUSE = INVENTORIED
TRANSFORMÔMETRO DOMAIN OWNERSHIP = PRESERVED
MCP/ACTIONS TOOL EXPLOSION = AVOIDED
IMPLEMENTATION = NOT AUTHORIZED
```

Portal Transforma+ não é dono do domínio. Transformômetro continua dono de processo, instância, revisão, medição, melhoria, custo, diagnóstico (quando existir), evidência, diagrama, ata e das demais capabilities já comprovadas. A mudança é shell, informação e workspace. Não há rename de API, schema, tabela, package, MCP, Action, URL ou OpenAPI.

```text
UI PATTERN REUSE != DOMAIN COUPLING
UI PAGE != API ROUTE != MCP TOOL != GPT ACTION
profile != authorization
cargo != authorization
menu oculto != AuthZ
```

AuthZ: quem tem acesso vê todos os processos. Filial não autoriza. Desenho em [AUTHZ-FINAL-DESIGN.md](./AUTHZ-FINAL-DESIGN.md). Não é runtime.

```text
Portal Transforma+
  → capabilities do domínio Transformômetro
  → TÉO como interface conversacional
```

TÉO continua especialista em transformação digital. O nome da experiência não muda o owner das writes.

## Navegação — revisão visual

```text
TOPBAR = estrutura estável
HOME LAUNCHER = catálogo de capabilities
FAVORITES = personalização individual, ainda sem contrato transversal
```

TopBar funcional nesta revisão: Início, Visão geral, Meus processos, Administração. Buscar usa o Command Palette compartilhado só para caminhos do portal.

TARGET, não PROVEN e não exibido: Sala de interação, Minhas tarefas, Ajuda, Favoritos, Usuário. A sala do Comercial não é reutilizada. Pendências de ata não viram Minhas tarefas. `user_favorite_apps` do Core é favorito de app do portal, não atalho deste launcher.

O Início cataloga Operação, Gestão, Registros e Administração. Atas, Configurações e Exportar/Importar continuam nas rotas atuais.

## 1. O que o Transformômetro já mostra

PROVEN em `TransformometroNav` e no parser de rotas. Home atual **é** o dashboard (`/apps/transformometro`).

| Peça | Estado |
|---|---|
| Dashboard, Processos, Atas, Configurações, Exportar/Importar | PROVEN |
| Workspace do processo (visão geral, dados, mapeamento, diagrama, arquivos, melhorias, priorização, timeline) | PROVEN |
| Configurações: unidades, departamentos, recursos compartilhados | PROVEN |
| `PluginShell` dentro do MFE Transformômetro | Ausente. PROVEN que não existe |
| Manual de portal | Ausente. Há tooltips em `helpTooltips` |

Rotas atuais permanecem. Alias futuro e redirect são plano separado. Paths abaixo são conceituais, não contrato.

## 2. Inventário do Portal Comercial

Fonte: `plugins/commercial/src/content/shellNav.ts`, `homeLauncher.ts`, `PluginShell.tsx`, `pluginRoutes.ts`, `OverviewPage.tsx`, `homeFavoritesApi.ts`, `OpenOrdersTable.tsx`, `CustomersTable.tsx`. API de salas e favoritos: `commercial-api`.

Nav PROVEN, nesta ordem: Início, Visão geral, Sala de interação, Minhas tarefas, Meus pedidos, Minha Carteira, Administração, Ajuda. Cada item some se a capability da sessão não permitir. Isso é filtro de menu, não autorização.

| Elemento | Onde | Classe |
|---|---|---|
| `TopBar`, `PageHero`, `CommandPalette`, `NavigationCard`, `KpiCard`, `FiltersRow`, `FilterBarShell`, `SectionCard`, `EmptyState`, `UnderlineNav`, `CatalogSearchBar`, `InitialsAvatar` | `@delpi/plugin-ui` `components/layout` | PROVEN_SHARED · REUSABLE_WITHOUT_CHANGE |
| Tokens / tema | `plugin-ui` theme | PROVEN_SHARED. Auditoria pixel a pixel de breakpoint: TO_INVENTORY |
| `shellNav.ts`, `homeLauncher.ts`, textos «Portal Comercial» | MFE Comercial | COMMERCIAL_SPECIFIC. O padrão de catálogo filtrado por capability é REUSABLE_WITH_ADAPTER (copiar a ideia, não o arquivo) |
| `PluginShell.tsx` | MFE Comercial. Supplies tem o seu | DO_NOT_REUSE por import. ABSTRACTION_CANDIDATE bloqueada: duas cópias parecidas não justificam extração |
| `OpenOrdersTable`, board de faturamento, `CustomersTable` | Comercial | DO_NOT_REUSE |
| Visões Tabela / Cards em pedidos e carteira; Board em pedidos | Comercial | Padrão de view switch é referência. Componente e kanban de pedido: DO_NOT_REUSE |
| Sala de interação, mensagens, pins, menções | `commercial-api` `/interaction-rooms*` | COMMERCIAL_SPECIFIC · DO_NOT_REUSE. Não há sala transversal no Core |
| Minhas tarefas / follow-ups | Comercial (`my-tasks`) | COMMERCIAL_SPECIFIC · DO_NOT_REUSE |
| Favoritos `GET/PUT /me/home-favorites` | `commercial-api` | COMMERCIAL_SPECIFIC. Extração só com Abstraction Gate. TO_INVENTORY |
| Favoritos de **apps** do portal | Core (`reorder_favorite_apps`) | CORE_OWNED. Não é favorito de processo |
| Busca Ctrl+K | Palette do kit + `homeSearchQuery` do Comercial | Palette: PROVEN_SHARED. A query que lista caminhos comerciais: COMMERCIAL_SPECIFIC |
| Perfil / menu de carteiras | `ShellUserPortfolioMenu` | COMMERCIAL_SPECIFIC · DO_NOT_REUSE. Identidade: Keycloak |
| Overview (hero, filtros, KPI, drill-down) | `OverviewPage` + catálogo de métricas comerciais | Página: DO_NOT_REUSE. Padrão hero+filtro+KPI: REUSABLE_WITH_ADAPTER sobre o kit |
| Administração (carteiras, equipe, SLA) | Comercial | DO_NOT_REUSE |
| Manual / glossário comercial | `userManualTermCatalog.ts` | DO_NOT_REUSE o texto. Estrutura de manual: referência |
| Host, menu global, bridge `DELPI_NAVIGATE` | Portal Minha DELPI | PORTAL_HOST_OWNED. Já usado pelo TM (`useDelpiPortalBridge`) |
| RBAC de apps | Core | CORE_OWNED |

Supplies repete o mesmo desenho de nav (Início, Visão geral, Minhas tarefas, …) em arquivo próprio. Isso confirma o padrão, não um componente compartilhado.

Abstraction Gate para extrair o shell: há dois consumidores do **padrão**, não um componente genérico com owner. Parametrizar o `PluginShell` do Comercial arrastaria pedido, carteira e sala. Decisão: implementações independentes até existir chrome sem domínio e um owner (`plugin-ui`).

## 3. Mapa Comercial → Transforma+

Nomes ainda passam por revisão de UX.

| Comercial | Transforma+ | O que muda |
|---|---|---|
| Início | Início | Mesmo papel de saudação, atalho e launcher. Conteúdo é do TM |
| Visão geral | Visão geral do programa de transformação | KPI do dashboard TM, não receita comercial |
| Sala de interação | Sala de processos/melhorias | Sem owner compartilhado. TO_INVENTORY |
| Minhas tarefas | Minhas tarefas | Projeção de obrigações do TM, não follow-up comercial |
| Meus pedidos | Meus processos | Lista autorizada de processos. Não é pedido de venda |
| Minha Carteira | Meu portfólio / Minha carteira Transforma+ | Read model. Não é carteira de cliente |
| Administração | Administração do domínio Transforma+ | Só catálogos já do TM |
| Ajuda | Manual Transforma+ | Glossário de processo, não de pedido |

## 4. Shell alvo

```text
Início
Visão geral
Sala de interação
Minhas tarefas
Meus processos
Meu portfólio
Administração
Ajuda
```

Mais busca, favoritos e perfil/contexto. Sala, tarefas, portfólio, busca de entidade e favoritos não entram no shell implementável enquanto o inventário de owner estiver aberto.

AuthZ: o item pode sumir da nav. A API continua fail-closed.

## 5. Início

Padrão conceitual do Comercial: saudação, highlights, eventos, atalhos, launcher, últimos acessos, favoritos, busca. Últimos acessos do Comercial estão em `homeRecentViews.ts` (estado local daquele MFE). Não copiar a store.

Cards candidatos:

| Card | Classe | Por quê |
|---|---|---|
| Resultados / ganhos medidos (economia líquida e bruta, horas, investimento, ROI) | PROVEN como campos de `DashboardResumo` | Não inventar outro cálculo |
| Revisões vencendo ou vencidas | PROVEN como `DashboardVencimentos` | Não chamar isso de «ação atrasada» |
| Alertas de economia acumulada | PROVEN como `DashboardAlertas` | Não é «processo que precisa de atenção» genérico |
| Processos sob acompanhamento | TO_INVENTORY | Não há relação usuário↔processo além de `access`. Unidade não filtra a lista |
| Melhorias em andamento | TO_INVENTORY | «Em andamento» não tem fase canônica única neste inventário |
| Tarefas pendentes | TO_INVENTORY | Não há task store do TM |
| Ações atrasadas | TARGET | Plano de ação ainda não existe |
| Processos que precisam de atenção | TARGET | Exige regra canônica; o alerta atual não basta |

Hero alvo: «Portal Transforma+» e saudação com o nome do token, se o token já trouxer o nome. Sem nome canônico, não inventar.

## 6. Eventos

O bloco «Eventos e interações» do Comercial lê a fila de tarefas comerciais. Equivalente Transforma+ só com fonte já existente:

| Sinal | Fonte | Classe |
|---|---|---|
| Vencimento de vigência | dashboard vencimentos | PROVEN |
| Alerta de resultado | dashboard alertas | PROVEN |
| Ata com assinatura pendente | `meeting-minutes/pending-signatures` | PROVEN |
| Linha do tempo | timeline / auditoria | PROVEN como histórico, não como inbox |
| Ação vencendo, medição pendente como tarefa, processo aguardando informação | — | TO_INVENTORY |

Não criar motor de notificação.

## 7. Launcher

Categorias conceituais, não arquitetura fechada:

```text
Operação — meus processos, tarefas, mapeamento, pendências
Gestão à vista — visão geral, indicadores, resultados já calculados
Transformação — melhorias, priorização, AS-IS × TO-BE, diagnósticos
Documentos — evidências, atas, arquivos
Ajuda — manual, métodos do TÉO (guia já existente)
Administração — unidades, departamentos, recursos
```

Itens sem capability PROVEN ficam fora do launcher até a fase de domínio correspondente. Métodos do TÉO são atalho para o guia, não menu por metodologia.

## 8. Visão geral

Referência: hero, filtro, período, KPI e drill-down do Overview comercial. A página comercial não se reutiliza.

| KPI candidato | Classe |
|---|---|
| Horas economizadas, ganho (economia), investimentos, ROI | PROVEN em `DashboardResumo` |
| Payback | TO_INVENTORY neste passe. A pergunta de produto existe no overview histórico; não promover o card sem apontar o campo do read model nesta revisão |
| Soluções implementadas | PROVEN como `solucoes_implementadas` no mesmo resumo. Não renomear para «melhorias implantadas» sem conferir a definição do calculador |
| Processos ativos, mapeados, com baseline, cobertura documental, ações atrasadas | TARGET. Sem fonte única neste inventário |
| Filtros período, filial, setor | PARTIAL. O dashboard já aceita parâmetros; a lista completa (família, responsável, status, fase) é TARGET e só entra se o cálculo for canônico |

Indicador financeiro sai de medição, revisão, investimento ou do read model do dashboard. Não de card estático.

## 9. Meus processos

Inspirado em «Meus pedidos». Mostra processos que o backend autoriza. Cargo não define a lista.

Resumo: processos, o que pede atenção (só com regra), melhorias ligadas, pendências com fonte.

Filtros «em mapeamento», «em diagnóstico», «em implantação», «sem baseline», «com pendências» são TARGET. Só implementáveis quando a semântica for calculável. «Todos» e a lista atual são PARTIAL/PROVEN.

Views: Tabela é o alvo natural da lista. Cards é padrão visual já usado no Comercial, refeito no TM se a fase de UI passar. Board por status ou completude não é kanban operacional comprovado. Não criar board sem necessidade.

Colunas conceituais: código, processo, setor, filial, status, responsável, estado documental, baseline, melhoria ativa, última atualização. Setor e filial no mestre não são colunas de `processos` (escopo organizacional é outro agregado). A coluna precisa nascer da instância ou do escopo, não de um campo inventado no mestre.

Abrir um processo entra no workspace já existente, reorganizado como no ciclo de inteligência. Sem segunda cópia dos dados.

Visão geral do processo: identificação, objetivo, escopo, responsáveis, revisão ativa, baseline, melhorias, indicadores medidos, atividades da timeline, pendências com fonte. Completude: `PRESENT | PARTIAL | MISSING | NOT_APPLICABLE`. Sem nota de qualidade.

## 10. Sala, tarefas, portfólio

| Área | Decisão |
|---|---|
| Sala | Não há capability compartilhada. Comercial é o owner das salas atuais. TO_INVENTORY / TARGET. Não implementar chat paralelo |
| Tarefas | Não criar task store. Candidatos: plano de ação (ainda TO_INVENTORY), assinatura de ata (PROVEN), vigência vencendo (PROVEN). «Minhas tarefas» é projeção, não cargo |
| Portfólio | Não criar agregado Portfolio. Se a fase H passar no Abstraction Gate, é read model de processos e melhorias já autorizados |

## 11. Administração, perfil, ajuda, busca, favoritos

Administração do Portal Transforma+, no alvo, é equipe, grupos e acessos. Esses objetos continuam na Core. O app não cria usuário, papel nem grupo locais. Unidades, departamentos, recursos, exportação e recálculo da Visão geral são uso normal: `access`. O texto antigo que chamava esses cadastros de administração do produto está superado.

Perfil: se o kit tiver avatar e o token tiver nome/e-mail, exibir. Cargo, se aparecer, é rótulo. Escopo autorizado vem do backend.

Ajuda TARGET: primeiros passos, conceitos, mapa de telas, processos, melhorias, indicadores, diagnóstico, acesso, TÉO, glossário. O glossário separa processo, instância, revisão, baseline, AS-IS, TO-BE, melhoria, medição, evidência e diagnóstico.

Busca TARGET: processos, melhorias, atas, evidências e ações, no escopo autorizado. Antes de backend novo, esgotar palette de caminhos (kit) e `search_records`. Busca de entidade do Comercial não existe como serviço Core.

Favoritos de página: owner atual é o Comercial. Favoritos de app são do Core. Não criar favorito de domínio duplicado.

## 12. Matriz de reuso

| Peça | Owner | Genérico? | Uso Transforma+ | Modo | Risco | Decisão |
|---|---|---|---|---|---|---|
| TopBar, PageHero, CommandPalette, NavigationCard, KpiCard, filtros, SectionCard, EmptyState | plugin-ui | Sim | Chrome | Reuse | Baixo | PROVEN_SHARED |
| Catálogo `shellNav` / launcher | Comercial | Não | Não o arquivo | Nenhum | Alto | DO_NOT_REUSE |
| `PluginShell` | Comercial | Não | Não | Nenhum | Alto | DO_NOT_REUSE. Extração adiada |
| `OpenOrdersTable` | Comercial | Não | Não | Nenhum | Alto | DO_NOT_REUSE |
| Sala / tarefas / favoritos `/me` | commercial-api | Não | Não | Nenhum | Alto | DO_NOT_REUSE |
| Favoritos de apps | Core | Portal | Não para processo | Nenhum | Médio | CORE_OWNED |
| Dashboard TM, workspace, atas, catálogos | Transformômetro | Domínio próprio | Sim, reorganizar | Reuse interno | Baixo | PROVEN |
| Overview comercial, manual comercial, menu de carteira | Comercial | Não | Não | Nenhum | Alto | DO_NOT_REUSE |

## 13. Rotas

Conceitual, não final:

```text
/apps/transformometro          hoje = dashboard
/overview                      TARGET
/interactions                  bloqueado até owner
/tasks                         bloqueado até projeção
/processes                     hoje /processos (+ alias EN já existente no app)
/processes/:id                 workspace atual
/portfolio                     bloqueado até read model
/administration                hoje /configuracoes e /settings
/help                          TARGET
```

Não renomear URL neste passe. Compatibilidade exige plano próprio.

## 14. Read models e TÉO

Home e overview devem evitar N+1, mas não ganham mega-endpoint sem contrato. Ordem: dashboard e `analyze` atuais, `get_process_context` em seções, `search_records` / `get_record`. Endpoint novo só com gap medido.

Não criar `get_my_processes`, `get_transforma_home`, `get_portal_overview`, `get_my_portfolio`.

## 15. Fases A–I

Histórico de agrupamento de UX. **Não são a ordem vigente.** A ordem está em [ARCHITECTURE-RUNWAY.md](./ARCHITECTURE-RUNWAY.md). Nenhuma fase está autorizada.

| Fase | Conteúdo | Aceite mínimo | Depende de |
|---|---|---|---|
| A | Este inventário | Comercial classificado; nenhum import de domínio | Feito como documentação |
| B | Shell, Início, nav, busca de caminhos, favoritos só se o owner existir | Home não apaga `/dashboard`; kit em vez de cópia de CSS comercial | A |
| C | Meus processos + workspace + completude objetiva | Mesmos registros do workspace atual; completude sem score | Workspace PROVEN. Completude = PI-6 |
| D | Interfaces / mapeamento mais semântico | Sem colisão com escopo organizacional | PI-1 |
| E | Diagnóstico | Hipótese não vira fato | PI-2 |
| F | Indicadores e definição de KPI | Medição atual intacta | PI-3 |
| G | AS-IS × TO-BE, plano, resultados | Cenário não vira produção na UI | PI-4 e PI-5 |
| H | Sala, tarefas, portfólio | Owner nomeado ou a fase para | Inventário ainda aberto |
| I | Arquitetura corporativa | Fora da árvore de um processo | PI-7 |

## 16. O que este adendo não faz

Não altera frontend, API, MCP, Actions, OpenAPI, Keycloak, RBAC, migrations nem runtime. Não copia regra de pedido, carteira, SLA ou sala. Não trata documentação como prova de produção.
