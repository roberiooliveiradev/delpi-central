# Wireframes visuais e cores — páginas e componentes

> **Canônico de cor/tokens:** [DESIGN-FRONTEND.md §1](./DESIGN-FRONTEND.md) · **Layout estrutural:** [WIREFRAMES.md](./WIREFRAMES.md) · **CSS vivo:** `plugins/production-pulse/src/index.css`  
> **Prefixo:** `.dashboard-production-pulse` · BEM `pp-` · Kit `--delpi-ui-*` espelhado  
> **Regra:** zero hex solto em componente React; só `var(--pp-*)` / kit

Este documento fixa **como cada tela e peça deve parecer** (cor, contraste, hierarquia) — wireframes coloridos em ASCII + tabela de tokens por superfície.

---

## 1. Legenda de cores (ASCII)

| Símbolo | Token / papel | Claro (fallback) | Escuro |
|---------|---------------|------------------|--------|
| `▓▓` accent | `--pp-accent` | `#089bdb` | primary portal |
| `██` title/navy | `--pp-title` | `#003866` | mix primary+white |
| `░░` soft | `--pp-accent-soft` | accent 12% | accent 18% |
| `··` canvas | `--pp-canvas` | app bg | app bg |
| `▢▢` surface | `--pp-surface` | `#fff` | slate mix |
| `++` success | `--pp-success` | `#15803d` | verde portal |
| `!!` danger | `--pp-danger` | `#b42318` | vermelho portal |
| `??` warning | `--pp-warning` | `#b45309` | âmbar portal |
| `--` muted | `--pp-text-muted` | 70% text | 64% white |
| `WW` on-brand | `--pp-hero-brand-fg` | branco | branco 96% |

```text
Exemplo leitura:
┌─ ▢▢ surface ─────────────────┐
│ ██ título                     │
│ -- meta                       │
│ [▓▓ primary btn]  [ghost]     │
│ ● ++ Online                   │
└───────────────────────────────┘
```

---

## 2. Tokens por papel (mapa rápido)

| Papel UI | Token | Onde |
|----------|-------|------|
| Fundo página | `--pp-canvas` + gradiente 5% accent | `.dashboard-page` |
| Card / tabela / modal body | `--pp-surface` + `--pp-border` | SectionCard, DataTable |
| Título seção / KPI label | `--pp-title` | SectionCard title, KPI |
| Corpo | `--pp-text` | default |
| Meta / timestamp | `--pp-text-muted` | subtítulos |
| CTA primário | `--pp-accent` + texto branco | ActionButton primary |
| Ghost / secondary | border + text | ActionButton ghost |
| Online / OK | `--pp-success` | StatusBadge, chip |
| Offline / erro | `--pp-danger` | StatusBadge, banner |
| Atenção / sem binding | `--pp-warning` | StatusBadge, alert warn |
| Hero admin brand | gradiente title→accent, texto `WW` | PageHero compact |
| BrandBar operador | mesmo gradiente navy→cyan | `.pp-operator-brandbar` |
| Pad + | accent fill | `.pp-operator-pad__btn--plus` |
| Pad − | text / outline | minus |
| Pad Limpar | warning outline | clear |
| Gráfico série | `#089bdb` (= accent) | `ppCharts` / ComparativeAreaChart |
| Anel rotação in_band (P2) | accent / success | `.pp-operator-ring` |
| Anel out_of_band (P2) | danger | ring + banner |
| Meta % barra fill | accent | GoalStrip |
| Alert sticky warn | warning bg soft + border | ALERT |
| Alert sticky danger | danger bg soft + border | ALERT |

---

## 3. Shell admin — WF-PP-00 (visual)

```text
·· canvas + wash accent 5% ··········································
┌─ Sidebar portal (host) ─┬─ MFE ·· ────────────────────────────────┐
│                         │ ┌─ ██▓▓ Brand Hero ───────────────────┐ │
│                         │ │ WW  PULSO DE PRODUÇÃO                 │ │
│                         │ │ WW  Monitoramento IoT…                │ │
│                         │ │ [WW ghost Filial] [WW ghost Poll]     │ │
│                         │ └───────────────────────────────────────┘ │
│                         │ ▢▢ conteúdo (KPI / tabela / form)         │
└─────────────────────────┴───────────────────────────────────────────┘
```

