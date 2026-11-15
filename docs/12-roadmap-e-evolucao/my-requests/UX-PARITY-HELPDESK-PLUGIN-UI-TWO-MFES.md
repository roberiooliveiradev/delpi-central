# UX parity — Minhas Solicitações × Meus Chamados de TI × Plugin UI

> **TASK_ID:** MYREQ-HELPDESK-PLUGIN-UI-CROSS-MFE-UX-CONTRACT-01
> **Decisão de produto:** aprovada na conversa em 15/11/2026: as quatro abas de Minhas Solicitações permanecem **acima do hero**; paridade visual e comportamental com Meus Chamados de TI; componentes/primitivos reutilizáveis pertencem ao **Plugin UI** e são importados pelos dois MFEs.
> **Fase deste registro:** PLANNED / REQUIREMENTS_APPROVED_FOR_DOCUMENTATION. **Não** é comprovação de implementação, build, E2E ou deploy. Nenhum direito de produção decorre deste texto.
> **Owners:** Plugin UI (primitivos/apresentação neutra), my-requests (jornada e modelos do solicitante), helpdesk (jornada/chamados), requests-api (solicitações corporativas), Engineering API (PRC); Core (RBAC/rotas), Keycloak (identidade).
> **Referências:** [WIREFRAMES My Requests](./WIREFRAMES.md), [Helpdesk list](../helpdesk/13-listagem-de-chamados.md), [Helpdesk wireframes](../helpdesk/WIREFRAMES.md), [My Requests playbook](./PLAYBOOK.md).

## 1. Inventário factual (GitHub main, 15/11/2026)

| Artefato | Fato evidenciado | Classificação |
|---|---|---|
| `plugins/my-requests/src/components/AppShell.tsx` | `MyRequestsTopBar` com Minhas, Fila, Nova, Administração sob gates existentes; `MyRequestsPageHeader` contextual | PROVEN |
| `plugins/my-requests/src/pages/MinePage.tsx` | Mescla `requests-api` e PRC da Engineering API; `mergeUnifiedRows`; janela por fonte limitada a 100; `RequestListFilters`; `DataTable`; card externo com título duplicado | PROVEN |
| `plugins/my-requests/src/pages/WorkQueuePage.tsx` | `listWorkQueue`, filtros q/type/status/branch/mineScope; `DataTable`, `CompactPagination`; fila não é a fila global de Engenharia | PROVEN |
| `plugins/my-requests/src/components/RequestListFilters.tsx` | Debounce 300 ms, selects de Tipo/Status/Filial e `mineScope`; botão Limpar | PROVEN |
| `plugins/my-requests/src/pages/NewRequestPage.tsx` | Escolha de tipo por NavigationCard; permissões de criação; wizard NF, schema genérico e fluxo PRC com navegação própria | PROVEN |
| `plugins/my-requests/src/pages/AdminTypesPage.tsx` | Catálogo de tipos READ e gate `canManage`; lista atual de cinco colunas | PROVEN |
| `plugins/helpdesk/src/pages/HelpdeskPage.tsx` e `src/presentation/ticketListViewModel.ts` | Hero compacto, busca, builder de critérios, até 3 níveis de ordenação e catálogo de colunas; composição específica de chamados | PROVEN |
| `plugins/helpdesk/src/presentation/useHelpdeskTicketListColumns.ts` | Hook canônico `useTableColumnVisibility`, chaves locais de preferência e migração | PROVEN |
| `plugins/plugin-ui/src/components/data/TableColumnVisibilityMenu.tsx` | Menu canônico com checkboxes, reset, DnD e `AnchoredPanelPortal` | PROVEN |
| Factories Helpdesk `plugins/helpdesk/src/ui/helpdeskUi.tsx` | `createDashboardPageHero`, `createDashboardScopeChipBar`, `createDashboardDataCardsGrid`, `createFilterBarShell`, `createDashboardSegmentToggle`, etc. | PROVEN |
| Filtros avançados e ordenação unificada multi-source em My Requests | Contratos/backend e provas de paginação ainda por inventariar; **não** presumir equivalência com Helpdesk | TO_INVENTORY |

**Regra de extração:** não importar `HelpdeskPage`, `ticketListViewModel`, tipos GLPI, CSS específico ou hooks privados do Helpdesk em my-requests. Generalizar apenas a *mecânica de UI* (apresentação), no owner `plugins/plugin-ui`, via exports públicos; preservar catálogos, estados, hooks de dados e contratos de cada MFE. Não clonar o código do Helpdesk.

## 2. Sistema visual comum — contrato alvo

