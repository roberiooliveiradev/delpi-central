# Trilha — Home hub (H0–H6)

Fonte: [plan.md](./plan.md). Autoridade: instruções oficiais do arquiteto e `.cursor` > padrão visual dos Portais (`docs/11-padroes-de-desenvolvimento/padrao-visual-portais-minha-delpi.md`) > `30-plugin-ui-reuse-map.md` > este track > plan.md.

## 1. Regras

1. `main`, sem branch, sem stash/reset/clean. `git add` **só com caminhos explícitos** da etapa (outros agentes usam a mesma árvore; nunca `git add -A`, `git add .`, `commit -a`). Push a cada etapa.
2. Protocolo: LER → INVENTARIAR → ALTERAR (mínimo) → TESTAR → VERIFICAR → DOCUMENTAR (quadro e registro deste track no mesmo commit) → REPORTAR.
3. Até 3 ciclos de correção por problema; no 4º, BLOCKED.
4. Sem permission nova (só `controllership-finance.access`/`.manage`; acesso ao LNF é leitura das permissões efetivas do Core). Backend autoriza; UI só esconde.
5. `@delpi/plugin-ui` first; reaproveitar o que o Comercial usa. Mudança no plugin-ui só se indispensável, aditiva e com prova dos consumidores (lição da T13R).
6. Migration nova só a V030; nunca editar migration aplicada.
7. Repositório público: nenhum dado real.
8. Evidência `PROVEN | TO_INVENTORY | INCONCLUSIVE`; teste `PASS | FAIL | TEST_NOT_RUN`. Página que não foi aberta é INCONCLUSIVE.

## 2. Paradas

| # | Quando parar |
|---|---|
| Z1 | 4º ciclo no mesmo problema |
| Z2 | Falha nova em suíte (não pré-existente no pai) |
| Z3 | O padrão do Comercial exige mudança no plugin-ui que não seja aditiva |
| Z4 | A regra de entrada do app LNF não pode ser lida das permissões efetivas sem acoplar ao domínio do LNF — listar opções |
| Z5 | Escolha de produto não coberta por D1–D8 (DECISION_REQUIRED) |
| Z6 | Falha em PROD → rollback e parar |

## 3. Quadro de status

| Etapa | Status | SHA |
|---|---|---|
| H0 Inventário do padrão Comercial × CF | TODO | |
| H1 BFF: `lnfAccess` no viewer-context | TODO | |
| H2 BFF: favoritos (V030 + rotas) | TODO | |
| H3 MFE: cards (Portal sai, Notas fiscais, Administração) | TODO | |
| H4 MFE: favoritos (estrela, store, barra do topo) e Ajuda | TODO | |
| H5 HML | TODO | |
| H6 PROD | TODO | |

## 4. Etapas

**H0 — Inventário (somente leitura).** No Comercial: `pluginRouteCatalog.ts` (seções, ordem, ícones `hubRouteIcons.tsx`), `HomePage.tsx` (estrela, «Últimos acessos», busca), `homeFavoritesApi.ts`, `homeFavoritesStore.ts`, `ShellFavoritesStrip.tsx`, testes estruturais (`homeLauncher.structural.test.mjs`, `pluginRouteCatalog.test.mjs`); `commercial-api` V006, rotas, repositório e testes. No CF: os equivalentes e o `/viewer-context`. Saída: tabela «peça do Comercial → peça do CF (existe / criar / adaptar)» e as respostas de D7/D8 (o que o Comercial faz).

**H1 — `lnfAccess`.** `GET /viewer-context` ganha `capabilities.lnfAccess` (aditivo), calculado das permissões efetivas do Core com a mesma regra de entrada do app LNF. Testes: com e sem permissão do LNF; contrato do viewer.

**H2 — Favoritos na BFF.** V030 `controllership_finance.home_favorites`; `GET/PUT /home-favorites` no padrão do Comercial; autorização `access` ou `accessDre`; usuário = `sub`; validação dos itens contra os caminhos do catálogo e limite de quantidade; testes (200/401/403/422, persistência, isolamento por usuário).

**H3 — Cards.** `HUB_SECTIONS` no alvo do plan §1: tira `portal`; card `notas-fiscais` (ícone do padrão, ex.: `FileText`/`Receipt` do lucide) com Auditoria de Entradas e o link externo `/apps/lancamento-notas-fiscais` (`requiredCap: "lnfAccess"`, novo `kind` para link externo se o catálogo não tiver); card `administration` com os três itens de manage; Central de Fechamento só com os três de access; DRE inalterado. Busca e «Últimos acessos» como o Comercial (D7). Testes do catálogo e estrutural do Início.

**H4 — Favoritos no MFE e Ajuda.** API, store, estrela por caminho (D8), «Favoritos» na barra do topo com o componente do plugin-ui, favorito sem permissão escondido; `CF_HELP` do Início atualizado. Testes de render e de store; `tsc`.

**H5 — HML.** Publicar BFF (V030) e MFE. Playwright: perfis access, manage, LNF sim/não, DRE → cards certos; favoritar → recarregar → continua; abrir pela barra; celular; claro/escuro; teclado/foco. Screenshots no report (não commitar).

**H6 — PROD.** Tags `rollback-home-hub-controllership-finance-api` e `rollback-home-hub-controllership-finance`; BFF (V030) → MFE; Início abre (página, não só remoteEntry); `/home-favorites` com usuário real pelo próprio app; logs sem token. Falha → rollback (Z6).

## 5. Rollback

MFE e BFF pelas tags. V030 só cria tabela nova: rollback da BFF não precisa desfazer a tabela.

## 6. Registro

| Data | Etapa | SHA | Status | Nota |
|---|---|---|---|---|
| 2026-11-14 | plano | — | READY | Doc 170. D1–D4 do owner; D5 regra do produto; D6–D8 propostas pelo Claude. |
