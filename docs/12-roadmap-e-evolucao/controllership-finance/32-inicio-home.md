# 32 — Início — Home do Portal

## Estado

**TARGET / PAGE_DOCUMENTATION_GATE_V2 PASS / READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY**

```text
DOCUMENTED != IMPLEMENTED
IMPLEMENTATION_AUTHORIZED = NO

VISUAL_SPEC_DEFINED      = PASS
CONTRACT_DEFINED         = PASS
AUTHZ_DEFINED            = PASS
PLUGIN_UI_REUSE_DEFINED  = PASS
STATES_DEFINED           = PASS
TEST_MATRIX_DEFINED      = PASS
```

Runtime do Portal Controladoria & Finanças: **NOT_IMPLEMENTED**.

Este documento fecha o **Item 2 — Início** como especificação visual, funcional e de integração pronta para futuro brief de implementação.

A implementação permanece proibida nesta fase de revisão global do Portal.

## Família visual

```text
VISUAL_FAMILY = HOME
REFERENCE      = Portal Comercial / Home family
IMPLEMENTATION = plugin-ui first
```

O Início do Portal Controladoria & Finanças deve seguir a mesma gramática visual das Homes dos demais Portais.

O conteúdo muda por domínio; o shell, o Hero, Eventos e interações, busca de caminhos, Últimos acessos, cards de seções, Favoritos, responsividade e temas permanecem na família comum.

Fontes de referência:

- [Padrão Visual dos Portais Minha DELPI](../../11-padroes-de-desenvolvimento/padrao-visual-portais-minha-delpi.md);
- `plugins/commercial/src/app/PluginShell.tsx`;
- `plugins/commercial/src/features/home/HomePage.tsx`;
- `plugins/commercial/src/content/pluginRouteCatalog.ts`;
- `plugins/commercial/src/app/commercialUi.ts`;
- `@delpi/plugin-ui`.

## Objetivo

O Início responde:

> O que precisa da minha atenção agora e por onde entro nas funcionalidades do Portal?

Ele combina:

```text
SAUDAÇÃO / CONTEXTO
+ SINAIS OPERACIONAIS
+ EVENTOS / INTERAÇÕES
+ BUSCA DE FUNCIONALIDADES
+ ÚLTIMOS ACESSOS
+ LAUNCHER DO PORTAL
```

O Início **não** substitui:

- Visão geral financeira;
- Cockpit da Competência;
- Minhas tarefas;
- Sala de interação;
- Administração.

## Invariantes

```text
HOME != ANALYTICS
HOME != COCKPIT
HOME != TASK WORKSPACE
HOME != BUSINESS WORKFLOW
```

Também:

- indicadores financeiros pertencem à **Visão geral**;
- regras de fechamento pertencem aos owners P1–P5;
- tarefas pertencem às projeções/owners de Minhas tarefas;
- mensagens pertencem à Sala de interação;
- o Início apenas compõe, orienta e navega;
- falha de dados dinâmicos não deve inutilizar o launcher;
- rota futura no roadmap não aparece como funcionalidade disponível.

## Responsabilidade, owners e non-goals

A Home é uma **composição/launcher**. Ela não cria regra operacional própria para competência, tarefas, blockers ou eventos.

| Informação/capability | Owner semântico | Papel da Home |
|---|---|---|
| identidade/primeiro nome | Core | apresentar saudação |
| competência ativa | Central de Fechamento / owner do estado | projetar contexto |
| TaskProjection | owners P2/P4/P5 + composição do Portal | preview/navegação |
| blockers | P1 compondo owners P2/P3/P5 | contar/apontar owner |
| eventos/alertas | owner de cada evento | compor sem mudar state |
| catálogo de rotas | MFE/router do Portal | launcher autorizado |
| favoritos | capability a inventariar | pin/unpin sem conceder acesso |
| recentes | MFE local efêmero | conveniência, sem dado sensível |
| indicadores financeiros | Visão geral / owners dos indicadores | **não pertence à Home** |

Explicitamente não pertence à Home:
- cálculo de regra financeira;
- lifecycle de fechamento;
- criação/edição de tarefa;
- envio de mensagem;
- CRUD administrativo;
- persistência de competência;
- regra própria de prioridade;
- SLA/overdue;
- autorização final.