| Elemento | Fundo | Texto | Borda |
|----------|-------|-------|-------|
| PageHero | gradiente `--pp-title` → mix accent | `--pp-hero-brand-fg` | accent 28% |
| Botão hero ghost | `hero-brand-btn-bg` | WW | `hero-brand-btn-border` |
| Área conteúdo | canvas | text | — |

---

## 4. Painel — WF-PP-01 (visual)

```text
···
┌─ Hero ██▓▓ ───────────────────────────────────────────────────────┐
└───────────────────────────────────────────────────────────────────┘
┌─ ▢▢ KPI ──┐ ┌─ ▢▢ KPI ──┐ ┌─ ▢▢ KPI ──┐ ┌─ ▢▢ KPI ──┐
│ ░░ ícone  │ │ ░░ ++     │ │ ░░ !!     │ │ ░░ ??     │
│ -- Total  │ │ -- Online │ │ -- Offline│ │ -- Sem am.│
│ ██ 12     │ │ ++ 9      │ │ !! 2      │ │ ?? 1      │
└───────────┘ └───────────┘ └───────────┘ └───────────┘
┌─ ▢▢ FiltersRow ───────────────────────────────────────────────────┐
│ ··· busca ···  [Select]  [▓▓ SC|ES]  [ghost Limpar]               │
└───────────────────────────────────────────────────────────────────┘
┌─ ▢▢ DataTable ────────────────────────────────────────────────────┐
│ header --muted / border                                           │
│ row: nome ██ · badge âncora ░░ · ● ++ · métrica -- · [ghost]      │
└───────────────────────────────────────────────────────────────────┘
```

**KPI icon wells:** fundo `--pp-accent-soft`; online/offline/warning usam cor semântica no valor.

**DeviceCard (mobile):** surface; faixa esquerda 3px = status (success/danger/warning/muted).

---

## 5. Formulário — WF-PP-02 (visual)

```text
···
┌─ Hero + BackLink -- ──────────────────────────────────────────────┐
└───────────────────────────────────────────────────────────────────┘
┌─ ▢▢ Section Dispositivo ──────────────────────────────────────────┐
│ ██ Dispositivo                                                     │
│ -- intro                                                           │
│ [fields surface inputs · border · focus ▓▓ ring]                   │
└───────────────────────────────────────────────────────────────────┘
┌─ ▢▢ Section Onde está ────────────────────────────────────────────┐
│ Segmented: [▓▓ ativo] [ghost] [ghost] …                            │
│ campos condicionais                                                │
│ <details TOTVS> --muted                                            │
└───────────────────────────────────────────────────────────────────┘
┌─ sticky footer ▢▢ / border-top ───────────────────────────────────┐
│ [ghost Cancelar]                          [▓▓ Salvar]             │
└───────────────────────────────────────────────────────────────────┘
```

| Estado campo | Visual |
|--------------|--------|
| Default | border `--pp-border`, bg surface |
| Focus | outline/ring accent |
| Erro | border danger + texto danger (mensagem validation JSON) |
| Switch enabled | track accent quando on |

---

## 6. Detalhe device — WF-PP-03 (visual)

```text
···
┌─ Hero ██▓▓ · device name WW · ● ++ Online ────────────────────────┐
│ [WW Poll] [WW Editar] …                                            │
└────────────────────────────────────────────────────────────────────┘
┌─ UnderlineNav ▢▢ ─────────────────────────────────────────────────┐
│ [▓▓ Visão geral]  [-- Histórico]  [-- Comandos]                   │
└────────────────────────────────────────────────────────────────────┘

Overview:
┌─ ▢▢ MetricHero ─────────────┐  ┌─ ▢▢ Binding card ──────────────┐
│ ██ valor grande (kpi size)  │  │ âncora badge ░░                 │
│ -- unidade / sync           │  │ -- placement_label              │
│ [▓▓ +] [ghost −] [?? Limpar]│  │                                 │
└─────────────────────────────┘  └─────────────────────────────────┘
┌─ ▢▢ Chip health -- ───────────────────────────────────────────────┐
│ firmware · uptime · rssi (muted values)                            │
└────────────────────────────────────────────────────────────────────┘
┌─ ▢▢ ChartCard ────────────────────────────────────────────────────┐
│ título ██ · série ▓▓ area fill soft                                │
└────────────────────────────────────────────────────────────────────┘

Histórico:
┌─ presets segment [▓▓] [ghost] … · datetime-local ─────────────────┐
┌─ ▢▢ chart ▓▓ ─────────────────────────────────────────────────────┐
┌─ ▢▢ tabela / ReadingCard ─────────────────────────────────────────┘
```

