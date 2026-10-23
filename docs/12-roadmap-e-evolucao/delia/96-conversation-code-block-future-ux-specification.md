# 96 — DÉLIA | ConversationCodeBlock — Aparência e funcionalidades futuras

**Data:** 2026-10-16  
**Status:** `PRODUCT_UX_SPEC / IMPLEMENTATION_DEFERRED / MARKDOWN_B2_DEPENDENCY_OPEN`  
**Natureza:** especificação de experiência futura; **não** autoriza implementação, ativação, backend, deploy, CP ou progressão de fase.  
**Owner da apresentação:** `plugins/plugin-ui`; **consumidor:** `plugins/delia` (standalone).  
**Reanchor na execução futura:** HEAD/git status → Project Instructions/.cursor → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → arquitetura técnica → product spec → specs 82/83/84/91 e documentos temáticos pertinentes → ledger. Em conflito, prevalece a autoridade superior e sinalize `EXECUTION_DRIFT`.  
**Base factual de consulta:** `main` observado em `826897b498e3b955f4775cb8b73be785221debe3`. Nunca assumir esse SHA como HEAD de implementação.

> **DECISÃO VIGENTE DO PRODUCT MASTER — 2026-10-22 (substitui o bloqueio histórico por L1 interno):** Markdown B2 textual seguro pode avançar sem capability→URL interna ou sistema de links privados administrado pela DÉLIA. Links públicos HTTPS só se houver fonte admitida e validação de scheme/destino; URLs inventadas pelo modelo, advindas de metadados não confiáveis ou não verificadas são texto inerte. Referências internas são opcionais e apenas quando contratualmente publicadas; Portal navega, Core decide RBAC/rotas e Domain API decide acesso final ao recurso. A DÉLIA não pré-autoriza navegação, não cria RBAC/allowlist privada e não infere rotas por ID. O L1 interno permanece evolução futura independente, não gate do núcleo Markdown B2. **G3 ainda exige brief formal aprovado e os gates de contrato/segurança aplicáveis; CP-333 continua não PASS; runtime não foi alterado.** Histórico de 2026-10-16 mantido como evidência, não como direção vigente nesse ponto. Ver decisão de produto no doc 83 e reconciliação de 2026-10-22.

## 1. Objetivo de produto

Oferecer blocos de código legíveis, copiáveis e acessíveis **dentro de respostas Markdown expressamente admitidas**, preservando texto exato, indentação, linhas em branco, caracteres e semântica do código. O recurso é de **leitura e cópia**, jamais de execução.

Esta especificação é intencionalmente **diferida**. O produto decidiu **não tratar a implementação de code blocks agora**, pois `ConversationMarkdown` ainda não está ativado e validado integralmente de ponta a ponta. O alvo visual documentado não muda essa realidade.

## 2. Estado real e dependências

Segundo o código consultado:
- `plugins/plugin-ui/src/components/markdown/ConversationMarkdown.tsx` já representa tokens `code` via `<pre><code>{token.text}</code></pre>`, sem executar código, HTML, JS ou Mermaid; Markdown permanece `enabled=false` por padrão.
- `plugins/plugin-ui/src/components/markdown/conversationMarkdownModel.ts` usa `marked.lexer`, com limites atuais: 16.384 caracteres, 256 nós, profundidade 8 e 16 links.
- Doc [91](./91-conversation-markdown-frontend-component-implementation.md) registra código frontend `ConversationMarkdown` e integração DÉLIA implementados, mas `RUNTIME_MARKDOWN_ACTIVATION=OFF`, produtor backend `presentation.v2` não implementado, binding L1 não provado, QA browser `TEST_NOT_RUN` e CP-333 não aceito.
- Doc [82](./82-conversation-rich-content-and-structured-presentation-specification.md) prevê texto rico proporcional e code blocks inertes, e distingue isso de tabelas/gráficos tipados futuros.

