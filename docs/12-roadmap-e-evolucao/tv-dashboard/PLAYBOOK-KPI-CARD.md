# Playbook — KPI Card (TV Dashboard)

> **Arquivo:** `docs/12-roadmap-e-evolucao/tv-dashboard/PLAYBOOK-KPI-CARD.md`  
> **Data:** 2026-07-23  
> **Status:** implementado (jul/2026) — Onda 0 tipografia + Ondas A–D (float/ribbon, meta/delta, sparkline, layouts)  
> **Relacionado:** inventário código KPI vs Chart; Power BI Card/KPI, Tableau BAN, Looker Scorecard

---

## 1. Diagnóstico (estado atual)

O float do KPI compartilha o shell do gráfico (`+` / pincel / funil), mas o conteúdo é pobre:

| Camada | KPI hoje | Gráfico (referência) |
|---|---|---|
| Float `+` | Checklist 5 parts | Flyouts PPT (eixos, grade, legenda…) |
| Float pincel | 4 tons + ciclo de formato | Paletas + receitas (claro/escuro/…) |
| Float funil | Fonte + métricas (âncoras) | Modal dados + eixos/séries |
| Ribbon | Cai na aba **Forma** | Aba **Gráfico** dedicada |
| Dados | Valor; `colorRules` só no pane | Projeção rica + UI no float |

**Contratos a preservar:** `kpiParts` / `kpiOptions` / `kpiProjection.metrics[]`; render único `KpiViewBlockView` → `DelpiKpiCard` (editor = prévia = TV).

---

## 2. Bug P0 — valor não acompanha o tamanho da fonte

### Sintoma (jul/2026)

Ribbon **Fonte — Valor** mostra `40`, mas o número no palco fica miúdo dentro de um frame grande da part `value` (texto “encolhido” no canto).

### Causa raiz

Em `plugin-ui` → `kpiCardParts.ts` → `kpiPartUsesAutoFitFont`:

```ts
// fontSize === default (value=40, title=18) ⇒ trata como AUTO-FIT
return Math.round(explicit) === KPI_PART_FONT_SIZE_DEFAULTS[kind];
```

Efeitos:

1. A ribbon resolve o tamanho com `resolveKpiPartFontSize` → mostra **40**.
2. O render usa `FitText` com `fixedPx={null}` (auto-fit) porque 40 ≡ default.
3. Auto-fit mede o host; com frame livre / flex, o fit pode ficar preso perto de `minPx` → valor visual ≠ 40.
4. Digitar **40** na ribbon **não muda** o modo (continua auto-fit). Só tamanhos ≠ default viram `fixedPx`.

Testes atuais **documentam** o comportamento indesejado (`kpiCardParts.test.ts`, `DelpiKpiCard.test.tsx`: “fontSize 40 → auto-fit”).

### Correção canônica (Onda 0 — antes das features)

| # | Entrega | Onde |
|---|---------|------|
| 0.1 | Separar **modo tipográfico**: `auto` vs `fixed`. Auto-fit **só** se `fontSize` ausente **ou** flag explícita `typographyMode: "auto"` (nome final no contrato). | `kpiCardParts.ts` |
| 0.2 | Qualquer `fontSize` persistido (incluindo 40) ⇒ `FitText fixedPx={n}` — ribbon e palco batem. | `DelpiKpiCard.tsx` |
| 0.3 | Default de fábrica: ou seed sem `fontSize` (auto) **ou** seed `fontSize: 40` fixo — escolher um e alinhar UI (“Automático” vs número). Preferência: seed **sem** size = auto; ao usuário editar tamanho na ribbon, gravar `fontSize` e sair do auto. | factory + ribbon |
| 0.4 | Com part `value` framed: auto-fit deve usar o frame da part (não colapsar em `minPx`); regressão visual frame grande + auto. | `FitText` + CSS part |
| 0.5 | Atualizar testes que assertam “40 ⇒ auto”; adicionar: ribbon 40 persistido ⇒ DOM `40px`. | `kpiCardParts.test.ts`, `DelpiKpiCard.test.tsx`, target tipografia MFE |

**Aceite Onda 0**

- [x] Selecionar valor → Fonte `40` → texto no palco ~40px (não miúdo).
- [x] Alterar para `72` / voltar a `40` → ambos respeitados.
- [x] Modo automático (se mantido) é explícito na UI, não “default mágico”.
- [x] TV/prévia = editor.

