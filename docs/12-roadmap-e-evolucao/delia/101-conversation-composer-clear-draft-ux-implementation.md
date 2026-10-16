# 101 — DÉLIA | ComposerClearDraftButton — Ação local de limpar rascunho

**Data:** 2026-10-16  
**Task:** `DELIA-UX-COMPOSER-CLEAR-DRAFT-V1`  
**Produto:** DÉLIA standalone; componente compartilhado no `plugins/plugin-ui`.  
**Status:** `CODE_COMMITTED_CANDIDATE`; testes, build, QA browser e aceite independentes `TEST_NOT_RUN/PENDING`.  
**Autoridade:** antes de promover aceite ou expandir escopo, reancorar HEAD/git status → instruções e .cursor → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → arquitetura/product spec/contratos → ledger.

## 1. Responsabilidade

Ação secundária pequena de **limpar somente o texto ainda não enviado** da caixa de composição, sem apagar histórico, mensagens, sessão, memória, anexos ou ações preparadas. Executa exclusivamente callback explícito do host; sem fetch, armazenamento, autenticação, autoridade ou operação material.

O componente preserva distinção `draft != send`. Não é a função **Nova conversa**, cuja sessão persistida ainda depende de contratos backend; não é pesquisa conversacional nem execução de ferramentas.

## 2. Reuse Gate e integração

- `EXISTING_EQUIVALENT=YES`: `MessageComposer`, `IconButton`, slot `secondaryActions`, estados controlados de loading/request e `DeliaComposer` já presentes.
- `REUSE_DECISION=EXTEND`: `MessageComposer` ganhou prop opcional `onClearDraft`; o `ComposerClearDraftButton` é apenas composição render-only de `IconButton` + `X` Lucide, não cria novo input ou toolbar.
- `plugins/delia/src/ui/DeliaComposer.tsx` liga `onClearDraft={() => onChange("")}` ao estado transitório controlado pelo App.
- `plugins/plugin-ui/src/index.ts` possui export nomeado protegido contra tree-shake Module Federation; `scripts/verify-host-exports.mjs` exige a exportação.

## 3. Aparência e interação

A ação é um ícone X discreto à esquerda da dica de teclado e da ação **Enviar**, dentro da toolbar existente. Em light/dark o botão é **ghost** sem fundo persistente, com hover tonal, foco acessível e target compacto. `aria-label="Limpar rascunho"`, `type=button` herdado do `IconButton`.

### Condições de visibilidade

O botão aparece **somente** quando:
1. o host fornece `onClearDraft`;
2. há texto no rascunho (`value.length > 0`);
3. composer não está desabilitado e nenhuma requisição está em andamento (`loading` ou `requestMode != idle`).

Acioná-lo chama `onClearDraft` uma vez. Não chama `onSubmit`, não altera a timeline, não limpa mensagens aceitas e não promete desfazer ação remota. A interface fica sem botão após o host atualizar o valor controlado para vazio.

Em compact/mobile o botão mantém label acessível por leitor de tela, sem gerar um novo campo nem afetar o comportamento de Enter/Shift+Enter.

## 4. Critérios de teste e aceite

- Valor vazio: nenhum botão. Rascunho não vazio sem callback: nenhum botão.
- Com callback e conteúdo: ícone visível; clique gera callback e não envio.
- Disabled, loading, responding e stopping: botão não disponível.
- Tema dark/light: conferir transparência em repouso e foco/hover reais.
- Convivência com `ComposerStopButton`, secondaryActions, contador, limite de caracteres e draft controlado.
- QA página completa, Companion Dock, touch/keyboard, TypeScript, Vitest e Module Federation no mesmo SHA do build efetivo.

**Evidência:** arquivos e cenários de teste publicados via GitHub. Não há evidência de execução de Vitest/build/QA autenticado nesta task; nenhuma alteração de fase ou CP é inferida de commit.

```text
FRONTEND = CODE_COMMITTED_CANDIDATE
BACKEND_DEPENDENCY = NONE
WRITE_OR_EXECUTE = NO
TESTS = TEST_NOT_RUN
BUILD = TEST_NOT_RUN
BROWSER_QA = TEST_NOT_RUN
INDEPENDENT_REVIEW = PENDING
PHASE_PROGRESSION = NONE
```


## 5. Refinamento visual R2 — fundo apenas em hover (2026-10-16)

**Solicitação do Product Master:** alinhar o X de Limpar rascunho ao padrão clean aprovado para colapsar sidebar e fechar o card de contexto, com **paridade real entre tema claro e escuro**.

**Causa técnica identificada no HEAD consultado:** `plugins/plugin-ui/src/styles.css` importava `message-composer.css` na linha anterior a `action-controls.css`, cujo seletor escuro `:root[data-theme="dark"] .delpi-ui-icon-btn` injeta fundo e borda permanentes. O CSS local, embora especificasse `background:transparent`, podia perder por ordem de precedência no tema escuro.

**Correção bounded publicada:** carregar `message-composer.css` **após** `action-controls.css`; manter seletores de maior especificidade para `__clear` em light/dark, reforçar fundo transparente em repouso, hover e press tonal discreto, foco com outline sem fundo, e `prefers-reduced-motion`. Não alterar `IconButton` global nem criar outro botão. Sem mudança de comportamento no callback ou valor controlado. A alteração de ordem foi limitada ao CSS de compositor.

**Validação:** verificação de fonte e ordem dos imports por fetch no GitHub; TypeScript/Vitest/Module Federation/QA autenticado permanecem `TEST_NOT_RUN`. Para aceite, comparar hover, focus, press e estado normal em ambos os temas na página/Dock. O documento 102 formaliza o futuro undo e **não** autoriza sua implementação nesta task.