## Rota e acesso

Rota:

```text
/apps/controllership-finance
```

Permission:

```text
controllership-finance.access
```

`MANAGE` isolado não implica acesso ao Início.

Não criar permission para:

- Hero;
- eventos;
- favorito;
- card;
- busca;
- funcionalidade individual.

## TopBar

A Home usa o shell comum definido em [24-inicio-e-navegacao-principal.md](./24-inicio-e-navegacao-principal.md).

Topbar canônica:

```text
Início
Visão geral
Sala de interação
Minhas tarefas
Administração
Ajuda
```

Lado direito:

```text
Buscar | Favoritos | Avatar/Nome
```

A TopBar não é renderizada pela Home; pertence ao shell do Portal.

A Home é a rota raiz do Portal e, por padrão, **não usa PagePath**. `PagePath` fica reservado a superfícies profundas/contextuais; não adicionar breadcrumb apenas para satisfazer uniformidade visual.


## Arquitetura visual — desktop

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ Início | Visão geral | Sala | Minhas tarefas | Administração | Ajuda       │
│                                      Buscar | Favoritos | [avatar] Usuário │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│ PORTAL CONTROLADORIA & FINANÇAS                                             │
│ Olá, {primeiro nome}                                                        │
│ Acompanhe o fechamento da competência e abra as funcionalidades —            │
│ indicadores financeiros ficam na Visão geral.                               │
│                                                                              │
│ Competência ativa        Minhas tarefas        Blockers                      │
│ 09/2026                  4                     2                              │
│                                                     [CTA contextual]         │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│ EVENTOS E INTERAÇÕES                                      [Atualizar]        │
│ Ações, validações e alertas que pedem sua atenção.        [Minhas tarefas]  │
│                                                                              │
│ [alerta / blocker] [ação]                                                     │
│ [tarefa / validação] [ação]                                                  │
│ [esclarecimento] [ação]                                                      │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│ CAMINHOS E FUNCIONALIDADES                                                  │
│ Busque ou abra uma funcionalidade do portal.                                │
│                                                                              │
│ [ Buscar caminhos e funcionalidades...                                  ]   │
│                                                                              │
│ Últimos acessos: [Cockpit] [Minhas tarefas] [Visão geral]                   │
│                                                                              │
│ ┌────────────────────────────┐ ┌────────────────────────────┐                │
│ │ CENTRAL DE FECHAMENTO      │ │ GESTÃO                     │                │
│ │ Cockpit                 ☆  │ │ Visão geral             ☆  │                │
│ │ Checklist               ☆  │ └────────────────────────────┘                │
│ │ Estoque e conciliação   ☆  │                                               │
│ │ Classificações          ☆  │ ┌────────────────────────────┐                │
│ │ Pacote e envio          ☆  │ │ COLABORAÇÃO                │                │
│ └────────────────────────────┘ │ Sala de interação       ☆  │                │
│                                │ Minhas tarefas          ☆  │                │
│ ┌────────────────────────────┐ └────────────────────────────┘                │
│ │ AJUDA                      │                                               │
│ │ Manual do usuário       ☆  │ ┌────────────────────────────┐                │
│ └────────────────────────────┘ │ ADMINISTRAÇÃO*             │                │
│                                │ Painel                  ☆  │                │
│                                └────────────────────────────┘                │
└──────────────────────────────────────────────────────────────────────────────┘

* somente para viewer com controllership-finance.manage e rota implementada.
```

## Arquitetura visual — mobile

```text
TOPBAR COMPACTA
Buscar | Favoritos | Avatar

┌─────────────────────────────┐
│ PORTAL CONTROLADORIA...     │
│ Olá, {nome}                 │
│ descrição                   │
│                             │
│ Competência ativa  09/2026  │
│ Minhas tarefas     4        │
│ Blockers           2        │
│                             │
│ [CTA contextual           ] │
└─────────────────────────────┘

┌─────────────────────────────┐
│ Eventos e interações       │
│ [Atualizar]                │
│                            │
│ alerta / tarefa            │
│ alerta / tarefa            │
└─────────────────────────────┘

