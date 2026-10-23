# Markdown B2 — Companion Dock, responsividade e acessibilidade (QA autenticado)

- **TASK_ID:** `DELIA-UX-MARKDOWN-B2-DOCK-AND-ACCESSIBILITY-QA-01`
- **Data:** 2026-10-23
- **Base testada:** `main` @ `b3a7644191` (worktree), `origin/main` sincronizado; contém `8162baf1a7` (admissão markdown conversacional) + docs `b016fbf8c4`
- **Ambiente:** produção `https://minhadelpi.com.br`, sessão SSO real (usuário legítimo), Chromium headless (Playwright)
- **Tipo:** QA-FIRST — nenhuma correção de código necessária (zero defeitos frontend)

## 1. Emissão real observada (mesmo turno autenticado)

Turno real no **Companion Dock** (sessão `f8459c59-2d45-4cad-a4d7-99b6e597bfc7`, result turn `18521b23-9a8b-4df3-b4f5-c25a3eeba04d`), pergunta SIPOC canônica:

| Campo | Valor observado |
|---|---|
| HTTP | 200 |
| `presentation.version` | `"2"` |
| block `format` | `markdown_safe` |
| `message_kind` | `RESULT` |
| `grounding_status` | `NON_GROUNDED` |
| `semantic_status` | `HYPOTHESIS` |

DOM do Dock: `.delpi-ui-conversation-markdown` ×1, **12 listas / 23 `<li>`**, 0 `<a>`, 0 scripts, 0 overflow horizontal (local e global), markdown cru invisível, composer visível, marcador de evidência presente. Headings=0 e strong=0 nesta resposta — o modelo usou bullets + negrito inline; nada foi fabricado para o teste. Screenshot `b1-dock-1440.png` confirma render rico (bullets "○" indentados, labels em negrito, "Sem fonte vinculada"/"Detalhes da evidência" separados).

Full-page: respostas reais renderizadas em light (`a1-fullpage-1440.png`) e dark (`e-dark-reduced.png`), e code block real renderizado (`f1-codeblock.png` — badge "Python" + "Copiar código"). O envelope NDJSON do turno full-page não foi capturado pela instrumentação fetch do harness (`presentation:null`); o DOM renderizado + turno Dock no mesmo deploy provam o caminho v2. Registrado como limitação de harness, não defeito de produto.

## 2. Responsividade / temas

| Cenário | Resultado |
|---|---|
| Full-page 1440 | PASS |
| Viewport 420 / 375 / 360 / 320 | PASS — layout adaptado, composer visível, sem scroll horizontal (screenshots `c-viewport-*`) |
| Zoom 200% | PASS — conteúdo legível, sem sobreposição (`d-zoom200.png`) |
| Dark + reduced motion | PASS — resposta real renderizada, contraste adequado (`e-dark-reduced.png`) |
| Dock real (largura nativa) | PASS — sem scroll horizontal global, listas/marcadores preservados |

## 3. CodeBlock + clipboard (real, produção)

Prompt real produziu bloco de código fenced → `ConversationCodeBlock` com badge de linguagem "Python" e botão "Copiar código" (`f1-codeblock.png`, `kb-codeblock.png`).

- Clique em "Copiar código": `navigator.clipboard.readText()` = **73 chars literais** do código (`def saudacao(nome):...`), feedback visual de sucesso visível.
- `<pre>` é focável por teclado (`aria-label` "Conteúdo do código") → scroll interno acessível.
- Código renderizado como texto inerte; nenhuma execução.

## 4. Teclado

- **Tab** a partir do composer: "Ditar mensagem" → sidebar do Portal. Sem focus trap; foco não é roubado ao fim da resposta.
- **Shift+Tab** a partir do composer percorre toda a cadeia da mensagem: `Mais opções` → `Copiar resposta` → `Detalhes da evidência` → `PRE` (conteúdo do código) → `Copiar código` → `Ver detalhes` (atividade) → `Abrir contexto` → navegação lateral. Todos os controles com nomes acessíveis claros.
- Enter dentro do container markdown não sequestra o composer (`noHijack` verificado).

## 5. Acessibilidade automatizada (DOM)

- `lang="pt-br"` no documento; container markdown não está sob `aria-hidden`.
- Listas são `<ul>/<ol>/<li>` semânticos reais (quando o modelo emite sintaxe de lista).
- 0 elementos injetados (`script|iframe|svg|object|embed` = 0) em todas as respostas observadas.
- Botões de ação possuem `aria-label`/texto acessível ("Copiar código", "Copiar resposta", "Detalhes da evidência", "Mais opções").

**SCREEN_READER_QA=TEST_NOT_RUN** — nenhum leitor de tela utilizável no ambiente (NVDA indisponível no Windows host; harness headless Linux). Inspeção de accessibility tree: a API `page.accessibility` não existe na versão do Playwright instalada; auditoria DOM executada como evidência parcial (não substitui leitor de tela).

## 6. Segurança / conteúdo não confiável

