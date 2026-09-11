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

Ícone `?` standalone **não** é o padrão quando já existe label ou controle: o próprio elemento é o gatilho (`FieldLabel`, `SectionHintLabel`, `HintAction`, `PpContextMenuItem` com `hintTrigger="label"`). Ver `FieldLabel` / `SectionHintLabel` / `HintAction` / `ContextMenuItem` em `@delpi/plugin-ui`.

---

## WF-PP-00 — Shell admin (`ProductionPulseShell` + `PpTopBar`)

| Elemento UI | Chave help | Texto |
|-------------|------------|-------|
| TopBar áreas | `shell.topBar` | Admin · Operador (☰ quando não couber) |
| Título hero | `shell.heroTitle` | Monitoramento IoT na filial… |
| Filial | `shell.heroFilial` | Filial operacional… |
| [Atualizar tudo] | `shell.pollAll` | Poll imediato em todos ativos… |

## WF-PP-OTA-HUB — Admin mapa

Superfície única Admin: canvas fullscreen + `HubMapChrome` colapsável à direita (contexto, nav, Novo, busca/filtros, diagnósticos), catálogos/jobs em `PpDetailDialog`, detalhe/CRUD em modais host-contained e popovers ancorados (`AnchoredPanelPortal`). Feedback transitório via FloatingNotice; confirmações destrutivas via ConfirmModalPanel.

**Single Surface Principle:** resumo do nó e menu ⋯ = uma moldura (`variant="bare"` + `delpi-ui-popover-surface`); classes `pp-*` só layout. Hub chrome recolhido = `IconButton` sem card externo; Saúde/Conexões = disclosure inline. Ver [DESIGN-FRONTEND §3.6.1](./DESIGN-FRONTEND.md).

**Conexões:** linha sólida = vínculo OTA explícito; sem linha = sem vínculo. Compatibilidade de driver só no **modo vínculo** (menu Vincular / arraste FW→IoT) — sem linha tracejada permanente. **Lifecycle:** Desativar / Arquivar (reversível) · Excluir permanentemente (irreversível, dependency-aware, typed confirm). **Menu ⋯:** cada item com `hint` no próprio label (`PpContextMenuItem` / `PP_HELP.hub.menu*`). **Legenda:** título via `PpSectionHintLabel` (sem `HelpTooltip` standalone).

Helps: `PP_HELP.hub.*`, `PP_HELP.otaLinks.*`.

| Elemento UI | Chave help |
|-------------|------------|
| Hero / CTAs | `hub.hero` · `hub.newMenu` · `hub.newDevice` · `hub.newFirmware` · `hub.refresh` · `hub.collapseFilters` |
| KPIs / frota | `hub.fleetHealth` · `hub.kpiPublished` · `hub.kpiLinked` · `hub.kpiUpdating` · `hub.kpiFailed` |
| Canvas / legenda | `hub.edgeModesHint` · `hub.edgeSolid` · `hub.edgeNone` · `hub.linkMode*` |
| Menu ⋯ IoT/FW | `hub.menuEditDevice` … `hub.menuArchiveFirmware` · `hub.startLinkFrom*` |
| Catálogo | `hub.catalog` · `hub.catalogSearch` · `hub.firmwaresCatalogList` · `hub.firmwareVersionSwitcher` |
| Form OTA / jobs | `hub.jobs` · `ota.jobCreate` · `ota.jobsList` |

## WF-PP-FW-NEW — Novo firmware

| Elemento UI | Chave help |
|-------------|------------|
| Identificação | `firmwareCreate.sectionIdentity` · `ota.firmwareKey` |
| Sketch .ino | `firmwareCreate.sectionSource` · `firmwareCreate.sourceField` |
| Binário .bin | `firmwareCreate.sectionArtifact` · `firmwareCreate.artifactField` |
| Ações | `firmwareCreate.saveDraft` · `firmwareCreate.publish` |

**Nova versão (mesma família):** modal `firmware-version` · título «Nova versão» · `firmwareCreate.breadcrumbNewVersion` · família OTA travada (`lockFamily`).

## WF-PP-FW-DETAIL — Detalhe versão firmware

| Elemento UI | Chave help |
|-------------|------------|
| Switcher de versão | `hub.firmwareVersionSwitcher` |
| Metadados | `ota.detailMetadata` |
| Sketch | `ota.detailSource` · `ota.sourceTextarea` |
| Artefato | `ota.detailArtifact` · `ota.artifactImmutable` |
| Publicar | `ota.publishVersion` · `ota.publishConfirmTitle` |
| Arquivar | `ota.archiveFirmware` |

## WF-PP-DEVICE-FW — Aba firmware do IoT

| Elemento UI | Chave help |
|-------------|------------|
| Sketch instalado | `detail.firmwareInstalledSource` |
| Sketch alvo | `detail.firmwareTargetSource` |
| Legado device | `detail.firmwareLegacySource` · `detail.firmwareLegacyBadge` |
| Desativar | `detail.deactivate` · `modals.deactivateTitle` |

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

### OTA (P4) — `PP_HELP.ota` + `PP_HELP.otaLinks` + canvas hub

| Elemento | Chave |
|----------|-------|
| Campos publish/campanha | `ota.firmwareKey`, `ota.version`, `ota.jobTrigger`, `ota.archiveConfirm*`, … |
| Hub `/firmware-links` | `otaLinks.hero`, `refresh`, `canvas`, `disconnect`, `launchOta`, `oneFirmwarePerDevice` |
| KPI frota | `ota.openCatalog` / `ota.jobsHero` (titleHint) |
| Botões do hero (painel/OTA/detalhe) | `PpHintAction` + `shell.backToPanel`, `ota.openCatalog` / `openLinks`, `otaLinks.refresh`, `detail.editDevice` / `pollNow`, `shell.modeOperator`, `operator.adminLink` |
| Progresso OTA | `ota.downloadProgress`, `ota.phase.*` (incl. wakePending/Accepted/Failed), `ota.progressPhases`, `ota.runningVersion`, `ota.status.*`, `ota.operation.*`, `ota.failureMessages.*` |

Wireframes: WF-PP-OTA-01…05 (hub em `/firmware-links`; `/firmware-jobs` redireciona). Homologação: [HOMOLOGACAO-OTA-P4.md](./HOMOLOGACAO-OTA-P4.md).

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
| Driver / Tipo de driver | `form.driver` / `ota.driverType` |
| Família OTA | `ota.firmwareFamily` |

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

**Default create (2026-09):** novo IoT nasce com `anchorType=standalone` (Avulso) e persiste binding explícito; edit não converte `no_binding` legado. Binding operacional ≠ vínculo OTA.

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

Estes textos aparecem **abaixo do título** da seção (prosa curta), além do help no próprio título/label:

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
