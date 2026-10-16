# 102 — DÉLIA | ConversationDraftRecovery — Especificação futura completa

**Data:** 2026-10-16  
**Status:** `PRODUCT_UX_SPEC / IMPLEMENTATION_DEFERRED`  
**Decisão explícita:** documentar a recuperação de rascunho, **sem implementar ainda**. Corrigir separadamente, nesta mesma task, a apresentação do botão `ComposerClearDraftButton` existente.  
**Owners:** `plugins/plugin-ui` (apresentação e interações render-only), `plugins/delia` (estado transitório do draft e regras de transição permitidas). Não é serviço backend, persistência de conversas, memória nem nova capacidade de ação.  
**Referências:** [101 — ComposerClearDraftButton](./101-conversation-composer-clear-draft-ux-implementation.md), [98 — layout DÉLIA](./98-delia-full-page-three-region-layout-product-ux-specification.md), [99 — sidebar](./99-conversation-sidebar-left-product-ux-specification.md), [95 — StopResponse](./95-conversation-stop-response-product-ux-specification.md).  
**Reancoragem para execução futura:** HEAD/git status → Project Instructions/.cursor → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → arquitetura técnica → product spec → specs temáticas → ledger. Este documento não altera decisões de autoridade superior.

## 1. Intenção e limites do produto

O usuário pode limpar por engano um **texto ainda não enviado** no compositor. A funcionalidade `ConversationDraftRecovery` permitirá restaurar **exclusivamente o último rascunho explicitamente limpo**, enquanto a mesma sessão local de UI permanecer ativa. A ação preferida de UX é **Desfazer** apresentada temporariamente depois de limpar, sem botão permanente adicional na toolbar. Essa escolha é uma **direção recomendada/documentada**, não aceite para implementação; confirmar no próximo gate de produto.

`ComposerClearDraftButton` já existente limpa o conteúdo local; recuperação é funcionalidade distinta e **não está implementada**. Preservar `draft != send`, `read != write`, `PREPARE != ACT`. A recuperação não desfaz envio, confirmação, Domain write, API call, atividade, operação governada nem conversa.

## 2. Reuse Gate / Contracts

- `EXISTING_EQUIVALENT=YES`: `MessageComposer`, `ComposerClearDraftButton`, `IconButton`, `DeliaComposer`, `ConversationWorkspace`, feedback/transient status do kit.
- `REUSE_DECISION=EXTEND`: preferir prop/evento e feedback de apresentação já disponíveis em `plugin-ui`; não criar outro compositor, serviço, armazenamento ou controller de sessão.
- `EXISTING_EQUIVALENT=TO_INVENTORY` especificamente para componentes existentes de snackbar/toast com ação de desfazer e timers controlados; **revalidar** antes de nomear novo componente de feedback.
- Estado da recuperação pertence ao **consumer DÉLIA**. `plugin-ui` recebe props `visible`, `message`, `onUndo`, `onDismiss` quando houver contrato tipado revisado, sem acessar `localStorage`, `IndexedDB`, backend, DOM global ou APIs de sessão.
- Nenhum backend é exigido para uma recuperação exclusivamente local e efêmera. Não transformar isso em persistência de histórico.

## 3. Visual e posicionamento — alvo

A interface mantém o compositor existente, incluindo o botão X de limpar e o botão Enviar. Após limpeza voluntária que realmente descartou conteúdo, surge um **feedback compacto e temporário** junto/abaixo do compositor, com texto e ação:

```text
+-----------------------------------------------------+
| Pergunte à DÉLIA...                                 |
|                                                     |
| [toolbar]                                     Enviar |
+-----------------------------------------------------+
       Rascunho limpo                 [Desfazer]
```