┌─────────────────────────────┐
│ Caminhos e funcionalidades │
│ [Buscar...]                │
│                            │
│ Últimos acessos            │
│ [chip] [chip] [chip]       │
│                            │
│ Central de Fechamento      │
│ [Cockpit               ☆]  │
│ [Checklist             ☆]  │
│ [Estoque               ☆]  │
│ ...                        │
│                            │
│ Gestão                     │
│ [Visão geral           ☆]  │
│                            │
│ Colaboração                │
│ [Sala de interação     ☆]  │
│ [Minhas tarefas        ☆]  │
│                            │
│ Ajuda                      │
│ [Manual                ☆]  │
│                            │
│ Administração*             │
│ [Painel                ☆]  │
└─────────────────────────────┘
```

Não criar carrossel horizontal obrigatório para as seções principais.

## Hero

### Componente

Usar `createDashboardPageHero` através do adapter fino do Portal.

A saudação usa:

```text
formatPortalGreeting
```

com o primeiro nome do usuário autenticado.

A identidade do usuário vem do Core conforme [31-pagina-do-usuario.md](./31-pagina-do-usuario.md).

### Copy TARGET

Eyebrow:

```text
Portal Controladoria & Finanças
```

Título:

```text
{saudação}, {primeiro nome}
```

Descrição:

```text
Acompanhe o fechamento da competência e abra as funcionalidades — indicadores financeiros ficam na Visão geral.
```

Não usar copy que transforme o Início em dashboard financeiro.

### Highlights operacionais

O Hero possui três highlights TARGET:

```text
Competência ativa
Minhas tarefas
Blockers
```

#### Competência ativa

Valor:
- competência corrente/aberta comprovada pelo contract da Central de Fechamento;
- exemplo: `09/2026`.

Regras:
- não assumir o mês corrente do calendário;
- sem competência aberta comprovada → `Nenhuma aberta` somente quando a source respondeu com sucesso;
- source indisponível → `—` + estado parcial;
- não criar competência ao carregar a Home.

#### Minhas tarefas

Valor:
- quantidade de itens acionáveis da projeção pessoal.

Dependência:
- Item 4 — revisão de Minhas tarefas;
- contract de `TaskProjection`.

Regras:
- indisponibilidade da projeção → `—`;
- zero real → `0`;
- sem SLA comprovado, não converter em "atrasadas".

#### Blockers

Valor:
- contagem de blockers materiais da competência ativa.

Owners possíveis:
- P2;
- P3;
- P5;
- composição P1.

Regras:
- somente blockers definidos pelos owners;
- não transformar warning informativo em blocker;
- source parcial → `—` ou parcial, nunca zero;
- >0 pode usar tone warning/danger conforme semântica comprovada;
- zero real pode usar tone neutral/positive do kit sem criar "fechamento concluído".

## CTA contextual do Hero

Prioridade TARGET:

```text
1. blocker material disponível
   → Abrir Cockpit / foco blockers

2. tarefa pessoal acionável
   → Abrir Minhas tarefas

3. competência ativa sem blocker/tarefa prioritária
   → Abrir Central de Fechamento / Cockpit

4. nenhuma condição comprovada
   → sem CTA contextual