```text
[TOPBAR DE CADA MFE, fora do hero]
 Minhas solicitações | Fila de trabalho | Nova solicitação | Administração
[BREADCRUMB — PagePath do kit, adaptado à rota]
 Início / Minhas Solicitações / <área>
[HERO ÚNICO, densidade compacta]
 contexto + Título da área + descrição curta         [Contagem] [Atualizar] [Nova solicitação*]
 Busca dominante (largura disponível)
 Chips rápidos (scope/status, sem conflito com filtros adicionais)
 [Filtros] [Ordenar] [Colunas]                     [Tabela | Cards]
[AQUI TERMINA O HERO — sem título duplicado nem toolbar solta]
[TABELA UNFRAMED ou CARDS — único conjunto autorizado/paginado]
[FOOTER DE PAGINAÇÃO fora da rolagem vertical]
```
`*` Nova solicitação na tela Minhas (e na aba de criação); não destacar como ação primária da Fila. Ações só quando `allowed_actions`/permission realmente permitirem. Áreas Admin/Nova têm composição adequada à tarefa, não forçar toolbar de listagem onde não existe listagem.

Layout: hero sem card externo redundante da listagem; gap curto e consistente; PT-BR completo; ícones Lucide com rótulo/tooltip (não icon-only sem nome); status em badges; dados pessoais por avatar canônico somente quando disponíveis; data/hora localizadas; conteúdo responsivo sem scroll horizontal da *página*. Barra fica no rodapé do hero, imediatamente antes dos dados; overlay ancorado via portal, não `absolute` recortado por `overflow:hidden`.

### 2.1 Regras obrigatórias de interação

- Contador derivado do `total` autoritativo da consulta ativa, anterior à paginação; erro/403/unavailable não se tornam `0` fictício; estado vazio legítimo distinto de falha.
- Chip rápido selecionado descreve o filtro **efetivo** da consulta; botão `Todas` remove o recorte, sem reset oculto de outro filtro.
- Busca: debounce/Enter; estado em URL para query e paginação; trocar filtro/ordem reinicia na página 1; back/forward e refresh restauram estado.
- Popups de Filtros, Ordenar e Colunas usam posicionamento `AnchoredPanelPortal` / primitives públicos, flip/clamp, theme scope completo, Escape, click-outside, foco e sobreposição aninhada; tema claro/escuro e zoom 200%.
- Desktop: controles de mesma hierarquia do Helpdesk, dados ocupam largura disponível. Mobile: painel adaptativo do kit, rolagem interna, ações alcançáveis, cards em uma coluna; sem z-index/CSS de popup criado no MFE.
- Colunas: `TableColumnVisibilityMenu` + `useTableColumnVisibility`; mostrar/ocultar, reordenar, restaurar; identificação (Número) obrigatória. Chaves distintas: `my-requests:mine:columns` e `my-requests:work-queue:columns`; preferencias não migram silenciosamente de Helpdesk.
- Modos Tabela | Cards: mesmo catálogo de campos, mesma autorização, mesma ordem de preferência, mesmo recorte/total/paginação. Cards não podem esconder campos disponíveis por usar `children` em vez do renderer; evitar DnD de workflow.
- Ordenação: cabeçalho bidirecional com `aria-sort`; popover multi-sort com até 3 campos únicos, direção e prioridade; desempate estável; sort sobre todo o universo autorizado **antes** de LIMIT/OFFSET. Não ordenar só as linhas já carregadas.
- Filtros avançados: composição de 1..N critérios tipados, operadores adequados (eq/neq, contains, intervalo quando contrato suportar), `AND` como padrão, aplicar/limpar; UI não promete `OR`/agrupamento sem contrato comprovado. Mostrar resumo removível dos critérios ativos sem duplicar status.
- Erros: 401/403, fonte parcial indisponível, timeout e vazio têm componentes `StateBanner`/`EmptyState` distintos; nunca misturar dados de identidade sem permissão.
- Sem mudanças de workflows, ações de negócio, autorização ou source of truth por paridade visual.

## 3. Páginas do MFE my-requests — wireframes e composição

### WF-MR-01 — Minhas Solicitações (`/apps/my-requests` / `/mine`)

**Persona:** solicitante. **Objetivo:** localizar e acompanhar exclusivamente registros de seu escopo autorizado, inclusive PRC quando integrado por contrato.