**Reuse Gate:** `EXISTING_EQUIVALENT=YES` para renderização inerte de bloco de código e para primitives visuais no `plugin-ui`; `REUSE_DECISION=EXTEND` *como direção futura sujeita a gate*, não como implementação autorizada. Para eventual highlighter específico, `EXISTING_EQUIVALENT=TO_INVENTORY` até verificação de dependências/política/bundle. Não importar renderer de documento/HTML arbitrário para a conversa.

## 3. Aparência completa — alvo

```text
  Resposta da DÉLIA...
  [Explicação em prosa, quando pertinente]

  +---------------------------------------------------------+
  | </>  SQL                              [Copiar código ⧉] |
  +---------------------------------------------------------+
  | SELECT produto, SUM(quantidade)                         |
  | FROM producao                                           |
  | GROUP BY produto;                                       |
  +---------------------------------------------------------+

  [Continuação da explicação / evidências da resposta]
```

- **Contêiner:** bloco único, largura da coluna da resposta; borda discreta, radius consistente com `plugin-ui`, fundo sutilmente diferenciado da prosa; não criar um card pesado.
- **Cabeçalho:** strip compacta, com rótulo da linguagem **somente quando houver metadado explícito e validado**. Na ausência, mostrar “Código” ou omitir a linguagem sem classificá-la por heurística baseada no texto.
- **Ação primária:** botão “Copiar código”, ícone Lucide `Copy`, feedback efêmero de sucesso `Check` **somente após confirmação real de clipboard**; estado de erro honesto quando clipboard falha/está indisponível.
- **Código:** fonte monoespaçada, linhas preservadas, seleção nativa, tabulações/indentação legíveis; contraste AA, espaçamento e `line-height` adequados; nenhum word-wrap silencioso que modifique conteúdo lógico. Modo de quebra de linha deve ser consciente e, se oferecido futuramente, apenas apresentação.
- **Linhas longas:** rolagem horizontal **dentro** do contêiner de código, sem alargar mensagem, timeline ou dock e sem ativar rolagem horizontal na página.
- **Tamanho:** adaptar cabeçalho e botões às larguras compactas; o corpo do código continua rolável e selecionável em 320/420px e zoom 200%.
- **Temas:** tokens light/dark do kit, sem esquema paralelo, cores semânticas arbitrárias ou highlighter dependente de estilo externo não avaliado.
- **Interações:** hover/focus-visible discretos; alvo de toque confortável; texto de botão disponível ao leitor de tela mesmo quando colapsado visualmente.
- **Espaçamento:** separação proporcional da prosa que o antecede/sucede; não deslocar `EvidenceDetails`, `ConversationStatus`, `ActivityViewer` ou `ConversationAssistantActions`.
- **Reduced motion:** sem animações obrigatórias. Feedback de cópia não pode causar layout shift.

## 4. Funcionalidades esperadas

### 4.1 Reconhecimento e renderização

1. Reconhecer apenas **token de bloco de código do Markdown B2 explicitamente admitido** (`presentation.v2` + formato `markdown_safe`); jamais reinterpretar prosa literal `presentation.v1` como Markdown.
2. Preservar o corpo do código como **texto inerte**. Não executar código, compilar, interpretar, conectar a SQL, disparar requests, chamar shell, abrir terminal ou habilitar “Executar”.
3. Linguagem opcional e fornecida por token validado; permitir um conjunto bounded de labels conhecidos (ex.: SQL, Python, JSON, TypeScript, Bash, YAML) sem inferir linguagem pela sintaxe. Valores desconhecidos = label genérico neutro, sem executar loaders.
4. Vários blocos em uma mesma resposta têm identidade e clipboard independentes; sem contador/sistema de tabs inventado.
5. Inline code (`codespan`) continua apresentação leve dentro da prosa, **sem cabeçalho e sem botão de cópia por trecho**.
6. Linguagem declarada não comprova que o exemplo é executável, correto ou autorizado operacionalmente.

### 4.2 Copiar