- Superfície pequena, light/dark adaptada aos tokens de feedback do `plugin-ui`, borda/raio/contraste discretos; não criar card pesado ou alerta alarmista.
- Ação **Desfazer** é o elemento de maior reconhecimento visual no feedback; hover/focus legíveis. Ícone opcional `Undo2`, sem duplicar label.
- Posicionamento sem cobrir campo de digitação, atalhos, botão Enviar nem conteúdo de conversa; em Dock/mobile ocupar a largura disponível com wrapping previsível.
- Não deslocar toda a timeline/recepção abruptamente, especialmente em resposta em streaming. Animações leves opcionais; `prefers-reduced-motion` elimina movimento.
- Label para screen reader e status curto de modo **não redundante** (reusar região live já aprovada); tab/shift-tab, Enter/Space no Desfazer e Escape se houver semântica de dismissal aprovada.
- Não manter um botão permanente “Restaurar” dentro da toolbar a menos que decisão de produto posterior substitua explicitamente a estratégia de feedback temporário.

## 4. Regras completas de comportamento

### 4.1 Quando cria um candidato de recuperação

1. Usuário aciona explicitamente **Limpar rascunho** com conteúdo não vazio e enquanto `requestMode=idle`, sem estado `loading/disabled`. A limpeza já ocorre hoje.
2. Antes de modificar o valor controlado, o **owner de estado** captura snapshot do texto corrente e sua identidade local/epoch, enquanto está na sessão local atual.
3. O host limpa o draft com a mesma ação, sem enviá-lo.
4. Somente se o valor efetivamente mudou, publica o feedback “Rascunho limpo — Desfazer”.
5. No máximo **um** candidato de recuperação por sessão local; limpeza subsequente substitui/invalida o anterior de maneira determinada.

Não capturar rascunhos automaticamente ao digitar, navegar, recarregar a página ou enviar mensagens. Não guardar o snapshot em logs, analytics de conteúdo, prompt, embeddings, Personal Memory ou Storage API.

### 4.2 Vida útil do Desfazer

- Feedback permanece por intervalo curto e previsível. **Alvo UX inicial:** 8 segundos, sujeito a validação de acessibilidade; duração não congelada e não substitui user controls.
- Pausar countdown enquanto houver hover ou foco dentro do feedback, se o mecanismo compartilhado permitir. Considerar tempo adicional para tecnologias assistivas.
- Após expirar, descartar o snapshot em memória, desmontar feedback e não permitir reexibição a partir de eventos atrasados.
- Encerrar/invalida candidato ao sair/alterar de conversa, unmount/reload, autenticação/contexto revogados, enviar uma mensagem ou iniciar novo fluxo governado.
- **Nenhum dado persiste entre reloads**, abas, dispositivos, usuários ou sessões. Não prometer restauro após queda do navegador.

### 4.3 Restaurar de forma segura

- A ação Desfazer é habilitada somente se o snapshot ainda pertence à mesma instância de conversa, identidade local e epoch **e o composer continua em estado permitido**.
- **Condição crítica:** não sobrescrever texto novo digitado depois da limpeza. Se houver novo texto, o sistema deve preservar o novo conteúdo e **inabilitar/descartar a restauração** (com aviso sucinto, caso necessário) em vez de mesclar silenciosamente.
- Se draft segue vazio e candidato válido, restaura texto **exato**, incluindo linhas, whitespace e caracteres Unicode; não submete mensagem nem aplica normalização.
- Consumir token de restauração de forma atômica e idempotente: clique duplo gera no máximo uma restauração. Depois fechar feedback.
- Devolver foco ao campo de escrita sem rolar a página indevidamente; posição do cursor volta de forma previsível (fim do texto ou offset capturado, se implementado/validado).
- Não alterar mensagens já enviadas, `turns`, `ConversationScrollNavigator`, nem status de operações em andamento.

### 4.4 Concorrência e segurança

