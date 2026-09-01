# Wireframes — Production Pulse (Pulso de Produção)

> **Id:** `production-pulse` · **basePath:** `/apps/production-pulse`  
> **Design:** [DESIGN-FRONTEND.md](./DESIGN-FRONTEND.md) · **API:** [ESPECIFICACAO-PLUGIN.md](./ESPECIFICACAO-PLUGIN.md)  
> **Helps:** [HELP-CONTENT.md](./HELP-CONTENT.md) · catálogo [`content/helpTooltips.ts`](./content/helpTooltips.ts) (`PP_HELP`)  
> **Kit:** `@delpi/plugin-ui` · modais host-contained

---

## Convenções

| Símbolo | Significado |
|---------|-------------|
| `[Botão]` | `ActionButton` |
| `[ghost]` | variant ghost |
| `[primary]` | variant primary |
| `·····` | input / busca |
| `●` / `○` | online / offline |
| `│ ░░░ │` | skeleton |
| `†` | gate permissão |
| `▼` | seção expansível |
| `?` | help hover (`FieldLabel` / `SectionHintLabel` → chave `PP_HELP.*`) |

**Layout:** sidebar Minha DELPI à esquerda (portal). Root MFE `.dashboard-production-pulse.dashboard-page`.

### Breakpoints (todas as telas admin)

| Faixa | Largura | Regra geral |
|-------|---------|-------------|
| Desktop | `> 1100px` | Layout de referência nos wireframes «A» |
| **Tablet** | **`769px – 1100px`** | KPI 2×2; filtros em 2 linhas; tabela compacta ou scroll; form 1 col; operador grid 2–3 col |
| **Mobile** | **`≤ 768px`** | Hero coluna; KPI 1 col; tabela → **cards**; form sticky footer; padding `--pp-page-padding` 16px |
| Operador narrow | `≤ 600px` | Hub/picker 1 col; pad contador empilhado (+ full width primeiro) |

