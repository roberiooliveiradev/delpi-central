# F02-A — Conversation Starter Suggestions — evidência de implementação

**TASK_ID:** `DELIA-UX-F02A-STARTER-SUGGESTIONS-FRONTEND-01`
**Spec:** `93-conversation-starter-suggestions-product-ux-specification.md` §§12–14
**BASE_HEAD:** `d65d5035a8a30cd2f8f23773780ab4d095f21f64`
**TESTED_SHA:** `2348814d02e90a49db843c799fd009996e7957d5`

## 1. Escopo e decisões

- `ConversationStarterSuggestions` — **NEW** em `plugins/plugin-ui` (nenhum
  componente equivalente existia; `EXISTING_EQUIVALENT_SUGGESTIONS=NO`).
- Render-only: props de apresentação + callback de intenção `onSelect`.
  Sem fetch, sem Core/Keycloak/MCP, sem autorização, sem capacidades.
- Integração: sibling de `DeliaReception` no branch `turns.length === 0`
  do `App.tsx` — o componente compartilhado de recepção não foi alterado.
- Fixtures QA: as quatro perguntas do §14 ficam em
  `plugins/delia/src/suggestions/starterSuggestions.ts` (owner DÉLIA).
- **Gate de visibilidade (spec §14):** `resolveStarterSuggestions`
  retorna `[]` salvo quando o modo QA governado existente está ativo
  ponta-a-ponta — bundle admitido (`isDemoAllowed()`: Vite dev ou build
  `VITE_DELIA_DEMO=1`) **e** `?delia-demo=<scenario>` explícito na URL
  (`resolveDemoScenario`). Produção (`items=[]`) nunca expõe as fixtures;
  nenhuma permissão ou feature backend nova foi criada.
- Dockerfile da DÉLIA recebeu `ARG VITE_DELIA_DEMO` seguindo o padrão
  já existente `ARG VITE_DELIA_AUDIO_QA` (QA-only, default off).
- `isDemoAllowed()` ganhou parâmetro `env` opcional para testabilidade
  (retrocompatível — default `import.meta.env`).

## 2. Seleção — comportamento implementado

- Clique/Enter/Space (botões reais) → `setInput(draftText)` + foco e caret
  no fim do composer (`#delia-interaction-input`).
- **Nunca** chama `handleSubmit`/`/interaction/turns`/provider.
- Draft não vazio → não sobrescreve; exibe nota leve
  (`role=status`): "Edite ou apague o texto atual antes de usar uma
  sugestão." A nota limpa ao primeiro edit no draft.
- Clique repetido após seleção não duplica texto (fail-safe do draft).
- `draftText` truncado a `INTERACTION_INPUT_CHAR_LIMIT` (16.384).
- `turns.length > 0` remove a seção junto com a recepção.

## 3. Vitest

- `plugin-ui` `ConversationStarterSuggestions.test.tsx`: **15/15** —
  0/1/2/3/4+ itens, cap `maxVisible`, label/aria-labelledby, click,
  botões reais, disabled global e por item, HelpTooltip wrap
  (`aria-describedby` + bubble sob demanda), loading skeleton honesto
  (`aria-busy`), nota `role=status`, densidade compact, sem ícone,
  **zero fetch** e texto hostil inerte (sem HTML injetado).
- `delia` `starterSuggestions.test.tsx`: **9/9** — gate
  (`resolveStarterSuggestions` com/sem demo scenario), integridade das
  fixtures, seção ausente fora do modo QA, cards→`turns>0` escondem,
  draft+foco+sem submit, preservação + nota, repetição não duplica,
  posição DOM recepção→sugestões→composer.
- Suítes completas: **plugin-ui 2269/2269**, **delia 276/276**.
- `tsc --noEmit` limpo nos dois plugins; `npm run build` OK;
  `verify-host-exports` OK (federation).

## 4. Browser QA (Playwright, Chrome headless real, `e2e-delia`, stack local)

Imagem `delia` local buildada com `--build-arg VITE_DELIA_DEMO=1`
(QA-only); `plugin-ui` rebuildada com o componente. Gateway restartado
uma vez por DNS stale de upstream (172.18.0.15 → 172.18.0.24), sem
relação com o diff.

**42/42 PASS** (`qa-f02a.mjs` + `qa-f02a-theme.mjs`):

| Checagem | Resultado |
|---|---|
| Sem `?delia-demo` → seção ausente | PASS |
| Seção + label + 4 cards + 2 colunas (1440px) | PASS |
| Tooltip HelpTooltip em card | PASS |
| Clique → draft preenchido + foco no composer | PASS |
| `POST /interaction/turns` = **0** em todas as seleções | PASS |
| Draft não vazio → preservado + nota leve | PASS |
| Teclado (foco + Enter) → draft preenchido | PASS |
| Focus ring visível (outline 3px) | PASS |
| Após turn enviado → seção some com a recepção | PASS |
| 420/360/320px: ≤2 cards, 1 coluna, sem overflow | PASS |
| ≤400px: description oculta (minimal) | PASS |
| Viewport curto (720×400): ≤1 card, composer intacto | PASS |
| Zoom 200%: composer visível, sem overflow | PASS |
| Companion Dock: ≤2 cards, sem description, sem overflow | PASS |
| Dock: clique preenche draft, zero submit | PASS |
| `prefers-color-scheme: dark`: superfície escura (lum≈17) | PASS |
| `prefers-reduced-motion: reduce`: transitions 0s | PASS |

Screenshots: `shots-f02a/01..10` (page, draft, turn, 320/360/420, short,
zoom200, dock, dark, reduced-motion).

## 5. Status dos critérios (spec 93 §12.5/§13.4/§14)

| Critério | Estado |
|---|---|
| SS-V01..SS-V10 | PASS (testes unitários + browser) |
| SS-V11..SS-V16 | PASS (caps por container/altura, zero fallback inventado) |
| SS-F01 | PASS — render-only em `plugin-ui` |
| SS-F02 | PASS — fixtures só no consumer DÉLIA, elegibilidade honesta |
| SS-F03 | PASS — clique/Enter/Space → draft + foco, sem submit |
| SS-F04 | PASS — draft existente preservado, nota leve |
| SS-F05 | PASS — zero sugestões fora do gate QA; produção `items=[]` |
| SS-F06 | PASS — 0–4 cards; fullpage/Dock/320–420 |
| SS-F07 | PASS — tooltip, teclado, a11y, light/dark, reduced-motion |
| SS-F08 | PASS — suites/typecheck/build/federation/browser neste SHA |
| SS-F09 | PASS — nenhuma mudança em STT, Keycloak, Core, API, MCP |
| SS-F10 | PASS — este registro distingue fixtures QA de capabilities |

## 6. Ressalvas / residuais

- As quatro perguntas são **fixtures de apresentação QA**, não
  capabilities admitidas. Exibição pública futura exige projeção de
  elegibilidade por sessão (owner/contrato legítimo) — `DEFERRED`.
- QA do comportamento "1 card em altura curta" exercitado via viewport
  720×400 (equivale a zoom extremo); estado `loading` testado em Vitest
  apenas (não há loading real — spec proíbe loading fictício).
- `EXECUTION_DRIFT=NONE`; `PHASE_ADVANCE=NO`; `I04_ACCEPTED=NO`;
  `C3_EXECUTED=NO`.