- Topbar: quatro abas acima do hero, gates existentes e active tab, sem segunda navegação no hero.
- PagePath: `Início / Minhas Solicitações / Minhas solicitações`; ancestrais navegáveis, overflow no mobile.
- Hero: título único, texto curto, contador real, Atualizar, CTA Nova solicitação quando canCreate; busca em destaque; chips `Todas/Pendentes/Enviadas/Em atendimento/Aguardando informações/Concluídas/Rejeitadas` **apenas quando mapeáveis aos domínios e statuses disponíveis**; popups Filtros/Ordenar/Colunas e seletor Tabela|Cards.
- Catálogo de campos proposto: `number` fixo (link interno e origem), `type`, `subject`, `status`, `createdAt` padrão; `branch`, `updatedAt`, `assignedTo` opcionais quando disponíveis. Não incluir Solicitante por padrão porque o contexto já é próprio.
- Filtros: q, tipo, status, filial e período quando existente. Nenhum valor falseado para PRC sem filial. Registro com fonte legada preserva sua identidade e rota legítima.
- Sorting: Número, Tipo, Assunto, Status, Abertura/Atualização apenas se as duas fontes expuserem contrato determinístico compatível; campos sem paridade devem permanecer não-ordenáveis com explicação.
- Detalhe: links PRC abrem superfície própria coerente de solicitação (sem enviar atendimento para outro app arbitrariamente); registros corporativos preservam `/requests/:id` e permissões.
- UX empty: «Nenhuma solicitação no escopo atual»; erro parcial com mensagem específica sem transformar `total` desconhecido em `0`.

**RISCO CRÍTICO:** o merge atual `mergeUnifiedRows` usa janelas paginadas por fonte limitadas (`MERGE_WINDOW_MAX=100`). Filtros ou sorts multi-campo só podem ser anunciados como corretos se houver plano de query/merge com ordenação/paginação globais e validação de total e autorização. Proibir sort/filter client-side depois da paginação e proibir leitura de universo completo no browser como atalho. Definir contrato de agregação governado antes de habilitar opção cruzando fontes.

### WF-MR-02 — Fila de trabalho (`/work-queue`)

**Persona:** analista/processador autorizado; não equivale à fila global PRC da Engenharia.

- Topbar e PagePath `Início / Minhas Solicitações / Fila de trabalho`.
- Hero: «Fila de trabalho», descrição de atendimento, contador real de casos no escopo, Atualizar; sem CTA de criação primária, preservada a aba Nova.
- Busca dominante + chips rápidos de estados da fila, sem expor tipos/estados não suportados.
- Filtros adicionais atuais: q, tipo, status, filial e `mineScope` `Todas / Concluídas por mim / Atribuídas a mim` (preservar semântica); campos solicitante/responsável/período somente após confirmação do contrato.
- Colunas padrão: Número, Tipo, Assunto, Solicitante, Status, Filial; opcionais: Concluída por, Responsável, Abertura, Atualizada, quando fornecidos. Colunas e ordenação documentadas separadamente de Minhas.
- Mesma ação de linha: abrir detalhe governado; `allowed_actions` apenas no detalhe ou quick action se owner/contrato explícito. Não inventar botão «Concluir» direto na lista.
- Mensagem vazia diferenciada de sem permissão/erro; atualização via `MyRequestsRealtimeProvider` existente continua válida.
- Ordenar até 3 níveis somente com whitelist, tipo de campo e tiebreak no `requests-api`.

### WF-MR-03 — Nova solicitação (`/new` e `/new?type=...`)

**Objetivo:** iniciar um tipo permitido sem duplicar domínio; **não** aplicar barra de ordenação/colunas a formulário.

- Topbar: Nova solicitação ativa quando permitida; PagePath `Início / Minhas Solicitações / Nova solicitação` e detalhe de tipo quando necessário.
- Hero direcional compacto: «Nova solicitação», instrução curta, ajuda, retorno à lista; grade de `NavigationCard` tipada, estados sem tipos/permissão.
- Seleção de tipo em cards canônicos com ícone e descrição objetiva; form especifico mantém seus componentes (`InvoiceIssuanceWizard`, `PrcRequestPage`, `SchemaFormPage`, `GenericCreateForm`).
- Formulários por `TextField/SelectField/SegmentToggle/FileDropzone/ProgressTracker/FormActions`; erro por campo e resumo global; salvar/confirmar somente após backend allow + idempotência; sem alterar sua jornada nesta rodada sem RQ próprio.
- PRC pertence a Engineering API; My Requests é canal de entrada e acompanhamento, não autoridade de publicação de produto/revisão nem escrita TOTVS.

### WF-MR-04 — Administração (`/admin`)

**Persona:** pessoa com `canManage`; preservar o gate e RBAC backend, não confiar em ocultação da aba.

