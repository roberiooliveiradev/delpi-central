# 112 — DÉLIA | NavigationActions — Toggles, Nova conversa, Pesquisar e Opções

**Data:** 2026-10-16  
**Status:** `PRODUCT_UX_SPEC / PLANNED / NOT_IMPLEMENTED`; **documentação somente**.  
**Master:** [103 — DeliaNavigationSidebar](./103-delia-navigation-sidebar-master-product-ux-specification.md).  
**Base verificada:** `main` `e7159c86756ba05f885cf0ccdbfe6fb2faecb54b` antes dos commits desta série. Documentação não é runtime nem autorização de execução.  
**Autoridades para reancoragem antes de código:** HEAD/git status + Project Instructions/.cursor → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → arquitetura → product spec → temática → ledger. `EXECUTION_DRIFT`/`ARCHITECTURE_DECISION_REQUIRED` em conflito.  
**Owner de apresentação:** `plugin-ui`; **consumer/estado:** DÉLIA; Core/Portal/Domain APIs preservam seus boundaries.  

**Referências:** [99 — sidebar](./99-conversation-sidebar-left-product-ux-specification.md), [97 — pesquisa backend](./97-conversation-search-backend-first-future-ux-specification.md), [101 — limpar draft](./101-conversation-composer-clear-draft-ux-implementation.md).

## Subcomponentes de ação e aparência

### Toggle único do painel (`NavigationPanelToggle` — nome de UX)

Controla rail/painel, não fecha a navegação inteira no desktop. Reutiliza `IconButton` + Lucide `PanelLeftOpen/Close` conforme R5: em light/dark, fundo transparente em repouso, hover cinza tonal, focus-visible, área 40×40px e um único elemento visual por estado. Não criar botão duplicado simultâneo no cabeçalho DÉLIA. Quando painel aberto, toggle está no header do painel; quando fechado, no topo do rail.

### Nova conversa (`ConversationNewSession`)

Ação visual `SquarePen`, rótulo “Nova conversa” aberto e somente ícone+tooltip no rail. Depende de sessão conversacional real e decisão sobre draft pendente, interação streaming e PREPARE/ACT; não tratar `setTurns([])` como persistência. Até contrato, mostrar affordance desabilitada e copy honesta, ou omitir, **não** simular criação. Quando autorizada: backend cria sessão, confirmação authoritative, navegação segura, idempotência, postcondition, errors tipados. O botão não equivale ao X de limpar draft.

### Pesquisar conversas (`ConversationSidebarSearch` existente)

No painel, linha de navegação com lupa, não input decorativo sem backend; no rail ícone `Search` acessível. Busca deve ocorrer sobre histórico persistido autorizado ([97](./97-conversation-search-backend-first-future-ux-specification.md)), incluindo mensagens não carregadas na memória React, paginação e recuperação do contexto original. Sem contrato, disabled; não criar busca frontend efêmera.

### Opções (`ConversationNavigationOptions` — nome de UX)

No rodapé visual, uma ação `Settings2` ou ícone semântico equivalente, dedicada a opções da conversa que realmente existam. Não duplicar configurações, perfil ou IAM do Portal. Menu ancorado com teclado/escape/foco e items somente se callback legítimo; sem menu vazio/fictício. No rail ícone+tooltip; painel aberto label “Opções”. Preferências persistentes só após owner/settings contract, não `localStorage` ad hoc.

## Estados comuns

`idle`, `hover`, `focus`, `disabled`, `pending_real`, `error`, `success_authoritative`, `unavailable`. Visual pressed é distinto de selected; confirmação de ação só após resultado real, não apenas HTTP 200. Nunca permitir clique repetido produzir duas sessões/writes. Tooltip disabled não afirma capacidade disponível.

## Eventos e testes sugeridos

`onTogglePanel`, `onNewConversation`, `onOpenSearch`, `onOpenOptions` são callbacks tipados de intenção, não endpoints. Props opcionais: ausência resulta disabled/omissão. Testar retorno de foco, `aria-expanded`, Escape, clique duplo, disabled sem interação, tema claro/escuro, raio/tokens, 320px, overlay e ausência de formulário fake.

**Reuse Gate:** `EXISTING_EQUIVALENT=YES` para `IconButton`, `ConversationSidebarSearch`, `ConversationSidebar`; `REUSE_DECISION=EXTEND`; novas integrações com sessions/search/settings `TO_INVENTORY` e condicionadas.

## Contrato de qualidade transversal

Usar cores/tokens do kit em light/dark, sem tons cinzas permanentes em botões ghost de repouso. Ícones 16–20px, hit target 40–44px, foco 2px, labels reais, keyboard e tooltip acessível; movimento 180–240ms ou nulo em `prefers-reduced-motion`. Validar container 1440/1280/1024/768/420/375/320px, zoom 200% e Companion Dock; sem overflow horizontal, remount de conversa ou perda de draft. Snapshots ou exemplos de UI nunca substituem dados/permission reais. Testes e browser QA permanecem `TEST_NOT_RUN`; independente `PENDING`.