- Cópia isolada do conteúdo do bloco, sem delimitadores de Markdown (```), sem cabeçalho de linguagem, sem decoração de UI.
- Preservar caracteres, recuos, aspas, CR/LF conforme projeção determinística definida; não remover linhas ou ajustar silenciosamente código.
- Sucesso visível somente após `navigator.clipboard.writeText` realmente resolver; falha não exibe confirmação falsa.
- Cópia do bloco não altera a ação geral “Copiar resposta” da barra de ações; ambas coexistem e têm finalidades distintas.
- Desabilitar controles durante operação de cópia quando necessário para evitar concorrência visual, sem bloquear a leitura do código.

### 4.3 Destaque de sintaxe

- **Alvo opcional, não pré-requisito do primeiro slice**. Só considerar quando mecanismo adequado já existente no `plugin-ui` passar por reuse/security/bundle/accessibility review.
- O highlighter não pode executar código, introduzir HTML arbitrário, baixar linguagens remotas, alterar o texto copiado, bloquear renderização ou ignorar limites.
- Em falha: fallback para código monoespaçado sem highlight; nunca degradar para HTML não sanitizado.

### 4.4 Casos limites e ausência de metadados

- Linguagem ausente/desconhecida, código vazio, conteúdo com caracteres especiais, JSON com tags, blocos muito longos, várias fences ou Markdown malformado devem renderizar de forma segura.
- Os limites de tokenização e de payload seguem o contrato B2 aprovado, não regras inventadas pelo componente.
- Código em resultado de fonte/modelo **não se torna FACT ou instrução executável** por estar formatado visualmente.
- Não permitir links automáticos, iframes, imagens, Mermaid ou `dangerouslySetInnerHTML` dentro do bloco.

## 5. Ownership e arquitetura futura

- **`plugin-ui`:** componente/composição visual compartilhada (nome de produto `ConversationCodeBlock`), tokens, CSS, ações acessíveis de cópia, estados e testes. Preferir **estender o renderer `ConversationMarkdown` existente** e primitives do kit; evitar parser/renderer paralelos.
- **`plugins/delia`:** importar `ConversationMarkdown` e componentes publicados pelo entrypoint `@delpi/plugin-ui/index`; fornecer somente formato autorizado e conteúdo admitido por contrato. Não criar primitivas de code block locais.
- **Backend DÉLIA:** produtor contratual de apresentação; não autorizado por esta spec a emitir `presentation.v2` novo ou modificar schema.
- **Core/Domain:** autoridade de permissões/dados permanece intacta. Code block é superfície de leitura/cópia, não execução governada.

**Abstraction Gate futuro:** demonstrar necessidade real, equivalentes e consumidores; `REUSE` ou `EXTEND` preferidos; novo componente apenas como composição bounded, nunca serviço/capability/engine novo.

## 6. Estados de interação e acessibilidade

| Estado | Renderização/resultado |
|---|---|
| Código válido sem linguagem | Bloco inerte, label neutro ou ausente, cópia quando suportada |
| Código válido com linguagem | Bloco inerte, rótulo de linguagem validado, cópia |
| Copiando | Botão temporariamente indisponível, sem sucesso antecipado |
| Copiado | Feedback confirmado acessível, sem alarme e sem alterar código |
| Falha de clipboard | Feedback não enganoso, código permanece selecionável |
| Sem suporte a Clipboard API | Controle desabilitado/feedback apropriado, seleção manual mantida |
| Markdown não ativado ou inválido | Preservar fallback contratual do `ConversationMarkdown`; sem CodeBlock rich |
| Texto extenso | Overflow próprio horizontal, layout full-page/dock preservado |

Teclado: botão com `type=button`, foco visível, Enter/Space; código deve ser selecionável/copiável por keyboard/screen reader; não capturar atalhos do composer nem dificultar rolagem vertical. Preferir mensagem de estado acessível controlada e não duplicar regiões `aria-live`.

## 7. Critérios futuros de aceite (não executados)

1. Reuse Gate comprovado no HEAD e nenhuma primitive nova dentro da DÉLIA.
2. Código Markdown v1 literal nunca convertido em code block rich; ativação condicionada ao B2 admitido.
3. Fences e inline codes distintos; corpo inerte sem execução, links ou HTML.
4. Código copiado fielmente e separadamente da resposta completa, incluindo whitespace sensível.
5. Erro e indisponibilidade do clipboard sem falso sucesso.
6. Múltiplos blocos, linguagens conhecidas/desconhecidas, cargas adversariais e limites bounded.
7. Segurança/XSS, keyboard, ARIA, tema, responsividade e `prefers-reduced-motion`.
8. Build `plugin-ui` e DÉLIA, verificação dos exports e de Module Federation, QA full-page/dock.
9. Regressões do `ConversationMarkdown` e `ConversationAssistantActions`.
10. Testes, configuração/HEAD, gates G1-G4 e aceite independente documentados antes de qualquer promoção de estado.

## 8. Decisão explícita de postergação

**Não implementar nesta tarefa:** código TSX/CSS, componente, testes de runtime, exports, highlighter, backend, deploy ou integração; esta solicitação é **somente documental**. Não alterar 16/20/25 ou ledger para sugerir avanço de fase.

Antes de implementar, revalidar `presentation.v2` producer, gate do Markdown B2, contratos e aceites realmente existentes e a compatibilidade com `ConversationMarkdown`. Esta especificação **não supre dependências faltantes** nem autoriza que sejam ignoradas.

```text
SPEC_STATUS = DOCUMENTED_FUTURE_TARGET
FRONTEND_MARKDOWN_COMPONENT = IMPLEMENTED_BUT_RUNTIME_OFF (doc 91)
MARKDOWN_GATES = PENDING_INDEPENDENT_VALIDATION
CONVERSATION_CODE_BLOCK = NOT_IMPLEMENTED
EXISTING_EQUIVALENT = YES (INERT_CODE_PRESENTATION)
REUSE_DECISION = EXTEND_WHEN_AUTHORIZED
SYNTAX_HIGHLIGHTER = TO_INVENTORY
TESTS = TEST_NOT_RUN
DEPLOY = NOT_AUTHORIZED
PHASE_PROGRESSION = NONE
NEXT = DEFERRED_UNTIL_MARKDOWN_B2_CONTRACT_AND_COORDINATION_GATE
```

## 9. Fechamento da especificação — revisão de implementação (2026-10-22, F02-B)

`TASK_ID=DELIA-UX-F02B-CODE-BLOCK-VISUAL-SPEC-AND-MARKDOWN-B2-GATE-01`. Escopo: documental — nenhum runtime alterado. HEAD auditado: `4a6d85286c6670c1e2c7e54d5b3b2e86a5a7bed6`.

### 9.1 Inventário de reuso verificado no HEAD

| Responsabilidade | Equivalente real no HEAD | EXISTING_EQUIVALENT | REUSE_DECISION |
|---|---|---|---|
| Renderização de código (conversa) | `ConversationMarkdown` token `code` → `<pre><code>{token.text}</code>` inerte (`ConversationMarkdown.tsx:132`); `codespan` → `<code>` inline (`:55`) | YES | EXTEND |
| Tokenização/parse seguro | `conversationMarkdownModel.ts` — `marked.lexer` parse-only, bounds `16_384` chars / `256` nodes / depth `8` / `16` links; `token.lang` do marked ainda **não é tipado** em `MarkdownToken` (extensão aditiva mínima necessária) | YES | EXTEND |
| Prior art visual code block | `MarkdownCodeBlock` interno de `MarkdownDocument.tsx` — strip `FileCode2`+lang, botão `Copy`→`Check` pós-resolve, `<pre><code>`; CSS `delpi-ui-md-doc__code*` (`markdown-document.css:120-186`) | YES (document-grade, não exportado, sem feedback de erro, sem tooltip) | EXTEND pattern |
| Botão copiar | Padrão honesto em `ConversationAssistantActions.tsx:110-126` — sucesso só após `writeText` resolver, `onCopyError` em falha/indisponível | YES | REUSE pattern |
| Tooltip | `HelpTooltip`/`HintAction` (`components/help/`) | YES | REUSE |
| Feedback de cópia | `copied` + reset 1500–1600ms (ConversationAssistantActions / MarkdownCodeBlock); erro ainda silencioso no prior art — spec exige estado de erro explícito | YES_PARTIAL | EXTEND |
| Renderização Markdown | `ConversationMarkdown` (conversation-grade, `enabled=false` default, `authorizedLinks` allowlist) | YES | REUSE |
| Segurança/sanitização | Parse-only sem HTML string, zero `dangerouslySetInnerHTML`, tokens desconhecidos → raw text, links só via allowlist | YES | REUSE |
| Syntax highlighting | **Ausente** — sem prism/highlight.js/shiki em `plugins/plugin-ui/package.json` ou `plugins/delia/package.json` | NO | NÃO_ADICIONAR (v1 sem highlight) |

### 9.2 Estado factual de Markdown B2

| Item | Estado | Evidência |
|---|---|---|
| Contrato `presentation.v2` (`text/format=markdown_safe` + `authorized_links`) | CONTRACT_APPROVED | `plugins/delia/src/api/presentation.ts:177` (`V2_FORMATS`), `:315-327` |
| Adaptador frontend (extract `markdownSource`, `contentFormat`, `authorizedLinks`) | IMPLEMENTED + TESTED | `interactionClient.ts:409-462`, `presentation.test.ts` |
| Renderer `ConversationMarkdown` | IMPLEMENTED + TESTED | `ConversationMarkdown.tsx` + 244-linhas de teste |
| Integração `DeliaAssistantMessage` | IMPLEMENTED | `markdownEnabled = presentationFault===null && contentFormat==="markdown_safe" && markdownSource` (`DeliaAssistantMessage.tsx:128-133`) |
| Emissor backend `markdown_safe` | **NOT_IMPLEMENTED** | zero ocorrências de `markdown_safe`/`markdown_source`/`authorized_links` em `delia-api/app` |
| Ativação runtime | **OFF** | doc 91: `RUNTIME_MARKDOWN_ACTIVATION = OFF (sem emitter v2 real)` |
| Browser QA B2 | TEST_NOT_RUN | doc 91 |
| CP-333 | NOT_ACCEPTED | doc 91 §status |

**Blockers efetivos para code blocks em mensagens reais:** (1) emissor `presentation.v2`/`markdown_safe` inexistente no `delia-api`; (2) `authorized_links` nunca produzido; (3) QA browser B2 e aceite independente CP-333 pendentes. Import/export **não** é evidência de ativação — `markdownEnabled` é derivado de dados admitidos, nunca da forma do texto.

### 9.3 Anatomia e dimensões (fechadas)

```text
┌──────────────────────────────────────────────────────┐
│ </> SQL                              [⧉ Copiar código]│  bar 30px
├──────────────────────────────────────────────────────┤
│ SELECT produto, SUM(quantidade)                       │
│ FROM producao;                                        │  pre 12/14px
└──────────────────────────────────────────────────────┘
```

| Elemento | Valor candidato (tokens) |
|---|---|
| Contêiner | `border: 1px solid var(--delpi-ui-border)`, `radius 10px`, `overflow:hidden`, fundo `color-mix(text 4%)`, `margin: 0.45em 0` (alinhado ao ritmo `conversation-markdown.css`), `max-width:100%` |
| Barra de cabeçalho | altura ~30px, `padding: 5px 10px`, `border-bottom: 1px`, fundo `color-mix(text 3%)`, justify-content space-between |
| Label linguagem | `FileCode2` 13px + texto mono 11px/600/lowercase/letter-spacing 0.02em; uppercase visual para label, valor bruto preservado internamente |
| Botão copiar | ícone 13px + label 11px/600, área de clique ≥28px (`min-height`/`padding`), `type=button` |
| Corpo `pre` | `padding: 12px 14px`, `font-size: 0.86em`, `line-height: 1.55`, `tab-size: 2`, `overflow-x: auto`, `white-space: pre` (não `break-spaces` — §9.4) |
| Altura máxima | `max-height: 320px` desktop / `240px` ≤480px e Dock, com `overflow-y: auto` no `pre` |
| Ícones | `FileCode2` (linguagem), `Copy`, `Check`, `AlertCircle`/`ClipboardX` (erro) — Lucide, 13px |

Diferença deliberada do prior art `md-doc`: margem menor (`0.45em`, ritmo da conversa), `white-space: pre` com scroll horizontal honesto (não `break-spaces`), feedback de erro visível, tooltip, e namespace `delpi-ui-conversation-code-block` (não reutilizar `delpi-ui-md-doc__*` — contexto distinto, mas mesmas medidas/tokens).

### 9.4 Cópia

- `navigator.clipboard.writeText(code)` somente sobre `token.text` (nunca `token.raw` — exclui fences e info-string).
- Sucesso `Check`+`Copiado` **somente após resolve**; reset 1600ms; sem anúncio antecipado.
- Falha/indisponível → estado de erro visível (ícone + `Não foi possível copiar`), `aria-live="polite"` pontual no botão; seleção manual permanece. Fallback `execCommand` **não** reutilizado (padrão do prior art legado, deprecated).
- Múltiplos blocos: estado de cópia local por bloco.
- Whitespace preservado byte-a-byte; scroll horizontal em vez de wrap para não quebrar linhas lógicas na visualização. Word-wrap, se oferecido no futuro, é toggle de apresentação e nunca altera o texto copiado.

### 9.5 Linguagens

`token.lang` vem do info-string da fence via `marked.lexer` (prova: `markdownDocumentModel.ts:157-161` extrai `code.lang`). Regras: allowlist de display `{sql, python, json, typescript, javascript, bash, yaml, text}` → label mapeado (SQL, Python, JSON, TypeScript, JavaScript, Bash, YAML, Texto); lang válida fora da lista → label com o valor sanitizado (≤20 chars, `[a-z0-9+#.-]`, fallback `Código`); ausente/desconhecida → `Código`; nunca inferir por conteúdo ou LLM. Bloco vazio → corpo `pre` vazio, cópia permanece disponível (string vazia copiável). Markdown/HTML literal dentro do código permanece texto inerte.

### 9.6 Syntax highlighting

**v1 sem highlight.** Nenhum mecanismo reutilizável aprovado existe no HEAD. Não adicionar dependência (prism/hljs/shiki) para efeito visual. Se futuro, gate separada: bundle size, tokenização local, zero execução, fallback para `pre` simples.

### 9.7 Responsividade

Full-page, Dock e mobile 320/360/375/420px: largura = coluna da mensagem, `max-width:100%`, scroll horizontal **interno ao `pre`** — nunca overflow na conversa/página (critério mensurável: `scrollWidth` do contêiner da mensagem == `clientWidth` com linha de 300 chars). Zoom 200% mantém barra e corpo operáveis. Temas via tokens (zero cor arbitrária). `prefers-reduced-motion`: feedback de cópia sem animação/transição. ≤480px: label do botão copiar pode colapsar para ícone mantendo `aria-label` (padrão `ComposerEnqueueButton`).

### 9.8 Acessibilidade

- `role="group"`/`aria-label="Bloco de código"` (ou `aria-label="Bloco de código {lang}"`) no contêiner.
- Botão `type=button`, `aria-label="Copiar código"`, foco visível `outline 2px`, Enter/Space nativos.
- Corpo selecionável e navegável; `pre` com `tabindex="0"` e `role="region"` + `aria-label` quando rolável (scroll keyboard).
- Erro de clipboard via `aria-live="polite"` no status do botão, sem região duplicada.
- Contraste AA dos tokens; inline `codespan` permanece `<code>` sem cabeçalho/cópia — distinção fenced vs inline garantida.
- Zero captura de atalhos globais do composer.

### 9.9 Contrato de apresentação

```ts
type ConversationCodeBlockProps = {
  code: string;              // token.text — corpo exato
  language?: string;         // token.lang admitido; label via allowlist
  copyEnabled?: boolean;     // default true; host pode desligar
  className?: string;
  labels?: Partial<ConversationCodeBlockLabels>; // PT defaults no componente
};
```

Wiring: `ConversationMarkdown` case `"code"` delega para `ConversationCodeBlock` (mesmo renderer, mesmo gate `enabled`) — **não** criar parser/renderer paralelo nem expor o componente fora do fluxo admitido. `MarkdownToken` ganha `lang?: string` (extensão aditiva tipada). Sem dependência de backend/MCP/AuthZ/persistência/execução.

### 9.10 Segurança

Herda os bounds do lexer (16_384/256/8/16). Todo conteúdo é texto inerte renderizado como filho React (nunca `dangerouslySetInnerHTML`); linguagem usada só como label sanitizado (nunca `className` dinâmico de highlighter); fences malformadas degradam para parágrafo de raw (comportamento atual); Unicode/controle exibido literalmente; conteúdo nunca executa, linka ou vira FACT/instrução por formatação; cópia preserva whitespace exato sem sanitização silenciosa.

### 9.11 Matriz de aceite (métodos de verificação previstos)

| ID | Critério | Método |
|---|---|---|
| CB-V01 | Anatomia compacta (bar 30px, sem card-dentro-de-card) | screenshot/DOM probe + medidas CSS |
| CB-V02 | `code` literal preservado (whitespace, tabs, CR/LF) | unit test com payload adversarial |
| CB-V03 | Copiar → feedback só pós-resolve | unit test com `writeText` mock resolve/reject |
| CB-V04 | Clipboard indisponível/falha → erro honesto, seleção mantida | unit test sem `navigator.clipboard` |
| CB-V05 | Lang conhecida/desconhecida/ausente → labels corretos | unit test por matriz |
| CB-V06 | Múltiplos blocos independentes | integração: 2+ blocos, cópias isoladas |
| CB-V07 | Linha longa → scroll interno, zero overflow da conversa | DOM probe `scrollWidth==clientWidth` + browser 320px |
| CB-V08 | fenced vs inline codespan distintos | unit + visual |
| CB-V09 | HTML/script/Unicode no código = texto inerte | unit adversarial + inspection DOM |
| CB-V10 | full-page/Dock/mobile 320-420 | Playwright real |
| CB-V11 | zoom 200%, temas, reduced motion | Playwright + CSS contract test |
| CB-V12 | teclado (foco, Enter/Space, scroll) + SR name/live | a11y test + probe teclado |
| CB-V13 | nenhum execution path (sem eval/HTML/links dentro) | residual search + unit |
| CB-V14 | `enabled=false` → nenhum bloco rico; gates B2 intactos | unit + integração DeliaAssistantMessage |
| CB-V15 | regressão `ConversationMarkdown`/`ConversationAssistantActions`/document renderer | suites completas plugin-ui+delia |

### 9.12 Delimitação e decisão

```text
CODE_BLOCK_VISUAL_SPEC=READY
EXISTING_EQUIVALENT=YES (renderer+tokens+clipboard pattern+visual prior art)
REUSE_DECISION=EXTEND (ConversationMarkdown case "code" → ConversationCodeBlock; lang?: string aditivo)
MARKDOWN_B2=GATED (adapter+renderer implementados/testados; emissor v2 markdown_safe INEXISTENTE; QA+CP-333 pendentes)
STANDALONE_RENDER_COMPONENT=AUTHORIZED_CANDIDATE (componente compartilhado isolado pode ser implementado sob gate próprio, sem ativação)
DELIA_RUNTIME_ACTIVATION=BLOCKED (aguarda emissor v2 + CP-333 + QA B2)
SYNTAX_HIGHLIGHTER=OUT_OF_SCOPE_V1
NEXT_BOUNDED_IMPLEMENTATION=componente+unit tests no plugin-ui atrás do mesmo enabled-gate; NENHUM caminho de produção até emissor v2 existir
PHASE_PROGRESSION=NONE
```

Menor próximo slice: `ConversationCodeBlock` + extensão `lang?: string` em `MarkdownToken` + delegação no case `code` do `ConversationMarkdown` + CSS `delpi-ui-conversation-code-block` + suite unit/integration — tudo inerte atrás de `enabled`, sem ativação e sem emissor backend.


## 10. Implementação F02-C — estado factual (2026-10-22)

Componente implementado e verificado conforme §9. Arquivos: `ConversationCodeBlock.tsx` + `.test.tsx` (`components/conversation/`), `conversation-code-block.css` (`styles/`), `MarkdownToken.lang?: string` aditivo, delegação `case "code"` no `ConversationMarkdown`, export público + `REQUIRED_HOST_EXPORTS`, fixture `markdown_code` em `demoMode.ts` (QA-gated).

```text
COMPONENT=ConversationCodeBlock (plugins/plugin-ui, export público via index)
CONTRACT={code, language?, copyEnabled?, className?, labels?} — render-only, inerte
MARKDOWN_TOKEN_LANG=ADDITIVE (lang?: string)
MARKDOWN_DELEGATION=YES (case "code" → ConversationCodeBlock)
COPY=navigator.clipboard.writeText(code) — sucesso pós-resolve, erro visível+aria-live, sem execCommand
VITEST=plugin-ui 2315/2315, delia 322/322
TYPECHECK=PASS (ambos)
BUILD+FEDERATION=PASS (verify-host-exports OK)
BROWSER_QA=46/46 (fixture ?delia-demo=markdown_code, dev server; ver evidência §3)
CB_V01_V15=ALL PASS (métodos §9.11 executados — evidência code-block-f02c)
MARKDOWN_B2_RUNTIME=OFF (emissor v2 continua inexistente — gate preservado)
CP_333=NOT_ACCEPTED
BACKEND_CHANGED=NO
SYNTAX_HIGHLIGHTER=NONE (spec §9.6 mantida)
EVIDENCE=docs/12-roadmap-e-evolucao/delia/evidence/code-block-f02c/
```

O componente está pronto para apresentar código assim que um emissor `presentation.v2` legítimo ativar Markdown B2 — task independente (produtor + contrato + QA + CP-333).


## 11. Aceite do componente e homologação de frontend (Product Owner, 2026-10-23)

**Decisão:** `ConversationCodeBlock` (F02-C) e a experiência frontend Markdown B2 testada em full-page/Companion Dock estão **ACEITOS PELO PRODUCT OWNER** no escopo visual e funcional avaliado. A homologação `DELIA-UX-MARKDOWN-B2-DOCK-AND-ACCESSIBILITY-QA-01` encerrou sem defeitos de frontend e sem mudanças runtime; evidência em [`markdown-b2-dock-accessibility-qa-01`](./evidence/markdown-b2-dock-accessibility-qa-01/markdown-b2-dock-accessibility-qa-01-evidence.md), commit `ea8633dd348d50c6bd4c515d1f7f8ccbb410d5e1`.

**Atualização temporal:** o registro histórico do §10 (`MARKDOWN_B2_RUNTIME=OFF`, emissor inexistente) descrevia o estado da F02-C; foi superado pelas mudanças posteriores de backend relatadas no handoff de coordenação (emissor `presentation.v2` e admissão conversacional, commit `8162baf1a7`) e pelo QA produtivo de 2026-10-23. Não reverter o runtime por interpretação do estado histórico.

**Aceite não implica:** `CP-333=PASS`, conclusão de fase ou ausência de residuais. `SCREEN_READER_QA=TEST_NOT_RUN`; headings reais não observados nesta rodada (cobertos por testes); envelope NDJSON full-page não capturado pelo harness (v2 observado no Dock real); emissão positiva de links autorizados não exercitada nesta rodada. A coordenação permanece owner do aceite CP-333. Não reabrir o componente aceito sem defeito reproduzido.

```text
F02C_COMPONENT=PRODUCT_OWNER_ACCEPTED
MARKDOWN_B2_FRONTEND_UX=PRODUCT_OWNER_ACCEPTED_IN_TESTED_SCOPE
DOCK_AND_FULLPAGE=PASS_REPORTED
SCREEN_READER_QA=TEST_NOT_RUN
CP_333=AWAIT_COORDINATION_DECISION
PHASE_PROGRESSION=NONE
RUNTIME_CHANGED_BY_THIS_ACCEPTANCE=NO
NEXT=OTHER_BOUNDED_FRONTEND_EVOLUTIONS
```
