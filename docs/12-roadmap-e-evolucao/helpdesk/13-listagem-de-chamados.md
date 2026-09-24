# 13 — Listagem de chamados

> **Status:** inventário sincronizado com o código (E7 + H13). Paridade [`16-plano-paridade.md`](./16-plano-paridade.md) **concluída**. Não altera [`06-plano-execucao.md`](./06-plano-execucao.md).
> **Tela publicada:** [`WIREFRAMES.md`](./WIREFRAMES.md) §1 — tabela/cards, builder AND, rodapé `createDashboardPaginationKit` + `HintAction`, datas absolutas, `solved_at`/`closed_at`, `requester_display_name`, `q` no conteúdo, `pending`/`approval`, `created_*`.
> **Fotos de 21/09/2026:** MFE `/apps/helpdesk` e GLPI Super-Admin `front/ticket.php` (bancada, não o produto).
> **Contrato vigente:** [`03-contrato.md`](./03-contrato.md).
> **Lacunas antigas da lista:** L-01…L-12 em [`11-lacunas-da-experiencia.md`](./11-lacunas-da-experiencia.md) — sincronizadas com este arquivo.
> **Corpo da mensagem:** [`12-conteudo-da-mensagem.md`](./12-conteudo-da-mensagem.md) — a lista **não** mostra HTML.

Este documento responde: o que o GLPI considera uma listagem de chamados, o que a HLAPI 2.2 devolve, o que a Minha DELPI **entrega hoje**, e o que permanece CONSOLE / BLOQUEADO.

## 1. Recorte do produto

Meus Chamados de TI lista os chamados que o **token da pessoa** enxerga. Não é `front/ticket.php` do Super-Admin.

```text
lista do solicitante   = achar e abrir o próprio chamado
bancada Super-Admin    = parque, entidade, Kanban, ações em massa, 128 mil linhas
```

Há dois fluxos distintos:

| Fluxo | Pergunta |
|---|---|
| Leitura da grade | o que já está no chamado precisa aparecer na linha? |
| Recorte | o que a pessoa pode pedir ao helpdesk para achar o chamado? |

Isto **estende** HD-008 (listar) e HD-016 (ajuda). Não é HD-019. Não abre H5. Não muda a busca para HTML do corpo ([`12`](./12-conteudo-da-mensagem.md) M-42). Saved search, export, massa e Forms: [`15`](./15-capacidades-glpi.md).

## 2. Fontes e grau de evidência

