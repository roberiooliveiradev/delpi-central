# 96 — DÉLIA | ConversationCodeBlock — Aparência e funcionalidades futuras

**Data:** 2026-10-16  
**Status:** `PRODUCT_UX_SPEC / IMPLEMENTATION_DEFERRED / MARKDOWN_B2_DEPENDENCY_OPEN`  
**Natureza:** especificação de experiência futura; **não** autoriza implementação, ativação, backend, deploy, CP ou progressão de fase.  
**Owner da apresentação:** `plugins/plugin-ui`; **consumidor:** `plugins/delia` (standalone).  
**Reanchor na execução futura:** HEAD/git status → Project Instructions/.cursor → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → arquitetura técnica → product spec → specs 82/83/84/91 e documentos temáticos pertinentes → ledger. Em conflito, prevalece a autoridade superior e sinalize `EXECUTION_DRIFT`.  
**Base factual de consulta:** `main` observado em `826897b498e3b955f4775cb8b73be785221debe3`. Nunca assumir esse SHA como HEAD de implementação.

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
