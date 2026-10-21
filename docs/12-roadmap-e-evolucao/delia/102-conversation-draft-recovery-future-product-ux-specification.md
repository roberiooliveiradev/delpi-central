# 102 — DÉLIA | ConversationDraftRecovery — Especificação futura completa

**Data:** 2026-10-16  
**Status:** `PRODUCT_UX_SPEC / IMPLEMENTATION_AUTHORIZED (task DELIA-UX-CONVERSATION-DRAFT-RECOVERY-FULL-IMPLEMENTATION-01, 2026-10-21)`  
**Decisão explícita:** documentar a recuperação de rascunho. O status `IMPLEMENTATION_DEFERRED` original é **substituído pela autorização de produto** da task `DELIA-UX-CONVERSATION-DRAFT-RECOVERY-FULL-IMPLEMENTATION-01`, restrita ao escopo definido nesta especificação: recuperação local, transitória e em memória do último rascunho explicitamente limpo, com feedback temporário e ação Desfazer. Sem persistência, sem backend, sem recuperação de mensagens enviadas nem restauração após reload. A correção separada de `ComposerClearDraftButton` (doc 101 §5) já está publicada.  
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

> **Atualização (2026-10-21):** o parágrafo acima registra a decisão original da task de documentação. A autorização de produto da task `DELIA-UX-CONVERSATION-DRAFT-RECOVERY-FULL-IMPLEMENTATION-01` substitui o deferimento para o escopo definido nesta spec — ver §8.

## 8. Resultado de implementação (2026-10-21)

**Task:** `DELIA-UX-CONVERSATION-DRAFT-RECOVERY-FULL-IMPLEMENTATION-01` · base `670fc6568742` · implementação em `plugins/delia` + export federado no `plugin-ui`.

**Arquitetura entregue:**

```text
ComposerClearDraftButton (existente)
→ DeliaComposer.onClearDraft(clearedValue)   // seam nova, valor antes de limpar
→ App.handleClearDraft                       // gate: não-vazio + idle + sem loading
→ useDraftRecovery.capture(text)             // snapshot em memória + epoch + timer 8s
→ EditorChromeNotice (plugin-ui, export novo) // "Rascunho limpo — Desfazer", role=status
→ Desfazer → undo(): epoch + canRestore + consume-atômico → onRestore → setInput + foco
```

**Comportamento entregue (verificado em Vitest + browser QA):** snapshot apenas na limpeza explícita; um candidato por vez; expiração de 8 s com pausa em hover/focus; invalidação por texto novo, envio, epoch/request-mode, unmount e reload (memória apenas); restauração exata (whitespace/Unicode/multiline); foco devolvido ao composer; zero `POST /interaction/turns` no ciclo clear→undo; sem persistência, telemetria de conteúdo ou storage.

**Owners preservados:** `plugin-ui` = apresentação (`EditorChromeNotice`, role=status, ação tipada, `:focus-visible` no action); `plugins/delia` = estado transitório, epoch (`requestEpochRef`), invalidação e autorização local do restore. Nenhum componente compartilhado lê estado da DÉLIA.

Evidência completa: [`evidence/draft-recovery/draft-recovery-evidence.md`](evidence/draft-recovery/draft-recovery-evidence.md).

```text
DRAFT_RECOVERY_SPEC = DOCUMENTED_TARGET_AUTHORIZED
DRAFT_RECOVERY_IMPLEMENTATION = IMPLEMENTED_TESTED (frontend, in-memory only)
DRAFT_RECOVERY_VISUAL_PATTERN = TEMPORARY_UNDO_DELIVERED
EXISTING_EQUIVALENT = YES_PARTIAL (composer seam + EditorChromeNotice reuse)
REUSE_DECISION = EXTEND_EXISTING
BACKEND_PERSISTENCE = NOT_REQUIRED_FOR_LOCAL_UNDO
DRAFT_CLEAR_VISUAL_FIX = SEPARATE_BOUNDED_IMPLEMENTATION_DONE
TESTS = PASS (hook 10/10; App integration 5/5; delia 291/291; plugin-ui dir. 335/335)
BROWSER_QA = PASS 33/33 (dock, fullpage, expiry, pause, new-text, replace, overlap, zoom-eq, dark, kbd, starters, VD-F05)
PHASE_PROGRESSION = NONE
```