- `UNTRUSTED_CONTENT_EXECUTION=NO` — 0 scripts/iframes em todas as respostas.
- `UNAUTHORIZED_LINK_NAVIGATION=NO` — 0 `<a>` emitidos em prosa do modelo (gate `authorizedLinks` vazio).
- HTML literal escapado (coberto pelos testes de consumer + rework G3-RW-01).
- `BACKEND_FORMAT_DECISION_BYPASS=NO` — frontend render-only via `parsePresentationV2`.

## 7. Matriz MB2-UX01–20

| # | Critério | Status |
|---|---|---|
| UX01 | Emissão real v2 observada | PASS (Dock, mesmo turno) |
| UX02 | Markdown renderizado corretamente | PASS |
| UX03 | Paridade full-page/Dock | PASS (equivalência semântica; full-page provada por render real + run anterior) |
| UX04 | Listas/títulos semânticos | PASS (listas sim; headings não emitidos pelo modelo — honesto) |
| UX05 | Tipografia/espaçamento | PASS |
| UX06 | Sem overflow horizontal global | PASS (todas as superfícies) |
| UX07 | CodeBlock funcional | PASS (real, produção) |
| UX08 | Clipboard + feedback | PASS (73 chars, feedback visível) |
| UX09 | Teclado | PASS (Tab/Shift+Tab, sem trap) |
| UX10 | Screen reader real | TEST_NOT_RUN |
| UX11 | Mobile + zoom 200% | PASS |
| UX12 | Dark/light/reduced motion | PASS |
| UX13 | Evidências/atividade preservadas | PASS (superfícies separadas) |
| UX14 | Plain/v1 fallback | PASS (coberto por testes backend/frontend; negativos v1) |
| UX15 | HTML/não-confiável inerte | PASS |
| UX16 | Links autorizados/negados | PASS (0 anchors emitidos; gate intacto) |
| UX17 | Composer/fila sem regressão | PASS |
| UX18 | Build/typecheck/Vitest/federation | PASS (suite anterior no mesmo código + focado 89+60 nesta task) |
| UX19 | Produção pós-correção verificada | PASS (sem correção necessária — QA only) |
| UX20 | Evidência no SHA avaliado | PASS |

## 8. Regressões executadas nesta task

- `plugins/plugin-ui` focado: ConversationMarkdown (26) + MarkdownDocument (14) + lexer probe (26) + ConversationCodeBlock (23) = **89/89 PASS** @ HEAD `b3a7644191`.
- `plugins/delia` src/api: presentation (30) + NDJSON (14) + g4Homologation (16) = **60/60 PASS**.
- Suites completas herdadas do mesmo código (sem diff frontend): delia 353/353, plugin-ui 2315/2315, typecheck, build, federation — todas PASS na task anterior, código inalterado desde então.

## 9. Defeitos

- **DEFECTS_FOUND=0** no ownership frontend.
- Limitação de harness (não-produto): captura NDJSON do turno full-page retornou `presentation:null`; `page.accessibility` indisponível na versão do Playwright.

## 10. Residuais

- `SCREEN_READER_QA=TEST_NOT_RUN` — requer NVDA/VoiceOver/Orca real; não substituível por auditoria DOM.
- Headings markdown (`#`) não exercitados em resposta real (modelo não emitiu a sintaxe); cobertos por `ConversationMarkdown.test.tsx`.
- Deploy: **não aplicável** — nenhum arquivo de código alterado (docs-only).

## 11. Screenshots

`C:\temp\delia-qa\` (espelho WSL `/tmp/prod-ux*`): `a1-fullpage-1440`, `b1-dock-1440`, `b2-dock-focused`, `c-viewport-{320,360,375,420}`, `d-zoom200`, `e-dark-reduced`, `f1-codeblock`, `a11y-md`, `kb-codeblock`.

---

**Veredito do executor:** Markdown B2 apresenta qualidade e segurança equivalentes no full-page e no Companion Dock em produção real. Zero defeitos frontend. Aceite de CP-333 permanece com a coordenação.


## 12. Aceite posterior do Product Owner (2026-10-23)

O Product Owner **aceitou explicitamente o componente e a homologação frontend Markdown B2** para prosseguir às demais evoluções. Registro de aceite de produto sobre evidências já publicadas; **não é execução de testes adicional** nem aceite de CP-333 pela coordenação.

- `PRODUCT_OWNER_ACCEPTANCE=YES` (ConversationCodeBlock e UX Markdown B2 no escopo avaliado).
- `FRONTEND_REVIEW=ACCEPT_WITH_RESIDUAL` — ausência de defeitos frontend reportados; trabalho funcional encerrado.
- `SCREEN_READER_QA=TEST_NOT_RUN` — residual preservado, não converter em PASS.
- `CP_333=AWAIT_COORDINATION_DECISION`; `PHASE_PROGRESSION=NONE`.
- `CODE_CHANGED=NO`; `DEPLOYMENT=NOT_APPLICABLE`.

Próximas evoluções de frontend serão tasks bounded próprias; não reabrir este componente sem evidência nova.