```

A Home não executa a ação de negócio do blocker/tarefa.

O CTA apenas navega ao owner.

## Eventos e interações

Família visual:

```text
EventsSection
→ alerts
→ preview de worklist
→ optional scope chips
```

Título:

```text
Eventos e interações
```

Subtitle TARGET:

```text
Ações, validações e alertas que pedem sua atenção.
```

### Conteúdo permitido

Podem aparecer:

- blockers materiais da competência;
- tarefas pessoais acionáveis;
- validações que dependem do usuário;
- esclarecimentos que dependem do usuário;
- source operacional indisponível quando exigir ação/atenção e o owner expuser isso como alerta;
- eventos futuros explicitamente aprovados.

Não criar:
- alerta por mera existência de dado;
- "atrasada" sem SLA/due formal;
- ação administrativa para viewer sem MANAGE;
- regra paralela de prioridade na Home.

### Worklist preview

A Home pode mostrar preview das tarefas, mas:

```text
HOME PREVIEW
!= TASK OWNER
```

Ações devem navegar/acionar o caso de uso owner conforme contrato de Minhas tarefas.

A Home não persiste status próprio de tarefa.

### Chips da fila

`ScopeChipBar` é opcional.

Não usar por padrão:

```text
Atrasadas | Hoje | Depois
```

porque o Portal ainda não possui SLA/due formal transversal.

Os chips só entram quando o contrato de Minhas tarefas provar uma categorização estável.

Se não houver categoria canônica:
- omitir chips;
- não inventar taxonomia apenas para preencher o componente.

### Empty positivo

Quando todas as sources necessárias responderem e não houver item prioritário:

```text
Nenhuma ação prioritária agora.
```

Pode oferecer:

```text
Abrir Minhas tarefas
```

Não usar `Fila em dia` se isso sugerir cumprimento de SLA inexistente.

## Caminhos e funcionalidades

Esta é a seção de launcher do Portal.

Título:

```text
Caminhos e funcionalidades
```

Subtitle:

```text
Busque ou abra uma funcionalidade do portal.
```

### Catálogo TARGET

O catálogo é MFE-owned e descreve rotas existentes do Portal.

Seções TARGET:

```text
Central de Fechamento
Gestão
Colaboração
Ajuda
Administração
```

### Central de Fechamento

Rotas candidatas, exibidas somente quando implementadas:

- Cockpit da Competência;
- Checklist e Documentos;
- Estoque e Conciliação;
- Classificações e Pendências;
- Pacote e Envio.

A seção pode existir parcialmente conforme o rollout page-by-page.

### Gestão

- Visão geral.

### Colaboração

- Sala de interação;
- Minhas tarefas.

### Ajuda

- Manual do usuário.

### Administração

- Painel de Administração;
- outras rotas administrativas somente após implementação.

Toda rota administrativa exige viewer com `controllership-finance.manage`.

### Página do usuário

A Página do usuário **não** entra no catálogo principal do Início.

Ela permanece contextual:
- avatar/nome na TopBar;
- links de pessoas quando aplicável.

## Visibilidade de rota

Uma rota só aparece no launcher quando:

```text
IMPLEMENTED_IN_RUNTIME
AND declared_in_portal_router/catalog
AND viewer_authorized
```

Roadmap, markdown ou manifest futuro isoladamente não autorizam exibição.

Se uma rota deixa de existir:
- não renderizar;
- remover/ignorar favorito stale;
- remover/ignorar recente stale.

## Busca local do Início

Usar `createDashboardCatalogSearchBar`.

Query deep-link:

```text
?q=
```

Regras:
- busca em label, keywords e seção;
- normalização accent/case conforme util canônico;
- resultado limitado e ranqueado;
- selecionar navega à rota;
- rotas não autorizadas não entram no índice;
- rotas não implementadas não entram no índice;
- busca vazia mostra catálogo completo;
- zero resultados mostra EmptyState do kit.

A busca local do Início é diferente da busca global da TopBar:

```text
TopBar Buscar
= Command Palette do Portal