## 9. Decisao de produto — R1: Desfazer por icone na toolbar do composer (2026-10-21)

**Autorizacao do Product Master para alterar a direcao visual:** apos observar em producao a barra horizontal "Rascunho limpo — Desfazer" abaixo do composer, substituir **essa apresentacao** por **um unico botao temporario de icone `Undo2` (seta de voltar)** na toolbar ja existente do composer, preferencialmente proximo ao microfone e a acao de limpar. O feedback nao deve criar outra linha abaixo do composer, deslocar a timeline ou ocupar largura inteira. A preferencia anterior de `EditorChromeNotice` inline no §3 e o estado `TEMPORARY_UNDO_DELIVERED` da §8 descrevem a entrega anterior e ficam **superados somente no aspecto visual** por esta nova decisao; nao remover seus registros historicos nem alterar a logica aceita.

**Interacao e acessibilidade:** o botao aparece apenas enquanto houver candidato valido apos limpeza explicita de texto; desaparece depois de restaurar, invalidador ou timeout. `aria-label="Desfazer limpeza do rascunho"`; `title` ou `HelpTooltip` acessivel com mesmo significado; target e foco visivel conforme `IconButton` compartilhado. Posicionar ao lado dos controles secundarios da toolbar, evitando conflito com limpar, ditado e enviar. Nada de label visivel permanente, toast separado, badge ou segundo botao. Preservar operacao por teclado (Enter/Space) e reduced motion.

**Comportamento congelado da entrega original:** `useDraftRecovery` continua sendo o owner dos snapshots, epoch, expiracao aproximada de 8s, pausa durante hover/foco, protecao contra sobrescrita de texto novo, request-mode gates, invalidacao ao enviar/trocar contexto e undo atomico. Integrar os callbacks de pausa/retomada pelo elemento interativo ou wrapper existente, sem acoplar o estado ao `plugin-ui`. Quando o botao for desmontado, nenhuma recuperacao continua acessivel. Nao modificar backend, persistencia, AuthZ, MCP, VD-F05 ou as quatro sugestoes.

**Abstraction Gate:** primeiro inspecionar `MessageComposer.secondaryActions`, `ComposerClearDraftButton`, `IconButton`, `HelpTooltip`, `DeliaComposer` e a implementacao atual; `EXISTING_EQUIVALENT=YES`, `REUSE_DECISION=EXTEND_EXISTING` (a confirmar no HEAD), **sem criar componente novo** se o kit suporta a composicao. Evitar migrar para uma notification stack ou criar nova toolbar.

**Aceite R1 (PLANNED):** (1) apos Limpar, surge um unico icone Desfazer dentro da toolbar; (2) sem barra/aviso separado e sem layout shift; (3) clique/teclado restaura texto exato e devolve foco; (4) expiracao 8s com pausa em hover/foco, nova digitacao e transicoes invalidam; (5) full-page e Companion Dock, 320/360/420px, zoom 200%, temas claro/escuro, sem sobreposicao; (6) zero auto-submit e regressao zero em dictation, enviar, limpar, Starter Suggestions; (7) Vitest/typecheck/build/federation/QA e deploy com evidencias no SHA efetivo.

**Task proposta:** `DELIA-UX-DRAFT-RECOVERY-R1-UNDO-ICON-TOOLBAR-01`. Esta secao **autoriza a decisao de produto** e especifica o comportamento, mas nao prova execucao nem deployment. `IMPLEMENTATION=PENDING`; `TESTS=TEST_NOT_RUN`; `DEPLOYMENT=PENDING`; `PHASE_PROGRESSION=NONE`.
