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