Home Buscar
= filtro/launcher da Home
```

Ambas consomem o mesmo catálogo canônico para não divergir.

## Últimos acessos

Usar `createDashboardRecentAccessStrip`.

TARGET:

```text
MAX_RECENTS = 5
```

Estado efêmero local:

```text
controllership-finance.home.recentViews.v1
```

Pode usar `localStorage`, seguindo o padrão comprovado do Comercial.

Regras:
- dedupe por routeId + search;
- mais recente primeiro;
- filtrar rota desconhecida;
- filtrar rota sem autorização atual;
- filtrar rota removida do runtime;
- falha/corrupção do storage → lista vazia, sem quebrar Home;
- não guardar dado financeiro/PII no recent state.

## Favoritos

Favorito é uma capability do shell/Home e deve refletir na TopBar.

UX:

```text
estrela no caminho
↔ persistência de favorito
↔ Favoritos da TopBar
```

Regras:
- somente rota implementada e autorizada pode ser favoritada;
- pin/unpin com feedback acessível;
- falha ao salvar faz rollback do estado otimista;
- falha ao carregar favoritos não bloqueia launcher;
- stale favorite é ignorado/limpo;
- nenhum favorito concede acesso a rota.

### Persistência

No HEAD atual:
- foi comprovado o padrão product-local do Portal Comercial via `GET/PUT /me/home-favorites`;
- **não foi comprovada uma capability transversal equivalente no Core**.

Classificação:

```text
FAVORITES_PERSISTENCE = TO_INVENTORY_BEFORE_IMPLEMENTATION
```

Stop condition:
1. revalidar Core/shared preference capability no HEAD futuro;
2. se existir contrato transversal adequado, reutilizar;
3. se não existir, avaliar contrato product-local no `controllership-finance-api` seguindo a semântica do Comercial;
4. não criar migration/store preventivamente nesta fase documental.

Proibido usar `localStorage` como fallback silencioso de persistência de Favoritos se o contrato futuro decidir persistência server-side.

## Central de Fechamento na Home

A Central de Fechamento é a primeira funcionalidade de negócio do Portal.

Na Home ela aparece como **SectionRouteCard/launcher**, não como mini Cockpit.

Pode mostrar:
- nome/descrição da funcionalidade;
- rotas implementadas;
- badges factuais quando houver contract;
- favorito por rota.

Não deve mostrar:
- conciliação completa;
- checklist completo;
- histórico;
- ações de fechamento;
- tabela operacional.

```text
HOME = launcher
P1 = cockpit
```

## Contratos TARGET — MFE → BFF → owners

O browser consome apenas `controllership-finance-api` para dados dinâmicos do Portal.

```text
plugins/controllership-finance
→ controllership-finance-api
→ Core / owners da Central / demais owners autorizados
```

Proibido:

```text
MFE → Core direto
MFE → api-delpi direto
MFE → banco/serviço vizinho
```

A FASE A congela **operações semânticas**, não paths físicos:

| Operação lógica da Home | BFF responsibility | Owner downstream |
|---|---|---|
| resolveViewerContext | AuthZ + identidade mínima | Core effective access/profile |
| getActiveCompetenceSummary | composição read-only | owner da competência/P1 |
| getMyTaskPreview | projeção self-only | TaskProjection / P2/P4/P5 |
| getBlockerSummary | composição sem duplicar regra | P1 / P2 / P3 / P5 |
| getAttentionEvents | compor eventos já autorizados | owners correspondentes |
| getFavorites / saveFavorites | somente se capability física for decidida | H01 TO_INVENTORY |
| routeCatalog | não precisa BFF para catálogo estático | MFE/router |
| recentViews | não precisa BFF | state local efêmero |

### Política de endpoint

Não congelar um `GET /home` agregado por preferência.

Na futura implementação:

1. revalidar contratos existentes dos owners;
2. expor no BFF as menores surfaces necessárias;
3. se múltiplos roundtrips criarem problema material comprovado, propor read-model/agregação;
4. qualquer agregador continua composição, nunca novo owner das regras.

### Contrato de degradação

- authorization dependency falhou → fail-closed;
- competência indisponível → módulo correspondente `UNAVAILABLE`, launcher preservado se seguro;
- TaskProjection indisponível → tasks `UNAVAILABLE`, sem inventar zero;
- blocker owner indisponível → blocker `UNAVAILABLE`, sem inferir “sem blockers”;
- um módulo falho não transforma siblings confiáveis em error;
- nenhuma source externa é chamada diretamente pelo MFE.

## Dados dinâmicos e composição

Não criar endpoint agregado `/home` apenas para copiar o Comercial sem evidência.

A Home deve reutilizar contratos owners.

Dependências TARGET:

| Informação | Owner / contract |
|---|---|
| nome/primeiro nome | Core / perfil self |
| competência ativa | state/contract próprio da Central |
| minhas tarefas | projeção de Minhas tarefas |
| blockers | P1 composição de P2/P3/P5 |
| eventos/alertas | owners correspondentes |
| favoritos | TO_INVENTORY |
| catálogo | MFE/router |
| recentes | estado local efêmero |

Se, durante implementação, múltiplos roundtrips produzirem problema material de latência/consistência, um read-model/composition endpoint pode ser proposto com evidência. Não antecipar agora.

## Estados da experiência

### INITIAL / LOADING

- shell e launcher podem renderizar enquanto dados dinâmicos carregam;
- Hero highlights usam loading/placeholder do kit, não `0`;
- Eventos usa `LoadingActivityCard`;
- busca/catalog estático continua disponível se autorizado.

### SUCCESS

Todas as sources necessárias responderam.

### PARTIAL

Exemplos:
- tasks indisponível, catálogo funcional;
- blocker source indisponível, competência conhecida;
- favoritos indisponíveis, launcher funcional.

Regra:

```text
degrade independently
```

Não derrubar Home inteira por uma source.

### EMPTY

Válido quando:
- consulta dinâmica concluiu sem itens;
- catálogo autorizado realmente não possui entradas além das superfícies comuns.

Empty de eventos não é error.

### UNAVAILABLE / UNAVAILABLE_SOURCE

Identificar a capability afetada sem converter para zero.

`UNAVAILABLE` é o estado de experiência; `UNAVAILABLE_SOURCE` pode ser o qualifier interno de uma capability/source.

### ERROR

Erro total da Home somente quando o Portal não consegue resolver o mínimo necessário para operar a página/sessão.

Erros de módulos internos preferem estado parcial.

### FORBIDDEN

Sem `controllership-finance.access`:
- Home não renderiza conteúdo;
- backend/route guard falha fechado.

### NOT_FOUND

Não é estado normal da rota root.

Deep link de catálogo inválido/removido deve ser tratado pela rota de destino/router, não pela Home como dado existente.

## Reuso obrigatório de @delpi/plugin-ui

Import preferencial:

```ts
import {
  formatPortalGreeting,
  createDashboardPageHero,
  createDashboardTitleWithHelp,
  createDashboardStatusBadge,
  createDashboardEventsSection,
  createDashboardScopeChipBar,
  createDashboardWorklistItem,
  createDashboardLoadingActivityCard,
  createDashboardCatalogSearchBar,
  createDashboardRecentAccessStrip,
  createDashboardSectionRouteCard,
  createDashboardNavigationCard,
  createDashboardCommandPalette,
  createDashboardTopBar,
  createDashboardTopBarSearchTrigger,
  createDashboardTopBarFavoritesStrip,
  createDashboardTopBarUtilityCluster,
  createDashboardTopBarUserIdentity,
  ActionButton,
  EmptyState,
  StateBanner,
} from "@delpi/plugin-ui/index";
```

Styles:

```ts
await import("@delpi/plugin-ui/styles");
```

O shell deve instanciar as factories por meio de adapter fino equivalente ao padrão `commercialUi.ts`.

### Mapeamento

| Necessidade | Reuso canônico |
|---|---|
| saudação | `formatPortalGreeting` |
| Hero | `createDashboardPageHero` |
| help no título | `createDashboardTitleWithHelp` |
| badge/tone | `createDashboardStatusBadge` |
| eventos | `createDashboardEventsSection` |
| chips | `createDashboardScopeChipBar` |
| item de worklist | `createDashboardWorklistItem` |
| loading de painel | `createDashboardLoadingActivityCard` |
| busca de caminhos | `createDashboardCatalogSearchBar` |
| recentes | `createDashboardRecentAccessStrip` |
| seção com subrotas | `createDashboardSectionRouteCard` |
| card simples | `createDashboardNavigationCard` |
| busca TopBar | `createDashboardCommandPalette` |
| shell TopBar | factories `createDashboardTopBar*` |
| ações | `ActionButton` |
| empty | `EmptyState` |
| partial/error contextual | `StateBanner` |

### DO NOT RECREATE

- TopBar;
- Command Palette;
- PageHero;
- EventsSection;
- worklist item;
- catalog search;
- recent strip;
- section route card;
- navigation card;
- favorite strip;
- generic state/loading/empty chrome.

## Tema claro e escuro

A árvore de componentes é idêntica.

```text
SAME DOM
+ SAME COMPONENTS
+ SAME CONTENT PRIORITY
+ THEME TOKENS
```

Validar:

### Claro
- canvas claro;
- Hero com tint azul suave;
- cards claros;
- accent azul;
- bordas discretas.

### Escuro
- canvas/surfaces escuros;
- Hero azul/escuro;
- texto claro;
- accent azul preservado;
- bordas translúcidas.

Não criar CSS específico para reproduzir o print do Comercial.

Usar tokens do padrão visual mestre.

## Responsividade

Desktop:
- Hero em largura total;
- highlights em linha quando houver espaço;
- cards de seção em grid;
- Eventos antes do launcher.

Tablet:
- reduzir colunas;
- Hero highlights podem quebrar;
- toolbar de Eventos reorganiza.

Mobile:
- TopBar compacta;
- Hero highlights empilhados/compactados conforme kit;
- ações full-width quando necessário;
- cards de seção em uma coluna;
- recentes wrap/scroll conforme kit;
- sem conteúdo crítico apenas em hover.

## Acessibilidade

Obrigatório:
- heading/section semantics;
- foco visível;
- pesquisa com label;
- estrela de favorito com nome acessível;
- cards/rotas acionáveis por teclado;
- status/badges sem depender de cor;
- atalhos do Command Palette com accessible name;
- `Ctrl/Cmd+K` não deve capturar foco de input indevidamente;
- loading/partial anunciado adequadamente;
- target touch adequado.

## Deep links

### Home search

```text
/apps/controllership-finance?q={query}
```

F5 preserva a busca.

### Rotas dos cards

Usar router/view catalog canônico.

Não construir URLs absolutas duplicadas em cada card.

### Recent/favorites

Podem preservar search params aprovados quando fazem parte do destino.

Nunca persistir arbitrary URL externa como favorito do Portal.

## Segurança

- MFE filtra visualmente; backend/route guards autorizam;
- `ACCESS` é necessário para Home;
- Administração exige `MANAGE`;
- favorito não concede permission;
- recente não concede permission;
- search não revela rota que o viewer não pode usar;
- nenhum dado financeiro sensível entra em localStorage de recents/search;
- falha do Core effective permission → fail-closed.

## Help

A Ajuda deve documentar o Início somente quando a Home estiver implementada.

Conteúdo:
- Hero e highlights;
- diferença Início vs Visão geral;
- Eventos e interações;
- busca local;
- busca global da TopBar;
- Últimos acessos;
- Favoritos;
- Central de Fechamento;
- por que algumas rotas podem não aparecer;
- diferença entre indisponível e zero;
- Administração visível somente com MANAGE.

## RQ / AC

### RQ-HOME-01 — Home family comum

Aceite:
- mesma gramática dos Portais;
- TopBar comum;
- Hero + Eventos + launcher;
- plugin-ui first.

### RQ-HOME-02 — Hero operacional, não analítico

Aceite:
- Competência ativa, Minhas tarefas e Blockers;
- indicadores financeiros não migram para Home;
- indisponível não vira zero;
- CTA somente navega ao owner.

### RQ-HOME-03 — Eventos resilientes

Aceite:
- preview de tarefas/alerts owners;
- sem SLA inventado;
- source parcial não derruba launcher;
- empty positivo só após sources válidas.

### RQ-HOME-04 — catálogo autorizado

Aceite:
- somente rota implementada + autorizada;
- Administração somente MANAGE;
- Página do usuário fora do launcher;
- stale route não aparece.

### RQ-HOME-05 — busca local/deep link

Aceite:
- `?q=` preservado em F5;
- ranking/catálogo usa mesmas rotas do launcher;
- busca não vaza rota não autorizada.

### RQ-HOME-06 — recentes

Aceite:
- máximo 5;
- localStorage somente route/search/label/timestamp;
- stale/unauthorized filtrado;
- storage corrompido não quebra Home.

### RQ-HOME-07 — favoritos

Aceite:
- estrela ↔ TopBar;
- load/save failure não concede acesso nem quebra launcher;
- persistência física permanece inventário até o slice;
- nenhum store criado preventivamente nesta fase.

### RQ-HOME-08 — light/dark/mobile/a11y

Aceite:
- mesmos componentes/DOM conceitual;
- tokens;
- desktop/mobile;
- teclado/foco;
- sem estado por cor.

### RQ-HOME-09 — Help sync

Aceite:
- conteúdo publicado junto do runtime;
- diferença Home/Overview explicada;
- links válidos.

## Matriz mínima de testes futura

### Positive
- ACCESS abre Home;
- Hero com competência/tarefas/blockers;
- Hero com valores zero reais;
- CTA blocker;
- CTA tarefas;
- catálogo parcial page-by-page;
- MANAGE vê Administração;
- busca `?q=`;
- recent push/dedupe;
- favorite pin/unpin.

### Sibling
- navegar para P1 não altera estado de P2/P3/P5;
- favorite A não favorita B;
- recent A não substitui B indevidamente;
- erro de tasks não contamina blocker/competência;
- troca de usuário não reutiliza recents/favorites incorretos.

### Negative
- sem ACCESS → 403;
- MANAGE sem ACCESS → 403;
- rota futura documentada não aparece;
- rota sem MANAGE não aparece em Administração;
- stale favorite ignorado;
- search não encontra rota não autorizada;
- source unavailable não vira 0;
- localStorage corrompido não quebra Home;
- favorite backend failure faz rollback;
- sem SLA, nenhuma label "atrasada" é inferida.

### Experiência
- loading;
- partial;
- empty;
- unavailable;
- error;
- desktop;
- mobile;
- light;
- dark;
- keyboard/focus;
- F5 em `?q=`;
- Help.

## Scripts/validators planejados para a fase de implementação

Não criar estes scripts agora.

TARGET para o futuro slice:

```text
validate-home-route-catalog
- cada routeId existe no router
- rota futura não é publicada
- capability/permission mapping é válido