## Rework R1 — ações desambiguadas e widget contracts

- `NavigationPanelToggle`: exatamente um controle por estado, no header de painel aberto ou topo do rail fechado; jamais duplicado no header central em página ampla. Em `launcher_only`, único botão no header da conversa.
- `Nova conversa`: disabled até owner de sessão persistida + guardas de draft/stream/PREPARE/ACT + idempotência + postcondition; nenhum `setTurns([])` como “criação”.
- `Pesquisar`: sem backend de histórico do doc 97, entrypoint disabled; nem input fake, nem busca local.
- `Opções`: menu somente para comandos existentes/legítimos, sem duplicar settings do Portal.
- `Fixar/Renomear/Arquivar/Excluir`: não fazem parte do shell frontend-only; menu apenas depois de contratos de write e autorização live.

`EXISTING_EQUIVALENT=YES` para `IconButton`, `ConversationSidebarSearch` e `ConversationSidebar`; `REUSE_DECISION=EXTEND` dentro da composição única. Interfaces propostas são `onSelectCategory`, `onTogglePanel`, `onNewConversation?`, `onOpenSearch?`, `onOpenOptions?`; **callbacks opcionais nunca autorizam ação por si só**. A matriz owner/classificação está no [103 — Rework R1](./103-delia-navigation-sidebar-master-product-ux-specification.md).

## Implementação bounded 09 — NavigationActions (2026-10-17)

**Autorização:** Product Master solicitou "Ok, implementar" após `PluginNavigation`, seguindo o princípio de um componente por vez. **BASE_HEAD GitHub main:** `bcce6462e379bc3bd73f9f58a3357502ab63a46e`. **Escopo:** extração do componente de apresentação `NavigationActions` e reutilização dos controles atuais, sem implementar backend, nova toolbar, menus ou writes.

**Reuse-before-design:** `EXISTING_EQUIVALENT=YES` para `ConversationThreeRegionLayout` (toggle), `ConversationSidebar` (Nova conversa/Opções), `IconButton`, `ConversationSidebarSearch`. `REUSE_DECISION=EXTEND`: extração de apresentação em `plugins/plugin-ui/src/components/conversation/NavigationActions.tsx`; não foram criados `ConversationNewSession`, outro `NavigationPanelToggle` separado, novo search input ou options menu. Pesquisa continua **exclusivamente** em `ConversationSidebarSearch`, sem implementação duplicada.

**Contrato:** união tipada `action="toggle"` com `expanded:boolean`, `onAction:()=>void`, `label?` e `className?`, ou `action="new"|"options"` com `collapsed?`, `onAction?` e `className?`. Para toggle, reuse do `IconButton`, mesmos ícones `PanelLeftOpen/Close`, mesmas classes, `aria-expanded` e nomes "Expandir/Recolher conversas". Para botões de Nova conversa/Opções, mesmas classes/ícones, labels e mensagens indisponíveis; **sem callback, disabled**. Callback é apenas intenção de UI; nenhum resultado de backend ou autorização é inferido do clique.

**Integração:** `ConversationSidebar` renderiza `NavigationActions action="new"` e `action="options"` exatamente uma vez; shell `ConversationThreeRegionLayout` renderiza `NavigationActions action="toggle"` no slot de cabeçalho existente, mantendo apenas um toggle em qualquer estado. Nenhuma alteração no `DeliaConversationPage` foi necessária, pois o consumidor já usa os dois componentes. Os componentes existentes continuam com domínio/estado próprios; `ConversationWorkspace` não deve remontar durante toggle.

**Arquivos:** novo `NavigationActions.tsx` e `NavigationActions.test.tsx`; alterados `ConversationSidebar.tsx`, `ConversationThreeRegionLayout.tsx`, exports `components/conversation/index.ts` e `src/index.ts`, gate `scripts/verify-host-exports.mjs`. **Sem CSS novo**: reuse integral dos estilos já publicados.

**Testes escritos:** ações sem callback disabled, ícones acessíveis quando collapsed, callbacks de intenção, um toggle por estado, nenhum segundo toolbar/search, preservação do centro. `VITEST=TEST_NOT_RUN`; `TSC=TEST_NOT_RUN`; `FEDERATION_BUILD=TEST_NOT_RUN`; `BROWSER_QA=TEST_NOT_RUN`. Testes criados não significam PASS. `INDEPENDENT_REVIEW=PENDING`. Não há progresso de CP/fase/ledger.

**Autoridades e limitações:** o HEAD e as fontes temáticas 112 e componentes atuais foram conferidos via GitHub. A reancoragem integral .cursor → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → arquitetura/product → ledger, bem como git status local, **não foram comprovados** neste conector: `INCONCLUSIVE`. Nenhuma action backend está autorizada/ativada por este slice; antes de aceitar runtime, revalidar authorities, testes no SHA/config e QA Portal/Dock.
