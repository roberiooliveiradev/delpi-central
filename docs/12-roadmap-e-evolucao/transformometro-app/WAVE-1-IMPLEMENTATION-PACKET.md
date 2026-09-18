# Wave 1 — Implementation Packet

> **Status:** READY_FOR_ARCH_REVIEW. **IMPLEMENTATION = NOT AUTHORIZED.**  
> **Sequência:** [ARCHITECTURE-RUNWAY.md](./ARCHITECTURE-RUNWAY.md). Este arquivo é o único pacote da Wave 1.  
> DoR preenchido abaixo não é DoD e não é licença para codar.

## Goal

Dar a primeira experiência Portal Transforma+ sem mudar o modelo de domínio: shell, navegação, lista de processos já autorizada e o workspace que já existe.

## Owner

| Peça | Owner |
|---|---|
| Shell e navegação | MFE `plugins/transformometro` |
| Processo, revisão, dashboard, ata, arquivo | Transformômetro (`transformometro-api`) |
| Identidade | Keycloak |
| RBAC de app | Core, via códigos do manifesto |
| Chrome visual | `@delpi/plugin-ui` |
| TÉO | Consumidor. Não é owner desta wave |

## Canonical source

Nav: `TransformometroNav.tsx`. Rotas: `plugins/transformometro/src/constants/routes.ts`. Lista: `GET /processos` em `crud_routes.list_processos` (o MFE chama `/processes`). Workspace: `processWorkspaceNav.ts`. Dashboard: `DashboardResumo` e rotas de dashboard já usadas pela UI. Permissões: `transformometro.manifest.json`.

## Current state

Nav PROVEN: Dashboard, Processos, Atas, Configurações, Exportar/Importar. Home é o dashboard. Lista filtra por `status` e `q` (`ProcessesPage`). O backend também aceita `filial_id`, `setor_id` e `familia_processo`, devolve `{total, items}` sem paginação, e aplica `filter_rows_for_access`. 403 vira título «Acesso negado» (`apiErrorMessage.ts`). A página passa `error` para `StatusAlerts` e `emptyMessage` só para lista vazia. Workspace PROVEN: visão geral, dados, mapeamento, diagrama, arquivos, melhorias, priorização, timeline. O MFE não chama `get_process_context`.

## Target state

Shell visual no padrão do kit, sem importar o Comercial e sem `PluginShell` compartilhado.

Nav desta wave:

| Item | Rota existente | Nota |
|---|---|---|
| Início | `/apps/transformometro` | Atalhos e o que o dashboard já souber mostrar. Sem «recentes»: não há fonte |
| Visão geral | `/dashboard` | O dashboard atual. Sem read model novo |
| Meus processos | `/processes` | Ver semântica abaixo |
| Atas | `/meeting-minutes` | Capability já na nav |
| Configurações | `/settings` | Não rotular «Administração». O que existe é unidade, departamento e recurso |
| Exportar/Importar | `/data` | Permanece. Não é admin de usuário |

Ajuda, Sala, Tarefas e Portfólio **não entram** na nav. Ajuda hoje é tooltip, não página.

**Meus processos** não significa «processos de que sou dono». Significa os registros que `list_processos` devolve depois do filtro de acesso. Não usar cargo, `gestor_responsavel` nem perfil para montar a lista.

## Out of scope

SIPOC, diagnóstico, finding, causa, definição de KPI, plano de ação, portfólio, tarefas, sala, favorito de processo, busca global, arquitetura corporativa, migration, rota nova, tool, Action, permissão nova, rename, bounded context novo, `PluginShell` extraído. Seções TARGET não aparecem na UI.

## Domain / persistence / API / adapters

| Impacto | Valor |
|---|---|
| Domínio | NO |
| Persistência / migration | NO |
| Rota HTTP nova | NO |
| Read model novo | NO |
| MCP | NO |
| GPT Actions | NO |
| AuthZ model | NO |
| `ProcessContextService` | NOT_USED |

Visão geral lê o dashboard já existente (`economia_liquida_total`, `economia_bruta_total`, `horas_economizadas_total`, `investimento_total`, `roi_medio`, e os demais campos de `DashboardResumo` que a UI já mostra). Não acrescentar ação atrasada, tarefa ou portfólio.

