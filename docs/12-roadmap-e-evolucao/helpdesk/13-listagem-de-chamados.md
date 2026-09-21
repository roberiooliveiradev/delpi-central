# 13 — Listagem de chamados

> **Status:** inventário e alvo. **Não autoriza implementação.** Não altera [`06-plano-execucao.md`](./06-plano-execucao.md). Não cria HD novo em [`07-requisitos.md`](./07-requisitos.md).
> **Pedido:** a listagem deve cobrir o que o GLPI já entrega para o solicitante achar e ler o próprio chamado. Este arquivo só documenta.
> **Tela publicada:** [`WIREFRAMES.md`](./WIREFRAMES.md) §1 — tabela com filtros, sem total do parque.
> **Fotos de 21/09/2026:** MFE `/apps/helpdesk` (tabela + filtros) e GLPI Super-Admin `front/ticket.php` (128 128 linhas). A segunda é bancada, não o produto.
> **Contrato vigente:** [`03-contrato.md`](./03-contrato.md).
> **Lacunas antigas da lista:** L-01…L-12 em [`11-lacunas-da-experiencia.md`](./11-lacunas-da-experiencia.md) — várias já publicadas; este arquivo é a fonte da paridade GLPI × Minha DELPI.
> **Corpo da mensagem:** [`12-conteudo-da-mensagem.md`](./12-conteudo-da-mensagem.md) — a lista **não** mostra HTML.

Este documento responde: o que o GLPI considera uma listagem de chamados, o que a interface simplificada do solicitante mostra, o que a HLAPI 2.2 devolve, o que a Minha DELPI faz hoje e o que **deve** entrar na grade quando houver autorização de código.

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

Isto **estende** HD-008 (listar) e HD-016 (ajuda). Não é HD-019. Não abre H5. Não muda a busca para HTML do corpo ([`12`](./12-conteudo-da-mensagem.md) M-42).

## 2. Fontes e grau de evidência

