# DÉLIA — F02-B Evidence: ConversationCodeBlock spec review + Markdown B2 gate audit

`TASK_ID=DELIA-UX-F02B-CODE-BLOCK-VISUAL-SPEC-AND-MARKDOWN-B2-GATE-01`
HEAD auditado: `4a6d85286c6670c1e2c7e54d5b3b2e86a5a7bed6`
Escopo: **documental** — nenhum runtime alterado, nenhum teste executado.

## 1. Inventário de reuso (verificado no HEAD)

| Responsabilidade | Equivalente real | Veredito |
|---|---|---|
| Renderização de código (conversa) | `ConversationMarkdown.tsx:132` — token `code` → `<pre><code>{token.text}</code>` inerte; `:55` — `codespan` → `<code>` | YES / EXTEND |
| Parse seguro | `conversationMarkdownModel.ts` — `marked.lexer` parse-only; bounds 16_384 chars / 256 nodes / depth 8 / 16 links; `MarkdownToken` **não declara `lang`** (extensão aditiva necessária — marked emite `token.lang` em fenced code) | YES / EXTEND |
| Prior art visual | `MarkdownCodeBlock` (interno, `MarkdownDocument.tsx`) — bar `FileCode2`+lang, `Copy`→`Check` pós-resolve 1600ms; CSS `delpi-ui-md-doc__code*` (`markdown-document.css:120-186`). Limites: não exportado, erro de clipboard silencioso, fallback `execCommand` deprecated, sem tooltip | YES (document-grade) / EXTEND pattern |
| Clipboard honesto | `ConversationAssistantActions.tsx:110-126` — sucesso só após `writeText` resolver, `onCopyError` em falha/indisponível | YES / REUSE pattern |
| Tooltip/ícones | `HelpTooltip`, `HintAction` (`components/help/`); `IconButton`, `ActionButton` (`components/actions/`); `FileCode2`/`Copy`/`Check`/`AlertCircle` Lucide | YES / REUSE |
| Renderer Markdown | `ConversationMarkdown` (`enabled=false` default, `authorizedLinks` allowlist, CSS `conversation-markdown.css`) | YES / REUSE |
| Sanitização | Parse-only, zero `dangerouslySetInnerHTML`, tokens desconhecidos → raw, links só via allowlist + forbidden-query keys | YES / REUSE |
| Syntax highlighting | **AUSENTE** — sem prism/highlight.js/shiki nos package.json de plugin-ui/delia | NO / OUT_OF_SCOPE_V1 |

## 2. Estado factual de Markdown B2

```text
presentation.v2 adapter   = IMPLEMENTED + TESTED   (presentation.ts:177 V2_FORMATS; :315-327 extract; presentation.test.ts)
conversation renderer     = IMPLEMENTED + TESTED   (ConversationMarkdown.tsx + test 244 linhas)
DeliaAssistantMessage     = IMPLEMENTED            (markdownEnabled = presentationFault===null && contentFormat==="markdown_safe" && markdownSource; :128-133)
backend markdown_safe     = NOT_IMPLEMENTED        (zero ocorrências em delia-api/app — grep markdown_safe|markdown_source|authorized_links)
runtime activation        = OFF                    (doc 91: "sem emitter v2 real")
browser QA B2             = TEST_NOT_RUN           (doc 91)
CP-333                    = NOT_ACCEPTED           (doc 91)
```

**Conclusão:** import/export/wiring **não** ativam nada — `markdownEnabled` deriva de dados admitidos pelo wire; sem emissor v2 real, blocos de código ricos nunca aparecem em produção. Blockers: (1) emissor `markdown_safe` + `authorized_links` inexistente no delia-api; (2) QA browser B2; (3) aceite independente CP-333.

## 3. Spec fechada (doc 96 §9)

- Anatomia/dimensões: bar ~30px, `pre` 12/14px, `0.86em`/`1.55`/`tab-size 2`, `max-height` 320px desktop / 240px estreito+Dock, `radius 10px`, `border 1px` — medidas do prior art `md-doc` adaptadas ao ritmo da conversa (`margin 0.45em`), namespace próprio `delpi-ui-conversation-code-block`.
- Cópia: `writeText(token.text)` pós-resolve; erro visível + `aria-live`; sem `execCommand`.
- Linguagens: allowlist display + sanitização de lang desconhecida; nunca inferência.
- Highlight: v1 sem (nenhum mecanismo aprovado existe).
- Responsivo/a11y/segurança: scroll horizontal interno (`white-space:pre`), zoom 200%, temas via tokens, reduced motion, `pre` rolável com `tabindex`/`role=region`, teclado, contraste AA.
- Contrato: `ConversationCodeBlockProps{code, language?, copyEnabled?, className?, labels?}`; wiring = `ConversationMarkdown` case `code` delega; `MarkdownToken` ganha `lang?: string`.
- Matriz CB-V01..V15 com método de verificação por critério.

## 4. Decisão

```text
CODE_BLOCK_VISUAL_SPEC=READY
EXISTING_EQUIVALENT=YES
REUSE_DECISION=EXTEND
MARKDOWN_B2=GATED
STANDALONE_RENDER_COMPONENT=AUTHORIZED_CANDIDATE
DELIA_RUNTIME_ACTIVATION=BLOCKED
NEXT_BOUNDED_IMPLEMENTATION=ConversationCodeBlock + lang?: string + case "code" delega + CSS + testes (inerte, gated)
RUNTIME_CHANGED=NO
DEPLOYMENT=NOT_APPLICABLE
TESTS=TEST_NOT_RUN
PHASE_PROGRESSION=NONE
```