**⚠ Não** “corrigir” só no MFE com CSS override — a regra vive em `kpiPartUsesAutoFitFont` / `DelpiKpiCard`.

---

## 3. Pesquisa de mercado (norte de produto)

| Ferramenta | Anatomia | Destaques |
|---|---|---|
| **Power BI** | Valor + meta + tendência; Card 2025 com sparkline / reference labels | Formatação condicional RAG; high/low is good |
| **Tableau** | BAN + delta ▲/▼ + sparkline | 3–7 KPIs; cor semântica consistente |
| **Looker Studio** | Scorecard + comparação + sparkline **ou** progresso | Sparkline e progresso mutuamente exclusivos |

**Anatomia alvo**

```text
[rótulo]                    [ícone]
[VALOR GRANDE]              ← tipografia = ribbon (Onda 0)
[▲ +3,2% vs meta/período]   [sparkline opcional]
[barra/anel de progresso opcional]
```

---

## 4. North star

1. Paridade de **profundidade de edição** com o gráfico (float PPT-like + estilos + dados).
2. Em &lt;1s: *qual o número?* *está bom?* *para onde vai?*
3. Contrato estável `kpiParts` + `kpiOptions` + `kpiProjection`; um pipeline de render.

---

## 5. Arquitetura canônica

| Camada | Onde | Papel |
|---|---|---|
| Tipografia / parts | `plugin-ui` — `kpiCardParts`, `DelpiKpiCard`, `FitText` | Onda 0 + novas parts |
| Contrato | `tv-dashboard-presentation` — options, projection, `resolveKpiPresentation` | Meta, comparação, sparkline |
| Editor | `tv-dashboard` — float, ribbon KPI, catálogos | UX paridade chart |
| Dados | enrichment + `kpiProjection` | Série temporal / meta |

---

## 6. Ondas

### Onda 0 — Tipografia valor/título (bug) ✅ prioridade

Ver §2. **Bloqueia percepção de qualidade** das ondas seguintes.

### Onda A — Paridade de editor (UX)

1. Add-element com flyouts (formato select, layout presets, “Mais opções…”).
2. Pincel: tons + atalho `colorRules` + presets aparência.
3. Funil: + “Formato e regras…”.
4. Ribbon contextual **KPI** (hoje some na Forma).

### Onda B — Meta + comparação

- `target` / `comparison` em `kpiProjection`.
- Parts `comparison` (+ opcional `progress`).
- Direção `higherIsBetter` | `lowerIsBetter`.

### Onda C — Sparkline

- Part `sparkline` + série no `resolved`.
- Exclusão mútua com progresso (Looker).

### Onda D — Layouts / multi-métrica

- Presets de frames %; multi-métrica editável no palco; reference labels.

### Fora de escopo

Mini-chart completo, drill-through, import PPTX de cards, forecast ML.

---

## 7. Ordem

```text
0 (fonte = palco) → A (float/ribbon) → B (meta/delta) → C (sparkline) → D (layouts)
```

---

## 8. Critérios globais

- [x] Onda 0 verde (fonte ribbon = px no valor).
- [x] Float KPI com profundidade análoga ao chart.
- [x] Valor + (meta ou comparação) + (sparkline ou progresso).
- [x] Persistência parts/options; F5/WS ok.
- [x] TV/prévia = editor.
- [x] Testes unitários + regressão tipografia.

---

## 9. Arquivos-chave (referência rápida)

| Bug / feature | Path |
|---|---|
| Auto-fit vs fixed | `plugins/plugin-ui/src/components/layout/kpiCardParts.ts` (`kpiPartUsesAutoFitFont`) |
| Render valor | `plugins/plugin-ui/src/components/layout/DelpiKpiCard.tsx` |
| Fit | `plugins/plugin-ui/src/components/layout/FitText.tsx` |
| Ribbon fonte | `plugins/tv-dashboard/src/utils/selectedTextFormatTarget.ts` + `FormatRibbonTypographySections.tsx` |
| Float KPI | `plugins/tv-dashboard/src/components/KpiSelectionFloatToolbar.tsx` |
| Catálogo elementos | `plugins/plugin-ui/src/components/layout/kpiElementCatalog.ts` |