| Fonte | Classe | Uso |
|---|---|---|
| [Tickets](https://help.glpi-project.org/documentation/modules/assistance/tickets) | CONFIRMADO_EM_DOCUMENTACAO_CANONICA | o objeto chamado; não detalha cada coluna da grade |
| [Search](https://help.glpi-project.org/documentation/readme-1-1/search) | CONFIRMADO_EM_DOCUMENTACAO_CANONICA | critérios, paginação, ordenação, export, ações em massa, lixeira, pesquisas salvas, vista mapa, multi-sort |
| [Saved searches](https://help.glpi-project.org/faq/glpi/saved_searches) | CONFIRMADO_EM_DOCUMENTACAO_CANONICA | bookmark da busca; visibilidade por perfil/entidade |
| [Search result display](https://help.glpi-project.org/documentation/modules/configuration/general/search-result-display.md) | CONFIRMADO_EM_DOCUMENTACAO_CANONICA | colunas globais vs pessoais; interface helpdesk tem vista própria |
| Foto Super-Admin `front/ticket.php` (21/09/2026) | CONFIRMADO_EM_DOCUMENTACAO_CANONICA (captura) | colunas da bancada + 128 128 + contadores |
| Capturas Search UI (filtros dinâmicos, colunas, multi-sort, toolbar) | CONFIRMADO_EM_DOCUMENTACAO_CANONICA (captura) | shape do motor central — §3.5 |
| Foto MFE `/apps/helpdesk` (21/09/2026) | CONFIRMADO_NO_CODIGO (tela) | tabela + filtros já publicados |
| Issue GLPI #23387 (lista self-service) | CONFIRMADO_EM_DOCUMENTACAO_CANONICA | interface simplificada: colunas configuráveis à parte; critérios de busca restritos |
| HLAPI 2.2 `GET /Assistance/Ticket` (`filter`, `start`, `limit`, `sort`) | CONFIRMADO_NO_CODIGO | binding em `mapping.build_ticket_list_query` |
| Changelog HLAPI `date_solve`, `date_close` | CONFIRMADO_EM_DOCUMENTACAO_CANONICA | campos no schema Ticket; o BFF **não** os publica |
| `team` no JSON, filtro RSQL por `team` | CONFIRMADO_EM_DOCUMENTACAO_CANONICA (forum/issue) | `team` é montado em PHP; **não** filtra em SQL |
| `TicketListTable` / `parseTicketListFilters` | CONFIRMADO_NO_CODIGO | colunas e query na URL |
| Presença de `type` / `priority` / `date_solve` no GET de lista **desta** produção | HIPOTESE_A_VALIDAR | capturar um item do `GET /Assistance/Ticket` |

O motor de busca do GLPI (centenas de critérios, AND/OR, export) é o da **interface central**. A interface simplificada do solicitante é um recorte. Meus Chamados copia o recorte do solicitante, não o motor inteiro.

## 3. O que o GLPI coloca numa listagem

### 3.1 Duas telas

| Tela | Quem vê | O que é |
|---|---|---|
| `front/ticket.php` (foto Super-Admin) | perfil central / Super-Admin | parque, árvore de entidade, Kanban, modelos, contadores, 15/128128 |
| Interface simplificada / Helpdesk | Self-Service, colaborador | «meus chamados»; colunas e critérios menores |

A foto do Super-Admin **não** é o alvo visual. Serve para inventariar capacidades e marcar CONSOLE_GLPI.

### 3.2 Colunas da bancada (foto 21/09/2026)

| Coluna GLPI | Campo típico | Destino na Minha DELPI |
|---|---|---|
| ID | `id` | IMPLEMENTADO — «Chamado» |
| Título | `name` | IMPLEMENTADO |
| Entidade | `entities_id` | CONSOLE_GLPI — HD-011 |
| Status | `status` | IMPLEMENTADO (rótulo + badge) |
| Data de abertura | `date` / `date_creation` | **IMPLEMENTADO** — «Aberto» (data-hora absoluta) |
| Data da resolução | `date_solve` / `solvedate` | **IMPLEMENTADO** — `solved_at` |
| Última atualização | `date_mod` | **IMPLEMENTADO** — «Atualizado» (data-hora absoluta) |
| Requerente | `team` role `requester` | **IMPLEMENTADO** — `requester_display_name` (rótulo; **não ordena**) |
| Atribuído — técnico | `team` role `assigned` | **IMPLEMENTADO** — rótulo; **não ordena** |
| Categoria | `category` | IMPLEMENTADO |
| Última edição por | `users_id_lastupdater` | CONSOLE_GLPI — bancada; nome não identifica |

A bancada **não** mostra urgência na foto. A Minha DELPI mostra: o colaborador escolhe urgência ao abrir.

### 3.3 Motor de busca da interface central (doc Search)

A doc oficial lista, além das colunas:

| Peça GLPI | Destino |
|---|---|
| Critérios múltiplos (contains / is / before / after, AND, AND NOT) | CONSOLE_GLPI |
| Critério em outro itemtype (multi) | CONSOLE_GLPI |
| Lixeira (ver / restaurar / apagar) | CONSOLE_GLPI; o BFF já exclui `is_deleted` |
| Pesquisa salva + alerta | CONSOLE_GLPI |
| Export CSV / PDF / SLK (página ou todas) | CONSOLE_GLPI |
| Ações em massa (lixeira, atualizar, atribuir…) | CONSOLE_GLPI |
| Vista mapa | CONSOLE_GLPI |
| Multi-sort (Ctrl+clique / popover) | **IMPLEMENTADO** no MFE (`TicketListSortLevel[]`, até 3 níveis); console GLPI continua à parte |
| Itens por página + «Showing 1 to 15 of N» | total **não** inventar; seletor `page_size` 10/20/50 **IMPLEMENTADO** |
| Busca rápida global (tickets + ativos + usuários) | CONSOLE_GLPI — outro módulo |
| Kanban / modelos / adicionar em massa | CONSOLE_GLPI |
| Contadores do parque (1 000, 100 novos, 128 128) | CONSOLE_GLPI |
| Árvore de entidade | CONSOLE_GLPI |

### 3.4 Interface simplificada (solicitante)

Issue #23387 + prática GLPI 11: o solicitante vê uma grade curta; a busca costuma limitar-se a características do chamado e a atores «requerente». Observador como filtro pode faltar. Colunas da vista Helpdesk configuram-se à parte da vista central.

Alvo da Minha DELPI = essa grade + achar o próprio chamado (busca, filtro, ordenação, página), no kit, sem motor de inventário.

### 3.5 Motor Search na UI central — captura 21/09/2026

Fotos do GLPI `front/ticket.php` (interface central). **Não** são a tela do solicitante; documentam o shape que o modelo declarativo da Minha DELPI precisa receber sem refatorar a grade depois.

| Peça na captura | Comportamento GLPI | Destino Meus Chamados |
|---|---|---|
| Builder «Pesquisar» | linha = campo + operador + valor; `+ regra` / grupo; lógica AND/OR | **IMPLEMENTADO** AND (`TicketListFilterBuilder`); OR/grupo aninhado = CONSOLE/evolução |
| Chip «Filtrado por Status» | resumo do recorte ativo | **IMPLEMENTADO** `TicketListToolbar` chips |
| «Ordenado por Última atualização» + popover | multi-nível ASC/DESC | **IMPLEMENTADO** multi-sort na URL/BFF |
| Modal «Selecione os itens padrões…» | visão global vs pessoal; colunas fixas/arrastáveis | **IMPLEMENTADO** catálogo + prefs localStorage; Entidade/último editor CONSOLE |
| Toolbar grade/mapa | troca lista ↔ mapa | mapa = CONSOLE |
| Seleção + lixeira vermelha | ações em massa | CONSOLE |
| Ícone colunas + atualizar + Exportar | preferência, reload, CSV/PDF | colunas/atualizar **IMPLEMENTADO**; export = CONSOLE |

Contrato futuro do BFF para grupos/regras continua ADDITIVE e RSQL — sem copiar o JSON interno do Search Engine do PHP.

## 4. O que a HLAPI 2.2 confirma

`GET /api.php/v2.2/Assistance/Ticket` com `filter` RSQL, `start`, `limit`, `sort`. Campos filtráveis = propriedades do schema, notação ponto.

| Necessidade | HLAPI | BFF hoje |
|---|---|---|
| Título | `name=like=*termo*` | `q` (OR com content) |
| Conteúdo | `content=like=` | `q` → `(name=like=…,content=like=…)` |
| Status | `status.id==` / `=in=` | grupos `open` / `in_progress` / `solved` / `closed` / `pending` / `approval` |
| Urgência | `urgency==1…5` | `urgency_id` |
| Categoria | `category.id==` | `category_id` |
| Abertura | `date_creation=ge=` / `=le=` | `created_from` / `created_to` |
| Atualização | `date_mod=ge=` / `=le=` | `updated_from` / `updated_to` |
| Resolução / fechamento | `date_solve` / `date_close` | lê e publica `solved_at` / `closed_at`; sort por resolução se pedido |
| Tipo incidente/requisição | `type` no schema ITIL | não publica |
| Prioridade / impacto | schema ITIL | não publica |
| Técnico | `team` no JSON; **RSQL em `team` não funciona** | só rótulo `assigned_display_name` |
| Lixeira | `is_deleted==false` | sempre |
| Ordem | `sort` no campo do schema | multi-nível; campos id/name/status/category/urgency/dates |
| Página | `start` / `limit` | `page` / `page_size` (10/20/50) + `has_more` |
| Total do parque | a coleção **não** devolve total confiável | proibido inventar |

`q` só conserva letra, número, espaço, hífen e underscore. Status ou sort desconhecidos: 422.

## 5. O que a Minha DELPI faz hoje

```text
URL ?q=&status=&urgency_id=&category_id=&created_from=&created_to=&updated_from=&updated_to=&sort=&page=&page_size=
  → GET /tickets (BFF)
    → GET /Assistance/Ticket filter/start/limit/sort
      → items[] (+ solved_at/closed_at/status_id) + has_more
        → HelpdeskDataTable + TicketListToolbar + FilterBuilder
```

| Superfície | Hoje |
|---|---|
| Colunas | id, título, status (badge por id), categoria, urgência, técnico, requerente, aberto, atualizado, resolução, fechamento (+ slots entity/last_editor ocultos) |
| Datas na grade | data-hora absoluta (`absoluteDateTimeLabel`) |
| Busca | título **ou** conteúdo (`q`) |
| Filtros | status agrupado (`open`/`in_progress`/`solved`/`closed`/`pending`/`approval`), urgência, categoria, aberto de/até, atualizado de/até |
| Ordenação | multi-nível na URL; técnico sem sort |
| Página | número + setas + seletor 10/20/50; sem total |
| Estado na URL | sim — F5 mantém o recorte |
| Vazio | «nenhum chamado» vs «nenhum neste recorte» |
| Default | `status` vazio = Todos; subtítulo «Chamados no seu nome» |
| Kit | `DataTable` + `FiltersKit` + toolbar/builder; sem CSS de grade no MFE |

**Causa das diferenças para a foto Super-Admin:** recorte de produto (colaborador) + CONSOLE (export, massa, mapa, entidade). Não é gap de datas/`content`/`pending` — esses já estão no BFF/MFE.

## 6. Paridade GLPI × Minha DELPI × alvo

| Capacidade | GLPI (solicitante / schema) | Hoje | Alvo |
|---|---|---|---|
| Id | sim | sim | invariante |
| Título | sim | sim | invariante |
| Status | sim | sim + grupos | invariante; ver G-21 pendente |
| Categoria | sim | sim | invariante |
| Urgência | schema; self-service cria com ela | sim | invariante |
| Técnico (rótulo) | sim | sim | invariante |
| Aberto / atualizado | data-hora | data-hora absoluta | invariante |
| Data de resolução | bancada e schema | `solved_at` | invariante |
| Data de fechamento | schema `date_close` | `closed_at` | invariante |
| Requerente | bancada | **IMPLEMENTADO** `requester_display_name` | invariante (G-05) |
| Busca no título | sim | sim | invariante |
| Busca no conteúdo | motor central; self-service limitado | `q` OR content | invariante |
| Filtro atualizado | sim | sim | invariante |
| Filtro aberto | sim | `created_from` / `created_to` | invariante |
| Filtro técnico | UI central | não | BLOQUEADO — `team` não filtra em RSQL |
| Tipo / prioridade / impacto | ITIL | não | FORA do colaborador (abertura só urgência) |
| Entidade / último editor | bancada | não | CONSOLE_GLPI |
| Total / contadores | bancada | `has_more` | invariante — sem total inventado |
| Itens por página | 15 na foto | seletor 10/20/50 | invariante |
| Export / massa / Kanban / saved search / lixeira / mapa | doc Search | não | CONSOLE_GLPI |
| HTML do título | título não é HTML | `display_text` | invariante |

## 7. Ledger — estado vigente

```text
IMPLEMENTADO          → já na tela/contrato
ALVO_LEITURA          → ainda não entregue
ALVO_RECORTE          → ainda não entregue
BLOQUEADO             → evidência impede agora
CONSOLE_GLPI          → fora do MFE
FORA                  → não entra neste produto
```

### 7.1 Grade (colunas)

| ID | Capacidade | Estado | Dono |
|---|---|---|---|
| G-01 | Id, título, status, categoria, urgência, técnico, requerente, aberto, atualizado | **IMPLEMENTADO** | requerente é rótulo (G-05); não ordena |
| G-02 | Data-hora absoluta na célula | **IMPLEMENTADO** | MFE `absoluteDateTimeLabel` |
| G-03 | `solved_at` a partir de `date_solve` | **IMPLEMENTADO** | BFF aditivo |
| G-04 | `closed_at` a partir de `date_close` | **IMPLEMENTADO** | BFF aditivo; `sort=closed_at` → `date_close` |
| G-05 | `requester_display_name` na lista | **IMPLEMENTADO** | mesmo `_requester_name` do detalhe; coluna opcional no catálogo |
| G-06 | Ordenar por técnico | **IMPLEMENTADO** (exceção Search legado + HLAPI hydrate) | `sort=assigned`; exige `GLPI_LEGACY_*` |
| G-07 | Ordenar por resolução e fechamento | **IMPLEMENTADO** | `solved_at` → `date_solve`; `closed_at` → `date_close` |
| G-08 | Coluna entidade / último editor / prioridade / tipo / impacto | CONSOLE_GLPI / FORA | — |
| G-09 | Badge de status pelos tokens do kit | **IMPLEMENTADO** | por `status_id` |

### 7.2 Recorte (filtros e busca)

| ID | Capacidade | Estado | Dono |
|---|---|---|---|
| G-20 | `q` no título | **IMPLEMENTADO** | — |
| G-21 | `q` também no `content` (texto, não HTML) | **IMPLEMENTADO** | BFF `(name=like,content=like)` |
| G-22 | Status agrupado | **IMPLEMENTADO** | — |
| G-23 | Grupo `pending` (status 4) explícito | **IMPLEMENTADO** | [`14`](./14-pagina-e-estados-do-chamado.md) S-05 |
| G-24 | Urgência, categoria, atualizado de/até | **IMPLEMENTADO** | — |
| G-25 | Aberto de/até (`created_from` / `created_to`) | **IMPLEMENTADO** | `date_creation` |
| G-26 | Filtro por técnico | **IMPLEMENTADO** (exceção Search legado + HLAPI hydrate) | `assignee_id`; exige `GLPI_LEGACY_*` |
| G-27 | Default «Abertos» | FORA neste inventário | default Todos + subtítulo «no seu nome» |
| G-28 | Caracteres de `q` | invariante | sem injetar RSQL |

### 7.3 Página, URL, vazios

| ID | Capacidade | Estado |
|---|---|---|
| G-30 | `page` / `has_more` sem total | **IMPLEMENTADO** |
| G-31 | Seletor `page_size` 10/20/50 | **IMPLEMENTADO** |
| G-32 | Recorte na URL e F5 | **IMPLEMENTADO** |
| G-32b | Voltar do detalhe/abertura restaura o recorte | **IMPLEMENTADO** | `listNavigationMemory` + seta Voltar |
| G-32c | Filtros só no construtor; page_size na paginação | **IMPLEMENTADO** | sem FiltersRow no topo |
| G-32d | Toggle Tabela \| Cards (localStorage) | **IMPLEMENTADO** | `usePersistedViewLayout` + DataCardsGrid |
| G-32e | Rodapé paginação do kit (setas, Ir para, resumo) + ajuda no controle | **IMPLEMENTADO** | `HelpdeskListPaginationFooter`; commits `4ea3ae19d`…`1d999772a` |
| G-33 | Vazio vs recorte vazio | **IMPLEMENTADO** |
| G-34 | 403/409 não viram lista vazia | **IMPLEMENTADO** |
| G-35 | Lixeira fora da lista | **IMPLEMENTADO** |
| G-36 | «Showing 1–15 of 128128» | CONSOLE_GLPI |

### 7.4 Satélites

| ID | Capacidade | Estado |
|---|---|---|
| G-40 | `helpTooltips.list` / `.filters` descrevem data absoluta, resolução e busca no texto | **IMPLEMENTADO** |
| G-41 | Lista não renderiza HTML do título/corpo | invariante — [`12`](./12-conteudo-da-mensagem.md) |
| G-42 | Identidade: id/e-mail; nome na coluna é rótulo | invariante |
| G-43 | Sem CSS de tabela no MFE | invariante |

### 7.5 Listagem dinâmica (modelo + chrome)

Estado novo: `PREP_COMPONENTES` = tipos e slots já no MFE; comportamento GLPI completo ainda não.

| ID | Capacidade | Estado | Dono |
|---|---|---|---|
| G-50 | Modelo de regras/grupos (`TicketListFilterGroup`) alimentado pelo recorte plano | IMPLEMENTADO | MFE `ticketListViewModel` |
| G-51 | Multi-sort tipado (`TicketListSortLevel[]`); até 3 níveis na URL/BFF | IMPLEMENTADO | MFE + `_sort_clause` |
| G-52 | Catálogo de colunas + preferência visível/ordem; fixas id/título | IMPLEMENTADO | `TicketListTable` via catálogo |
| G-53 | Toolbar: chips de filtro/sort + atualizar (+ slot colunas) | IMPLEMENTADO | `TicketListToolbar` |
| G-54 | Builder visual AND (+ regra); OR/grupo aninhado | IMPLEMENTADO (AND); OR → CONSOLE/evolução | MFE `TicketListFilterBuilder`; BFF flat query |
| G-55 | Preferência de colunas persistida (pessoal) | IMPLEMENTADO | `useTableColumnVisibility` localStorage — **não** `front/ticket.php` |
| G-56 | Export CSV/PDF, massa, lixeira, mapa, saved search | CONSOLE_GLPI | — |

## 8. Ownership

```text
PRODUCER          GLPI GET /Assistance/Ticket
TRANSFORMER       mapping.build_ticket_list_query / parse_ticket_list / _summary
CANONICAL OWNER   helpdesk-api (contrato da lista)
CONSUMERS         MFE HelpdeskPage, TicketListTable, TicketListToolbar, ticketListViewModel, parseTicketListFilters
NÃO-CONSUMIDOR    api-delpi, Chat, portal
FALLBACK          items: [] + has_more false
PERSISTENCE       recorte na URL do MFE; prefs de coluna em localStorage (`helpdesk:ticket-list:columns:v1`)
RELOAD            F5 na mesma query; botão atualizar da toolbar; builder reaplica na URL
SURFACES          /apps/helpdesk apenas
TESTS             test_mapping / ticketView.test / ticketListViewModel.test
DOCS/HELP         este arquivo + helpTooltips no entregável de código
```

Ler `TicketListTable`, `ticketListViewModel` e `build_ticket_list_query` **antes** de mudar o JSON. Campos novos são aditivos.

## 9. Contrato vigente (campos aditivos já publicados)

Evolução **ADDITIVE** já aplicada. Não reabrir como alvo.

| Campo / query | Estado |
|---|---|
| `created_at`, `updated_at` | instante ISO |
| `solved_at`, `closed_at` | opcionais; string vazia se o GLPI não trouxer |
| `status_id` + `status` | lista e detalhe |
| `q` | título **ou** conteúdo |
| `updated_from` / `updated_to` | — |
| `created_from` / `created_to` | — |
| `status=pending` / `approval` | ADDITIVE; `open` ainda inclui 10 |
| `page_size` | 10/20/50 na tela |
| `requester_display_name` na lista | **IMPLEMENTADO** (G-05; rótulo; não ordena) |

Sem path novo. Sem total inventado. Sem filtrar por nome de pessoa.

## 10. Arquitetura-alvo (quando for implementar)

```text
URL do MFE (recorte)
  → BFF monta RSQL só com campos do schema
  → GLPI devolve a página do token
  → BFF traduz rótulos + datas + assigned + requester
  → DataTable do kit  render-only
```

| Camada | Faz | Não faz |
|---|---|---|
| BFF | RSQL, grupos de status, datas, `has_more` | total do parque, filtro por `team` |
| Contrato | snake_case já usado | nomes cru do GLPI (`date_mod`) |
| plugin-ui | tabela, filtro, badge | path `/apps/helpdesk` |
| MFE | URL, factories, data absoluta | filtrar no browser a página inteira |

Não filtrar no cliente a coleção do Super-Admin. O token decide o universo; o BFF pagina.

## 11. Superfícies

| Fluxo | Superfície | Papel |
|---|---|---|
| Achar chamado | `/apps/helpdesk` | P0 deste inventário |
| F5 / compartilhar URL | mesma query | G-32 |
| Abrir linha | `/tickets/{id}` | invariante |
| Abrir (+) | `/tickets/new` | fora da grade |
| Lista × conversa | detalhe | HTML fica no 12 |
| Console | host GLPI | parque, massa, export |
| Ajuda | `helpTooltips.list` / `.filters` | G-40 |

## 12. Estado antes × depois

| Caso | Hoje | Alvo |
|---|---|---|
| P0 — achar o 1114 na foto | id, título, Novo, categoria, urgência, datas relativas | + data-hora absoluta; resolução quando existir |
| Irmão — só atualizados esta semana | filtro de/até em `date_mod` | invariante + filtro de abertura |
| Irmão — buscar palavra que só está na descrição | não acha | acha **se** H1 |
| Negativo — Super-Admin no MFE | o token vê o que o perfil vê; sem 128 128 inventado | não muda: sem contador, sem entidade |
| Negativo — filtro por técnico | não existe | continua sem (RSQL) |
| Invariante | lixeira, massa, export, Kanban | CONSOLE_GLPI |
| Identidade | nome só rótulo | não vira chave |

## 13. Decisões travadas × ainda não prontas

### Travadas

| ID | Decisão | Evidência |
|---|---|---|
| D-01 | Produto = lista do solicitante, não `front/ticket.php` | 01 + foto 128 128 |
| D-02 | Evolução ADDITIVE; sem total inventado | contrato + L-11 |
| D-03 | Sem filtro/ordem por `team` | RSQL não vê `team` |
| D-04 | Sem entidade, último editor, Kanban, export, massa, saved search, lixeira, mapa **na UI** | Search doc + HD-011 + captura toolbar |
| D-05 | Tipo/prioridade/impacto fora da abertura e da grade do colaborador | formulário só urgência |
| D-06 | HTML do corpo não entra na célula | 12 M-42 |
| D-07 | Identidade por id/e-mail | C-05 |
| D-08 | Sem CSS de grade no MFE (só chrome de página) | kit |
| D-09 | Default da lista permanece Todos | subtítulo já não diz «abertos» |
| D-10 | Listagem dinâmica: modelo declarativo no MFE **antes** do builder; contrato BFF ADDITIVE | captura Search + G-50…G-55 |

### Não prontas — fechadas em E6.S1 (21/09/2026)

| ID | Veredito | Bloqueia |
|---|---|---|
| H1 | **PROVEN** — `filter=content=like=*token*` HTTP 200 e achou o chamado 1119 | G-21 **segue** (E7.S3) |
| H2 | **PROVEN** — item da lista traz `date_solve` e `date_close` (null se aberto) | G-03, G-04 **seguem** (E7.S3) |
| H3 | **PROVEN** — Colaborador lista vazia / 404 nos ids 1114 e 1101; Super-Admin 206 com itens | confirma D-01 |
| H4 | **PROVEN** — item traz `type` e `priority` (int) | continua **fora** da grade (D-05) |
| H5 | **PROVEN** — token Colaborador 404 em 1114/1101 | G-05 |

Item da lista (chaves, sem corpo): `id`, `name`, `content`, `status.{id,name}`, `date_creation`, `date_mod`, `date_solve`, `date_close`, `resolution_date`, `sla_ttr`, `sla_tto`, `team[]`, `category`, `urgency`, `entity`, `user_recipient`. Senha de teste não entra em commit.

## 14. Prova, quando houver autorização

| Caso | Resultado |
|---|---|
| Positivo — grade | 1114 aparece com id, título, status, datas absolutas |
| Irmão — filtro atualizado | recorte de/até some quem está fora; não vira 403 |
| Irmão — abertura | `created_from` não usa `date_mod` |
| Irmão — conteúdo (se H1) | termo só no `content` acha o chamado; `q` vazio lista normal |
| Negativo — RSQL | `q` com `;` ou `=` não vira filtro extra |
| Negativo — técnico | não existe combo «filtrar por Michael» |
| Negativo — parque | nenhum número 128 128 na UI |
| F5 | a mesma query reabre o mesmo recorte |
| Contrato antigo | cliente sem `solved_at` continua válido |
| Tema | tokens do kit |

O teste `strips_html` da lista (título) **não** passa a devolver HTML. Título continua texto.

## 15. Ajuda in-app (satélite)

Quando houver implementação, no mesmo entregável, sem path de API:

| Tooltip | Hoje | Alvo |
|---|---|---|
| `helpTooltips.list` | tabela, +, setas, recorte | + datas completas; resolução se a coluna existir |
| `helpTooltips.filters` | busca e filtros pedem ao helpdesk | + busca no texto da abertura se H1; + período de abertura |

## 16. O que este arquivo não faz

- não abre E*.S* nem marca H5 `PROVEN`;
- não cria HD-019;
- não autoriza filtrar no browser o parque Super-Admin;
- não autoriza coluna de entidade nem seletor de entidade;
- não autoriza ações em massa, export, Kanban, pesquisa salva;
- não trata nome como identidade;
- não muda o corpo da conversa (isso é o 12).

Quando o pedido passar de «documentar» para «implementar», a primeira subetapa é fechar H1–H2 (e H5 se a coluna de requerente for desejada) no pipeline real. Só então G-02…G-25 viram plano executável.
