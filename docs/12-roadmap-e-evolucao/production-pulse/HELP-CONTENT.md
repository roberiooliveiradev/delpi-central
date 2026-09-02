# Helps e explicações de UI — Production Pulse

> **Fonte de verdade (implementação):** [content/helpTooltips.ts](./content/helpTooltips.ts) → copiar para `plugins/production-pulse/src/content/helpTooltips.ts`  
> **Padrão:** `FieldLabel hint={getPpHelp("form.ip")}` · `SectionHintLabel` nos títulos de seção  
> **Proibido:** textos de help hardcoded em componentes; paths API; IPs fixos como regra.

---

## Como usar no MFE

```tsx
import { PP_HELP, getPpHelp } from "../content/helpTooltips";

<FieldLabel label="Endereço IP" hint={PP_HELP.form.ip} />
<SectionHintLabel hint={PP_HELP.form.sectionDevice}>Dispositivo IoT</SectionHintLabel>
```

Ícone `?` do kit aparece no hover/focus — ver `FieldLabel` / `SectionHintLabel` em `@delpi/plugin-ui`.

---

## WF-PP-00 — Shell (`ProductionPulsePageHero`)

| Elemento UI | Chave help | Texto |
|-------------|------------|-------|
| Título hero | `shell.heroTitle` | Monitoramento IoT na filial… |
| FilialSwitcher | `shell.heroFilial` | Filial operacional… |
| [Atualizar tudo] | `shell.pollAll` | Poll imediato em todos ativos… |
| Link modo operador | `shell.modeOperator` | Visão tablet… |

---

## WF-PP-01 — Painel

### KPI strip (`DeviceKpiStrip`)

| KPI | Chave | Componente kit |
|-----|-------|----------------|
| Total | `panel.kpiTotal` | `SimpleKpiCard` + ícone `Cpu` |
| Online | `panel.kpiOnline` | `Wifi` · cor success |
| Offline | `panel.kpiOffline` | `WifiOff` · cor danger |
| Sem amarração | `panel.kpiWithoutBinding` | `Link2Off` · cor warning |

### FilterBar (`DeviceFiltersBar`)

| Filtro | Chave |
|--------|-------|
| Tipo amarração | `panel.filterAnchorType` |
| Papel (role) | `panel.filterRole` |
| Status | `panel.filterStatus` |
| Busca | `panel.filterSearch` |
| Agrupar por | `panel.filterGroupBy` |
| Toggle Lista | `panel.viewList` |
| Toggle Agrupado | `panel.viewGrouped` |

### Tabela (`DeviceTable`)

| Coluna | Chave |
|--------|-------|
| Nome | `panel.colName` |
| Objeto | `panel.colPlacement` |
| Papel | `panel.colRole` |
| Métrica | `panel.colMetric` |
| Status | `panel.colStatus` |
| Última leitura | `panel.colLastSeen` |
| Ação Poll | `panel.rowPoll` |
| Ação Reset | `panel.rowReset` |

### Estados vazios

| Estado | Chave | Componente |
|--------|-------|------------|
| Filial vazia | `panel.emptyFilial` | `EmptyGuidance` |
| Filtro vazio | `panel.emptyFilters` | `EmptyState` |

### Agrupado (`DeviceGroupedByPlacement`)

Cabeçalho de grupo: `placement_label` + `AnchorTypeBadge` — helps dos badges em `badges.anchor*`.

---

## WF-PP-02 — Formulário (`DeviceForm` + `DeviceBindingSection`)

### Seções

| SectionHintLabel | Chave |
|------------------|-------|
| «Dispositivo IoT» | `form.sectionDevice` |
| «Onde está instalado» | `form.sectionPlacement` |
| «Vincular ao TOTVS (opcional)» | `form.sectionTotvs` |

### Campos — dispositivo

| Campo | Chave |
|-------|-------|
| Nome do dispositivo | `form.name` |
| Filial | `form.filial` |
| Endereço IP | `form.ip` |
| Driver | `form.driver` |
| Preview driver | `form.driverPreview` |
| Intervalo poll | `form.pollInterval` |
| Ativo | `form.enabled` |
| [Testar conexão] | `form.testConnection` |

### Campos — amarração (`AnchorTypeSegmented`)

| Campo / tipo | Chave |
|--------------|-------|
| Segmented (geral) | `form.anchorType` |
| Posto PCP → CT | `form.anchorWorkCenter` |
| Máquina | `form.anchorMachine` |
| Equipamento | `form.anchorEquipment` |
| Área | `form.anchorArea` |
| Avulso | `form.anchorStandalone` |
| CT (bloco TOTVS) | `form.workCenterOptional` |
| Recurso | `form.resourceOptional` |
| Ferramenta | `form.toolOptional` |
| Observações | `form.notes` |

### Rodapé

| Botão | Chave |
|-------|-------|
| Cancelar | `form.cancel` |
| Salvar | `form.save` |

---

## WF-PP-03 — Detalhe (`DeviceDetailPage`)

### Abas (`UnderlineNav`)

| Aba | Chave |
|-----|-------|
| Visão geral | `detail.tabOverview` |
| Histórico | `detail.tabHistory` |
| Comandos | `detail.tabCommands` |

### Overview

| Bloco | Chave |
|-------|-------|
| Métricas live | `detail.liveMetrics` |
| Card amarração | `detail.bindingCard` |
| [Atualizar agora] | `detail.pollNow` |
| [Reset contador] | `detail.resetCounter` |
| [Desativar] | `detail.deactivate` |

### Histórico

| Bloco | Chave |
|-------|-------|
| Gráfico delta | `detail.chartDelta` |
| Gráfico série | `detail.chartSeries` |
| Tabela readings | `detail.readingsTable` |
| Coluna delta | `detail.delta` |

