import { describe, expect, it } from "vitest";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { dirname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");

function listSourceFiles(dir: string): string[] {
  const entries = readdirSync(dir);
  const files: string[] = [];
  for (const entry of entries) {
    const path = join(dir, entry);
    const stat = statSync(path);
    if (stat.isDirectory()) {
      files.push(...listSourceFiles(path));
      continue;
    }
    if (/\.(tsx|ts)$/.test(entry) && !entry.endsWith(".test.ts") && !entry.endsWith(".test.tsx")) {
      files.push(path);
    }
  }
  return files;
}

function readRelative(pathFromSrc: string): string {
  return readFileSync(join(root, pathFromSrc), "utf8");
}

describe("production-pulse kit contracts", () => {
  const sources = listSourceFiles(root).map((abs) => ({
    rel: relative(root, abs),
    source: readFileSync(abs, "utf8"),
  }));

  it("usa PpDataTable canônico — nunca DataTable cru do kit", () => {
    for (const { rel, source } of sources) {
      if (rel === "components/data/dataTableUi.tsx") continue;
      expect(source, rel).not.toMatch(/\bDataTable\b.*@delpi\/plugin-ui/);
      expect(source, rel).not.toMatch(/dataTableBemClasses\s*\(/);
    }
    expect(readRelative("components/DeviceTable.tsx")).toMatch(/PpDataTable/);
    expect(readRelative("components/DeviceCard.tsx")).toMatch(/PpDataRecordCard/);
    expect(readRelative("components/DeviceCard.tsx")).not.toMatch(/pp-device-card__ghost/);
    expect(readRelative("components/DeviceCard.tsx")).not.toMatch(/pp-device-card-hit/);
    expect(readRelative("components/DeviceCard.tsx")).not.toMatch(/\bhref=/);
    expect(readRelative("components/DeviceCard.tsx")).not.toMatch(/onNavigate/);
    expect(readRelative("components/DeviceCard.tsx")).toMatch(/cardOpenDetail/);
    expect(readRelative("index.css")).toMatch(/\.pp-data-record-card \{\s*cursor: default;/s);
    expect(readRelative("components/data/dataTableUi.tsx")).toMatch(/labels={LABELS}/);
    expect(readRelative("components/data/dataTableUi.tsx")).toMatch(/loadingMessage:/);
  });

  it("usa FiltersRow canônico — sem flex externo que encolhe o shell", () => {
    for (const { rel, source } of sources) {
      expect(source, rel).not.toMatch(/pp-filters-wrap/);
      expect(source, rel).not.toMatch(/createFilterBarShell/);
    }
    const filtersBar = readRelative("components/DeviceFiltersBar.tsx");
    expect(filtersBar).toMatch(/PpFiltersRow/);
    expect(filtersBar).toMatch(/PpFilterToolbarRowClasses/);
    expect(filtersBar).not.toMatch(/pp-filters-wrap/);
    expect(filtersBar).not.toMatch(/PpFilterBarShell/);
    expect(readRelative("components/data/filtersUi.tsx")).toMatch(/PpFiltersRow/);
  });

  it("hub operador usa busca automática do kit — sem botão Buscar", () => {
    const hub = readRelative("pages/operator/OperatorPlacementHub.tsx");
    expect(hub).toMatch(/PpCatalogSearchBar/);
    expect(hub).not.toMatch(/Buscar/);
    expect(hub).not.toMatch(/pp-operator-hub__search-actions/);
  });

  it("shell admin usa PpTopBar — Admin | Operador", () => {
    expect(readRelative("App.tsx")).toMatch(/ProductionPulseShell/);
    expect(readRelative("App.tsx")).toMatch(/isOperatorRoute/);
    expect(readRelative("components/ProductionPulseShell.tsx")).toMatch(/PpTopBar/);
    expect(readRelative("components/ProductionPulseShell.tsx")).toMatch(/resolvePulseNavId/);
    expect(readRelative("components/ProductionPulseShell.tsx")).not.toMatch(/collapseLabel/);
    expect(readRelative("constants/routes.ts")).toMatch(/firmwareDetail/);
    expect(readRelative("constants/routes.ts")).toMatch(/firmwareNew/);
    expect(readRelative("content/shellNav.ts")).toMatch(/id: "admin"/);
    expect(readRelative("content/shellNav.ts")).toMatch(/id: "operator"/);
    expect(readRelative("content/shellNav.ts")).not.toMatch(/id: "panel"/);
    expect(readRelative("content/shellNav.ts")).not.toMatch(/id: "hub"/);
    expect(readRelative("utils/resolvePulseNavId.ts")).toMatch(/"admin" \| "operator"/);
    expect(readRelative("pages/PanelPage.tsx")).not.toMatch(/productionPulseFirmwaresPath/);
    expect(readRelative("pages/FirmwareLinksPage.tsx")).not.toMatch(/productionPulseFirmwaresPath/);
  });

  it("operador permanece fora do ProductionPulseShell (freeze)", () => {
    const app = readRelative("App.tsx");
    expect(app).toMatch(/isOperatorRoute \? \(\s*adminContent\s*\)/);
    expect(readRelative("pages/operator/OperatorPage.tsx")).not.toMatch(/ProductionPulseShell/);
    expect(readRelative("pages/operator/OperatorPage.tsx")).not.toMatch(/PpTopBar/);
  });

  it("OTA: Admin mapa fullscreen, popovers, painéis e modais kit-first", () => {
    expect(readRelative("constants/routes.ts")).toMatch(/firmwares/);
    expect(readRelative("constants/routes.ts")).toMatch(/firmware-jobs/);
    expect(readRelative("constants/routes.ts")).toMatch(/firmware-links/);
    expect(readRelative("constants/routes.ts")).toMatch(/entity\?/);
    expect(readRelative("constants/routes.ts")).toMatch(/modal\?/);
    expect(readRelative("content/helpTooltips.ts")).toMatch(/ota:\s*\{/);
    expect(readRelative("content/helpTooltips.ts")).toMatch(/otaLinks:\s*\{/);
    expect(readRelative("content/helpTooltips.ts")).toMatch(/awaitingChip|awaitingDevice/);
    expect(readRelative("content/helpTooltips.ts")).toMatch(/archiveConfirmTitle|archiveFirmware/);
    expect(readRelative("pages/FirmwareCreatePage.tsx")).toMatch(/PP_HELP\.ota\.firmwareFamily/);
    expect(readRelative("pages/FirmwareCreatePage.tsx")).toMatch(/Família OTA/);
    expect(readRelative("pages/FirmwareCreatePage.tsx")).toMatch(/Tipo de driver/);
    expect(readRelative("pages/FirmwareCreatePage.tsx")).toMatch(/publishFirmware/);
    expect(readRelative("pages/FirmwareCreatePage.tsx")).toMatch(/embedded/);
    expect(readRelative("pages/FirmwareCreatePage.tsx")).toMatch(/onOpenDriverCreate/);
    expect(readRelative("pages/DriverFormPage.tsx")).toMatch(/createDriver|patchDriver/);
    expect(readRelative("pages/DriverDetailPage.tsx")).toMatch(/archiveDriver|unarchiveDriver/);
    expect(readRelative("pages/FirmwareLinksPage.tsx")).toMatch(/FirmwareCatalogListItem/);
    expect(readRelative("pages/FirmwareLinksPage.tsx")).toMatch(/DriverTypeListItem/);
    expect(readRelative("pages/FirmwareLinksPage.tsx")).toMatch(/panel === \"drivers\"/);
    expect(readRelative("pages/FirmwareLinksPage.tsx")).toMatch(/panel === \"devices\"/);
    expect(readRelative("pages/FirmwareLinksPage.tsx")).toMatch(/firmwaresDialogTitle/);
    expect(readRelative("pages/FirmwareLinksPage.tsx")).toMatch(/driversDialogTitle/);
    expect(readRelative("pages/FirmwareLinksPage.tsx")).toMatch(/devicesDialogTitle/);
    expect(readRelative("pages/FirmwareLinksPage.tsx")).not.toMatch(/AdminSidePanel/);
    expect(readRelative("pages/FirmwareLinksPage.tsx")).toMatch(/DeviceCatalogPanel/);
    expect(readRelative("pages/FirmwareLinksPage.tsx")).toMatch(/driver-create/);
    expect(readRelative("api/productionPulseApi.ts")).toMatch(/listDrivers/);
    expect(readRelative("api/productionPulseApi.ts")).toMatch(/archiveDriver/);
    expect(readRelative("utils/adminHubUiState.ts")).toMatch(/\"drivers\"/);
    expect(readRelative("utils/adminHubUiState.ts")).toMatch(/driver-create/);
    expect(readRelative("utils/adminHubUiState.ts")).toMatch(/type: \"driver\"/);
    expect(readRelative("pages/FirmwareDetailPage.tsx")).toMatch(/publishFirmwareVersion/);
    expect(readRelative("pages/FirmwareDetailPage.tsx")).toMatch(/attachFirmwareArtifact/);
    expect(readRelative("pages/FirmwareDetailPage.tsx")).toMatch(/embedded/);
    expect(readRelative("pages/FirmwareDetailPage.tsx")).toMatch(/PpPageHero/);
    expect(readRelative("pages/FirmwareDetailPage.tsx")).toMatch(/pp-detail-hero-actions/);
    expect(readRelative("pages/FirmwareDetailPage.tsx")).toMatch(/pp-hero-brand-btn/);
    expect(readRelative("pages/FirmwareDetailPage.tsx")).toMatch(/DetailLightCard/);
    expect(readRelative("pages/FirmwareDetailPage.tsx")).not.toMatch(/pp-embedded-fw-actions/);
    expect(readRelative("pages/DriverDetailPage.tsx")).toMatch(/PpPageHero/);
    expect(readRelative("pages/DriverDetailPage.tsx")).toMatch(/pp-detail-hero-actions/);
    expect(readRelative("pages/DriverDetailPage.tsx")).toMatch(/pp-hero-brand-btn/);
    expect(readRelative("pages/DriverDetailPage.tsx")).toMatch(/DetailLightCard/);
    expect(readRelative("pages/DriverDetailPage.tsx")).toMatch(/DetailCommandChips/);
    expect(readRelative("pages/DeviceDetailPage.tsx")).toMatch(/pp-detail-hero-actions/);
    expect(readRelative("pages/DeviceDetailPage.tsx")).toMatch(/liveConnectivityIssue/);
    expect(readRelative("pages/DeviceDetailPage.tsx")).toMatch(/DetailStatusBanner/);
    expect(readRelative("hooks/useDeviceDetail.ts")).toMatch(/liveConnectivityIssue/);
    expect(readRelative("hooks/useDeviceDetail.ts")).toMatch(/isDeviceConnectivityError/);
    expect(readRelative("content/helpTooltips.ts")).toMatch(/liveOfflineTitle/);
    expect(readRelative("pages/FirmwareJobsPage.tsx")).toMatch(/productionPulseFirmwareLinksPath/);
    expect(readRelative("pages/FirmwareJobsPage.tsx")).toMatch(/Redirecionando/);
    expect(readRelative("pages/FirmwaresPage.tsx")).toMatch(/productionPulseFirmwareLinksPath/);
    expect(readRelative("pages/FirmwaresPage.tsx")).toMatch(/Redirecionando/);
    expect(readRelative("pages/FirmwaresPage.tsx")).not.toMatch(/PpDataTable/);
    expect(readRelative("pages/FirmwareLinksPage.tsx")).toMatch(/PP_HELP\.ota/);
    expect(readRelative("pages/FirmwareLinksPage.tsx")).toMatch(/PP_HELP\.otaLinks|PP_HELP\.hub/);
    expect(readRelative("pages/FirmwareLinksPage.tsx")).toMatch(/createFirmwareUpdateJob/);
    expect(readRelative("pages/FirmwareLinksPage.tsx")).toMatch(/reloadJobs\(\{\s*soft:\s*true/);
    expect(readRelative("pages/FirmwareLinksPage.tsx")).toMatch(/useProductionPulseOtaMonitor/);
    expect(readRelative("pages/FirmwareLinksPage.tsx")).toMatch(/OtaTargetProgress/);
    expect(readRelative("pages/FirmwareLinksPage.tsx")).toMatch(/structuralError/);
    expect(readRelative("pages/FirmwareLinksPage.tsx")).toMatch(/PpDataTable/);
    expect(readRelative("pages/FirmwareLinksPage.tsx")).toMatch(/PpCatalogSearchBar/);
    expect(readRelative("pages/FirmwareLinksPage.tsx")).toMatch(/PpWorkbenchDialog/);
    expect(readRelative("pages/FirmwareLinksPage.tsx")).toMatch(/PpDetailDialog/);
    expect(readRelative("pages/FirmwareLinksPage.tsx")).toMatch(/PpConfirmDialog/);
    expect(readRelative("pages/FirmwareLinksPage.tsx")).toMatch(/PpFloatingNotices/);
    expect(readRelative("pages/FirmwareLinksPage.tsx")).not.toMatch(/PpHostContainedDrawer/);
    expect(readRelative("pages/FirmwareLinksPage.tsx")).toMatch(/AnchoredPanelPortal|EntitySummaryPopover/);
    expect(readRelative("pages/FirmwareLinksPage.tsx")).toMatch(/HubOtaKpiChips/);
    expect(readRelative("pages/FirmwareLinksPage.tsx")).toMatch(
      /current\.openLayer !== \"menu\"/,
    );
    expect(readRelative("components/EntityContextLayers.tsx")).toMatch(/hint=\{PP_HELP\.hub\.menu/);
    expect(readRelative("components/EntityContextLayers.tsx")).toMatch(/PpContextMenuItem/);
    expect(readRelative("components/EntityContextLayers.tsx")).not.toMatch(/<ContextMenuItem\b/);
    expect(readRelative("components/EntityContextLayers.tsx")).toMatch(/icon=\{Pencil\}|icon=\{Archive\}/);
    expect(readRelative("pages/FirmwareLinksPage.tsx")).toMatch(/panelDevices|panelFirmwares|panelJobs/);
    expect(readRelative("components/HubCanvasLegend.tsx")).toMatch(/PpSectionHintLabel/);
    expect(readRelative("components/HubCanvasLegend.tsx")).not.toMatch(/HelpTooltip/);
    expect(readRelative("content/helpTooltips.ts")).toMatch(/menuArchiveFirmware/);
    expect(readRelative("content/helpTooltips.ts")).toMatch(/menuUnlinkFirmware/);
    expect(readRelative("pages/FirmwareLinksPage.tsx")).toMatch(/HubCanvasLegend/);
    expect(readRelative("components/HubCanvasLegend.tsx")).toMatch(/edgeSolid|linkModeTitle/);
    expect(readRelative("components/HubCanvasLegend.tsx")).not.toMatch(/edgeDashed/);
    expect(readRelative("app/productionPulseUi.tsx")).toMatch(/hintTrigger=\{props\.hintTrigger \?\? "label"\}/);
    expect(readRelative("components/detail/DeviceMetricHero.tsx")).toMatch(/PpHintAction/);
    expect(readRelative("components/detail/DeviceMetricHero.tsx")).not.toMatch(
      /title=\{PP_HELP\.detail\.factoryReset\}/,
    );
    expect(readRelative("utils/firmwareLinkGraph.ts")).toMatch(/compatibleDriverKeys/);
    expect(readRelative("utils/firmwareLinkGraph.ts")).toMatch(/isFirmwareDeviceCompatible/);
    expect(readRelative("utils/firmwareLinkGraph.ts")).not.toMatch(/"inherited"|kind: "inherited"/);
    expect(readRelative("components/FirmwareDeviceLinkCanvas.tsx")).toMatch(/\bBan\b/);
    expect(readRelative("components/FirmwareDeviceLinkCanvas.tsx")).toMatch(/linkMode/);
    expect(readRelative("components/FirmwareDeviceLinkCanvas.tsx")).toMatch(/putDeviceFirmwareLink/);
    expect(readRelative("index.css")).toMatch(/pp-map-node-compatible-pulse/);
    expect(readRelative("index.css")).toMatch(
      /\.pp-firmware-link-canvas-wrap--linking\s+\.pp-map-node--connection-compatible/,
    );
    expect(readRelative("index.css")).toMatch(
      /\.pp-firmware-link-canvas-wrap--linking\s+\.pp-map-node--connection-incompatible/,
    );
    expect(readRelative("pages/FirmwareLinksPage.tsx")).toMatch(/onRequestLink|setLinkMode/);
    expect(readRelative("components/EntityContextLayers.tsx")).toMatch(/Vincular IoT|Vincular firmware/);
    expect(readRelative("content/helpTooltips.ts")).toMatch(/softDeleteDeviceConfirmTitle/);
    expect(readRelative("content/helpTooltips.ts")).toMatch(/edgeModesHint/);
    expect(readRelative("content/helpTooltips.ts")).toMatch(/startLinkFromFirmware/);
    expect(readRelative("components/EntityContextLayers.tsx")).toMatch(/soft delete/);
    expect(readRelative("pages/FirmwareLinksPage.tsx")).toMatch(/pp-admin-hub/);
    expect(readRelative("pages/FirmwareLinksPage.tsx")).toMatch(/pp-admin-bottom-bar/);
    expect(readRelative("pages/FirmwareLinksPage.tsx")).not.toMatch(/Campanhas OTA/);
    expect(readRelative("pages/FirmwareLinksPage.tsx")).not.toMatch(
      /<PpSectionCard title="Targets/,
    );
    expect(readRelative("components/HubOtaKpiChips.tsx")).toMatch(/AnchoredPanelPortal/);
    expect(readRelative("utils/hubOtaKpis.ts")).toMatch(/computeHubOtaKpis/);
    expect(readRelative("utils/hubOtaKpis.ts")).toMatch(/explicitFirmwareKey/);
    expect(readRelative("utils/adminHubUiState.ts")).toMatch(/AdminHubUiState/);
    expect(readRelative("utils/adminHubUiState.ts")).toMatch(/AdminHubModal/);
    expect(readRelative("utils/adminHubUiState.ts")).toMatch(/parseAdminModal/);
    expect(readRelative("pages/PanelPage.tsx")).not.toMatch(/FirmwareOtaKpiStrip/);
    expect(readRelative("pages/PanelPage.tsx")).not.toMatch(/productionPulseFirmwareJobsPath/);
    expect(readRelative("pages/FirmwareLinksPage.tsx")).toMatch(/fetchDevices/);
    expect(readRelative("pages/FirmwareLinksPage.tsx")).toMatch(/FirmwareDeviceLinkCanvas/);
    expect(readRelative("App.tsx")).toMatch(/firmwareJobs/);
    expect(readRelative("App.tsx")).toMatch(/productionPulseFirmwareLinksPath/);
    expect(readRelative("App.tsx")).toMatch(/dashboard-page--fill/);
    expect(readRelative("App.tsx")).toMatch(/modal:\s*"device-create"/);
    expect(readRelative("components/FirmwareDeviceLinkCanvas.tsx")).toMatch(/@xyflow\/react/);
    expect(readRelative("components/FirmwareDeviceLinkCanvas.tsx")).toMatch(/MiniMap/);
    expect(readRelative("components/FirmwareDeviceLinkCanvas.tsx")).toMatch(/ADMIN_HUB_MINIMAP_NODE_THRESHOLD/);
    expect(readRelative("components/FirmwareDeviceLinkCanvas.tsx")).toMatch(/FileCode/);
    expect(readRelative("components/FirmwareDeviceLinkCanvas.tsx")).toMatch(/Cpu/);
    expect(readRelative("components/FirmwareDeviceLinkCanvas.tsx")).not.toMatch(/Atualizar vinculados/);
    expect(readRelative("components/FirmwareDeviceLinkCanvas.tsx")).toMatch(/Panel/);
    expect(readRelative("components/FirmwareDeviceLinkCanvas.tsx")).toMatch(/useDelpiDarkMode/);
    expect(readRelative("components/FirmwareDeviceLinkCanvas.tsx")).toMatch(/colorMode=\{colorMode\}/);
    expect(readRelative("components/FirmwareDeviceLinkCanvas.tsx")).toMatch(/applyEdgeChanges/);
    expect(readRelative("components/FirmwareDeviceLinkCanvas.tsx")).toMatch(/deleteKeyCode/);
    expect(readRelative("components/FirmwareDeviceLinkCanvas.tsx")).toMatch(/onUnlink/);
    expect(readRelative("components/FirmwareDeviceLinkCanvas.tsx")).toMatch(/nodesFocusable/);
    expect(readRelative("components/FirmwareDeviceLinkCanvas.tsx")).toMatch(/edgesFocusable/);
    expect(readRelative("components/FirmwareDeviceLinkCanvas.tsx")).toMatch(/aria-label=/);
    expect(readRelative("components/FirmwareDeviceLinkCanvas.tsx")).toMatch(/aria-haspopup/);
    expect(readRelative("components/detail/DeviceFirmwareTab.tsx")).toMatch(
      /createFirmwareUpdateJob/,
    );
    expect(readRelative("components/detail/DeviceFirmwareTab.tsx")).toMatch(
      /fetchDeviceFirmwareSources/,
    );
    expect(readRelative("components/detail/DeviceFirmwareTab.tsx")).toMatch(
      /productionPulseFirmwareLinksPath/,
    );
    expect(readRelative("pages/DeviceDetailPage.tsx")).toMatch(/disableDevice/);
    expect(readRelative("pages/DeviceDetailPage.tsx")).toMatch(/embedded/);
    expect(readRelative("pages/DeviceFormPage.tsx")).toMatch(/embedded/);
    expect(readRelative("pages/DeviceFormPage.tsx")).not.toMatch(/TestConnectionModal/);
    expect(readRelative("components/DeviceForm.tsx")).not.toMatch(/firmwareSource/);
    expect(readRelative("utils/otaStatusLabels.ts")).toMatch(/formatOtaProgressDisplay/);
    expect(readRelative("utils/otaStatusLabels.ts")).toMatch(/resolveOtaProgressPercent/);
    expect(readRelative("content/helpTooltips.ts")).toMatch(/Aguardando dispositivo/);
    expect(readRelative("index.css")).toMatch(/pp-firmware-link-canvas--fill|pp-admin-hub/);
    expect(readRelative("index.css")).toMatch(/pp-admin-bottom-bar/);
    expect(readRelative("index.css")).toMatch(/pp-ota-state/);
    expect(readRelative("index.css")).toMatch(/pp-map-node__ota/);
    expect(readRelative("index.css")).not.toMatch(/\.delpi-ui-/);
    expect(readRelative("app/productionPulseUi.tsx")).toMatch(/PpHostContainedDrawer/);
    expect(readRelative("app/productionPulseUi.tsx")).toMatch(/PpDetailDialog/);
    expect(readRelative("app/productionPulseUi.tsx")).toMatch(/PpWorkbenchDialog/);
    expect(readRelative("app/productionPulseUi.tsx")).toMatch(/PpConfirmDialog/);
    expect(readRelative("app/productionPulseUi.tsx")).toMatch(/PpFloatingNotices/);
    expect(readRelative("app/productionPulseUi.tsx")).toMatch(/AnchoredPanelPortal/);
    expect(readRelative("components/AdminSidePanel.tsx")).toMatch(/PpWorkbenchDialog/);
  });

  it("Single Surface Principle: popovers bare + surface; sem panelRef no filho; CSS sem chrome paralelo", () => {
    const entityLayers = readRelative("components/EntityContextLayers.tsx");
    const healthChips = readRelative("components/HubOtaKpiChips.tsx");
    const css = readRelative("index.css");

    for (const source of [entityLayers, healthChips]) {
      expect(source).toMatch(/variant=["']bare["']/);
      expect(source).toMatch(/delpi-ui-popover-surface/);
      expect(source).toMatch(/density=["']compact["']/);
      expect(source).not.toMatch(/<\w[^>]*\sref=\{panelRef\}/);
    }

    expect(entityLayers).toMatch(/MoreHorizontal/);
    expect(entityLayers).toMatch(/PpIconButton/);
    expect(entityLayers).toMatch(/role=["']menu["']/);
    expect(entityLayers).toMatch(/Cpu/);
    expect(entityLayers).toMatch(/FileCode/);

    const sharedPopoverLayout = css.match(
      /\.pp-entity-summary,\s*\.pp-entity-menu\s*\{[^}]*\}/,
    )?.[0];
    const healthBlock = css.match(/\.pp-hub-health-popover\s*\{[^}]*\}/)?.[0];
    const collapsedBlock = css.match(
      /\.pp-map-overlay-stack--collapsed\s*\{[^}]*\}/,
    )?.[0];

    expect(sharedPopoverLayout).toBeTruthy();
    expect(healthBlock).toBeTruthy();
    for (const block of [sharedPopoverLayout!, healthBlock!]) {
      expect(block).not.toMatch(/background\s*:/);
      expect(block).not.toMatch(/box-shadow\s*:/);
    }

    expect(collapsedBlock).toBeTruthy();
    expect(collapsedBlock!).toMatch(/background:\s*transparent/);
    expect(collapsedBlock!).toMatch(/box-shadow:\s*none/);
    expect(collapsedBlock!).toMatch(/border:\s*0/);
    expect(readRelative("pages/FirmwareLinksPage.tsx")).toMatch(
      /pp-map-overlay-stack--collapsed/,
    );
  });

  it("Hub mobile: overlays assimétricos, labels compactáveis, MiniMap off e auto-collapse", () => {
    const css = readRelative("index.css");
    const hub = readRelative("pages/FirmwareLinksPage.tsx");
    const canvas = readRelative("components/FirmwareDeviceLinkCanvas.tsx");

    expect(css).toMatch(/\.pp-map-overlay-panel--left/);
    expect(css).toMatch(/\.pp-map-overlay-panel--right/);
    expect(css).toMatch(/pp-map-overlay-btn-label/);
    expect(css).not.toMatch(
      /@media \(max-width: 768px\) \{\s*\.pp-map-overlay-panel \{\s*max-width:\s*calc\(100vw - 1\.5rem\);/,
    );
    expect(css).toMatch(
      /\.pp-map-overlay-panel--left[\s\S]*?max-width:\s*min\(20rem,\s*calc\(100vw - 4\.5rem\)\)/,
    );
    expect(css).toMatch(
      /\.pp-map-overlay-panel--right[\s\S]*?max-width:\s*min\(11rem,\s*46vw\)/,
    );

    expect(hub).toMatch(/useViewportBucket/);
    expect(hub).toMatch(/pp-map-overlay-btn-label/);
    expect(hub).toMatch(/showMiniMap=\{!isMobile\}/);
    expect(hub).toMatch(/didAutoCollapseForMobileRef/);
    expect(canvas).toMatch(/pp-map-overlay-panel--left/);
    expect(canvas).toMatch(/pp-map-overlay-panel--right/);
  });

  it("botões do hero usam PpHintAction + PP_HELP (sem ação órfã)", () => {
    const heroPages = [
      "pages/PanelPage.tsx",
      "pages/FirmwareLinksPage.tsx",
      "pages/FirmwareDetailPage.tsx",
      "pages/DeviceDetailPage.tsx",
      "components/operator/OperatorBrandBar.tsx",
      "components/operator/CounterPadSurface.tsx",
      "components/operator/GaugeReadoutSurface.tsx",
      "pages/operator/OperatorDevicePicker.tsx",
    ];
    for (const rel of heroPages) {
      const source = readRelative(rel);
      expect(source, rel).toMatch(/PpHintAction/);
      expect(source, rel).toMatch(/hint=\{PP_HELP\./);
      const hintBlocks = source.match(/<PpHintAction\b[\s\S]*?<\/PpHintAction>/g) ?? [];
      expect(hintBlocks.length, rel).toBeGreaterThan(0);
      for (const block of hintBlocks) {
        // HintAction já exibe o balão — title= nativo duplica o tooltip do browser.
        expect(block, rel).not.toMatch(/\btitle=\{/);
      }
    }
    expect(readRelative("content/helpTooltips.ts")).toMatch(/openLinks:/);
    expect(readRelative("content/helpTooltips.ts")).toMatch(/editDevice:/);
    expect(readRelative("app/productionPulseUi.tsx")).toMatch(/PpHintAction = HintAction/);
  });

  it("botões do hero usam classe de domínio pp-hero-brand-btn com tokens de marca", () => {
    const css = readRelative("index.css");
    const detail = readRelative("pages/DeviceDetailPage.tsx");
    expect(css).toMatch(
      /\.pp-hero-brand-btn[\s\S]*--pp-hero-brand-btn-border[\s\S]*--pp-hero-brand-fg[\s\S]*--pp-hero-brand-btn-bg/,
    );
    expect(detail).toMatch(/pp-hero-brand-btn/);
    expect(css).not.toMatch(/\.delpi-ui-/);
  });

  it("FilterInputField declara type explícito no painel", () => {
    const filtersBar = readRelative("components/DeviceFiltersBar.tsx");
    expect(filtersBar).toMatch(/type="search"/);
    expect(filtersBar).not.toMatch(/onChange=\{\(event\)/);
  });

  it("StateBox usa action singular do kit — não actions", () => {
    for (const { rel, source } of sources) {
      if (!source.includes("PpStateBox")) continue;
      const withoutPageHero = source.replace(/<PpPageHero[\s\S]*?\/>/g, "");
      expect(withoutPageHero, rel).not.toMatch(/<PpStateBox[^>]*\bactions=/);
    }
  });

  it("modais de aviso usam PpHostContainedDialog — nunca ModalShell body-fixed", () => {
    const modalFiles = [
      "components/modals/TestConnectionModal.tsx",
      "components/modals/ResetCounterModal.tsx",
      "components/modals/FactoryResetModal.tsx",
      "components/modals/OperatorClearCounterModal.tsx",
      "components/modals/CommandJsonModal.tsx",
    ];
    for (const rel of modalFiles) {
      const source = readRelative(rel);
      expect(source, rel).not.toMatch(/\bModalShell\b/);
      expect(source, rel).toMatch(/PpHostContainedDialog/);
    }
    const uiKit = readRelative("app/productionPulseUi.tsx");
    expect(uiKit).toMatch(/createHostContainedModalShell/);
    expect(uiKit).toMatch(/dashboard-production-pulse/);
    expect(uiKit).toMatch(/containedLayout:\s*"dialog"/);
  });

  it("index.css não sobrescreve classes .delpi-ui-* do kit", () => {
    const css = readRelative("index.css");
    expect(css).not.toMatch(/\.delpi-ui-/);
  });

  it("inputs e selects só via ppFormFields ou filtersUi — sem HTML cru", () => {
    const kitGateways = new Set([
      "components/data/ppFormFields.tsx",
      "components/data/filtersUi.tsx",
    ]);
    const bannedKitImports = [
      /\bNativeTextControl\b/,
      /\bNativeSwitchControl\b/,
      /\bNativeTextField\b/,
      /\bNativeSelectField\b/,
      /\bNativeSelectControl\b/,
      /\bNativeTextAreaField\b/,
      /\bcreateDashboardNativeFormFields\b/,
      /\bFormSelectControl\b/,
      /\bSelectControl\b/,
      /\bFilterInputField as PluginFilterInputField\b/,
      /\bcreateDashboardFiltersKit\b/,
    ];

    for (const { rel, source } of sources) {
      if (kitGateways.has(rel)) continue;
      expect(source, rel).not.toMatch(/<input[\s/>]/);
      expect(source, rel).not.toMatch(/<select[\s/>]/);
      expect(source, rel).not.toMatch(/<textarea[\s/>]/);
      for (const pattern of bannedKitImports) {
        expect(source, rel).not.toMatch(pattern);
      }
    }

    expect(readRelative("components/DeviceForm.tsx")).toMatch(/PpNative(TextField|SelectField|InlineTextField|SwitchField)/);
    expect(readRelative("components/DeviceBindingSection.tsx")).toMatch(/PpNative(TextField|SelectField|TextAreaField)/);
    expect(readRelative("components/DeviceFiltersBar.tsx")).toMatch(/PpFilter(InputField|SelectField)/);
    expect(readRelative("components/detail/DeviceHistoryTab.tsx")).toMatch(/PpFilterInputField/);
    expect(readRelative("components/detail/DeviceHistoryTab.tsx")).toMatch(/PpSegmentToggle/);
    expect(readRelative("components/detail/DeviceHistoryTab.tsx")).toMatch(/datetime-local/);
    expect(readRelative("components/detail/DeviceHistoryTab.tsx")).not.toMatch(/Aplicar/);
    expect(readRelative("app/productionPulseUi.tsx")).toMatch(/from "\.\.\/components\/data\/ppFormFields"/);
    expect(readRelative("app/productionPulseUi.tsx")).toMatch(/from "\.\.\/components\/data\/dataTableUi"/);
    expect(readRelative("app/productionPulseUi.tsx")).toMatch(/from "\.\.\/components\/data\/filtersUi"/);
    expect(readRelative("app/productionPulseUi.tsx")).toMatch(/createDashboardFileDropzone/);
    expect(readRelative("app/productionPulseUi.tsx")).toMatch(/createDashboardAttachmentFileList/);
    expect(readRelative("app/productionPulseUi.tsx")).toMatch(/PpFirmwareArtifactField/);
    expect(readRelative("app/productionPulseUi.tsx")).toMatch(/PpFirmwareSourceField/);
    expect(readRelative("components/data/ppFormFields.tsx")).not.toMatch(/type=["']file["']/);
    expect(readRelative("pages/FirmwareCreatePage.tsx")).toMatch(/pp-firmware-create-layout/);
    expect(readRelative("pages/FirmwareCreatePage.tsx")).toMatch(/PpFirmwareArtifactField/);
    expect(readRelative("pages/FirmwareCreatePage.tsx")).toMatch(/PpFirmwareSourceField/);
    expect(readRelative("index.css")).toMatch(/pp-firmware-create-layout/);
    // Campo genérico de arquivo foi dividido em artefato (.bin) e source (.ino).
    for (const { rel, source } of sources) {
      expect(source, rel).not.toMatch(/PpFirmwareFileField/);
    }
  });

  it("consumidores importam data gateways só via productionPulseUi", () => {
    const uiHub = "app/productionPulseUi.tsx";
    const dataGateways = new Set([
      "components/data/dataTableUi.tsx",
      "components/data/filtersUi.tsx",
      "components/data/ppFormFields.tsx",
      "components/data/ppCharts.tsx",
      uiHub,
    ]);
    const bannedDirectImport =
      /from ["']\.\.?\/(?:components\/)?data\/(?:dataTableUi|filtersUi|ppFormFields|ppCharts)["']/;

    for (const { rel, source } of sources) {
      if (dataGateways.has(rel)) continue;
      expect(source, rel).not.toMatch(bannedDirectImport);
    }

    expect(readRelative("components/DeviceForm.tsx")).toMatch(/from "\.\.\/app\/productionPulseUi"/);
    expect(readRelative("components/DeviceTable.tsx")).toMatch(/from "\.\.\/app\/productionPulseUi"/);
    expect(readRelative("components/DeviceFiltersBar.tsx")).toMatch(/from "\.\.\/app\/productionPulseUi"/);
  });

  it("painel usa kit canônico — segment toggle de filial e paginação compacta", () => {
    const panel = readRelative("pages/PanelPage.tsx");
    expect(panel).toMatch(/PpSegmentToggle/);
    expect(panel).toMatch(/PpPagination/);
    expect(panel).toMatch(/embedded/);
    expect(panel).toMatch(/pp-panel-page--embedded/);
    expect(panel).not.toMatch(/FilialSwitcher/);
    expect(panel).not.toMatch(/pp-compact-pagination/);
    expect(sources.some(({ rel }) => rel === "components/FilialSwitcher.tsx")).toBe(false);
    expect(readRelative("components/DeviceCatalogPanel.tsx")).toMatch(/embedded/);
    expect(readRelative("components/AdminSidePanel.tsx")).toMatch(/size\?: "default" \| "wide"/);
    expect(readRelative("index.css")).toMatch(/pp-admin-side-panel--wide/);
    expect(readRelative("index.css")).toMatch(/pp-kpi-strip--compact/);
  });

  it("replacePanelFilters só roda no path do painel", () => {
    const hook = readRelative("hooks/usePanelFilters.ts");
    expect(hook).toMatch(/isPanelPath/);
    expect(hook).toMatch(/query\.has\("view"\)/);
  });

  it("operador contador e gauge usam shell responsivo WF-PP-OP-08", () => {
    const counter = readRelative("components/operator/CounterPadSurface.tsx");
    const gauge = readRelative("components/operator/GaugeReadoutSurface.tsx");
    const css = readRelative("index.css");
    expect(counter).toMatch(/pp-counter-pad__workspace/);
    expect(counter).toMatch(/pp-counter-pad__pad-host/);
    expect(counter).toMatch(/pp-counter-pad__controls/);
    expect(counter).toMatch(/pp-counter-pad__btn--increment/);
    expect(counter).not.toMatch(/isMobileViewport/);
    expect(counter).not.toMatch(/pp-counter-pad__pad--stack/);
    expect(gauge).toMatch(/pp-gauge-readout__workspace/);
    expect(css).toMatch(/--pp-operator-content-max/);
    expect(css).toMatch(/--pp-operator-counter-value/);
    expect(css).toMatch(/--pp-operator-content-max/);
    expect(css).toMatch(/\.pp-operator-surface[\s\S]*max-width: none/);
    expect(css).toMatch(/data-pp-viewport-short="true"/);
    expect(css).toMatch(/dashboard-page--fill/);
    expect(css).toMatch(/\.pp-counter-pad__workspace[\s\S]*flex: 1 1 auto/);
    expect(css).toMatch(/\.pp-counter-pad__stage[\s\S]*flex: 1 1 auto/);
    expect(css).not.toMatch(/grid-template-rows: auto auto auto minmax\(min-content, 1fr\) auto/);
    expect(css).not.toMatch(/\.pp-counter-pad__workspace[\s\S]*display: contents/);
    expect(css).toMatch(/container-type: inline-size/);
    expect(css).toMatch(/container-name: pp-counter-pad/);
    expect(css).toMatch(/pp-counter-pad__pad \.pp-counter-pad__btn \+ \.pp-counter-pad__btn[\s\S]*margin-inline-start: 0/);
    expect(css).toMatch(/@container pp-counter-pad \(min-width: 26rem\)/);
    expect(css).toMatch(/min-height: 0/);
    expect(css).toMatch(/min-width: 901px\)[\s\S]*pp-gauge-readout__grid/);
    expect(css).toMatch(/--pp-operator-card-min-height/);
    expect(css).toMatch(/dashboard-production-pulse--operator \.pp-device-status/);
  });

  it("modo operador device usa dashboard-page--fill (preenche área do portal)", () => {
    const app = readRelative("App.tsx");
    expect(app).toMatch(/dashboard-page--fill/);
    expect(app).toMatch(/isOperatorFillRoute/);
    expect(app).toMatch(/operatorDevice/);
  });

  it("trocar posto no operador volta ao hub — evita auto-redirect do picker", () => {
    const counter = readRelative("components/operator/CounterPadSurface.tsx");
    const gauge = readRelative("components/operator/GaugeReadoutSurface.tsx");
    const nav = readRelative("utils/operatorNavigation.ts");
    expect(counter).toMatch(/navigateOperatorPlacementHub/);
    expect(counter).not.toMatch(/productionPulseOperatorPlacementPath/);
    expect(gauge).toMatch(/navigateOperatorPlacementHub/);
    expect(gauge).not.toMatch(/productionPulseOperatorPlacementPath/);
    expect(nav).toMatch(/productionPulseOperatorPath/);
  });

  it("router hook escuta popstate e lê pathname do browser (não só do host)", () => {
    const hook = readRelative("hooks/useProductionPulseRouterPath.ts");
    expect(hook).toMatch(/addEventListener\("popstate"/);
    expect(hook).toMatch(/routeEpoch/);
    expect(hook).toMatch(/readPathname\(\)/);
    expect(hook).toMatch(/readSearch\(\)/);
    expect(hook).not.toMatch(/setPathname\(pathnameFromHost\)/);
  });

  it("textos de ação e modal não ficam hardcoded fora de helpTooltips", () => {
    const contentPaths = new Set(["content/helpTooltips.ts", "content/deviceApiMessages.ts"]);
    for (const { rel, source } of sources) {
      if (contentPaths.has(rel) || !rel.endsWith(".tsx")) continue;
      expect(source, rel).not.toMatch(/>\s*Poll\s*</);
      expect(source, rel).not.toMatch(/"Poll agora"/);
      expect(source, rel).not.toMatch(/"Testar conexão"/);
    }
    expect(readRelative("components/modals/TestConnectionModal.tsx")).toMatch(/PP_HELP\.modals/);
  });

  it("gráficos só via ppCharts — sem imports diretos do pacote de charts do kit", () => {
    const chartGateways = new Set(["components/data/ppCharts.tsx"]);
    const bannedChartImports = [
      /\bAreaSeriesChart\b/,
      /\bComparativeAreaChart\b/,
      /\bLineSeriesChart\b/,
      /\bBarSeriesChart\b/,
      /\bConfigurableSeriesChart\b/,
      /\bSeriesChartPrimitive\b/,
      /\bChartCard\b/,
      /\bchartCardBemClasses\b/,
    ];

    for (const { rel, source } of sources) {
      if (chartGateways.has(rel)) continue;
      for (const pattern of bannedChartImports) {
        expect(source, rel).not.toMatch(pattern);
      }
    }

    expect(readRelative("components/detail/DeviceOverviewTab.tsx")).toMatch(/PpReadingsAreaChart/);
    expect(readRelative("components/detail/DeviceHistoryTab.tsx")).toMatch(/PpReadingsAreaChart/);
    expect(readRelative("components/detail/DeviceHistoryTab.tsx")).toMatch(/PpChartCard/);
    expect(readRelative("components/detail/DeviceHistoryTab.tsx")).toMatch(
      /resolveHistoryReadingsResolution/,
    );
    expect(readRelative("app/productionPulseUi.tsx")).toMatch(/from "\.\.\/components\/data\/ppCharts"/);
    expect(readRelative("components/data/ppCharts.tsx")).toMatch(/ComparativeAreaChart/);
    expect(readRelative("components/data/ppCharts.tsx")).toMatch(/useDelpiDarkMode/);
    expect(readRelative("components/data/ppCharts.tsx")).toMatch(/ChartCard/);
    expect(readRelative("components/data/ppChartConfig.ts")).toMatch(/buildPpReadingsChartSeries/);
    expect(readRelative("components/data/ppFormFields.tsx")).toMatch(/searchable = true/);
    expect(readRelative("components/data/filtersUi.tsx")).toMatch(/searchable = true/);
  });

  it("hero usa paleta brand do operador em todo o plugin", () => {
    const css = readRelative("index.css");
    expect(css).toMatch(/\.dashboard-production-pulse \.pp-page-hero \{/);
    expect(css).toMatch(/--pp-hero-brand-fg:/);
    expect(readRelative("components/operator/OperatorBrandBar.tsx")).toMatch(/PpPageHero/);
  });

  it("páginas profundas usam PagePath — não BackLink", () => {
    const detail = readRelative("pages/DeviceDetailPage.tsx");
    const formPage = readRelative("pages/DeviceFormPage.tsx");
    const uiKit = readRelative("app/productionPulseUi.tsx");
    expect(detail).toMatch(/ProductionPulsePagePath/);
    expect(detail).not.toMatch(/PpBackLink/);
    expect(formPage).toMatch(/ProductionPulsePagePath/);
    expect(formPage).not.toMatch(/PpBackLink/);
    expect(uiKit).toMatch(/createDashboardPagePath/);
    expect(uiKit).not.toMatch(/PpBackLink/);
    expect(readRelative("components/ProductionPulsePagePath.tsx")).toMatch(/PpPagePath/);
  });

  it("cadastro usa grade responsiva e footer compacto", () => {
    const formPage = readRelative("pages/DeviceFormPage.tsx");
    const deviceForm = readRelative("components/DeviceForm.tsx");
    const bindingSection = readRelative("components/DeviceBindingSection.tsx");
    expect(formPage).toMatch(/isCompactViewport/);
    expect(formPage).toMatch(/pp-form-footer--sticky/);
    expect(deviceForm).toMatch(/pp-form-grid--pair/);
    expect(deviceForm).toMatch(/PpNativeTextField/);
    expect(deviceForm).not.toMatch(/<input[\s>]/);
    expect(bindingSection).toMatch(/PpNativeTextField/);
    expect(bindingSection).not.toMatch(/<datalist/);
    expect(readRelative("App.tsx")).toMatch(/data-pp-viewport/);
    expect(readRelative("App.tsx")).toMatch(/data-pp-viewport-short/);
    expect(readRelative("hooks/useShortViewport.ts")).toMatch(/isShortViewportHeight/);
    expect(readRelative("components/data/ppFormFields.tsx")).toMatch(/createDashboardNativeFormFields/);
    expect(readRelative("components/data/ppFormFields.tsx")).toMatch(/FormSelectControl/);
    expect(readRelative("components/data/ppFormFields.tsx")).not.toMatch(/<select[\s/>]/);
    const css = readRelative("index.css");
    expect(css).toMatch(/--pp-form-max-width/);
    expect(css).toMatch(/pp-form-grid--pair/);
    expect(css).toMatch(/pp-page-stack\.pp-form-page/);
    expect(css).toMatch(/display:\s*contents/);
  });
});
