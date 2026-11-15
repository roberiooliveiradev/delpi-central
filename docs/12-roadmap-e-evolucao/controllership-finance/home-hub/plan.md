# Plano — Início do Portal Controladoria & Finanças no padrão dos Portais

## 1. Hoje × alvo

**Hoje** (`plugins/controllership-finance/src/content/pluginRouteCatalog.ts`, `HUB_SECTIONS`; print do owner, 14/11/2026):

| Card | Caminhos | Permissão |
|---|---|---|
| Portal | Início, Meu perfil | access |
| Central de Fechamento | Fechamento mensal, Documentos e interações, Relatórios e divergências, Auditoria de Entradas | access |
| (mesmo card) | Administração do checklist, Documentos do fechamento, Catálogos governados | manage |
| Central de Fechamento (DRE) | Fechamento Mensal (documentos recebidos) | accessDre |

Sem favoritos; «Últimos acessos» mostra «Início».

**Alvo** (padrão do Comercial: cards por área de trabalho, administração no fim, estrela em cada caminho):

| Ordem | Card | Descrição | Caminhos | Quem vê |
|---|---|---|---|---|
| 1 | Central de Fechamento | Consultas e acompanhamento do fechamento mensal. | Fechamento mensal · Documentos e interações · Relatórios e divergências | access |
| 2 | **Notas fiscais** | Conferência e lançamento das notas de entrada. | Auditoria de Entradas · **Lançamento de notas fiscais** (abre o app LNF) | Auditoria: access · LNF: quem tem acesso ao app LNF |
| 3 | **Administração** | Checklist, documentos e catálogos do fechamento. | Administração do checklist · Documentos do fechamento · Catálogos governados | manage |
| — | Central de Fechamento (DRE) | (sem mudança) | Fechamento Mensal | accessDre |

Sai o card **Portal**: Início é a página que abre o Portal e está na barra do topo; Meu perfil está no avatar da barra do topo.

Barra do topo: entra **Favoritos** (como no Comercial). As demais abas (Visão geral, Sala de interação, Minhas tarefas, Ajuda) só entram quando a funcionalidade existir — não criar aba vazia.

## 2. Decisões

| # | Decisão | Origem |
|---|---|---|
| D1 | Card Portal (Início, Meu perfil) sai dos cards. | owner, 14/11/2026 |
| D2 | Card novo **Notas fiscais**: Auditoria de Entradas + link para o app Lançamento de Notas Fiscais. | owner |
| D3 | Card **Administração** próprio, só com `controllership-finance.manage`. | owner |
| D4 | **Favoritos** agora, igual ao Comercial: persistidos na BFF do Portal, estrela nos caminhos, «Favoritos» na barra do topo. | owner |
| D5 | Padrão de referência: Portal Comercial (`plugins/commercial` + `commercial-api`), reaproveitando componentes do `@delpi/plugin-ui` (`TopBarFavoritesStrip` e o que o Comercial usa). Não criar componente que já existe. | regra do produto |
| D6 | Link do LNF aparece só para quem pode abrir o app LNF. A BFF informa isso no `/viewer-context` (campo aditivo `capabilities.lnfAccess`) lendo as permissões efetivas do Core — **sem permission nova** no Portal; mesma regra de entrada do app LNF (a CLARA já calcula `has_lnf_any`). | Claude |
| D7 | Início e Meu perfil continuam na busca do Início («Buscar caminhos…» e Ctrl+K) se o Comercial fizer assim; senão, seguem o Comercial. «Últimos acessos» não lista o Início. | Claude (seguir o Comercial) |
| D8 | O link externo do LNF não tem estrela nesta etapa (favorito só de caminho do próprio Portal), salvo se o Comercial já favoritar link externo. | Claude |

## 3. Favoritos (igual ao Comercial)

| Camada | Comercial (referência) | Controladoria & Finanças (alvo) |
|---|---|---|
| Tabela | `commercial-api/migrations/V006__home_favorites.sql` — `home_favorites(user_id TEXT PK, items JSONB, updated_at)` | `controllership-finance-api/migrations/V030__home_favorites.sql` no schema `controllership_finance` |
| Rotas | `GET/PUT /home-favorites` (`home_favorites_routes.py`) + repositório Postgres | mesmas rotas na BFF, atrás de `controllership-finance.access` **ou** `accessDre` (cada um vê os seus); usuário = `sub` do JWT; itens validados contra o catálogo de caminhos (viewId/search conhecidos), com limite de quantidade |
| MFE | `api/homeFavoritesApi.ts`, `app/homeFavoritesStore.ts`, `app/ShellFavoritesStrip.tsx`, estrela no `HomePage.tsx` | os mesmos papéis em `plugins/controllership-finance`, mesmo comportamento (otimista, erro visível, sem perder estado) |

Favorito de caminho que o usuário deixou de poder ver (perdeu `manage`, por exemplo) some da barra e dos cards; não vira link quebrado.

## 4. Ajuda e textos

Ajuda (`CF_HELP`) do Início atualizada no mesmo gate: card Notas fiscais, card Administração, favoritos. Textos em PT-BR; identificadores técnicos em inglês.

## 5. Critério de aceite

1. Início com os cards do §1, na ordem; card Portal fora; Administração só com manage; link LNF só com acesso ao LNF; DRE sem mudança.
2. Estrela em cada caminho do Portal; marcar e desmarcar persiste (recarregar a página mantém); «Favoritos» na barra do topo abre o caminho.
3. Mesmo visual e comportamento do Comercial (desktop, celular, teclado, foco, claro e escuro).
4. `/viewer-context` com `capabilities.lnfAccess` aditivo; `/home-favorites` com 401/403 corretos; testes de contrato.
5. Suítes do MFE e da BFF sem falha nova contra o commit pai; consumidores do plugin-ui sem regressão se o plugin-ui for tocado.
6. HML: Playwright — usuário com access (sem manage), com manage, com LNF e sem LNF, DRE: cards certos para cada um; favoritar, recarregar, abrir pela barra.
7. PROD publicado com tag de rollback; Início abre; favoritos funcionam.