- Se algum envio ou requisição começou entre limpar e desfazer: candidato fica inválido; não usar `AbortController` para recuperação de draft.
- Quando `requestMode=responding_cancelable|responding_not_cancelable|stopping`, não oferecer restauração; nunca contornar gates do backend.
- Se a conversa mudou de identidade/escopo (inclusive quando futura persistência existir), snapshot é descartado. IDs frontend não constituem autorização.
- Evitar closures antigas e timers vencidos (request-id/epoch): efeitos atrasados não podem restaurar outra conversa ou draft.
- Quando uma confirmação governada existe, a ação não modifica `PREPARE`, `ACT` nem seus gates; ocultar/invalidar recuperação se comprometer a clareza do fluxo.
- Sem cópia do rascunho em telemetria; observabilidade pode registrar apenas eventos não sensíveis agregados, após contrato.
- Biometria, MCP, provider metadata, contexto cacheado e saída de modelo nunca autorizam recuperação.

## 5. Estados da UI e transições

| Estado | Condição | Efeito |
|---|---|---|
| `idle` | Sem snapshot | Sem feedback |
| `undo_available` | Limpeza explícita validada | Feedback “Rascunho limpo” + ação Desfazer |
| `undo_focused` | Interação hover/focus | Countdown pausado, quando permitido |
| `restoring` | Intenção válida, draft vazio | Restauração atômica |
| `restored` | Valor reposto | Fecha feedback, foco no compositor |
| `expired` | Prazo vencido | Descarta candidato; sem botão |
| `invalidated` | Novo draft, envio, troca de sessão ou revoked context | Descartar snapshot, sem sobrescrever texto |
| `failed` | Inconsistência de estado inesperada | Não restaurar; preservar draft atual; feedback honesto |

Ações visuais de callback/evento devem manter **determinismo**. A apresentação não decide se um dado pode ser restaurado; ela apenas reflete estado entregue pela DÉLIA.

## 6. Critérios de aceite futuros

1. Apenas limpeza explícita e válida gera snapshot; texto é restaurado byte-equivalente sob transformação Unicode/whitespace que não altere conteúdo.
2. Timeout/descarte reais e sem leaks de timer em unmount.
3. Digitação posterior preservada (nenhuma sobrescrita involuntária).
4. Troca de conversa/identidade invalida; duplo clique não restaura duas vezes.
5. Em `loading`, stop ou decisão governada não aparece Desfazer e nenhuma ação viola segurança.
6. Restauração não envia mensagem, não altera status de outcome, evidence ou ações.
7. A11y teclado/leitor de tela/foco, tempo suficiente e reduced motion; visual full-page e Companion Dock em 320/375/420px e zoom 200%.
8. Tema light/dark, selected/hover/pressed, CSS kit e controle de overflow sem layout shift problemático.
9. Build, lint/typecheck/Vitest e Module Federation no SHA efetivo; QA visual autenticado e independent review.
10. Reuse-before-design de toast/snackbar existente, contrato frontend fechado antes da implementação e ledger apenas com evidência factual.

## 7. Escopo explicitamente excluído nesta task

**Não implementar agora:** snapshots, callback de desfazer, timer, snackbar/toast, keyboard shortcut, storage, mudanças no App da DÉLIA ou contratos backend. Apenas a especificação futura é criada. A única mudança de runtime autorizada nesta task é a **correção do CSS de `ComposerClearDraftButton` existente**, registrada no doc 101.

```text
DRAFT_RECOVERY_SPEC = DOCUMENTED_FUTURE_TARGET
DRAFT_RECOVERY_IMPLEMENTATION = NOT_STARTED
DRAFT_RECOVERY_VISUAL_PATTERN = TEMPORARY_UNDO_PREFERRED_PENDING_PRODUCT_GATE
EXISTING_EQUIVALENT = YES_FOR_COMPOSER; TO_INVENTORY_FOR_SNACKBAR
REUSE_DECISION = EXTEND_WHEN_AUTHORIZED
BACKEND_PERSISTENCE = NOT_REQUIRED_FOR_LOCAL_UNDO
DRAFT_CLEAR_VISUAL_FIX = SEPARATE_BOUNDED_IMPLEMENTATION
TESTS = TEST_NOT_RUN
BROWSER_QA = TEST_NOT_RUN
PHASE_PROGRESSION = NONE
```