| Aba ativa | Underline / cor texto accent |
| Aba inativa | muted |
| Chip health ok | success tint no valor wifi |
| Hardware reset badge | warning soft |

---

## 7. Modais — WF-PP-04 (visual)

```text
···· dim host (portal) ····
    ┌─ ▢▢ Dialog max ~520px ─────────────────────────────┐
    │ ██ Título                                           │
    │ -- corpo                                            │
    │ [ghost Cancelar]              [▓▓ Confirmar]        │
    │                              ou [!! Desativar]      │
    └─────────────────────────────────────────────────────┘
```

Ações destrutivas (desativar / factory): botão **danger** ou warning, nunca accent.

---

## 8. Operador — BrandBar + hub (WF-PP-OP-HUB)

```text
┌─ ██▓▓ BrandBar full width ────────────────────────────────────────┐
│ WW  PULSO · Operador          [WW Trocar] [WW Admin?]             │
└───────────────────────────────────────────────────────────────────┘
·· canvas operador (pode ser mais “palco”: radial accent 8%) ··
┌─ segment filtros [▓▓ Todos] [ghost Postos] …  ··· busca ···      ┐
│                                                                   │
│  ┌─ ▢▢ hub card ──────────┐  ┌─ ▢▢ hub card ──────────┐          │
│  │ ██ CT-53 / label       │  │ ██ Ventilador A        │          │
│  │ badge âncora ░░        │  │ ● ++ 2 online          │          │
│  │ -- 2 cont · 1 sensor   │  │ ?? 1 atenção (P2)      │          │
│  │ min-h touch 128px      │  │                        │          │
│  └────────────────────────┘  └────────────────────────┘          │
```

| Card hover | border accent soft + shadow title 16% |
| Card pressed | scale leve (motion safe) |
| Empty state | muted text + surface |

---

## 9. Operador — picker (WF-PP-OP-PICK)

```text
BrandBar ██▓▓ …
┌─ ▢▢ device card ─────────────────────────────────────────────────┐
│ [badge Contador ░░]  Prensa A #1                                  │
│ ● ++ Online · ██ 1.284 golpes                                     │
└───────────────────────────────────────────────────────────────────┘
┌─ ▢▢ device card ─────────────────────────────────────────────────┐
│ [badge Sensor ░░]  Fusos                                          │
│ ● ++ · ██ 1.850 rpm                                               │
└───────────────────────────────────────────────────────────────────┘
```

Badge role: fundo accent-soft (contador) / success-soft (sensor) — ver DESIGN §1.4 / badges role.

---

## 10. Operador — contador (WF-PP-OP-01)

```text
BrandBar ██▓▓ · placement WW · ● ++ Online -- sync
·· palco radial accent ··
              ┌─ stage ▢▢ / glow ++ se online ─────────┐
              │                                        │
              │           ██ 1.284                     │  ← --pp-operator-counter-value
              │           -- golpes                    │
              │   (P2) meta ▓▓░░░░ 70%  -- faltam…     │
              │                                        │
              └────────────────────────────────────────┘
     ┌─ pad − ──┐   ┌─ pad Limpar ─┐   ┌─ pad + ▓▓ ─┐
     │  outline  │   │  ?? warning  │   │  fill accent│
     │  text ██  │   │  outline     │  │  texto WW   │
     └───────────┘   └──────────────┘   └────────────┘
              [ghost Sincronizar] --
```

| Peça | Cor |
|------|-----|
| Valor contador | `--pp-title` (claro) / accent-mix (dark) |
| Anel online | box-shadow success pulse |
| Banner offline | danger soft + texto danger |
| Modal limpar | ver §7 warning confirm |

---

## 11. Operador — gauge (WF-PP-OP-GAUGE)

```text
BrandBar …
┌─ ▢▢ tile ─────────────────┐  ┌─ ▢▢ tile ─────────────────┐
│      ██ 1.850             │  │      ██ 67,2               │
│      -- rpm               │  │      -- °C                 │
│  (warn: border ??)        │  │  (danger: border !!)       │
└───────────────────────────┘  └───────────────────────────┘
              [ghost Atualizar]
```

Thresholds: borda/valor em warning ou danger conforme `capabilities.thresholds` (API); fundo tile permanece surface.

---

## 12. Operador P2 — temperatura / rotação / combo / alert / meta

### TEMP

