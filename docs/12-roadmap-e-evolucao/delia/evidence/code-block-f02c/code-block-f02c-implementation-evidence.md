# F02-C — ConversationCodeBlock: evidência de implementação

> **Task:** `DELIA-UX-F02C-CONVERSATION-CODE-BLOCK-SHARED-IMPLEMENTATION-01`
> **Base reancorada:** `5ba8c24275eda0458fdc21fa0c4191f6407c0964` (origin/main)
> **Spec autoridade:** doc 96 §9 (F02-B) — implementação integral e verificação CB-V01–V15.
> **Escopo:** `plugins/plugin-ui` + fixture demo `plugins/delia` — zero backend.

## 1. Arquivos

| Arquivo | Mudança |
|---|---|
| `plugins/plugin-ui/src/components/conversation/ConversationCodeBlock.tsx` | **novo** — componente inerte |
| `plugins/plugin-ui/src/components/conversation/ConversationCodeBlock.test.tsx` | **novo** — 23 testes |
| `plugins/plugin-ui/src/components/markdown/conversationMarkdownModel.ts` | `MarkdownToken.lang?: string` (aditivo) |
| `plugins/plugin-ui/src/components/markdown/ConversationMarkdown.tsx` | case `"code"` → delegação |
| `plugins/plugin-ui/src/components/markdown/ConversationMarkdown.test.tsx` | +6 testes de integração; 1 seletor ajustado (`svg:not(.lucide)`) |
| `plugins/plugin-ui/src/styles/conversation-code-block.css` | **novo** — namespace `delpi-ui-conversation-code-block` |
| `plugins/plugin-ui/src/styles.css` | +`@import` |
| `plugins/plugin-ui/src/components/conversation/index.ts` | +export público |
| `plugins/plugin-ui/src/index.ts` | +export público + tipos |
| `plugins/plugin-ui/scripts/verify-host-exports.mjs` | `ConversationCodeBlock` em `REQUIRED_HOST_EXPORTS` |
| `plugins/delia/src/demo/demoMode.ts` | cenário `markdown_code` (fixture QA, gated) |

## 2. Contrato implementado

```ts
type ConversationCodeBlockProps = {
  code: string;
  language?: string;
  copyEnabled?: boolean;
  className?: string;
  labels?: Partial<ConversationCodeBlockLabels>;
};
```

- `role="group"` + `aria-label="Bloco de código {lang}"`; `pre` com `role="region"` + `tabIndex={0}`.
- Cópia: `navigator.clipboard.writeText(code)` — sucesso `Check`+`Copiado` **apenas pós-resolve**; falha/indisponível → `ClipboardX`+`Não foi possível copiar` num único `aria-live="polite"`; reset ~1600ms; `opRef` descarta respostas assíncronas fora de ordem; `mountedRef`+`clearTimeout` no unmount. **Sem `execCommand`.**
- Linguagens: allowlist `{sql,python,json,typescript,javascript,bash,yaml,text}` → labels PT; fora da lista → valor sanitizado (`[a-z0-9+#.-]`, ≤20 chars); vazio/inválido → `Código`.
- CSS: bar ~30px (`min-height`, `5px 10px`), `pre` `12px 14px`/`0.86em`/`1.55`/`tab-size: 2`/`white-space: pre`/`overflow auto`, `max-height: 320px` (240px ≤480px), label do copy colapsa ≤480px mantendo `aria-label`, `prefers-reduced-motion` zera transição, override de especificidade para `code { white-space: pre }` dentro de `conversation-markdown`.

## 3. Verificação

| Gate | Resultado |
|---|---|
| Vitest plugin-ui | **2315/2315** (+29: 23 componente + 6 integração) |
| Vitest delia | **322/322** |
| tsc plugin-ui + delia | **0 erros** |
| Build plugin-ui + `verify-host-exports` | OK — `ConversationCodeBlock` no chunk federado |
| Browser QA (Playwright, fixture `?delia-demo=markdown_code`) | **46/46** |

Browser QA cobriu: 6 blocos independentes; allowlist/fallback/sanitização de linguagem; HTML literal inerte; scroll horizontal **interno** com linha de 300 chars (`scrollW 2146 > clientW 508`, `docScrollW == docClientW`); cópia real com permissão (`Copiado`, conteúdo sem fences/lang, reset ~1.6s); rejeição e indisponibilidade de clipboard → erro honesto; foco+Enter copiando; mobile 320/360/375/420 sem overflow; label colapsado com nome acessível; `data-theme=dark`; reduced-motion; zoom-equivalente 200%; fixture sem POST backend; zero bloco rico fora de apresentação admitida.

## 4. Matriz CB-V01–V15 — resultado factual

| ID | Estado | Prova |
|---|---|---|
| CB-V01 anatomia compacta | PASS | unit + QA (bar 30px, lang, copy) |
| CB-V02 literal preservado | PASS | unit (tabs/CR/LF/blank) + QA (clipboard sem fences) |
| CB-V03 cópia honesta | PASS | unit + QA (Copiado só pós-resolve, reset 1600ms) |
| CB-V04 clipboard indisponível | PASS | unit + QA (reject + undefined → erro visível, aria-live único) |
| CB-V05 linguagens | PASS | unit (8 allowlist + unlisted + unsafe + ≤20) + QA |
| CB-V06 múltiplos blocos | PASS | unit + QA (6 blocos, estados independentes) |
| CB-V07 linhas longas | PASS | QA (scroll interno, doc não alarga) |
| CB-V08 fenced vs inline | PASS | unit (codespan → `<code>` simples) |
| CB-V09 HTML/script inerte | PASS | unit + QA (zero `script/img` materializado) |
| CB-V10 full-page/Dock/mobile | PASS | QA (1280px, 480px, 320–420px) |
| CB-V11 zoom/temas/reduced-motion | PASS | QA (dark attr, transition 0s, 640px dsf2) |
| CB-V12 teclado/leitor de tela | PASS | QA (focus+Enter, role=region, aria-live único) |
| CB-V13 sem execution path | PASS | zero eval/innerHTML/execCommand; revisão de diff |
| CB-V14 gates B2 preservados | PASS | `enabled=false` → `<p>` literal; fixture gated |
| CB-V15 regressão renderização | PASS | 2315+322 testes; seletor svg ajustado (lucide) |

## 5. Gates preservados (não alterados nesta task)

```text
MARKDOWN_B2_CONTRACT=CONTRACT_APPROVED
MARKDOWN_B2_RENDERER=IMPLEMENTED
MARKDOWN_B2_EMITTER=NOT_IMPLEMENTED (zero markdown_safe em delia-api)
MARKDOWN_B2_RUNTIME=OFF
CP_333=NOT_ACCEPTED
BACKEND_CHANGED=NO
I04_ACCEPTED=NO
```

## 6. Residuais honestos

1. `vite preview` (não `dev`) serviu o remoteEntry no QA — federation remotes não emitem remoteEntry em modo dev.
2. O fixture `markdown_code` roda no bundle demo-gated (`DEV`/`VITE_DELIA_DEMO=1`); produção nunca o admite.
3. `ConversationMarkdown.test.tsx` não executa cleanup global (pré-existente); novos testes usam queries escopadas em `container`.
4. Sem syntax highlighting (deliberado, spec §9.6).