- Topbar Administração ativa; PagePath `Início / Minhas Solicitações / Administração`.
- Hero «Administração de solicitações», subtítulo «Tipos e configurações autorizadas», contador legítimo se obtido; Atualizar quando útil.
- Catálogo de tipos: `code/name/active/branch_scope/presentation_mode` (PROVEN no `AdminTypesPage`); `DataTable` com colunas ajustáveis somente se operações e dados reais justificarem; filtro/busca simples se necessário, sem prometer ações CRUD inexistentes.
- Gate negado: `StateBanner` fail-closed, sem tabela de dados; tabela vazia legítima com `EmptyState`; alterações administrativas futuras dependem de contrato e decisão do owner.
- Nesta etapa, **manter administração read-only**; paridade visual de containers/hero/breadcrumb não autoriza CRUD.

### WF-MR-05 — Detalhe e edição (superfícies associadas)

`/requests/:id` e `/requests/:id/edit` mantêm as etapas «O que foi solicitado / Atendimento / Histórico», `allowed_actions`, mensagens, anexos, artefatos e formulário correto. Aplicar apenas tokens/primitive visuals compartilhados ao que for tocado; não alterar workflow de conclusão, comentários, estados de arquivo ou routing por refino das listas. Revisar em etapa separada antes de alterar interações.

## 4. Matriz de extração Helpdesk → Plugin UI → ambos os MFEs

| Mecânica visual | Fonte atual a inventariar | Owner da capacidade reutilizável | Integração Helpdesk | Integração My Requests |
|---|---|---|---|---|
| Hero compacto / composição título + ações + busca | `HelpdeskPageHero`, `createDashboardPageHero` | Plugin UI existente; evoluir apenas props neutras necessárias | adaptar wrapper para export público | `MyRequestsPageHero` via factory |
| Chips de escopo/status `aria-pressed` | `HelpdeskScopeChipBar` | `createDashboardScopeChipBar` existente | manter via kit | consumir catálogo de statuses próprio |
| Barra de busca e controles | `HelpdeskFilterBarShell`, `createFilterBarShell` | Plugin UI | trocar composição privada por capacidades públicas se houver gap | mesma mecânica, mapeamento de query próprio |
| Builder de filtros avançados | `ticketListViewModel` + popover/helpdesk | **Extrair apenas view neutra** de editor de regras, sob Abstraction Gate | dados GLPI via adapter Helpdesk | request-list rules via adapter My Requests |
| Ordenação multi-nível (máximo 3) | `TicketListSortLevel`, popover Helpdesk | componente neutro Plugin UI (`SortLevelsPanel` nome TARGET, verificar equivalente) | whitelist de campos GLPI | whitelist Requests API e agregação PRC |
| Menu Colunas | `TableColumnVisibilityMenu`, `useTableColumnVisibility` | Plugin UI **já existente** | manter import, eliminar duplicação residual | importar diretamente kit |
| Tabela com sort / estados | `DataTable`, `DataTableSection` se aplicável | Plugin UI existente | manter contrato own data | same renderer do catálogo |
| Cards | `createDashboardDataCardsGrid/DataRecordCard` | Plugin UI existente | render dados chamados | render mesmo catálogo da lista |
| Persistência layout | `usePersistedViewLayout` | Plugin UI existente | storage Helpdesk | storage isolado My Requests |
| Paginação responsiva | `HelpdeskListPaginationFooter` e `createDashboardPaginationKit` | Plugin UI: extrair apenas apresentação reutilizável, não lógica de BFF | adaptar import público | total/page/pageSize do contrato |
| Painel ancorado responsivo | `AnchoredPanelPortal` | Plugin UI existente | scope Helpdesk | scope my-requests, incluindo dark tokens |
| Feedback/empty/error/loading | `StateBanner/EmptyState/LoadingState` | Plugin UI existente | estados do domínio chamado | estados de Requests e PRC independentes |
| Avatar de pessoa | `createDashboardEntityAvatarLabel` | Plugin UI existente | Técnico/Requerente | Solicitante/Responsável quando fonte autorizada |
| Navegação/PagePath | `createDashboardTopBar`, `PagePath` | Plugin UI existente | sem mudar host routing | quatro abas **fora do hero**, Breadcrumb canônico |

**Critério de generalização:** dois consumers reais, diferença puramente visual, props typed sem entidades `Ticket`/`Request`, sem fetch, API, JWT, permission decision, storage schema de negócio ou acoplamento ao MFE. Se componente neutro existente resolver, reutilizá-lo; se não, evoluir kit por contrato/testes; sem abstração adicional para mera coincidência de layout.

## 5. Contratos, segurança e compatibilidade (gate antes do código)