```text
  !! sticky banner danger soft (se danger)
           ██ 72,4 °C
           -- margem
     ▓▓▓▓▓▓▓▓▓▓░░░░  barra até teto (accent ou danger se perto)
```

### ROTATION

```text
        ╭─ anel ▓▓ (in_band) / !! (out) ─╮
        │         ██ 1.850 rpm            │
        ╰─────────────────────────────────╯
        ▢▢ tile °C secundário
```

### COMBO board

```text
BrandBar · -- 3 online · ?? 1 atenção
┌─ card ++/!! border by alert ─┐ …
│ role badge · valor ██ · mini ▓▓% │
```

### ALERT sticky

| Nível | Fundo | Borda | Texto |
|-------|-------|-------|-------|
| warn | warning 12% | warning | title/text |
| danger | danger 12% | danger | title/text |
| stale | muted 8% | border | muted |

### GOAL strip

```text
-- Meta 1.200 · 70%
▓▓▓▓▓▓▓▓▓▓▓░░░░  fill accent · track border soft
```

---

## 13. Componentes — ficha visual

| Componente | Surface | Accent / ênfase | Estados especiais |
|------------|---------|-----------------|-------------------|
| `PageHero` | brand gradient | WW text | — |
| `ProductionPulsePageHero` | idem | FilialSwitcher ghost WW | — |
| `KpiCard` / Pp KPI | surface | accent-soft icon well | valor semântico |
| `PpFiltersRow` | surface/transparent | focus accent | — |
| `PpDataTable` | surface | header muted | row hover soft |
| `DeviceCard` | surface | status rail | — |
| `PpSectionCard` | surface | title color | — |
| `PpChartCard` + area | surface | série accent | empty muted |
| `UnderlineNav` | surface | active accent | — |
| `StatusBadge` | soft tint | success/danger/warning/muted | — |
| `AnchorTypeBadge` | mix por tipo | §1.4 DESIGN | — |
| `PpHostContainedDialog` | surface | primary/danger CTA | dim host |
| `OperatorBrandBar` | brand gradient | WW | — |
| `Operator hub/pick cards` | surface | hover accent | alert chip P2 |
| `OperatorCounterStage` | surface + glow | title number | online pulse |
| `OperatorActionPad` | — | + accent / clear warning | disabled muted |
| `OperatorGaugeStage` | surface tiles | threshold border | — |
| `OperatorAlertBanner` | soft semântico | — | sticky |
| `OperatorGoalStrip` | transparent | bar accent | at_risk → warning fill |

---

## 14. Claro × escuro (checklist)

| Token | Claro | Escuro (`:root[data-theme="dark"]`) |
|-------|-------|-------------------------------------|
| `--pp-surface` | branco | slate mix |
| `--pp-text` | quase preto | white 88% |
| `--pp-text-muted` | 70% | white 64% |
| `--pp-border` | `#e6e6e6` | white 12% |
| `--pp-title` | navy | primary mix white |
| Brand hero | navy→cyan | mesma lógica, botões WW |
| Success/danger/warning | tokens portal | idem (não inverter semântica) |

**Não fazer:** fundo escuro forçado no MFE fora do `data-theme` do portal; purple glow; cards no hero.

---

## 15. Contraste e touch

| Elemento | Mínimo |
|----------|--------|
| Texto corpo em surface | AA vs `--pp-surface` |
| WW em BrandBar | sobre navy/cyan (já contrastado) |
| Alvo touch operador | ≥ 44px (`--pp-operator-touch-min`) |
| Pad botões | altura token `--pp-operator-pad-height` |

---

## 16. Relação com outros docs

| Precisa de… | Doc |
|-------------|-----|
| Estrutura de layout / rotas | [WIREFRAMES.md](./WIREFRAMES.md) |
| Tokens e kit inventory | [DESIGN-FRONTEND.md](./DESIGN-FRONTEND.md) |
| Surfaces P2 comportamento | [OPERATOR-SURFACES-P2.md](./OPERATOR-SURFACES-P2.md) |
| Implementação CSS | `plugins/production-pulse/src/index.css` |

---

## 17. Critério de pronto (visual)

- [ ] Toda cor nova é token `--pp-*` (ou kit) — grep hex em `components/` = 0 (exceto chart series canônica documentada)
- [ ] Status online/offline/warn usam só success/danger/warning
- [ ] Operador e admin respeitam `data-theme` dark do portal
- [ ] P2 TEMP/ROTATION/COMBO/ALERT/GOAL seguem §12 sem inventar paleta paralela
