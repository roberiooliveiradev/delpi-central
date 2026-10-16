# 92 — DÉLIA: Conversation Assistant Actions — aparência e funcionalidades (proposta)

**Natureza:** especificação de UX e comportamento proposta pelo Product/Frontend; **não** autoriza implementação, fase, CP, contrato backend ou deploy.  
**Data:** 2026-10-16  
**Owner visual:** plugin-ui (primitives compartilhados); **consumer:** DÉLIA standalone.  
**Estado:** PRODUCT_UX_PROPOSAL / IMPLEMENTATION_NOT_AUTHORIZED / BACKEND_FEEDBACK_CONTRACT=TO_INVENTORY.

## 1. Objetivo

Oferecer ações discretas, contextuais e acessíveis abaixo de cada resposta da DÉLIA. Preservar a composição existente de `DeliaAssistantMessage`, a apresentação v1 literal e o Markdown B2 governado. Nenhuma ação cria autorização, capability, provenance ou efeito de negócio.

## 2. Inventário mínimo confirmado no código (main, 2026-10-16)

- `plugins/delia/src/ui/DeliaAssistantMessage.tsx` **já usa** `MessageActionBar` e `IconButton` de `@delpi/plugin-ui/index`.
- A barra atual já possui **Copiar resposta** com ícones Copy/Check e feedback após resolução do clipboard.
- O texto copiado em Markdown usa `conversationMarkdownToPlainText`; em v1 usa conteúdo literal; em fault usa texto neutro.
- Portanto, **não** criar uma segunda barra `ConversationAssistantActions` por conveniência. Avaliar EXTEND da barra/primitives existentes, sem substituir o contrato atual.

`EXISTING_EQUIVALENT = YES_PARTIAL` (barra e copiar); `REUSE_DECISION = REUSE/EXTEND` para proposta visual; demais ações `TO_INVENTORY` quanto a contrato e owner. Esta decisão não afirma existência de feedback persistente nem regeneração.

## 3. Aparência — direção proposta

- Barra horizontal compacta imediatamente abaixo do conteúdo e de seus detalhes de evidência, alinhada ao início do texto da resposta.
- Ícones Lucide pequenos (alvo de interação acessível, mesmo com glyph reduzido), sem borda permanente nem cartões pesados; cores e tokens herdados do plugin-ui.
- Hover/focus: realce de fundo discreto e tooltip/label acessível; foco por teclado visível; estados pressed/disabled distinguíveis sem depender apenas de cor.
- Não competir com corpo da resposta, EvidenceDetails, GovernedConfirmation ou indicadores de estado.
- Layout responsivo em full-page, Companion Dock e largura móvel: preservar ordem, evitar overflow horizontal e oferecer labels a tecnologias assistivas.
- Sequência conceitual: Copiar | Útil | Não útil | Refazer | Mais opções. **Não** renderizar ícones como ações ativas sem handler/contrato real.

## 4. Funcionalidades e gates

| Ação | Comportamento alvo | Estado/limite |
|---|---|---|
| Copiar | Copiar texto legível da resposta; feedback visual somente após sucesso real; falha tratada sem falso sucesso | **Já implementado parcialmente** em `DeliaAssistantMessage`; preservar e testar |
| Útil / Não útil | Registrar avaliação voluntária por resposta; seleção visual reversível conforme contrato | **PLANNED**; não persistir nem simular envio; ocultar/desabilitar até owner/contrato legítimo |
| Refazer resposta | Solicitar nova geração para turno elegível, preservando contexto e limites governados | **PLANNED**; depende de capability e contrato backend, autorização e idempotência quando aplicável; não chamar reenvio genérico por inferência |
| Mais opções | Menu contextual apenas de ações efetivamente suportadas | **PLANNED**; não exibir menu vazio ou links/ações inventados |

## 5. Contrato frontend proposto

Componente **presentational**, sem fetch, SDK de backend, storage próprio ou decisão de AuthZ. Props explícitas de disponibilidade, loading, selected feedback, texto de acessibilidade e callbacks fornecidos pelo consumidor. Sem handler real = ação indisponível; não sugerir sucesso técnico ou persistência. O nome final do componente depende do inventário do `MessageActionBar` existente; preferir composição/extensão à duplicação.

## 6. Segurança e ownership

- Core/Domain/Policy continuam autoridades de permissões e writes; frontend apenas representa estados recebidos.
- `read != write`; `draft != send`; `recommendation != authorization`; `PREPARE != ACT`.
- Nenhuma telemetria de feedback deve carregar tokens, conteúdo sensível ou payloads de especialistas sem contrato de privacidade.
- O conteúdo do modelo, metadata de MCP ou URLs não determinam quais ações ficam autorizadas.

## 7. Critérios de aceite futuros (não executados)

1. Reutilização demonstrada de `MessageActionBar`/`IconButton`, sem barra paralela.
2. Paridade visual e funcional em página completa e dock, com keyboard/focus/aria e mobile.
3. Cópia de v1 e Markdown B2 sem regressão, inclusive erro de clipboard.
4. Ações não disponíveis permanecem inertes, ocultas ou explicitamente disabled; nenhum feedback fictício.
5. Testes unitários, integração, build, federation e browser QA com evidências no SHA avaliado.
6. Contratos de feedback/regeneração, se necessários, definidos pelos owners antes de ativar.

## 8. Status e próximo passo

`SPEC_STATUS = PROPOSED`  
`EXISTING_EQUIVALENT = YES_PARTIAL`  
`REUSE_DECISION = REUSE_OR_EXTEND_EXISTING`  
`IMPLEMENTATION = NOT_STARTED_BY_THIS_DOCUMENT`  
`TESTS = TEST_NOT_RUN`  
`PHASE_PROGRESSION = NONE`  
`NEXT = COORDINATION_REVIEW_AND_BOUNDED_FRONTEND_BRIEF`

Este documento não altera as authorities 16/17/20/25 nem o ledger; caso haja divergência com a sequência canônica, prevalecem as authorities e a proposta aguarda coordenação.