### Comandos

| Bloco | Chave |
|-------|-------|
| Tabela audit | `detail.commandsTable` |

---

## WF-PP-04 — Modais

| Modal | Chave título / corpo |
|-------|----------------------|
| Reset admin | `modals.resetTitle` / `modals.resetBody` |
| Limpar operador | `modals.clearOperatorTitle` / `modals.clearOperatorBody` |
| Teste OK | `modals.testOk` |
| Teste falha | `modals.testFail` |
| Desativar | `modals.deactivateTitle` / `modals.deactivateBody` |

---

## WF-PP-OP — Modo operador

### Hub (`OperatorPlacementHub` + `OperatorBrandBar`)

| Elemento | Chave |
|----------|-------|
| Título / instrução | `operator.hubTitle` |
| Chip Todos | `operator.hubFilterAll` |
| Chip Postos | `operator.hubFilterWorkCenter` |
| Chip Máquinas | `operator.hubFilterMachine` |
| Chip Equipamentos | `operator.hubFilterEquipment` |
| Busca | `operator.hubSearch` |
| Meta do card | `operator.hubCardMeta` |

### Picker (`OperatorDevicePicker`)

| Elemento | Chave |
|----------|-------|
| Título | `operator.pickerTitle` |
| Badge contador | `operator.pickerBadgeCounter` |
| Badge sensor | `operator.pickerBadgeSensor` |

### Superfície contador

| Elemento | Chave |
|----------|-------|
| Status bar | `operator.statusBar` |
| Valor golpes | `operator.counterValue` |
| Botão + | `operator.counterIncrement` |
| Botão − | `operator.counterDecrement` |
| Limpar | `operator.counterClear` |
| Trocar posto | `operator.changePlacement` |
| Banner offline | `operator.offlineBanner` |

### Superfície gauge (P1)

| Elemento | Chave |
|----------|-------|
| Valor métrica | `operator.gaugeValue` |
| Atualizar | `operator.gaugeRefresh` |

### Superfícies P2 (temperatura, rotação, combo, meta, alerta)

| Elemento | Chave | Wireframe |
|----------|-------|-----------|
| Temperatura | `operator.tempValue` | WF-PP-OP-TEMP |
| Margem até teto | `operator.tempMargin` | WF-PP-OP-TEMP |
| Anel de rotação | `operator.rotationRing` | WF-PP-OP-ROTATION |
| Board do posto | `operator.comboBoard` | WF-PP-OP-COMBO |
| Barra de meta | `operator.goalBar` | WF-PP-OP-GOAL |
| Gráfico % | `operator.pctChart` | WF-PP-OP-PCT |
| Banner alerta | `operator.alertBanner` | WF-PP-OP-ALERT |

Spec: [OPERATOR-SURFACES-P2.md](./OPERATOR-SURFACES-P2.md).

### Chrome

| Elemento | Chave |
|----------|-------|
| Link painel admin | `operator.adminLink` |

---

## Badges (`AnchorTypeBadge`, `DeviceStatusBadge`, role pills)

| Badge | Chave |
|-------|-------|
| Posto | `badges.anchorWorkCenter` |
| Máquina | `badges.anchorMachine` |
| Equipamento | `badges.anchorEquipment` |
| Área | `badges.anchorArea` |
| Avulso | `badges.anchorStandalone` |
| Contador | `badges.roleCounter` |
| Sensor | `badges.roleGauge` |
| Telemetria | `badges.roleTelemetry` |
| Online | `badges.statusOnline` |
| Offline | `badges.statusOffline` |
| Sem amarração | `badges.statusNoBinding` |
| Desativado | `badges.statusDisabled` |

---

## Textos de seção (copy visível, não só tooltip)

Estes textos aparecem **abaixo do título** da seção (prosa curta), além do help no `?`:

| Local | Chave `PP_SECTION_INTROS` | Copy |
|-------|---------------------------|------|
| Form dispositivo | `form.device` | Informe o hardware na rede. O driver define o que será medido (golpes, rpm, temperatura). |
| Form amarração | `form.placement` | Onde o sensor está instalado. CT TOTVS só é obrigatório para postos PCP. |
| Form TOTVS `<details>` | `form.totvsDetails` | Opcional. Facilita cruzar com fila e apontamento do PCP. |
| Hub operador | `operator.hub` | Toque no local onde você vai trabalhar. A escolha fica salva neste tablet. |
| Detalhe histórico | `detail.history` | Leituras gravadas automaticamente pelo intervalo de poll ou por comando manual. |
| Painel devices | `panel.devices` | Visão consolidada dos dispositivos IoT da filial. |

Copy visível: [`content/sectionIntros.ts`](./content/sectionIntros.ts) (`PP_SECTION_INTROS`) — prosa abaixo do título; helps técnicos só em `PP_HELP`.

---

## Checklist E5 (helps)

- [ ] `sectionIntros.ts` copiado junto com helps
- [ ] Todo `FieldLabel` do form tem `hint`
- [ ] Todo `SectionHintLabel` das seções WF-PP-02/03 tem hint
- [ ] KPIs painel com hint no `SimpleKpiCard` (prop `hint` ou wrapper kit)
- [ ] Colunas tabela com header tooltip onde kit suportar
- [ ] Modais: corpo alinhado a `modals.*`
- [ ] Operador: hints nos botões via `aria-label` + texto curto visível
- [ ] Teste vitest: `getPpHelp("form.ip")` retorna string; todas chaves WF cobertas

---

## Referências

- [DESIGN-FRONTEND.md §3.7](./DESIGN-FRONTEND.md)
- [WIREFRAMES.md](./WIREFRAMES.md)
- `plugins/maintenance/src/content/helpTooltips.ts` — padrão `DM_HELP`