Cada tela inclui subseções **`tablet (769–1100px)`** e **`mobile (≤768px)`** com ASCII. CSS: [DESIGN-FRONTEND §7](./DESIGN-FRONTEND.md#7-responsividade).

**Tablet — portrait vs landscape (operador e painel):**

| Orientação | Largura típica | Ajuste extra |
|------------|----------------|--------------|
| Tablet portrait | 769–834px | Painel: tabela scroll ou ocultar coluna «Última»; hub **2 col** |
| Tablet landscape | 900–1100px | Painel: tabela 6 col visíveis; hub **3 col**; detalhe overview 2 col |

---

## Matriz responsiva — rota × wireframe

| Rota | Desktop (`>1100`) | Tablet (`769–1100`) | Mobile (`≤768`) |
|------|-------------------|---------------------|-----------------|
| `/` (painel) | WF-PP-01-A/B | **WF-PP-01 tablet** — KPI 2×2 · tabela compacta | WF-PP-01 mobile — DeviceCard |
| `/devices/new`, `/edit` | WF-PP-02 | **WF-PP-02 tablet** — 1 col · segmented wrap | WF-PP-02 mobile — sticky footer |
| `/devices/:id` | WF-PP-03-A/B/C | **WF-PP-03 tablet** — overview 2 col ≥900px | WF-PP-03 mobile — ReadingCard |
| Modais | WF-PP-04 | **WF-PP-04 tablet** — max 520px | WF-PP-04 mobile — stack `<360px` |
| `/operator` | WF-PP-OP-HUB | **WF-PP-OP-HUB tablet** — grid 2–3 col | WF-PP-OP-HUB mobile — 1 col |
| `/operator/placements/:key` | WF-PP-OP-PICK | **WF-PP-OP-PICK tablet** — grid 2 col | WF-PP-OP-PICK mobile — stack |
| `/operator/devices/:id` contador | WF-PP-OP-01 | **WF-PP-OP-01** (referência tablet) | WF-PP-OP-02 portrait |
| `/operator/devices/:id` gauge | WF-PP-OP-GAUGE | **WF-PP-OP-GAUGE tablet** — métricas 2 col | WF-PP-OP-GAUGE mobile — stack |
| Shell | WF-PP-00 | **WF-PP-00 tablet** — hero wrap | WF-PP-00 mobile — hero coluna |

---

| Rota | WF | Menu | Permissão |
|------|-----|------|-----------|
| `/apps/production-pulse` | WF-PP-01 | sim · «Pulso de Produção» | `access` + `devices.view` |
| `/apps/production-pulse/devices/new` | WF-PP-02 | não | `devices.manage` |
| `/apps/production-pulse/devices/:id` | WF-PP-03 | não | `devices.view` |
| `/apps/production-pulse/devices/:id/edit` | WF-PP-02 | não | `devices.manage` |
| `/apps/production-pulse/operator` | **WF-PP-OP-HUB** | sim† «Operador · Pulso» | `operator` |
| `/apps/production-pulse/operator/placements/:placementKey` | **WF-PP-OP-PICK** | não | picker devices |
| `/apps/production-pulse/operator/devices/:deviceId` | **WF-PP-OP** / **GAUGE** | não | superfície driver |

Rotas legado: redirect **308** — ver [ADR-004-routes-and-legacy-aliases.md](./ADR-004-routes-and-legacy-aliases.md).

---

## WF-PP-00 — Shell comum (template)

Todas as páginas internas (exceto redirect inicial).

```text
┌─ Sidebar Portal ─┬─ Área MFE .dashboard-production-pulse ─────────────────────────────┐
│ Minha DELPI      │ ┌─ PageHero compact ────────────────────────────────────────────┐ │
│ …                │ │ PULSO DE PRODUÇÃO                                               │ │
│ ► Pulso Produção │ │ Monitoramento IoT — dispositivos, sensores e postos de trabalho     │ │
│                  │ │ Filial: [Santa Catarina ▼]              [ghost Atualizar tudo]† │ │
│                  │ └─────────────────────────────────────────────────────────────────┘ │
│                  │ ┌─ conteúdo da rota (WF-PP-01 / 02 / 03) ────────────────────────┐ │
│                  │ │                                                                 │ │
│                  │ └─────────────────────────────────────────────────────────────────┘ │
└──────────────────┴─────────────────────────────────────────────────────────────────────┘
```

**Componentes:** `ProductionPulsePageHero` → wrapper `PageHero` density=`compact`.  
**Filial:** `FilialSwitcher` compact no `children` do hero (se >1 filial permitida).  
**Atualizar tudo:** `POST /devices/poll-all` — visível só com `devices.manage`†.

**Helps (`PP_HELP`):** `shell.heroTitle` · `shell.heroFilial` · `shell.pollAll` · ver [HELP-CONTENT § WF-PP-00](./HELP-CONTENT.md#wf-pp-00--shell-productionpulsepagehero).

### WF-PP-00 tablet (769–1100px)

Sidebar portal **estreita** (ícones) ou colapsável — área MFE ~`calc(100% - 64px)` a ~`780px`.

```text
┌─ Sidebar ─┬─ Área MFE ─────────────────────────────────────────┐
│ (icons)   │ ┌─ PageHero compact ─────────────────────────────┐ │
│           │ │ PULSO DE PRODUÇÃO                              │ │
│           │ │ Monitoramento IoT…                             │ │
│           │ │ Filial [SC ▼]     [ghost Atualizar tudo]†      │ │
│           │ │        ↑ wrap em 2ª linha se <900px            │ │
│           │ └────────────────────────────────────────────────┘ │
│           │ conteúdo rota (tablet variant)                       │
└───────────┴──────────────────────────────────────────────────────┘
```

- **769–900px:** filial e «Atualizar tudo» na **segunda linha** do hero (flex-wrap).
- **901–1100px:** mesma linha do desktop, botões compactos.
- Padding: `20px` (`--pp-page-padding` intermediário).

### WF-PP-00 mobile (≤768px)

Sidebar do portal colapsada (hamburger). Área MFE ocupa **100%** da viewport útil.

```text
┌─ Área MFE (full width) ─────────────────────────────┐
│ ┌─ PageHero compact — coluna ─────────────────────┐ │
│ │ PULSO DE PRODUÇÃO                               │ │
│ │ Monitoramento IoT…                              │ │
│ │ Filial: [Santa Catarina ▼]  ← linha própria     │ │
│ │ [ghost Atualizar tudo]†     ← full width ou 50% │ │
│ └─────────────────────────────────────────────────┘ │
│ ┌─ conteúdo rota ────────────────────────────────┐ │
│ │ (WF-PP-01 / 02 / 03 mobile)                    │ │
│ └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

- Hero: título + subtítulo empilhados; `FilialSwitcher` **abaixo** do título (não inline).
- `[Atualizar tudo]`: `width: 100%` ou par com link «Modo operador» em 2 colunas 50/50.
- Padding página: `16px`; sem scroll horizontal no hero.

---

## WF-PP-01 — Painel operacional

**Rota:** `/apps/production-pulse`  
**API:** `GET /summary`, `GET /devices`  
**Objetivo:** visão consolidada de **dispositivos**; lista ou agrupamento por âncora (CT, máquina, equipamento).

### WF-PP-01-A — Vista lista (default)

```text
┌─ KPI strip (grid 4) ────────────────────────────────────────────────────────────────┐
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                      │
│ │ [Cpu] Total │ │ [Wifi] On   │ │ [WifiOff]   │ │ [Link2Off]  │                      │
│ │     14      │ │     11 ●    │ │   Off  2 ○  │ │ Sem amarr. 1│                      │
│ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘                      │
└──────────────────────────────────────────────────────────────────────────────────────┘

┌─ FilterBarShell ─────────────────────────────────────────────────────────────────────┐
│ Tipo · [Todos ▼]  Âncora · [Todos ▼]  Status · [Todos ▼]  Busca ···················· │
│ Papel · [Todos ▼]              [Lista | Agrupado ▼]    [primary + Novo dispositivo]† │
└──────────────────────────────────────────────────────────────────────────────────────┘

┌─ DataTableSection «Dispositivos» ───────────────────────────────────────────────────┐
│ Nome          │ Objeto           │ Papel    │ Métrica   │ Status │ Última │ ⋮ │
│───────────────┼──────────────────┼──────────┼───────────┼────────┼────────┼───│
│ ESP prensa A  │ CT-53 · Usinagem │ Contador │ 1.284 gol │ ● On   │ 12 s   │ ⋮ │
│ ESP vent A    │ Ventilador ex. A │ Sensor   │ 1180 rpm  │ ● On   │ 8 s    │ ⋮ │
│ ESP motor B   │ Motor bomba #2   │ Sensor   │ 67,2 °C   │ ○ Off  │ 4 min  │ ⋮ │
│ (rascunho)    │ —                │ —        │ —         │ ⚠ Sem  │ —      │ ⋮ │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

**Colunas tabela:**

| Coluna | Campo API | Notas |
|--------|-----------|-------|
| Nome | `device.name` | Link → `/devices/:id` |
| Objeto | `binding.placement_label` + badge `anchor_type` | «—» se rascunho |
| Papel | `device.role_key` | Contador / Sensor / Telemetria |
| Métrica | `last_metrics[primary]` | Unidade do registry; tabular-nums |
| Status | derivado | `DeviceStatusBadge` |
| Última leitura | `last_seen_at` | relativo + tooltip ISO |
| ⋮ menu | — | Ver · Editar† · Poll · Reset† |

**Menu linha (IconButton ou dropdown kit):**

| Ação | Perm | API |
|------|------|-----|
| Ver detalhe | view | navigate |
| Editar | manage | `/devices/:id/edit` |
| Atualizar agora | view | `POST .../poll` |
| Reset contador | command | modal WF-PP-04-A |

**Query URL:** `?branch=01&status=online&anchorType=equipment&role=process_gauge&view=list&page=1`

**Helps (`PP_HELP`):** KPIs `panel.kpi*` · filtros `panel.filter*` · colunas `panel.col*` · ações `panel.row*` · vazios `panel.empty*` · badges `badges.*` — mapa completo em [HELP-CONTENT § WF-PP-01](./HELP-CONTENT.md#wf-pp-01--painel).

### WF-PP-01-B — Vista agrupada

Toggle `[Lista | Agrupado ▼]` — seletor **agrupar por:** Posto (CT) | Máquina | Equipamento | Área.

```text
▼ CT-53 · Usinagem CNC — [Posto] — 2 devices · 2 online
│ ESP prensa A #1  │ 1.284 gol │ ● On │
│ ESP prensa A #2  │   892 gol │ ● On │

▼ Ventilador exaustão setor A — [Equipamento] — 1 device · 1 online
│ ESP vent A       │ 1180 rpm  │ ● On │

▶ Sem amarração — 1 device (colapsado)
```

**Implementação:** `pp-placement-group` — cabeçalho com `AnchorTypeBadge` + meta online.

### WF-PP-01-B2 — Vista agrupada (legado só CT)

Equivalente ao agrupador anterior quando `groupBy=work_center` — ver PCP-style groups.

### WF-PP-01-C — Estados

**Loading inicial**

```text
│ KPI │ │ ░░░ │ │ ░░░ │ │ ░░░ │ │ ░░░ │
│ FilterBar skeleton │
│ DataTable 5 linhas skeleton │
```

**Empty — filial sem devices**

```text
┌─ EmptyGuidance ─────────────────────────────────────┐
│        [Cpu ilustração]                              │
│   Nenhum dispositivo cadastrado nesta filial         │
│   Cadastre sensores e contadores IoT — postos,       │
│   máquinas ou equipamentos.                          │
│              [primary Cadastrar dispositivo]†        │
└──────────────────────────────────────────────────────┘
```

**Empty — filtros sem resultado:** `EmptyState` «Nenhum dispositivo com esses filtros» + `[ghost Limpar filtros]`.

**Erro API:** `StateBox` vermelho + `[ghost Tentar novamente]`.

**403 filial:** `StateBox` «Sem permissão para esta filial».

### WF-PP-01 tablet (769–1100px)

**KPI:** grid **2×2** (4 cards em duas linhas).

```text
┌─ KPI 2×2 ─────────────────────────────────────────┐
│ [Cpu] Total 14      │ [Wifi] Online 11 ●          │
├─────────────────────┼─────────────────────────────┤
│ [WifiOff] Off 2 ○   │ [Link2Off] Sem amarr. 1     │
└─────────────────────┴─────────────────────────────┘
```

**Filtros:** duas linhas (wrap nativo `FilterBarShell`).

```text
┌─ FilterBar tablet ────────────────────────────────────────────────┐
│ Tipo [▼]  Status [▼]  Papel [▼]  Busca ························ │
│ [Lista | Agrupado ▼]                    [primary + Novo device]†   │
└───────────────────────────────────────────────────────────────────┘
```

**Tabela compacta** — manter `DataTable` (não cards); estratégia por largura:

| Largura | Colunas visíveis | Ocultas (tooltip no row expand ou ⋮) |
|---------|------------------|--------------------------------------|
| 901–1100px | Nome · Objeto · Papel · Métrica · Status · ⋮ | «Última leitura» → tooltip no status |
| 769–900px | Nome · Objeto · Métrica · Status · ⋮ | Papel → badge no nome; scroll horizontal **fallback** |

```text
┌─ DataTableSection (scroll-x se 769–900) ──────────────────────────┐
│ Nome         │ Objeto        │ Métrica  │ Status │ ⋮ │
│ ESP prensa A │ CT-53…        │ 1.284 gol│ ● On   │ ⋮ │
└───────────────────────────────────────────────────────────────────┘
```

**Vista agrupada tablet:** igual desktop; linhas do grupo com colunas reduzidas (3 col: nome · métrica · status).

**Novo dispositivo:** label curto «+ Novo» abaixo de 900px (ícone + texto).

### WF-PP-01 mobile (≤768px)

**KPI:** grid `1 coluna` — cards empilhados (ou carrossel horizontal swipe P2).

```text
┌─ KPI (1 col) ─────────────────────┐
│ [Cpu] Total          14           │
├───────────────────────────────────┤
│ [Wifi] Online        11 ●         │
├───────────────────────────────────┤
│ [WifiOff] Offline     2 ○         │
├───────────────────────────────────┤
│ [Link2Off] Sem amarr. 1           │
└───────────────────────────────────┘
```

**Filtros:** barra compacta + sheet/drawer «Filtros» (padrão kit `FilterBarShell` mobile).

```text
┌─ FilterBar mobile ────────────────────────────────┐
│ ····· Buscar dispositivo ·········    [≡ Filtros] │
│ [Lista | Agrupado]              [+ Novo]† (icon)  │
└───────────────────────────────────────────────────┘
```

Sheet «Filtros»: Tipo amarração · Papel · Status · Agrupar por — botões `[Aplicar]` `[Limpar]`.

**Lista → cards** (`.pp-device-card` — substitui `DataTable`):

```text
┌─ DeviceCard ──────────────────────────────────────┐
│ ESP prensa A #1                    ● Online    ⋮ │
│ CT-53 · Usinagem CNC          [Posto]            │
│ Contador · 1.284 golpes · há 12 s                │
│ [ghost Ver]  [ghost Poll]                        │
└──────────────────────────────────────────────────┘
┌─ DeviceCard ──────────────────────────────────────┐
│ ESP vent A                         ● Online    ⋮ │
│ Ventilador exaustão A         [Equipamento]      │
│ Sensor · 1180 rpm · há 8 s                       │
└──────────────────────────────────────────────────┘
```

- Tap no card → detalhe; `⋮` → menu linha (Editar† · Poll · Reset†).
- Métrica + status na mesma linha; badge `anchor_type` abaixo do placement.
- Paginação: `CompactPagination` full width no rodapé.

**Vista agrupada mobile:** acordeões full width — mesmo conteúdo WF-PP-01-B; dentro de cada grupo, **mini-cards** (não tabela).

```text
▼ CT-53 · Usinagem CNC — 2 online
  ┌─ mini-card ─ ESP prensa A · 1.284 gol · ● ┐
  └─ mini-card ─ ESP prensa A #2 · 892 · ● ┘
▶ Sem amarração — 1 device
```

**Empty / erro:** igual desktop; CTA `[Cadastrar]` full width.

---

## WF-PP-02 — Cadastro / edição de dispositivo

**Rotas:**  
- Criar: `/apps/production-pulse/devices/new?branch=01`  
- Editar: `/apps/production-pulse/devices/:id/edit`

**API:** `POST /devices`, `PUT /devices/:id`, `PUT /devices/:id/binding`, **`POST /devices/test-probe`** (novo) · `POST /devices/{id}/test` (edit)

```text
┌─ PageHero compact ──────────────────────────────────────────────────────────────────┐
│ ← Voltar (BackLink)                                                                 │
│ NOVO DISPOSITIVO                                                                    │
│ Cadastro do hardware e onde o sensor está instalado                                 │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─ SectionCard «Dispositivo IoT» ─────────────────────────────────────────────────────┐
│ Nome do dispositivo * ····· ESP ventilador setor A ································  │
│ Filial *            [Santa Catarina (01) ▼]                                           │
│ Endereço IP *       ····· 192.168.20.15 ·········  [ghost Testar conexão]†           │
│ Driver *            [ESP8266 sensores processo v1 ▼]  Preview: rpm · °C · leitura   │
│ Intervalo poll (s) *  ····· 30 ·········                                              │
│ [toggle] Dispositivo ativo                                                            │
└──────────────────────────────────────────────────────────────────────────────────────┘

┌─ SectionCard «Onde está instalado» ───────────────────────────────────────────────────┐
│ Tipo de amarração *   ( ) Posto PCP (CT)  (•) Equipamento  ( ) Máquina  ( ) Área     │
│                                                                                       │
│ ── Equipamento (obrigatório neste tipo) ──                                            │
│ Nome do equipamento * ····· Ventilador exaustão setor A ····························  │
│                                                                                       │
│ ▼ Vincular ao TOTVS (opcional — atalho PCP)                                          │
│   Centro de trabalho    ····· (vazio) ·····  SelectField search async                 │
│   Recurso / Ferramenta  ····· (opcional) ·····                                        │
└──────────────────────────────────────────────────────────────────────────────────────┘

┌─ Exemplo alternativo: tipo «Máquina» ────────────────────────────────────────────────┐
│ Tipo *  ( ) Posto  (•) Máquina  ( ) Equipamento                                       │
│ Máquina * ····· Motor bomba recirculação #2 ········································  │
│ Driver: gauge → mede temperatura do motor                                             │
└──────────────────────────────────────────────────────────────────────────────────────┘

                                    [ghost Cancelar]  [primary Salvar]†
```

### Comportamentos formulário

| Campo | Validação UI | Erro |
|-------|--------------|------|
| Nome | required, max 120 | inline FieldLabel |
| IP | IPv4 regex | «IP inválido» |
| Filial | required | — |
| CT | required se `anchor_type=work_center`; **opcional** nos demais | 422 API se CT inválido quando preenchido |
| Poll interval | 5–300 | clamp + message |

**Testar conexão** (ghost, ao lado IP):

1. Click → `InlineLoadingProgress` no botão  
2. **Novo:** `POST /devices/test-probe` `{ branch, ip_address, driver_key }` — sem gravar device  
3. **Edit:** `POST /devices/{id}/test`  
4. Sucesso → toast: «Conectado · golpes: 42» ou métricas conforme driver + `latencyMs`  
5. Falha → inline vermelho: `error` / `last_error`

**Salvar:**

- Create: `POST /devices` + `PUT binding` se CT preenchido  
- Redirect: `/devices/:id` (detalhe) ou painel se rascunho sem CT  
- 409 IP duplicado → highlight campo IP

**Edit:** filial read-only; IP editável com re-test; `enabled` toggle.

**Helps (`PP_HELP`):** seções `form.sectionDevice` · `form.sectionPlacement` · `form.sectionTotvs` · cada campo `form.*` (nome, IP, driver, anchor types, TOTVS opcional) — ver [HELP-CONTENT § WF-PP-02](./HELP-CONTENT.md#wf-pp-02--formulário-deviceform--devicebindingsection).

**Copy visível (abaixo do título):** «Informe o hardware na rede…» · «Onde o sensor está instalado…» — ver [HELP-CONTENT § textos de seção](./HELP-CONTENT.md#textos-de-seção-copy-visível-não-só-tooltip).

### WF-PP-02 tablet (769–1100px)

Formulário **1 coluna** centralizada `max-width: 720px` (não 2 col como desktop wide).

```text
┌─ PageHero ──────────────────────────────────────────┐
│ ← Voltar · NOVO DISPOSITIVO                         │
└─────────────────────────────────────────────────────┘
┌─ SectionCard «Dispositivo IoT» (max-w 720px) ───────┐
│ Nome * ············································ │
│ Filial * [SC ▼]    IP * ·········  [Testar]†        │
│        ↑ 769–900: IP + Testar em linha própria      │
│ Driver * [▼]  Preview rpm · °C                      │
│ Poll * ·· 30 ··   [toggle] Ativo                    │
└─────────────────────────────────────────────────────┘
┌─ SectionCard «Onde está instalado» ─────────────────┐
│ Tipo *  ( )Posto (•)Equip ( )Máq ( )Área ( )Avulso  │
│         ↑ segmented horizontal **wrap** 2 linhas    │
│ Nome equipamento * ································ │
│ ▼ TOTVS opcional                                    │
└─────────────────────────────────────────────────────┘
              [Cancelar]  [Salvar]†  ← footer fixo no fim do scroll, não sticky
```

| Elemento | Tablet |
|----------|--------|
| Largura form | `max-width: 720px`; margin auto |
| IP + Testar | Lado a lado ≥901px; empilhados 769–900px |
| Segmented | Horizontal com wrap (2 linhas max) |
| Footer | Botões alinhados à direita; **sem** sticky (só mobile) |
| Padding | `20px` |

### WF-PP-02 mobile (≤768px)

Cards empilhados; botões `[Cancelar][Salvar]` **sticky footer** `.pp-form-footer` (safe-area-inset-bottom).

```text
┌─ full width ──────────────────────────────────────┐
│ ← Voltar                                          │
│ NOVO DISPOSITIVO                                  │
│ Cadastro do hardware…                             │
├───────────────────────────────────────────────────┤
│ ┌─ SectionCard «Dispositivo IoT» ───────────────┐ │
│ │ Nome * ······································· │ │
│ │ Filial * [SC (01) ▼]                           │ │
│ │ IP * ········································· │ │
│ │ [ghost Testar conexão]†  ← full width        │ │
│ │ Driver * [ESP8266… ▼]                          │ │
│ │ Preview: rpm · °C                              │ │
│ │ Poll (s) * ··· 30 ···                          │ │
│ │ [toggle] Ativo                                 │ │
│ └────────────────────────────────────────────────┘ │
│ ┌─ SectionCard «Onde está instalado» ────────────┐ │
│ │ Tipo *  ← segmented **vertical** (stack)     │ │
│ │ ( ) Posto PCP                                  │ │
│ │ (•) Equipamento                                │ │
│ │ ( ) Máquina                                    │ │
│ │ ( ) Área                                       │ │
│ │ Nome equipamento * ··························· │ │
│ │ ▼ TOTVS (opcional) — `<details>` colapsado   │ │
│ └────────────────────────────────────────────────┘ │
│              (scroll — padding-bottom 88px)        │
├─ sticky .pp-form-footer ──────────────────────────┤
│ [ghost Cancelar]          [primary Salvar]†      │
└───────────────────────────────────────────────────┘
```

| Elemento | Mobile |
|----------|--------|
| `AnchorTypeSegmented` | Opções **empilhadas** (radio list), não horizontal |
| Testar conexão | Botão **abaixo** do IP, largura total |
| TOTVS `<details>` | Fechado por default — economiza scroll |
| Filial (edit) | Read-only, texto simples |
| Validação | Erros inline; scrollIntoView no primeiro erro |

---

## WF-PP-03 — Detalhe do dispositivo (abas)

**Rota:** `/apps/production-pulse/devices/:id?tab=overview|history|commands`  
**API:** `GET /devices/:id`, `/live`, `/readings`, `/commands`

```text
┌─ PageHero compact ──────────────────────────────────────────────────────────────────┐
│ ← Voltar ao painel                                                                  │
│ PRENSA A #1                                    [StatusBadge ● Online]               │
│ CT-53 · Usinagem CNC · 192.168.20.2                    [ghost Editar]† [Poll]     │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─ UnderlineNav ──────────────────────────────────────────────────────────────────────┐
│  Visão geral  │  Histórico  │  Comandos                                              │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### WF-PP-03-A — Aba «Visão geral» (`tab=overview`)

```text
┌─ grid 2 col (1 col mobile) ─────────────────────────────────────────────────────────┐
│ ┌─ Hero métrica contador ──────────────┐  ┌─ SectionCard «Amarração» ────────────┐ │
│ │                                      │  │ CT-53 · Usinagem CNC                 │ │
│ │           1.284                      │  │ Recurso: —                           │ │
│ │        golpes (cache)                │  │ Ferramenta: —                        │ │
│ │                                      │  │ Máquina: Prensa hidráulica #1       │ │
│ │   Última leitura: há 12 s            │  │ Equipamento: Sensor principal        │ │
│ │   Poll: 30 s · Driver ESP8266        │  │ Vigente desde: 01/09/2026            │ │
│ │                                      │  │ [link Ver histórico de vínculos]     │ │
│ │ [ghost Atualizar]  [Reset contador]† │  └──────────────────────────────────────┘ │
│ └──────────────────────────────────────┘                                            │
│                                                                                      │
│ ┌─ SectionCard «Mini histórico (24h)» ────────────────────────────────────────────┐ │
│ │ ChartCard + linha delta_since_previous (ConfigurableSeriesChart)                 │ │
│ │                                    [link Ver histórico completo →]               │ │
│ └──────────────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

**Contador grande:** typography `--pp-font-kpi`; label «golpes» muted.  
**Live refresh:** botão Atualizar chama `GET /live` (flash valor) ou `POST /poll` (persiste).

### WF-PP-03-B — Aba «Histórico» (`tab=history`)

```text
┌─ FiltersRow ────────────────────────────────────────────────────────────────────────┐
│ De [date]  Até [date]  [ghost Aplicar]  [ghost Export CSV] (P1)                     │
└──────────────────────────────────────────────────────────────────────────────────────┘

┌─ ChartCard «Evolução do contador» ────────────────────────────────────────────────────┐
│  linha counter_value (eixo Y) × recorded_at (eixo X)                                │
│  toggle: [Contador | Delta]                                                         │
└──────────────────────────────────────────────────────────────────────────────────────┘

┌─ DataTableSection «Leituras» ─────────────────────────────────────────────────────────┐
│ Data/hora           │ Contador │ Delta │ Origem (poll/manual/command)                 │
│ 01/09 14:32:01      │  1.284   │  +3   │ poll                                           │
│ 01/09 14:31:31      │  1.281   │  +1   │ poll                                           │
│ …                                                                                     │
│ CompactPagination                                                                     │
└───────────────────────────────────────────────────────────────────────────────────────┘
```

**Origem:** badge neutro — `StatusBadge` variant info ou texto sm.

### WF-PP-03-C — Aba «Comandos» (`tab=commands`)

```text
┌─ DataTableSection «Auditoria de comandos» ────────────────────────────────────────────┐
│ Data/hora        │ Comando │ Usuário      │ Resultado │ Detalhe                        │
│ 01/09 10:00      │ reset   │ joao@…       │ ✓ OK      │ [ghost Ver JSON]               │
│ 31/08 18:22      │ reset   │ maria@…      │ ✗ Falha   │ timeout                        │
└───────────────────────────────────────────────────────────────────────────────────────┘
```

**Ver JSON:** `ModalShell` read-only com `response_payload`.

### WF-PP-03-D — Drawer histórico de bindings (opcional MVP+)

Link «Ver histórico de vínculos» → `DrawerShell` lista `GET .../bindings/history`.

**Helps (`PP_HELP`):** abas `detail.tab*` · overview … — [HELP-CONTENT § WF-PP-03](./HELP-CONTENT.md#wf-pp-03--detalhe-devicedetailpage).

### WF-PP-03 tablet (769–1100px)

**Hero:** uma linha compacta; ações podem wrap.

```text
┌─ PageHero tablet ─────────────────────────────────────────────────┐
│ ← Voltar · PRENSA A #1 · [● Online]                               │
│ CT-53 · 192.168.20.2          [Editar]† [Poll]                    │
└───────────────────────────────────────────────────────────────────┘
```

**Overview (`tab=overview`):**

| Largura | Layout |
|---------|--------|
| **901–1100px** | Grid **2 col**: métrica hero (esq) + amarração (dir); gráfico mini **full width** abaixo |
| **769–900px** | **1 col** empilhado (métrica → amarração → gráfico) — igual mobile mas tipografia desktop |

```text
┌─ 901–1100: 2 col top ─────────────────────────────────────────────┐
│ ┌─ Hero métrica ─────────┐  ┌─ Amarração ──────────────────────┐ │
│ │       1.284 golpes       │  │ CT-53 · Usinagem…                │ │
│ │ [Atualizar] [Reset]†     │  │ Máquina · Equipamento…           │ │
│ └──────────────────────────┘  └──────────────────────────────────┘ │
│ ┌─ ChartCard mini 24h — full width, height ~220px ────────────────┐ │
│ └──────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

**Histórico:** filtros em **1 linha** ≥901px (`De | Até | Aplicar`); **2 linhas** 769–900px. Tabela mantida com scroll-x; gráfico height ~240px.

**Comandos:** tabela 4 col; ocultar «Detalhe» → ícone ⋮.

### WF-PP-03 mobile (≤768px)

**Hero:** coluna; ações em toolbar secundária.

```text
┌─ PageHero mobile ─────────────────────────────────┐
│ ← Voltar                                          │
│ PRENSA A #1                    [● Online]         │
│ CT-53 · Usinagem CNC                              │
│ 192.168.20.2                                      │
│ [ghost Editar]†  [ghost Poll]  [⋯ mais]           │
└───────────────────────────────────────────────────┘
┌─ UnderlineNav — scroll horizontal se necessário ──┐
│ Visão geral │ Histórico │ Comandos                 │
└───────────────────────────────────────────────────┘
```

**Aba Visão geral:** grid **1 coluna** — métrica hero → amarração → mini gráfico.

```text
┌─ Hero métrica (full width) ───────────────────────┐
│              1.284                                 │
│            golpes                                  │
│   Última leitura: há 12 s                          │
│ [Atualizar]  [Reset contador]†  ← stack ou 50/50  │
└───────────────────────────────────────────────────┘
┌─ SectionCard Amarração ───────────────────────────┐
│ CT-53 · Usinagem CNC                              │
│ Máquina: Prensa #1 · Equipamento: Sensor          │
│ [link Histórico vínculos]                         │
└───────────────────────────────────────────────────┘
┌─ ChartCard mini 24h ──────────────────────────────┐
│ (altura reduzida ~180px)                          │
│ [Ver histórico completo →]                        │
└───────────────────────────────────────────────────┘
```

**Aba Histórico:** filtros empilhados; gráfico full width; tabela → **cards de leitura**.

```text
┌─ Filtros (stack) ─────────────────────────────────┐
│ De [date]                                         │
│ Até [date]                                        │
│ [Aplicar]  [Export CSV] (P1)                      │
└───────────────────────────────────────────────────┘
┌─ ChartCard ───────────────────────────────────────┐
│ toggle [Contador | Delta] — chips full width      │
└───────────────────────────────────────────────────┘
┌─ ReadingCard ─────────────────────────────────────┐
│ 01/09 14:32 · poll                                │
│ Contador 1.284  ·  Delta +3                       │
└───────────────────────────────────────────────────┘
```

**Aba Comandos:** cards audit (Data/hora + Comando + Resultado); «Ver JSON» expande inline ou modal.

---

## WF-PP-04 — Modais

### WF-PP-04-A — Confirmar reset contador

```text
┌─ ModalShell (host-contained) ───────────────────────────────┐
│ Resetar contador?                                    [×]    │
│                                                             │
│ O contador do dispositivo **Prensa A #1** será zerado       │
│ no hardware. Esta ação é auditada.                          │
│                                                             │
│                    [ghost Cancelar]  [primary Resetar]†     │
└─────────────────────────────────────────────────────────────┘
```

API: `POST /devices/:id/commands/reset` → toast sucesso → refresh detalhe.

### WF-PP-04-B — Desativar dispositivo (edit page)

Mesmo padrão ModalShell — «Desativar dispositivo?» → soft delete `enabled=false`.

**Helps (`PP_HELP`):** `modals.resetTitle` · … — [HELP-CONTENT § WF-PP-04](./HELP-CONTENT.md#wf-pp-04--modais).

### WF-PP-04 tablet (769–1100px)

- `ModalShell`: `width: min(520px, calc(100% - 48px))` — centrado no host MFE.
- Botões **sempre** lado a lado (Cancelar | Primário) — min-width 120px cada.
- Modal operador «Zerar»: mesma largura; botões 48px altura (menor que portrait mobile 56px).

### WF-PP-04 mobile (≤768px)

Modais `ModalShell` **host-contained** — largura ~`calc(100% - 32px)`, max-width 480px, centrados.

```text
┌─ ModalShell mobile ───────────────────────────────┐
│ Resetar contador?                          [×]    │
│                                                   │
│ O contador **Prensa A #1** será zerado no         │
│ hardware. Esta ação é auditada.                   │
│                                                   │
│ [ghost Cancelar]     ← stack se <360px            │
│ [primary Resetar]†   ← ou 50/50 side by side      │
└───────────────────────────────────────────────────┘
```

- Botões: **coluna** abaixo de 360px (`flex-direction: column-reverse` — primário embaixo, thumb-friendly).
- Modal operador «Zerar» (WF-PP-OP-03): botões **56px** altura, full width em portrait.
- Toast teste conexão: posição bottom-center (kit padrão).

---

## WF-PP-05 — Manifesto menu (Portal)

```text
Menu lateral Minha DELPI
├── Produção (menuGroup)
│   └── Pulso de Produção     → /apps/production-pulse
```

**Ícone manifest:** `activity`  
**Permissão rota:** `production-pulse.access` (container) + conteúdo exige `devices.view`

Variante multi-filial futura (fora MVP menu duplicado):

```text
│   ├── Pulso SC              → /apps/production-pulse?branch=01
│   └── Pulso ES              → /apps/production-pulse?branch=02
```

MVP: **uma entrada** + FilialSwitcher no hero (padrão maintenance).

---

---

## WF-PP-OP-HUB — Hub operador (postos, máquinas, equipamentos)

**Rota:** `/apps/production-pulse/operator?branch=01`  
**API:** `GET /operator/placements?branch=&anchorType=&search=`  
**Objetivo:** tablet — escolher **onde** trabalhar (não só CT).

### Filtros touch (abaixo da BrandBar)

```text
[ Todos ]  [ Postos PCP ]  [ Máquinas ]  [ Equipamentos ]
········ Buscar ventilador, motor, CT-53 ·········
```

### Cards (exemplos mistos)

```text
┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│ CT-53               │  │ Motor bomba #2      │  │ Ventilador exaustão │
│ Usinagem CNC        │  │ [Máquina]           │  │ [Equipamento]       │
│ 1 cont · 1 sens     │  │ 1 sens · ● online   │  │ rpm · ● online      │
└─────────────────────┘  └─────────────────────┘  └─────────────────────┘
```

Tap → picker devices naquele `placement_key` → superfície driver.

**Alias MVP:** filtro «Postos PCP» = `anchor_type=work_center` (equivalente ao hub CT anterior).

**Helps (`PP_HELP`):** `operator.hubTitle` · … — [HELP-CONTENT § WF-PP-OP](./HELP-CONTENT.md#wf-pp-op--modo-operador).

### WF-PP-OP-HUB tablet (769–1100px)

Faixa **primária do operador** — layout touch landscape (iPad horizontal).

```text
┌─ OperatorBrandBar (sticky) ───────────────────────────────────────┐
│ PULSO · Filial 01 · Escolha onde vai trabalhar                      │
│ Toque no local… (intro)              [link Painel admin] (opcional) │
└─────────────────────────────────────────────────────────────────────┘
[ Todos ] [ Postos PCP ] [ Máquinas ] [ Equipamentos ]  ← wrap OK 2 linhas
········ Buscar ventilador, CT-53 ····································
┌─ grid hub ──────────────────────────────────────────────────────────┐
│ 901–1100px landscape:  **3 colunas**  minmax(220px, 1fr)            │
│ 769–900px portrait:      **2 colunas**  minmax(200px, 1fr)          │
│                                                                     │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐                              │
│ │ CT-53    │ │ Motor #2 │ │ Vent. A  │                              │
│ │ Usinagem │ │ [Máq.]   │ │ [Equip.] │                              │
│ │ 2 online │ │ 1 sens   │ │ rpm · On │                              │
│ └──────────┘ └──────────┘ └──────────┘                              │
└─────────────────────────────────────────────────────────────────────┘
```

| Regra | Valor |
|-------|-------|
| Card min-height | **128px** (769–1100) |
| Gap grid | 16px portrait · 20px landscape |
| Sidebar portal | Visível estreita ou oculta — preferir **área operador max-width** |
| Último placement | Borda accent + chip «Recente» |

### WF-PP-OP-HUB mobile (≤768px / ≤600px)

Modo operador **prioriza mobile/tablet** — ver também WF-PP-OP-HUB-02 (legado CT). Hub unificado:

```text
┌─ OperatorBrandBar (sticky) ───────────────────────┐
│ PULSO · Filial 01                                 │
│ Escolha onde vai trabalhar                        │
│ Toque no local… (copy intro)                      │
└───────────────────────────────────────────────────┘
┌─ Filtros chips — scroll horizontal ───────────────┐
│ [Todos][Postos][Máquinas][Equipamentos] →         │
└───────────────────────────────────────────────────┘
······· Buscar ventilador, CT-53 ····················
┌─ placement card (full width) ─────────────────────┐
│ CT-53                                             │
│ Usinagem CNC                          [Posto]     │
│ 1 cont · 1 sens · ● online                        │
└───────────────────────────────────────────────────┘
┌─ placement card ──────────────────────────────────┐
│ Ventilador exaustão A                 [Equip.]    │
│ 1180 rpm · ● online                               │
└───────────────────────────────────────────────────┘
```

| Regra | Valor |
|-------|-------|
| Grid | `1fr` abaixo **600px**; 2 col entre 601–900px landscape |
| Card min-height | **96px** mobile · **128px** tablet |
| Filtros | Chips horizontais com scroll; não wrap em 3+ linhas |
| Sidebar portal | Oculta ou overlay — área operador **fullscreen** |

---

## WF-PP-OP-HUB (legado CT-only) — referência PCP

**Rota:** `/apps/production-pulse/operator?branch=01`  
**Referência:** cockpit PCP `WorkCenterPicker` (`CockpitPage.tsx` + `cockpit.css`)  
**Objetivo:** operador no tablet **escolhe o posto** — cards touch; meta reflete **contadores e sensores**.

### WF-PP-OP-HUB-01 — Grid de postos (tablet landscape)

```text
┌─ Sidebar Portal (opcional) ─┬─ .dashboard-page--operator ─────────────────────────────────┐
│                             │ ┌─ OperatorBrandBar (gradiente escuro, sticky) ────────────┐ │
│                             │ │ [logo] PULSO DE PRODUÇÃO · Filial 01                    │ │
│                             │ │ Escolha o seu posto de trabalho          [12 postos]    │ │
│                             │ └──────────────────────────────────────────────────────────┘ │
│                             │  Toque no posto onde você vai trabalhar hoje.                │
│                             │  A escolha fica salva neste tablet.                         │
│                             │  ········· Buscar posto ou máquina ·········  (se >8 CTs)   │
│                             │                                                             │
│                             │  ┌─────────────────┐ ┌─────────────────┐ ┌──────────────┐ │
│                             │  │ CT-53           │ │ CT-12           │ │ CT-70        │ │
│                             │  │ Usinagem CNC    │ │ Torno automát.  │ │ Montagem     │ │
│                             │  │ 1 cont · 2 sens │ │ 1 contador      │ │ 2 sensores   │ │
│                             │  │ 3 online        │ │ ● online        │ │ 1 online     │ │
│                             │  └─────────────────┘ └─────────────────┘ └──────────────┘ │
│                             │  ┌─────────────────┐ ┌─────────────────┐                   │
│                             │  │ CT-01A          │ │ CT-22           │  ← min-h 128px   │
│                             │  │ …               │ │ …               │    tap = abrir   │
│                             │  └─────────────────┘ └─────────────────┘                   │
└─────────────────────────────┴─────────────────────────────────────────────────────────────┘
```

**Card CT (`.pp-operator-hub__card`):**

| Zona | Conteúdo |
|------|----------|
| Topo | **CT-53** — código grande, bold |
| Meio | Nome TOTVS truncado 2 linhas |
| Rodapé | `{by_role}` resumido + `{online}/{total}` online — ex.: «1 contador · 2 sensores · 3 online» |

**Regra hub:** lista CTs com ≥1 device `operatorEligible` (contador ou sensor operável). Devices só-admin ficam fora.

**Interação touch:**

- Card inteiro é `<button>` — alvo mín. **128×260px**
- `:active` scale 0.98 + borda accent
- Sem hover-only (tablet não tem hover)
- Último CT usado: borda accent 2px + chip «Usado recentemente»

**Tap no card:**

```text
GET /work-centers/CT-53/devices?branch=01
  → 0 devices elegíveis → toast «Posto sem dispositivo operável»
  → 1 device  → redirect superfície (contador ou gauge)
  → N devices → WF-PP-OP-PICK
```

### WF-PP-OP-HUB-02 — Portrait tablet / celular

```text
┌────────────────────────┐
│ BrandBar               │
│ Escolha o posto        │
├────────────────────────┤
│ ···· Buscar ····       │
│                        │
│ ┌────────────────────┐ │
│ │ CT-53              │ │  ← 1 coluna, cards full width
│ │ Usinagem CNC       │ │     min-height 96px
│ │ 2 cont · 2 online  │ │
│ └────────────────────┘ │
│ ┌────────────────────┐ │
│ │ CT-12              │ │
│ └────────────────────┘ │
└────────────────────────┘
```

Grid: `grid-template-columns: 1fr` abaixo 600px.

### WF-PP-OP-HUB-03 — Estados

| Estado | UI |
|--------|-----|
| Loading | Skeleton grid 6 cards |
| Empty filial | «Nenhum posto com dispositivo cadastrado» + contato supervisor |
| Busca vazia | «Nenhum posto encontrado» + limpar busca |
| Offline API | StateBox + retry |

---

## WF-PP-OP-PICK — Escolha do dispositivo (CT com N devices)

**Rota:** `/apps/production-pulse/operator/work-centers/:code`

```text
┌─ BrandBar ─────────────────────────────────────────────────────────┐
│ CT-53 · Usinagem CNC                    [ghost Trocar posto]       │
│ Qual equipamento você vai usar?                                    │
└────────────────────────────────────────────────────────────────────┘

┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
│ [Contador]           │  │ [Sensor]             │  │ [Sensor]             │
│  Prensa A #1         │  │  Fusos — rotação     │  │  Cabine — temperatura│
│  ● Online · 1.284    │  │  ● 1.850 rpm         │  │  ● 67,2 °C           │
└──────────────────────┘  └──────────────────────┘  └──────────────────────┘
        ↑ badge papel (role) + preview métrica principal
```

Tap → superfície conforme `operatorSurface` do driver (`counter_pad` ou `gauge_readout`).

**Helps (`PP_HELP`):** `operator.pickerTitle` · … · `operator.changePlacement`.

### WF-PP-OP-PICK tablet (769–1100px)

Grid **2 colunas** (≥769px); cards com mesma spec do hub.

```text
┌─ BrandBar ────────────────────────────────────────────────────────┐
│ CT-53 · Usinagem CNC              [ghost Trocar posto]            │
│ Qual equipamento você vai usar?                                   │
└───────────────────────────────────────────────────────────────────┘
┌─ pick grid 2 col (901–1100: pode 3 col se ≥3 devices) ────────────┐
│ ┌─────────────────────┐  ┌─────────────────────┐                  │
│ │ [Contador] Prensa A │  │ [Sensor] Fusos rpm  │                  │
│ │ ● 1.284 golpes      │  │ ● 1.850 rpm         │                  │
│ └─────────────────────┘  └─────────────────────┘                  │
│ ┌─────────────────────┐                                           │
│ │ [Sensor] Cabine °C  │                                           │
│ └─────────────────────┘                                           │
└───────────────────────────────────────────────────────────────────┘
```

- **769–900px:** sempre 2 col; card full width se só 1 device.
- Min-height card: **112px**; tap target ≥48px.

### WF-PP-OP-PICK mobile (≤768px)

Cards device **empilhados** (1 coluna); tap abre superfície.

```text
┌─ BrandBar ────────────────────────────────────────┐
│ CT-53 · Usinagem CNC                                │
│ Qual equipamento?              [Trocar posto]       │
└─────────────────────────────────────────────────────┘
┌─ device pick card (full width) ────────────────────┐
│ [Contador]  Prensa A #1                             │
│ ● Online · 1.284 golpes                             │
└─────────────────────────────────────────────────────┘
┌─ device pick card ─────────────────────────────────┐
│ [Sensor]  Fusos — rotação                           │
│ ● 1.850 rpm                                         │
└─────────────────────────────────────────────────────┘
┌─ device pick card ─────────────────────────────────┐
│ [Sensor]  Cabine — temperatura                      │
│ ● 67,2 °C                                           │
└─────────────────────────────────────────────────────┘
```

- Badge role no topo do card; métrica preview em destaque.
- Min-height card: **88px**; alvo touch ≥ **48px** padding vertical.

---

## WF-PP-OP — Superfície contador (`counter_pad`)

## WF-PP-OP-GAUGE — Superfície sensor (`gauge_readout`) — P1

**Mesma rota** `/operator/work-centers/:code/devices/:deviceId` — MFE roteia por driver.

```text
┌─ BrandBar ─ CT-53 · Fusos rotação ────────────────────────────────┐
│ CT-53 · Usinagem CNC                    [ghost Trocar posto]       │
└────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────────────┐
                    │      1.850                │
                    │      rpm                  │
                    │   Rotação fusos           │
                    └─────────────────────────┘

                    ┌─────────────────────────┐
                    │      67,2                 │
                    │      °C                   │
                    │   Temperatura cabine      │
                    └─────────────────────────┘

              ● Online · sync há 5 s    [ghost Atualizar]
```

Sem pad −/+/Limpar. Auto-sync 5 s. Somente leitura.

**Helps (`PP_HELP`):** `operator.gaugeValue` · … · `operator.offlineBanner`.

### WF-PP-OP-GAUGE tablet (769–1100px)

Métricas em **grid 2 colunas** (901–1100) ou **1 col centralizada** (769–900 portrait).

```text
┌─ BrandBar + status ───────────────────────────────────────────────┐
│ CT-53 · Fusos rotação · ● Online · sync 5s    [Trocar posto]      │
└───────────────────────────────────────────────────────────────────┘
┌─ 901–1100: 2 col ─────────────────────────────────────────────────┐
│ ┌─ gauge card ──────────┐  ┌─ gauge card ──────────┐             │
│ │      1.850 rpm        │  │      67,2 °C          │             │
│ │   Rotação fusos       │  │   Temp. cabine        │             │
│ └───────────────────────┘  └───────────────────────┘             │
│              [ghost Atualizar] — centered, max 320px              │
└───────────────────────────────────────────────────────────────────┘
```

- Valor: `clamp(3rem, 12vw, 5rem)` nesta faixa.
- Auto-sync 5 s; sem pad −/+/Limpar.

### WF-PP-OP-GAUGE mobile (≤768px)

Métricas **empilhadas** — 1 card por grandeza, full width.

```text
┌─ BrandBar + status ───────────────────────────────┐
│ CT-53 · Fusos rotação          [Trocar posto]     │
│ ● Online · sync há 5 s                              │
└─────────────────────────────────────────────────────┘
┌─ gauge card ──────────────────────────────────────┐
│           1.850                                    │
│           rpm                                      │
│      Rotação fusos                                 │
└─────────────────────────────────────────────────────┘
┌─ gauge card ──────────────────────────────────────┐
│           67,2                                     │
│           °C                                       │
│      Temperatura cabine                            │
└─────────────────────────────────────────────────────┘
        [ghost Atualizar]  ← full width, 48px min
```

- Valor: `clamp(2.5rem, 18vw, 4rem)` em mobile (menor que tablet).
- Auto-sync 5 s mantido; sem pad −/+/Limpar.

---

## WF-PP-OP (contador) — Tela centralizada

**Rotas:**  
- `/apps/production-pulse/operator/work-centers/:code/devices/:deviceId`

**Permissão:** `production-pulse.operator`  
**Objetivo:** contador grande + **− / Limpar / +** após escolha do posto (e do device se N).

### WF-PP-OP-01 — Vista principal (tablet landscape 769–1100px — referência)

**Faixa canônica tablet:** `769px – 1100px` landscape — pad **3 col** (− | Limpar | +), palco centrado. Abaixo de 768px → WF-PP-OP-02.

| Subfaixa | Palco contador | Pad |
|----------|----------------|-----|
| **901–1100px** landscape | `clamp(5rem, 20vw, 10rem)` | 3×1 grid, max-width **720px**, botões **112px** alt |
| **769–900px** landscape | `clamp(4.5rem, 18vw, 8rem)` | 3×1 grid, gap 16px, botões **96px** alt |
| **769–900px** portrait | Palco menor | Pad **3 col** mantido se largura ≥600px; senão → OP-02 |

```text
┌─ Sidebar Portal ─┬─ .dashboard-page--operator (área MFE fullscreen vertical) ─────────────┐
│ (opcional)       │  CT-53 · Usinagem CNC     [ghost Trocar posto]                         │
│                  │  Prensa #1 · ● Online · sync há 8 s                                     │
│                  │                                                                         │
│                  │                         ╭──────────────────────╮                         │
│                  │                         │                      │                         │
│                  │                         │       1.284          │  ← clamp 5–10rem       │
│                  │                         │       golpes         │                         │
│                  │                         │                      │                         │
│                  │                         ╰──────────────────────╯                         │
│                  │                              (anel pulse se online)                      │
│                  │                                                                         │
│                  │         ╭─────────────╮ ╭─────────────╮ ╭─────────────╮                 │
│                  │         │      −      │ │   ⌫ Limpar  │ │      +      │                 │
│                  │         │   Diminuir  │ │    Zerar    │ │   Aumentar  │                 │
│                  │         │   (Minus)   │ │  (Eraser)   │ │   (Plus)    │                 │
│                  │         ╰─────────────╯ ╰─────────────╯ ╰─────────────╯                 │
│                  │              ↑ 96–112px altura · ícones 48px · gap 20px                  │
│                  │                                                                         │
│                  │                    [ghost Sincronizar agora]                            │
└──────────────────┴─────────────────────────────────────────────────────────────────────────┘
```

**Símbolos nos botões (intuitivos à distância):**

| Botão | Ícone | Texto curto | Cor |
|-------|-------|-------------|-----|
| Esquerda | `Minus` **−** | Diminuir | Neutro, borda |
| Centro | `Eraser` ou `RotateCcw` | **Limpar** | Outline âmbar |
| Direita | `Plus` **+** | Aumentar | Preenchido accent |

Ordem **− | Limpar | +** espelha o ESP8266 físico (decrement · reset · increment) e evita confusão com ordem alfabética.

### WF-PP-OP-02 — Mobile / portrait narrow (≤768px ou ≤600px)

```text
┌──────────────────────────────┐
│ CT-53 · Prensa A #1    ● On  │
├──────────────────────────────┤
│                              │
│         ╭────────────╮       │
│         │   1.284    │       │
│         │   golpes   │       │
│         ╰────────────╯       │
│                              │
│  ╭────────────────────────╮  │
│  │  +   Aumentar golpe    │  │  ← full width, 96px, accent fill
│  ╰────────────────────────╯  │
│  ╭──────────╮ ╭────────────╮ │
│  │ − Dimin. │ │ ⌫ Limpar   │ │  ← row 2: 50% / 50%
│  ╰──────────╯ ╰────────────╯ │
│                              │
│     [ Sincronizar ]          │
└──────────────────────────────┘
```

Portrait: **+** primeiro (ação mais frequente), largura total; **−** e **Limpar** dividem segunda linha.

### WF-PP-OP-03 — Modal confirmar limpar

```text
┌─ ModalShell (grande, host-contained) ──────────────────────┐
│                                                              │
│              ⌫  Zerar contador?                              │
│                                                              │
│     O valor voltará a **0** no dispositivo e na tela.       │
│     Operação registrada em auditoria.                        │
│                                                              │
│   ╭──────────────────╮    ╭──────────────────╮               │
│   │    Cancelar      │    │  Sim, zerar (0)  │  ← 56px alt  │
│   ╰──────────────────╯    ╰──────────────────╯               │
└──────────────────────────────────────────────────────────────┘
```

**+/−** não pedem confirmação — feedback imediato (bump + valor atualizado).

### WF-PP-OP-04 — Offline

```text
│  CT-53 · Prensa A #1         ○ Offline · há 2 min            │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ ⚠ Sem conexão com o contador. Verifique rede ou ESP.   │ │
│  └─────────────────────────────────────────────────────────┘ │
│                         ╭──────────────╮                     │
│                         │     892      │  (valor cache muted) │
│                         │    golpes    │                     │
│                         ╰──────────────╯                     │
│              [ botões desabilitados / opacity 0.5 ]          │
│                   [primary Tentar reconectar]              │
```

### WF-PP-OP-05 — Picker devices

Substituído por **WF-PP-OP-PICK** (tela dedicada após hub CT, não chips inline).

### WF-PP-OP-06 — Interações e API

| Ação UI | API | Firmware |
|---------|-----|----------|
| Tap **+** | `POST .../commands/increment` | `POST /api/incrementar` |
| Tap **−** | `POST .../commands/decrement` | `POST /api/decrementar` |
| Tap **Limpar** → confirmar | `POST .../commands/reset` | `POST /api/reset` |
| Sincronizar | `POST .../poll` ou `GET .../live` | `GET /api/contador` |
| Auto-sync | polling UI a cada 5 s (só tela operador aberta) | — |

**Optimistic UI:** ao tap +/−, incrementa/decrementa valor local imediatamente; reconcilia com resposta API; rollback se falhar.

### WF-PP-OP-07 — Entradas

| Origem | Destino |
|--------|---------|
| Menu «Operador · Pulso» | `/operator` hub placements |
| Admin «Modo operador» | `/operator` |
| Superfície «Trocar posto» | `/operator` |

**Helps (`PP_HELP`):** `operator.statusBar` · `operator.counterValue` · `operator.counterIncrement` · `operator.counterDecrement` · `operator.counterClear` · modal `modals.clearOperator*` · `operator.offlineBanner` · `operator.adminLink`.

---

## WF-PP-06 — Fluxos satélite (operador)

| Fluxo | Comportamento |
|-------|---------------|
| Operador abre app | `/operator` hub; `localStorage` último `placement_key` por filial |
| Escolhe placement | 1 device → superfície; N → picker; 0 → toast |
| Trocar posto | Hub (`OperatorBrandBar` ghost) |
| Sem amarração | Grupo «Sem amarração» no painel; excluído do hub operador |

---

## Helps e tooltips — catálogo completo

**Fonte de verdade:** [`content/helpTooltips.ts`](./content/helpTooltips.ts) (`PP_HELP` + `getPpHelp()`).

**Mapa componente × wireframe × chave:** [HELP-CONTENT.md](./HELP-CONTENT.md) — inclui shell, painel, formulário, detalhe, modais, operador e badges.

| Namespace | Qtd chaves | Exemplos |
|-----------|------------|----------|
| `shell.*` | 5 | hero, filial, poll all, modo operador |
| `panel.*` | 22 | KPIs, filtros, colunas, ações linha, vazios |
| `form.*` | 24 | seções, campos device/binding, TOTVS opcional |
| `detail.*` | 14 | abas, métricas live, gráficos, auditoria |
| `modals.*` | 8 | reset, limpar operador, teste conexão, desativar |
| `operator.*` | 18 | hub, picker, contador, gauge, offline |
| `badges.*` | 12 | anchor types, roles, status |

**Proibido no help:** paths API, IPs de exemplo fixos como regra, códigos Protheus internos.

**Implementação E5:** copiar para `plugins/production-pulse/src/content/helpTooltips.ts` · ligar `FieldLabel hint={…}` e `SectionHintLabel` em todo formulário e seção · checklist em [HELP-CONTENT § E5](./HELP-CONTENT.md#checklist-e5-helps).

---

## Checklist implementação frontend (E5)

- [ ] Tokens `--pp-*` + `--delpi-ui-*` em `index.css`
- [ ] Factories kit `productionPulseUi.ts`
- [ ] `helpTooltips.ts` copiado de `docs/.../content/` + wired em todos os campos (ver [HELP-CONTENT](./HELP-CONTENT.md))
- [ ] WF-PP-01 lista + agrupada multi-âncora + estados
- [ ] WF-PP-02 form anchor segmented + TOTVS opcional
- [ ] **WF-PP-OP-HUB** hub placements (+ PICK + counter/gauge)
- [ ] URL sync query (P0 playbook excelência)
- [ ] `npm run build` verde
- [ ] Visual claro + escuro no portal federado
- [ ] Mobile ≤768 smoke — **todas** as rotas da matriz responsiva
- [ ] **Tablet 769–1100px** — painel KPI 2×2 · form max-w 720 · operador hub 2–3 col · contador OP-01
- [ ] **Tablet operador** landscape + portrait; mobile ≤600 pad empilhado (OP-02)
