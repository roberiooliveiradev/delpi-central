# 94 — DÉLIA | ConversationScrollNavigator — UX, contrato e implementação frontend

**Task:** `DELIA-UX-CONVERSATION-SCROLL-NAVIGATOR-PLUGIN-UI-01`  
**Data:** 2026-10-16  
**Produto:** DÉLIA standalone; `plugin-ui` = owner da apresentação; DÉLIA = consumer/owner da posição do viewport.  
**Natureza:** implementação frontend bounded autorizada pela solicitação do Product Master; **não** autoriza nova fase, backend, ACT, deploy ou persistência.  
**Reanchor:** 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → arquitetura técnica → product spec → conversa/UX → ledger. Em drift prevalece authority superior.

## 1. Direção visual e funcional

O controle flutuante **Ir para o final** é uma pílula discreta, centralizada imediatamente acima do compositor fixo. Fundo de superfície, borda e sombra suaves, ícone Lucide ArrowDown, label legível, foco visível e tamanho de toque de 40px. Usa tokens compartilhados do plugin-ui, tema claro/escuro e container queries para dock/full-page; nunca ocupa o corpo da resposta nem cria uma segunda scrollbar.

**Comportamento esperado:**
- Não aparece na recepção, quando não há turnos, nem durante a leitura do final.
- Quando existem turnos e o usuário sobe mais de 96px acima do final, aparece um controle para voltar à parte mais recente.
- O controle some após retornar ao final, inclusive por rolagem manual.
- Novas respostas só deslocam automaticamente quem já acompanhava o fim; preservar a leitura de mensagens anteriores.
- Ao clicar, navegar no **viewport da conversa**, sem alterar rolagem global do Portal ou criar chamadas de API.
- Sem contador de mensagens não lidas nesta versão (não há contrato de read/unread; evitar alegação falsa).
- Sem animação intrusiva; respeitar reduced motion no scroll do workspace existente.
- Foco por teclado, botão sem submit, `aria-label`, hover/focus/disabled; label personalizável e nunca depende apenas do ícone.

## 2. Reuse gate e arquitetura

**Existente:** `ConversationWorkspace` já hospeda header, viewport rolável, footer e expõe `bodyRef/onBodyScroll`. `plugins/delia/src/App.tsx` já detém `nearBottomRef`, autoscroll e threshold de 96px.

`EXISTING_EQUIVALENT = YES` (mecanismo de scroll/shell).  
`REUSE_DECISION = EXTEND` (slot `scrollNavigator` do workspace + componente chrome compartilhado).

- `plugins/plugin-ui/src/components/conversation/ConversationScrollNavigator.tsx`: render-only; props `visible`, `onGoToLatest`, `disabled`, `label`, `className`; sem conhecimento de scroll container, turnos, backend ou AuthZ.
- `ConversationWorkspace`: slot compartilhado acima do footer, fora do viewport; mantém seu scroll body intacto.
- `plugins/delia/src/App.tsx`: usa ref/threshold existentes para calcular visibilidade e retorna ao final por scroll no próprio viewport; importa `ConversationScrollNavigator` do entrypoint público.
- CSS em `plugins/plugin-ui/src/styles/conversation-workspace.css` e export Federation via `src/index.ts`/verify-host-exports.
- Nenhum primitive, ícone ou controle visual local novo na DÉLIA.

## 3. Gates e estados

`visible=false`: nada no DOM.  
`visible=true`: botão acessível e operável.  
`disabled=true`: sem invocação de callback.  
`no-turns`: a DÉLIA suprime o controle.  
`near-bottom`: a DÉLIA suprime o controle.  
`reading-history`: a DÉLIA não desloca automaticamente o usuário.  
`new-content`: atualizar apenas se a posição/estado justificarem, sem inferir 'não lidas'.

O viewport deve preservar a mesma área de scroll em full-page e Companion Dock. A interface não altera Core, Keycloak, Domain APIs, DÉLIA API, Automation Hub, capabilities, permissões ou armazenamento.

## 4. Evidência e critérios de aceite

Testes incluídos em `ConversationScrollNavigator.test.tsx` cobrem ausência quando oculto, callback explícito, disabled, foco, accessible label; `ConversationWorkspace.test.tsx` cobre composição acima do footer e fora do viewport.

**Ainda requer execução independente no SHA publicado:** testes unitários/regressão; typecheck; builds plugin-ui + DÉLIA; gate de exports; Module Federation; browser QA em página completa e dock (incluindo 320px, zoom 200%, dark mode e reduced motion). Testes que não forem executados continuam `TEST_NOT_RUN`.

**Não escopo:** backend, unread badge, scroll history persistente, carregamento de mensagens antigas, deploy, fase/CP promotion.

```text
OWNER = plugin-ui (visual) / DELIA MFE (viewport policy)
IMPLEMENTATION = CODE_COMMITTED_CANDIDATE
BACKEND_CHANGE = NONE
BUSINESS_ACTION = NONE
PHASE_PROGRESSION = NONE
INDEPENDENT_REVIEW = PENDING
BROWSER_QA = TEST_NOT_RUN
```