1. Identificar fields/types/sorts/filters realmente suportados em `requests-api` e Engineering API PRC; definir request/response, ordem, total, limites, nulls-last, stable tiebreak, erros 400/422/401/403/503 e observabilidade.
2. Para `/mine` multi-source: desenhar solução que ordene/filtre **globalmente** e pagine corretamente sem copiar o domínio PRC para Requests API; authority PRC segue Engineering API. Provar cenários intercalados A/B, >100 registros, totals, empate e permissão parcial. Se não houver contrato, bloquear advanced sort/filter até readiness.
3. Para `/work-queue`: manter o universo atual do requests-api; PRC da Engenharia não entra automaticamente nessa fila corporativa.
4. Usar URL como fonte de query; storage apenas para preferências de colunas/layout; versionar migração de preferências; não armazenar tokens/payload sensível.
5. Backend AuthZ por objeto e por operação permanece obrigatório; UI oculta apenas apresentação, nunca concede ação.
6. Nenhum write TOTVS, nenhuma migration, grant RBAC ou deploy PRD implicitamente autorizado por este design. Mudança de owner/authority/BC exige `ARCHITECTURE_DECISION_REQUIRED`.

## 6. RQ e AC verificáveis

| ID | Requirement / critério de aceite | Estado |
|---|---|---|
| RQ-01 / AC-01 | Quatro abas TopBar acima do hero; gates e navegação corretos em todas as rotas | TARGET |
| RQ-02 / AC-02 | Hero único compacto Minhas e Fila, sem card/título duplicado | TARGET |
| RQ-03 / AC-03 | Busca/chips/filtros ativos refletem API/URL/back-forward/refresh | TARGET |
| RQ-04 / AC-04 | Popup filtros tipados, apply/clear, sem clipping e com a11y | TARGET |
| RQ-05 / AC-05 | 3 sorts com prioridade, whitelist e prova global pre-pagination | TARGET |
| RQ-06 / AC-06 | Colunas visíveis/ordem/restauração independentes por página e persistentes | TARGET |
| RQ-07 / AC-07 | Tabela/Cards possuem field parity, total e navegação idênticos | TARGET |
| RQ-08 / AC-08 | Paginação consistente, total honesto e estados vazios/403/partial | TARGET |
| RQ-09 / AC-09 | Componentes neutros extraídos para Plugin UI, usados **pelos dois** MFEs, sem import cross-MFE | TARGET |
| RQ-10 / AC-10 | Tema claro/escuro, 1440/768/390/320px, zoom 200%, teclado/ARIA, overflow 0 | TARGET |
| RQ-11 / AC-11 | Admin/Nova preservam fluxo e permissions, com hero/breadcrumb adequados | TARGET |
| RQ-12 / AC-12 | Helpdesk sem regressão; Requests PRC, NF, workflow, realtime e Core AuthZ intactos | TARGET |
| RQ-13 / AC-13 | Backend global de Minhas demonstrado para 2 fontes, sem pós-paginação local e sem corrupção de acesso | TARGET / BLOCKED UNTIL CONTRACT |

**Evidências mínimas:** testes Plugin UI isolados + consumers Helpdesk e My Requests; contract/integration tests de filtros/sort/totals por fonte e merge; E2E real em HML (filtros, sorts, columnas, cards, deep-link, back/forward, denied, parcial, responsivo, mobile, dark); build+typecheck de ambos os MFEs e kit; evidência SHA/digest após deploy HML; regressão de NF/PRC/Helpdesk.

## 7. Entrega sugerida ao executor — na branch main, sem deploy PRD

Fase G0: reanchor HEAD/origin/main, git status, WIP concorrente, authorities, contratos e API atual; registrar o que é PROVEN/TO_INVENTORY. Fase G1: mapear componentes Helpdesk/Plugin UI, fazer Abstraction Gate e documentar nomes/props/imports exatos. Fase G2: promover apenas primitivas visuais faltantes para Plugin UI e converter Helpdesk ao export neutro; testes do kit e regressão. Fase G3: modernizar My Requests nas quatro páginas, priorizar Mine e Fila, sem duplicar título; matriz de campos; URL e preferências. Fase G4: corrigir contratos de filtro/sort/merge backend **somente mediante authority existente e gate aprovado**; caso contrário marcar BLOCKED, não simular. Fase G5: HML sequencial Plugin UI → Helpdesk → My Requests (e backends se requeridos), E2E visual/funcional; rollback e ledger.

**Controle de mudança:** apenas `main` (sem feature branch), ff-only, não descartar ou incluir WIP de outros executores; nenhuma liberação de PRD nesta etapa. Doc não substitui aceitação do PO, teste runtime ou autorização para deploy.
