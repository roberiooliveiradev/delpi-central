# 92 — DÉLIA: Conversation Assistant Actions — aparência e funcionalidades

**Natureza:** especificação de UX + registro de implementação frontend bounded.
**Task:** `DELIA-UX-CONVERSATION-ASSISTANT-ACTIONS-PLUGIN-UI-IMPLEMENTATION-01`
**Data:** 2026-10-16
**Owner visual:** plugin-ui (composição compartilhada); **consumer:** DÉLIA standalone.
**Estado:** `FRONTEND_IMPLEMENTED` / `BACKEND_FEEDBACK_CONTRACT=ABSENT` / `BACKEND_REGENERATE_CONTRACT=ABSENT` / `PHASE_PROGRESSION=NONE`.

## 1. Objetivo

Oferecer ações discretas, contextuais e acessíveis abaixo de cada resposta da DÉLIA. Preservar a composição existente de `DeliaAssistantMessage`, a apresentação v1 literal e o Markdown B2 governado. Nenhuma ação cria autorização, capability, provenance ou efeito de negócio.

## 2. Reuse efetivo

```text
EXISTING_EQUIVALENT = YES_PARTIAL
REUSE_DECISION = REUSE + EXTEND
```

| Recurso | Decisão |
|---|---|
| `MessageActionBar` | REUSE (chrome/reveal) |
| `IconButton` | EXTEND (`pressed` / `aria-pressed`) |
| `HintAction` | REUSE (tooltips acessíveis) |
| `AnchoredPanelPortal` | REUSE (menu “Mais opções”) |
| Clipboard / Markdown plain text | Host prepara `copyText`; componente só escreve no clipboard |
| `ConversationAssistantActions` | NEW composition no `plugin-ui` |

Não há segunda `MessageActionBar` nem primitives duplicados em `plugins/delia`.

## 3. Composição final

Sequência visual (alinhada à esquerda, abaixo de EvidenceDetails):

`[Copiar] [Útil] [Não útil] [Refazer] [Mais opções?]`

- “Mais opções” só aparece quando `moreActions.length > 0`.
- Feedback/refazer ficam **visíveis e disabled** sem callback/capability (preparados, não falsamente ativos).
- CSS no kit (`message-action-bar.css` + `action-controls.css`); zero CSS de ações na DÉLIA.

## 4. API pública

`ConversationAssistantActions` (`@delpi/plugin-ui/index`):

| Prop | Papel |
|---|---|
| `copyText` | Texto já preparado pelo host |
| `copyEnabled?` | Default: true se `copyText` não vazio |
| `onCopySuccess?` / `onCopyError?` | Observabilidade do host |
| `feedbackValue?` | `"positive" \| "negative" \| null` |
| `feedbackEnabled?` + `onFeedbackChange?` | Interativo só com ambos |
| `regenerateEnabled?` + `onRegenerate?` | Interativo só com ambos |
| `moreActions?` | `{ id, label, onSelect, disabled? }[]` |
| `disabled?` / `loading?` | Congela a faixa |
| `className?` / `labels?` | Chrome e a11y |

**plugin-ui:** apresentação, estados, a11y, clipboard UI, invocação de callbacks.
**DÉLIA:** texto do turno, capabilities, AuthZ, persistência (futuro).

## 5. Funcionalidades

| Ação | Estado |
|---|---|
| Copiar | **ATIVA** — v1 literal / Markdown B2 plain / fault neutro |
| Útil / Não útil | **PREPARADA / DISABLED** até contrato backend + callback |
| Refazer | **PREPARADA / DISABLED** até capability + callback |
| Mais opções | **OCULTA** sem ações contextuais reais |

## 6. Integração DÉLIA

`DeliaAssistantMessage` importa `ConversationAssistantActions` e passa `copyText` já calculado (mesma semântica anterior). Remove JSX local de `MessageActionBar`+`IconButton`+clipboard.

## 7. Evidência de testes (executor)

| Superfície | Resultado |
|---|---|
| plugin-ui `ConversationAssistantActions.test.tsx` | **10 PASS** |
| delia `DeliaAssistantMessage.test.tsx` | **33 PASS** |
| delia suite | ver execução da task |
| plugin-ui build + verify-host-exports | **PASS** (inclui `ConversationAssistantActions`) |
| delia build + federation | **PASS** |
| typecheck | **PASS_WITH_PREEXISTING_DEBT** se dívidas do kit persistirem |
| Browser full-page/dock | **TEST_NOT_RUN** (deploy não autorizado) |

## 8. Restrições e pendências

- Sem backend feedback/regenerate nesta task.
- Sem Core/Domain/AuthZ/ACT.
- Sem promoção de CP/fase.
- Aceite independente e browser QA reais pendentes.

```text
PLUGIN_UI_COMPONENT = IMPLEMENTED
DELIA_IMPORT = IMPLEMENTED
COPY_ACTION = ACTIVE
POSITIVE_FEEDBACK = PREPARED_DISABLED
NEGATIVE_FEEDBACK = PREPARED_DISABLED
REGENERATE_ACTION = PREPARED_DISABLED
MORE_OPTIONS = HIDDEN_UNTIL_ACTIONS
PHASE_PROGRESSION = NONE
```
