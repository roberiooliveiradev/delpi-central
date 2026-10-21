# F02-A-R3 — Centralização vertical do bloco de sugestões no Companion Dock

**TASK_ID:** DELIA-UX-F02A-R3-DOCK-STARTER-VERTICAL-CENTERING-01
**DATA:** 2026-10-21 · **SPEC:** doc 93 §19 (decisão de produto 2026-10-21) · **LEDGER:** §6.358

## 1. Escopo e reuse

- `EXISTING_EQUIVALENT=YES` · `REUSE_DECISION=EXTEND_CSS_ONLY` · `NEW_COMPONENT=NO` · `NEW_BACKEND=NO`.
- Único arquivo alterado: `plugins/plugin-ui/src/styles/conversation-starter-suggestions.css` (+12/−1 no bloco `.global-delia-dock`).
- Nenhum TSX, hook, observer, engine, backend, MCP, STT ou permissão tocado.

## 2. Geometria ANTES (fato medido, Dock autenticado QA)

Bloco `label+grid` ancorado 12px abaixo da recepção; todo o espaço livre ficava abaixo:

| Caso | bandH | blockH | freeAbove | freeBelow | offset |
|---|---|---|---|---|---|
| 360×900 | 312.6 | 214.2 | 12.0 | 86.4 | −37.2 |
| 420×900 | 330.5 | 214.1 | 12.0 | 104.4 | −46.2 |
| 520×900 | 299.0 | 118.2 | 12.0 | 168.8 | −78.4 |
| 420×720 | 264.7 | 214.1 | 12.0 | 38.6 | −13.3 |
| 420×650 | 168.7 | 118.1 | 12.0 | 38.6 | −13.3 |
| 360×450 | — | — | — | — | 0 cards |

## 3. Implementação

```css
.global-delia-dock .delpi-ui-starter-suggestions {
  padding: 12px;            /* vertical simétrico: não enviesa o centro */
  flex: 1 1 auto;           /* a seção preenche a faixa livre da coluna */
  min-height: 0;
  justify-content: center;  /* raiz já é flex-column → grupo centrado */
}
```

- A **seção** (item flex da `__column`) cresce e preenche o espaço entre a base da recepção e o fundo da coluna (topo do composer); `justify-content:center` empacota `label+grid` como grupo único no centro da faixa.
- O `justify-content:center` da coluna (R2) vira no-op com a seção visível e continua a centrar a recepção sozinha quando o budget esconde todos os cards (altura crítica).
- Recepção retorna ao topo → três regiões: recepção / sugestões centradas / composer.
- Sem `position:absolute`, sem transform, sem margins fixas por breakpoint. Full-page intocado (regra com escopo `.global-delia-dock`).

## 4. Geometria DEPOIS (fato medido)

| Caso | bandH | blockH | freeAbove | freeBelow | offset |
|---|---|---|---|---|---|
| 360×900 | 360.9 | 214.2 | 66.3 | 80.4 | **−7.1** |
| 420×900 | 395.7 | 214.1 | 83.2 | 98.4 | **−7.6** |
| 520×900 | 426.0 | 118.2 | 145.0 | 162.8 | **−8.9** |
| 420×720 | 276.7 | 214.1 | 24.0 | 38.6 | **−7.3** |
| 420×650 | 180.7 | 118.1 | 24.0 | 38.6 | **−7.3** |
| 360×450 | — | — | — | — | 0 cards (recepção centrada) |

Assimetria residual ~14–18px (`below−above`): gap de 12px da coluna (só existe acima da seção) + chrome do composer entre o fundo da coluna e `footer.top` — restrições legítimas de layout, dentro da tolerância do §19 (não exige simetria pixel-perfect).

## 5. Validação executada

- **Vitest direcionado:** plugin-ui `src/components/conversation/` 146/146; delia `src/suggestions/` + `App.test.tsx` 13/13.
- **Typecheck:** `tsc --noEmit` limpo (plugin-ui).
- **Build:** plugin-ui OK (warning de chunk grande pré-existente).
- **Federation:** `verify:host-exports` OK.
- **Browser QA autenticado (local, paridade produção): 44/44 PASS.**
  - Cards: 4 (360/420/520×900), 2 (420×650), 0 (360×450).
  - Centralização: `|offset| ≤ 12px` em toda banda com folga ≥50px.
  - Resize 420→340→520px: sem overlap, sem h-overflow, foco preservado, 4 cards ao alargar.
  - Clique/Enter: só preenche draft, rascunho anterior preservado, foco no composer, `turns=0`.
  - Tooltip HelpTooltip visível, mic VD-F05 presente, seção oculta após turn real, composer sempre acessível.
  - Full-page: 4 cards / 2 colunas, sem h-overflow.
  - Zoom 200% (sintético via `body.style.zoom`): 4 cards legíveis, sem h-overflow, sem overlap — o zoom sintético infla `100dvh` e empurra o composer além da dobra (artifact do método); a âncora do composer sob altura real crítica é coberta pelo caso 360×450.

## 6. Deployment em produção

- Pendente no momento da escrita desta evidência; preencher após `up-prod-sequential.sh` (apenas `plugin-ui` — Portal e demais serviços inalterados nesta task).

## 7. Não-objetos preservados

Perguntas congeladas, budget de altura R2 (4→3→2→1→0 e fileiras inteiras em 2 col), draft-only, zero auto-submit, HelpTooltip, teclado, reduced motion, temas, timeline pós-turn, VD-F05, backend/contratos/AuthZ/MCP.
