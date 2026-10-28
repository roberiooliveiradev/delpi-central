# ENGINEERING.HOME.R2 — Atualização única e catálogo sem atalho EVA

Status: implementado e publicado em `main`.
Baseline: `7f10276980` → rebase sobre `origin/main` `5ec34109ce`.

## Objetivo

1. Um único botão Atualizar na Home — o do Hero. Remover o botão
   duplicado do card Eventos e interações.
2. Remover a entrada `Assistente EVA — Em breve` do catálogo de
   funcionalidades navegáveis (card Suporte, busca, Command Palette,
   favoritos e últimos acessos).

## G0 — Inventário

### Refresh

- `useHomeData` expõe `reload`/`refreshing`; o Hero já atualiza todas
  as seções (eventos, tarefas, solicitações, LMPs).
- O card Eventos tinha um `actions={<EngineeringActionButton
  onClick={reload}/>}` duplicado — mesma operação, mesma flag.

### EVA

- Fonte declarativa: `ENGINEERING_CATALOG` em
  `content/engineeringRouteCatalog.ts`, seção `support`, rota `id:
  "eva"` com `comingSoon: true` (target interno `home`).
- Consumidores derivam tudo do catálogo: `visibleSections`,
  `searchCatalog` (busca local e Command Palette em
  `EngineeringPluginShell`), favoritos filtrados por `knownIds`, e
  `visibleRecents` filtrados por `knownRouteIds` — itens removidos do
  catálogo param de renderizar/executar automaticamente, sem apagar
  storage local.
- Ícone `eva: <Sparkles/>` em `HomePage.tsx`; testes que afirmavam a
  presença do item.
- HelpPage cita "Assistente EVA" apenas em *Limitações atuais* como
  capacidade futura — não como tela/menu; preservado (governança G3).

## Alterações

- `HomePage.tsx`: prop `actions` removida do `EngineeringEventsSection`;
  `Sparkles` e o mapeamento `eva` removidos. Hero/refresh intactos —
  exatamente um botão Atualizar.
- `engineeringRouteCatalog.ts`: rota `eva` removida da seção Suporte
  (comentário registra a decisão: EVA é especialista interoperável,
  não app navegável); `events.refreshLabel` removido (sem consumidor).
- `engineeringRouteCatalog.test.ts`: invariantes invertidas — EVA
  ausente do catálogo, da busca e de `findCatalogRoute`.

## Governança EVA (G3)

EVA permanece especialista inteligente de Engenharia (DÉLIA/ChatGPT
via MCP quando houver contrato). Nenhum endpoint, capability, grant,
rota ou integração MCP criado; nenhuma referência documental
arquitetural removida. Portal Engenharia não apresenta EVA como
aplicativo.

## Validação

- Vitest: **93/93** (11 files) — inclusive novas asserções de ausência
  do EVA.
- `tsc --noEmit`: 0. `eslint .`: 0. `vite build`: OK.
- Bundle: "Assistente EVA" persiste apenas no glossário de limitações
  da Ajuda (legítimo); nenhuma rota/favorito/recent o resolve.
- Grid HOME.R1 (`auto-fit`), LoadingActivityCard, temas e Top Bar:
  nenhum diff.
- QA visual autenticado: `TEST_NOT_RUN` (gate de sessão Core).

## Deploy e smoke

- Push `main` (ff) → `srv-api` `git pull --ff-only` →
  `up-prod-sequential.sh --build engineering` apenas.
- Smoke público: `/apps/engineering` 200; remoteEntry/bundle novo no
  edge verificado.

## Residuais

- `VISUAL_QA`/smoke autenticado (botão único, card Suporte sem EVA):
  `TEST_NOT_RUN` — mesmo gate `PENDING_GRANT_APPROVAL` anterior.

## Arquivos

- `plugins/engineering/src/features/home/HomePage.tsx`
- `plugins/engineering/src/content/engineeringRouteCatalog.ts`
- `plugins/engineering/src/content/engineeringRouteCatalog.test.ts`