| Fonte | Classe | Uso |
|---|---|---|
| [Tickets](https://help.glpi-project.org/documentation/modules/assistance/tickets) | CONFIRMADO_EM_DOCUMENTACAO_CANONICA | o objeto chamado; não detalha cada coluna da grade |
| [Search](https://help.glpi-project.org/documentation/readme-1-1/search) | CONFIRMADO_EM_DOCUMENTACAO_CANONICA | critérios, paginação, ordenação, export, ações em massa, lixeira, pesquisas salvas, vista mapa, multi-sort |
| [Saved searches](https://help.glpi-project.org/faq/glpi/saved_searches) | CONFIRMADO_EM_DOCUMENTACAO_CANONICA | bookmark da busca; visibilidade por perfil/entidade |
| [Search result display](https://help.glpi-project.org/documentation/modules/configuration/general/search-result-display.md) | CONFIRMADO_EM_DOCUMENTACAO_CANONICA | colunas globais vs pessoais; interface helpdesk tem vista própria |
| Foto Super-Admin `front/ticket.php` (21/09/2026) | CONFIRMADO_EM_DOCUMENTACAO_CANONICA (captura) | colunas da bancada + 128 128 + contadores |
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
| Data de abertura | `date` / `date_creation` | IMPLEMENTADO — «Aberto» (só relativo) |
| Data da resolução | `date_solve` / `solvedate` | ALVO_LEITURA — BFF ainda não publica |
| Última atualização | `date_mod` | IMPLEMENTADO — «Atualizado» (só relativo) |
| Requerente | `team` role `requester` | ALVO_LEITURA se o token vir chamado de outro; senão redundante |
| Atribuído — técnico | `team` role `assigned` | IMPLEMENTADO — rótulo; **não ordena** |
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
| Multi-sort (Ctrl+clique) | CONSOLE_GLPI / kit sem isso |
| Itens por página + «Showing 1 to 15 of N» | total **não** inventar; seletor de página ALVO menor |
| Busca rápida global (tickets + ativos + usuários) | CONSOLE_GLPI — outro módulo |
| Kanban / modelos / adicionar em massa | CONSOLE_GLPI |
| Contadores do parque (1 000, 100 novos, 128 128) | CONSOLE_GLPI |
| Árvore de entidade | CONSOLE_GLPI |

### 3.4 Interface simplificada (solicitante)

Issue #23387 + prática GLPI 11: o solicitante vê uma grade curta; a busca costuma limitar-se a características do chamado e a atores «requerente». Observador como filtro pode faltar. Colunas da vista Helpdesk configuram-se à parte da vista central.

Alvo da Minha DELPI = essa grade + achar o próprio chamado (busca, filtro, ordenação, página), no kit, sem motor de inventário.

## 4. O que a HLAPI 2.2 confirma

`GET /api.php/v2.2/Assistance/Ticket` com `filter` RSQL, `start`, `limit`, `sort`. Campos filtráveis = propriedades do schema, notação ponto.

| Necessidade | HLAPI | BFF hoje |
|---|---|---|
| Título | `name=like=*termo*` | `q` |
| Conteúdo | `content=like=` **se** a propriedade existir no item | não pede |
| Status | `status.id==` / `=in=` | grupos `open` / `in_progress` / `solved` / `closed` |
| Urgência | `urgency==1…5` | `urgency_id` |
| Categoria | `category.id==` | `category_id` |
| Abertura | `date_creation=ge=` / `=le=` | não pede |
| Atualização | `date_mod=ge=` / `=le=` | `updated_from` / `updated_to` |
| Resolução / fechamento | `date_solve` / `date_close` no changelog 2.1 | não lê nem filtra |
| Tipo incidente/requisição | `type` no schema ITIL (HIPOTESE no GET) | não publica |
| Prioridade / impacto | schema ITIL (HIPOTESE no GET) | não publica |
| Técnico | `team` no JSON; **RSQL em `team` não funciona** | só rótulo `assigned_display_name` |
| Lixeira | `is_deleted==false` | sempre |
| Ordem | `sort` no campo do schema | `id`, `name`, `status.id`, `category.name`, `urgency`, `date_mod`, `date_creation` |
| Página | `start` / `limit` | `page` / `page_size` (20, máx. 50) + `has_more` |
| Total do parque | a coleção **não** devolve total confiável | proibido inventar |

`q` só conserva letra, número, espaço, hífen e underscore. Status ou sort desconhecidos: 422.

## 5. O que a Minha DELPI faz hoje

```text
URL ?q=&status=&urgency_id=&category_id=&updated_from=&updated_to=&sort=&page=
  → GET /tickets (BFF)
    → GET /Assistance/Ticket filter/start/limit/sort
      → items[] + has_more
        → HelpdeskDataTable
```

| Superfície | Hoje |
|---|---|
| Colunas | id, título, status (badge), categoria, urgência, técnico, aberto, atualizado |
| Datas na grade | só relativo («4 minutos atrás»); o GLPI da foto usa data-hora absoluta |
| Busca | só título; placeholder «Título do chamado» |
| Filtros | status agrupado, urgência, categoria, atualizado de/até |
| Filtro de abertura | não existe |
| Ordenação | clique no cabeçalho → novo GET; técnico sem sort |
| Página | número + setas; sem total; sem escolher tamanho |
| Estado na URL | sim — F5 mantém o recorte |
| Vazio | «nenhum chamado» vs «nenhum neste recorte» |
| Default | `status` vazio = Todos (inclui solucionado/fechado); subtítulo «Chamados no seu nome» |
| Kit | `DataTable` + `FiltersKit`; sem CSS de grade no MFE |

**Causa das diferenças para a foto Super-Admin:** recorte de produto (colaborador) + contrato que ainda não lê `date_solve` / `date_close` / `content` na lista. Não é limitação escondida do kit.

[`11`](./11-lacunas-da-experiencia.md) §1 ainda descreve a lista MFE como cartões sem busca. Essa frase está **obsoleta** em relação à tela publicada; a autoridade da lista passa a ser este arquivo.

## 6. Paridade GLPI × Minha DELPI × alvo

| Capacidade | GLPI (solicitante / schema) | Hoje | Alvo |
|---|---|---|---|
| Id | sim | sim | invariante |
| Título | sim | sim | invariante |
| Status | sim | sim + grupos | invariante; ver G-21 pendente |
| Categoria | sim | sim | invariante |
| Urgência | schema; self-service cria com ela | sim | invariante |
| Técnico (rótulo) | sim | sim | invariante |
| Aberto / atualizado | data-hora | só relativo | **absoluta + relativo** |
| Data de resolução | bancada e schema | não | coluna quando `date_solve` vier |
| Data de fechamento | schema `date_close` | não | coluna ou a mesma célula se só uma existir |
| Requerente | bancada | não | só se o token listar chamado alheio |
| Busca no título | sim | sim | invariante |
| Busca no conteúdo | motor central; self-service limitado | não | se H1 confirmar `content=like` |
| Filtro atualizado | sim | sim | invariante |
| Filtro aberto | sim | não | `created_from` / `created_to` |
| Filtro técnico | UI central | não | BLOQUEADO — `team` não filtra em RSQL |
| Tipo / prioridade / impacto | ITIL | não | FORA do colaborador (abertura só urgência) |
| Entidade / último editor | bancada | não | CONSOLE_GLPI |
| Total / contadores | bancada | `has_more` | invariante — sem total inventado |
| Itens por página | 15 na foto | 20 fixo | seletor 10/20/50 no contrato já existente |
| Export / massa / Kanban / saved search / lixeira / mapa | doc Search | não | CONSOLE_GLPI |
| HTML do título | título não é HTML | `display_text` | invariante |

## 7. Ledger — o que deve ser implementado

Estado neste inventário (nenhum item autoriza diff):

```text
IMPLEMENTADO          → já na tela/contrato
ALVO_LEITURA          → a linha deve mostrar o que o GLPI já grava
ALVO_RECORTE          → o GET deve aceitar o critério
KIT_A_ESTENDER        → falta primitivo no plugin-ui
HERDA_KIT             → só ligar
HIPOTESE_A_VALIDAR    → falta captura no pipeline real
BLOQUEADO             → evidência impede agora
CONSOLE_GLPI          → fora do MFE
FORA                  → não entra neste produto
```

### 7.1 Grade (colunas)

| ID | Capacidade | Estado | Dono quando houver código |
|---|---|---|---|
| G-01 | Id, título, status, categoria, urgência, técnico, aberto, atualizado | IMPLEMENTADO | — |
| G-02 | Data-hora absoluta na célula (o relativo pode ficar como texto auxiliar) | ALVO_LEITURA | MFE; o JSON já é instante |
| G-03 | `solved_at` a partir de `date_solve` | ALVO_LEITURA + HIPOTESE campo no GET | BFF aditivo |
| G-04 | `closed_at` a partir de `date_close` | ALVO_LEITURA + HIPOTESE | BFF aditivo; se igual a `solved_at`, uma coluna basta |
| G-05 | `requester_display_name` na lista | ALVO_LEITURA se o token vir outro solicitante | BFF já tem a regra no detalhe |
| G-06 | Ordenar por técnico | BLOQUEADO | `team` não é coluna SQL da HLAPI |
| G-07 | Ordenar por resolução | ALVO_RECORTE se H2 | `sort=solved_at` → `date_solve` |
| G-08 | Coluna entidade / último editor / prioridade / tipo / impacto | CONSOLE_GLPI / FORA | — |
| G-09 | Badge de status pelos tokens do kit | IMPLEMENTADO | sem verde fixo do GLPI |

### 7.2 Recorte (filtros e busca)

| ID | Capacidade | Estado | Dono quando houver código |
|---|---|---|---|
| G-20 | `q` no título | IMPLEMENTADO | — |
| G-21 | `q` também no `content` (texto, não HTML) | ALVO_RECORTE + H1 | BFF `name=like` **ou** `content=like`; sem segunda caixa |
| G-22 | Status agrupado | IMPLEMENTADO | — |
| G-23 | Grupo `pending` (status 4) explícito | ALVO_RECORTE | mesmo enum de grupos; hoje `pending` cai em `open` |
| G-24 | Urgência, categoria, atualizado de/até | IMPLEMENTADO | — |
| G-25 | Aberto de/até (`created_from` / `created_to`) | ALVO_RECORTE | `date_creation`; ADDITIVE |
| G-26 | Filtro por técnico | BLOQUEADO | mesmo motivo de G-06 |
| G-27 | Default «Abertos» | FORA neste inventário | default Todos + subtítulo «no seu nome» já corrige o mentir de «abertos» |
| G-28 | Caracteres de `q` | invariante | sem injetar RSQL |

### 7.3 Página, URL, vazios

| ID | Capacidade | Estado |
|---|---|---|
| G-30 | `page` / `has_more` sem total | IMPLEMENTADO |
| G-31 | Seletor `page_size` 10/20/50 | ALVO_RECORTE — query já existe; a tela não oferece |
| G-32 | Recorte na URL e F5 | IMPLEMENTADO |
| G-33 | Vazio vs recorte vazio | IMPLEMENTADO |
| G-34 | 403/409 não viram lista vazia | IMPLEMENTADO |
| G-35 | Lixeira fora da lista | IMPLEMENTADO |
| G-36 | «Showing 1–15 of 128128» | CONSOLE_GLPI |

### 7.4 Satélites

| ID | Capacidade | Estado |
|---|---|---|
| G-40 | `helpTooltips.list` / `.filters` descrevem data absoluta, resolução e busca no texto | mesmo entregável de código |
| G-41 | Lista não renderiza HTML do título/corpo | invariante — [`12`](./12-conteudo-da-mensagem.md) |
| G-42 | Identidade: id/e-mail; nome na coluna é rótulo | invariante |
| G-43 | Sem CSS de tabela no MFE | invariante |

## 8. Ownership

```text
PRODUCER          GLPI GET /Assistance/Ticket
TRANSFORMER       mapping.build_ticket_list_query / parse_ticket_list / _summary
CANONICAL OWNER   helpdesk-api (contrato da lista)
CONSUMERS         MFE HelpdeskPage, TicketListTable, parseTicketListFilters
NÃO-CONSUMIDOR    api-delpi, Chat, portal
FALLBACK          items: [] + has_more false
PERSISTENCE       recorte só na URL do MFE; dono do chamado = GLPI
RELOAD            F5 na mesma query
SURFACES          /apps/helpdesk apenas
TESTS             test_mapping / ticketView.test (filtros); não cobrem date_solve
DOCS/HELP         este arquivo + helpTooltips no entregável de código
```

Ler `TicketListTable` e `build_ticket_list_query` **antes** de mudar o JSON. Campos novos são aditivos.

## 9. Contrato-alvo (quando for implementar)

Decisão travada: evolução **ADDITIVE**. Não é etapa de código.

| Hoje | Permanece | Novo se H2/H5 confirmarem |
|---|---|---|
| `created_at`, `updated_at` | instante ISO | — |
| — | — | `solved_at`, `closed_at` (opcionais, string vazia se o GLPI não trouxer) |
| — | — | `requester_display_name` na lista (opcional) |
| `q` | título | também `content` **se** H1 |
| `updated_from` / `updated_to` | — | `created_from` / `created_to` |
| `status=open` inclui 4 | documentar | `pending` como valor novo do enum (ADDITIVE) |
| `page_size` | 20 | a tela passa a enviar 10/20/50 |

Classificação: ADDITIVE nos GET e nas query. Sem path novo. Sem total inventado. Sem filtrar por nome de pessoa.

## 10. Arquitetura-alvo (quando for implementar)

```text
URL do MFE (recorte)
  → BFF monta RSQL só com campos do schema
  → GLPI devolve a página do token
  → BFF traduz rótulos + datas + assigned
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
| D-04 | Sem entidade, último editor, Kanban, export, massa, saved search, lixeira, mapa | Search doc + HD-011 |
| D-05 | Tipo/prioridade/impacto fora da abertura e da grade do colaborador | formulário só urgência |
| D-06 | HTML do corpo não entra na célula | 12 M-42 |
| D-07 | Identidade por id/e-mail | C-05 |
| D-08 | Sem CSS de grade no MFE | kit |
| D-09 | Default da lista permanece Todos | subtítulo já não diz «abertos» |

### Não prontas (não viram receita E*.S*)

| ID | Falta | Bloqueia |
|---|---|---|
| H1 | `content=like` no GET de produção | G-21 |
| H2 | `date_solve` / `date_close` no item da lista | G-03, G-04, G-07 |
| H3 | o token colaborador vs Super-Admin: quantos itens o GET devolve | só confirma D-01; paginação já existe |
| H4 | markup/campos de `type` e `priority` no item | só reforçaria D-05 |
| H5 | um token que vê chamado de outro solicitante | G-05 |

Captura aceitável (quando autorizada a **investigar**, sem produto): um item de `GET /Assistance/Ticket` (chaves do JSON, sem gravar corpo pessoal em log). Senha de teste não entra em commit.

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