| Página | Dado | Fonte | Read model novo |
|---|---|---|---|
| Início | atalhos | rotas atuais | NO |
| Visão geral | resumo | dashboard atual | NO |
| Meus processos | lista | `GET /processes` → `list_processos` | NO |
| Workspace | seções PROVEN | APIs já usadas pelo workspace | NO |

## Routing

Manter os paths de `TRANSFORMOMETRO_ROUTES`. Não criar `/diagnostic`, `/portfolio`, `/tasks`, `/help`.

## Shared UI

| Componente | Uso na wave |
|---|---|
| TopBar, PageHero, NavigationCard, KpiCard, SectionCard, EmptyState, FiltersRow | REUSE_WITH_COMPOSITION, se o shell precisar do chrome |
| CommandPalette | NOT_NEEDED. Não há busca de caminhos nesta wave |
| `PluginShell` do Comercial | NOT_NEEDED. Proibido importar |

## AuthZ

| Tela | Ler | Escrever nesta wave | Efeito na UI |
|---|---|---|---|
| Início, visão geral, lista | `transformometro.view` + filtro de filial já existente | nenhum write de aceite | esconder item não substitui 403 |
| Workspace leitura | view | writes atuais do workspace permanecem como estão; a wave não os amplia | regressão zero |
| Configurações / dados / atas | códigos já do manifesto | idem | idem |

Backend continua a autoridade. 403 não pode cair no empty «Nenhum processo».

## Frontend states

Início, visão geral, lista e workspace: loading, vazio, erro, 403 e dado parcial quando a API já devolver parcial. Sem mock permanente.

## Tests

Frontend: nav, item visível só com capability de menu já existente, rota antiga ainda abre, lista, filtro `status`/`q` que já existem, abrir processo, workspace sem regressão, vazio, erro, 403 distinto de vazio. Responsive no shell se o layout do chrome mudar.

Backend: regressão de `list_processos` e dashboard. Não é obrigatório teste novo de `get_process_context`, porque a wave não o usa.

E2E de aceite: portal → Meus processos → abrir processo → workspace. Nenhum write no critério de aceite.

## Acceptance

- AC-01 Usuário com `transformometro.view` abre o app.
- AC-02 A nav nova não importa módulo do Comercial.
- AC-03 A lista é o `items` devolvido por `list_processos`, já filtrado no backend.
- AC-04 Abrir um processo cai no workspace atual.
- AC-05 Seções PROVEN do workspace continuam.
- AC-06 Números da visão geral são os do dashboard atual, não um cálculo novo no MFE.
- AC-07 403 aparece como acesso negado, não como lista vazia.
- AC-08 Nenhuma rota, tool, Action, migration ou permissão nova.
- AC-09 TÉO não ganha tool de página.
- AC-10 Transformômetro continua dono do domínio.

## Rollback

Só o build do MFE. Sem migration, sem flag nova. Não há infraestrutura de feature flag do Transformômetro para inventar aqui.

## Runtime verification

Quando a wave for executada, o DoD exige SHA, build, deploy, health e smoke no browser da versão que subiu. Outcome de write: NOT_APPLICABLE.

## Risks

Chamar «Meus processos» de carteira pessoal. Colocar Ajuda vazia na nav. Reapresentar o dashboard e recalcular KPI no cliente. Tratar este pacote como autorização.

## Gaps

Recentes no Início: sem fonte. Paginação da lista: o endpoint não pagina. Ajuda como manual: fora. Drift do `ProcessContextService`: aberto e não usado aqui.

## DoR

| Item | Status |
|---|---|
| OWNER | PASS |
| SOURCE | PASS |
| BOUNDARY | PASS. MFE compõe; API não muda |
| DOMAIN CONTRACT | NOT_APPLICABLE. Nenhum contrato novo |
| AUTHZ | PASS. Códigos atuais |
| PERSISTENCE | NOT_APPLICABLE |
| API | PASS. Sem rota nova |
| MCP | NOT_APPLICABLE |
| ACTIONS | NOT_APPLICABLE |
| UX | PASS. Nav e exclusões acima |
| MIGRATION | NOT_APPLICABLE |
| TEST PLAN | PASS |
| ACCEPTANCE | PASS |

Nenhum item necessário está PENDING ou FAIL. Isso autoriza revisão de arquitetura. Não autoriza implementação.