validate-home-favorites
- somente routeId/search permitidos
- stale entries são rejeitados/ignorados
- limites do contrato são respeitados

validate-home-deep-links
- ?q=
- route search params
- F5
- no open redirect

validate-home-help
- links da Ajuda apontam para rotas implementadas
```

Os nomes são conceituais; a localização/forma do script deve seguir o padrão de testes vigente no HEAD da implementação.

## Inventários antes da implementação

### H01 — favoritos

```text
TO_INVENTORY
```

Provar Core/shared preference capability ou justificar product-local.

### H02 — TaskProjection

```text
CLOSED_PRODUCT_CONTRACT / TECHNICAL_INVENTORY_REMAINS
```

O contrato de produto está fechado em [27-minhas-tarefas.md](./27-minhas-tarefas.md):
- self-only;
- projection dos owners;
- sem task entity livre;
- summary com coverage COMPLETE/PARTIAL.

Antes da implementação, ainda revalidar TSK01–TSK04 do Item 5.

### H03 — active competence

```text
TO_INVENTORY
```

Confirmar contract/state owner da competência ativa.

### H04 — blocker summary

```text
TO_INVENTORY
```

Reusar P1/owners; não duplicar regra na Home.

Nenhum desses inventários autoriza implementar feature durante a fase atual de revisão global.

## Gate documental V2

```text
OBJECTIVE_BOUNDARY_DEFINED  = PASS
OWNERS_DEFINED              = PASS
VISUAL_SPEC_DEFINED         = PASS
CONTRACT_DEFINED            = PASS
AUTHZ_DEFINED               = PASS
PLUGIN_UI_REUSE_DEFINED     = PASS
STATES_DEFINED              = PASS
DEEP_LINK_F5_DEFINED        = PASS
RESPONSIVE_DEFINED          = PASS
LIGHT_DARK_DEFINED          = PASS
A11Y_DEFINED                = PASS
HELP_SYNC_DEFINED           = PASS
RQ_AC_DEFINED               = PASS
TEST_MATRIX_DEFINED         = PASS
SCRIPTS_ARTIFACTS_PLANNED   = PASS
IMPLEMENTATION_AUTHORIZED   = NO
```

Resultado:

```text
A02 INÍCIO
= READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY
!= IMPLEMENTED
```

Inventários H01/H03/H04 e TSK aplicáveis permanecem para o futuro brief físico e não autorizam runtime.

## Resultado esperado

O Início deve parecer a mesma Home dos demais Portais Minha DELPI, mas com conteúdo de Controladoria & Finanças.

```text
GREET
→ ORIENT
→ SHOW WHAT NEEDS ATTENTION
→ FIND A PATH
→ OPEN THE OWNER
```

Ele é o launcher operacional do Portal, não o lugar onde o processo ou os indicadores financeiros são executados.
