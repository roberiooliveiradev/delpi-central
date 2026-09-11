import { useId, useRef, useState } from "react";
import {
  ChevronDown,
  ChevronRight,
  CircuitBoard,
  Cpu,
  FileCode,
  ListTodo,
  PanelRightClose,
  PanelRightOpen,
  Plus,
  RefreshCw,
  TriangleAlert,
} from "lucide-react";

import {
  AnchoredPanelPortal,
  PpActionButton,
  PpCatalogSearchBar,
  PpContextMenuItem,
  PpHintAction,
  PpIconButton,
  PpSegmentToggle,
  PpSectionHintLabel,
} from "../app/productionPulseUi";
import type { BranchOption } from "../constants/branches";
import { PP_HELP } from "../content/helpTooltips";
import type { HubOtaKpis } from "../utils/hubOtaKpis";
import { HubCanvasLegend } from "./HubCanvasLegend";

export type HubMapChromeProps = {
  collapsed: boolean;
  onCollapsedChange: (collapsed: boolean) => void;
  context: {
    branch: string;
    branchOptions: BranchOption[];
    onBranchChange: (branchId: string) => void;
    refreshing?: boolean;
    onRefresh: () => void;
  };
  navigation: {
    activeJobs: number;
    onOpenDevices: () => void;
    onOpenFirmwares: () => void;
    onOpenDrivers: () => void;
    onOpenJobs: () => void;
  };
  create?: {
    onCreateDevice: () => void;
    onCreateFirmware: () => void;
  };
  filters: {
    search: string;
    onSearchChange: (value: string) => void;
    status: string;
    onStatusChange: (value: string) => void;
  };
  diagnostics: {
    kpis: HubOtaKpis;
    linkModeActive?: boolean;
    awaitingCount?: number;
    downloadingCount?: number;
    loading?: boolean;
  };
};

/**
 * Single Admin Hub chrome (top-right): context, catalog nav, create, filters, diagnostics.
 * Presentational only — page owns data, URL, and permissions.
 */
export function HubMapChrome({
  collapsed,
  onCollapsedChange,
  context,
  navigation,
  create,
  filters,
  diagnostics,
}: HubMapChromeProps) {
  const chromeId = useId();
  const createAnchorRef = useRef<HTMLSpanElement>(null);
  const createMenuRef = useRef<HTMLDivElement>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [healthOpen, setHealthOpen] = useState(false);
  const [legendOpen, setLegendOpen] = useState(false);

  if (collapsed) {
    return (
      <div className="pp-hub-map-chrome pp-hub-map-chrome--collapsed">
        <PpHintAction hint={PP_HELP.hub.collapseFilters} ariaLabel="Ajuda: Expandir Hub Admin">
          <PpIconButton
            aria-label="Expandir Hub Admin"
            aria-expanded={false}
            aria-controls={chromeId}
            onClick={() => onCollapsedChange(false)}
          >
            <PanelRightOpen size={18} aria-hidden="true" />
          </PpIconButton>
        </PpHintAction>
      </div>
    );
  }

  const branchLabel =
    context.branchOptions.find((item) => item.id === context.branch)?.label ?? context.branch;
  const multiBranch = context.branchOptions.length > 1;
  const { kpis } = diagnostics;

  return (
    <div
      id={chromeId}
      className="pp-hub-map-chrome"
      role="region"
      aria-label="Hub Admin OTA"
    >
      <div className="pp-hub-map-chrome__header">
        <div className="pp-hub-map-chrome__title-row">
          <strong className="pp-hub-map-chrome__title">Admin · OTA</strong>
          <PpHintAction hint={PP_HELP.hub.collapseFilters} ariaLabel="Ajuda: Recolher Hub Admin">
            <PpIconButton
              aria-label="Recolher Hub Admin"
              aria-expanded={true}
              aria-controls={chromeId}
              onClick={() => onCollapsedChange(true)}
            >
              <PanelRightClose size={16} aria-hidden="true" />
            </PpIconButton>
          </PpHintAction>
        </div>
        <div className="pp-hub-map-chrome__context">
          {multiBranch ? (
            <PpHintAction hint={PP_HELP.hub.branch} ariaLabel="Ajuda: Filial">
              <PpSegmentToggle
                ariaLabel="Filial"
                size="sm"
                widthMode="content"
                value={context.branch}
                onChange={context.onBranchChange}
                options={context.branchOptions.map((item) => ({
                  value: item.id,
                  label: item.label,
                }))}
              />
            </PpHintAction>
          ) : (
            <PpHintAction hint={PP_HELP.hub.branch} ariaLabel="Ajuda: Filial">
              <span className="pp-hub-map-chrome__branch-static">{branchLabel}</span>
            </PpHintAction>
          )}
          <PpHintAction hint={PP_HELP.hub.refresh} ariaLabel="Ajuda: Atualizar dados">
            <PpIconButton
              aria-label="Atualizar dados"
              disabled={context.refreshing}
              onClick={context.onRefresh}
            >
              <RefreshCw size={16} aria-hidden="true" />
            </PpIconButton>
          </PpHintAction>
        </div>
      </div>

      <div className="pp-hub-map-chrome__body">
        <nav className="pp-hub-map-chrome__nav" aria-label="Catálogos">
          <PpHintAction hint={PP_HELP.hub.panelDevices} ariaLabel="Ajuda: Painel IoTs">
            <button
              type="button"
              className="pp-hub-map-chrome__nav-item"
              onClick={navigation.onOpenDevices}
            >
              <Cpu size={16} aria-hidden="true" className="pp-hub-map-chrome__nav-icon pp-hub-map-chrome__nav-icon--device" />
              <span>IoTs</span>
            </button>
          </PpHintAction>
          <PpHintAction hint={PP_HELP.hub.panelFirmwares} ariaLabel="Ajuda: Painel Firmwares">
            <button
              type="button"
              className="pp-hub-map-chrome__nav-item"
              onClick={navigation.onOpenFirmwares}
            >
              <FileCode
                size={16}
                aria-hidden="true"
                className="pp-hub-map-chrome__nav-icon pp-hub-map-chrome__nav-icon--firmware"
              />
              <span>Firmwares</span>
            </button>
          </PpHintAction>
          <PpHintAction hint={PP_HELP.hub.panelDrivers} ariaLabel="Ajuda: Painel Drivers">
            <button
              type="button"
              className="pp-hub-map-chrome__nav-item"
              onClick={navigation.onOpenDrivers}
            >
              <CircuitBoard
                size={16}
                aria-hidden="true"
                className="pp-hub-map-chrome__nav-icon pp-hub-map-chrome__nav-icon--driver"
              />
              <span>Drivers</span>
            </button>
          </PpHintAction>
          <PpHintAction hint={PP_HELP.hub.panelJobs} ariaLabel="Ajuda: Painel Jobs">
            <button
              type="button"
              className="pp-hub-map-chrome__nav-item"
              onClick={navigation.onOpenJobs}
            >
              <ListTodo
                size={16}
                aria-hidden="true"
                className="pp-hub-map-chrome__nav-icon pp-hub-map-chrome__nav-icon--jobs"
              />
              <span>Jobs</span>
              {navigation.activeJobs > 0 ? (
                <span className="pp-hub-map-chrome__nav-badge" aria-label={`${navigation.activeJobs} ativos`}>
                  {navigation.activeJobs}
                </span>
              ) : null}
            </button>
          </PpHintAction>
        </nav>

        {create ? (
          <div className="pp-hub-map-chrome__create">
            <span ref={createAnchorRef} className="pp-hub-map-chrome__create-anchor">
              <PpHintAction hint={PP_HELP.hub.newMenu} ariaLabel="Ajuda: Novo">
                <PpActionButton
                  variant="primary"
                  className="pp-hub-map-chrome__create-btn"
                  aria-label="Novo"
                  aria-haspopup="menu"
                  aria-expanded={createOpen}
                  onClick={() => setCreateOpen((value) => !value)}
                >
                  <Plus size={14} aria-hidden="true" /> Novo
                </PpActionButton>
              </PpHintAction>
            </span>
            <AnchoredPanelPortal
              open={createOpen}
              anchorRef={createAnchorRef}
              panelRef={createMenuRef}
              variant="bare"
              className="delpi-ui-popover-surface pp-hub-map-chrome__create-menu"
              density="compact"
              role="menu"
              aria-label="Criar"
              preferredPlacement="bottom"
              allowFlip
              portalScopeClassName="dashboard-production-pulse"
              onDismiss={() => setCreateOpen(false)}
            >
              <PpContextMenuItem
                label="Novo IoT"
                icon={Cpu}
                hint={PP_HELP.hub.newDevice}
                onSelect={() => {
                  setCreateOpen(false);
                  create.onCreateDevice();
                }}
              />
              <PpContextMenuItem
                label="Novo firmware"
                icon={FileCode}
                hint={PP_HELP.hub.newFirmware}
                onSelect={() => {
                  setCreateOpen(false);
                  create.onCreateFirmware();
                }}
              />
            </AnchoredPanelPortal>
          </div>
        ) : null}

        <div className="pp-hub-map-chrome__filters">
          <PpHintAction hint={PP_HELP.hub.mapSearch} ariaLabel="Ajuda: Buscar no mapa">
            <div>
              <PpCatalogSearchBar
                value={filters.search}
                onChange={filters.onSearchChange}
                placeholder="Buscar no mapa…"
              />
            </div>
          </PpHintAction>
          <PpHintAction hint={PP_HELP.hub.statusFilter} ariaLabel="Ajuda: Filtro de status">
            <PpSegmentToggle
              ariaLabel="Filtro de status"
              size="sm"
              widthMode="fill"
              value={filters.status || "all"}
              onChange={(value) => filters.onStatusChange(value === "all" ? "" : value)}
              options={[
                { value: "all", label: "Todos" },
                { value: "online", label: "Online" },
                { value: "offline", label: "Offline" },
                { value: "disabled", label: "Inativos" },
              ]}
            />
          </PpHintAction>
        </div>

        <div className="pp-hub-map-chrome__summary" aria-live="polite">
          {diagnostics.loading ? (
            <span className="pp-muted">Carregando indicadores…</span>
          ) : (
            <>
              <span>
                <Cpu size={12} aria-hidden="true" /> {kpis.linkedDevices} vinculados
              </span>
              <span className="pp-hub-map-chrome__summary-sep" aria-hidden="true">
                ·
              </span>
              <span>
                <TriangleAlert size={12} aria-hidden="true" /> {kpis.outdatedDevices} desatual.
              </span>
            </>
          )}
        </div>

        <div className="pp-hub-map-chrome__section">
          <PpHintAction hint={PP_HELP.hub.fleetHealth} ariaLabel="Ajuda: Saúde da frota">
            <button
              type="button"
              className="pp-hub-map-chrome__section-toggle"
              aria-expanded={healthOpen}
              onClick={() => setHealthOpen((value) => !value)}
            >
              <span>Saúde da frota</span>
              {healthOpen ? (
                <ChevronDown size={16} aria-hidden="true" />
              ) : (
                <ChevronRight size={16} aria-hidden="true" />
              )}
            </button>
          </PpHintAction>
          {healthOpen ? (
            <div className="pp-hub-map-chrome__section-body" role="region" aria-label="Detalhe saúde da frota">
              <div className="pp-hub-map-chrome__fact">
                <strong>{kpis.publishedFirmwares}</strong>
                <span>Firmwares publicados</span>
              </div>
              <div className="pp-hub-map-chrome__fact">
                <strong>{kpis.linkedDevices}</strong>
                <span>IoTs vinculados</span>
              </div>
              <div className="pp-hub-map-chrome__fact">
                <strong>{kpis.outdatedDevices}</strong>
                <span>{PP_HELP.hub.kpiOutdatedSuffix}</span>
              </div>
              <div className="pp-hub-map-chrome__fact">
                <strong>{kpis.updatingDevices}</strong>
                <span>Em atualização</span>
              </div>
              {typeof diagnostics.awaitingCount === "number" ? (
                <div className="pp-hub-map-chrome__fact">
                  <strong>{diagnostics.awaitingCount}</strong>
                  <span>Aguardando consulta OTA</span>
                </div>
              ) : null}
              {typeof diagnostics.downloadingCount === "number" ? (
                <div className="pp-hub-map-chrome__fact">
                  <strong>{diagnostics.downloadingCount}</strong>
                  <span>Baixando</span>
                </div>
              ) : null}
              <div className="pp-hub-map-chrome__fact">
                <strong>{kpis.failedDevices}</strong>
                <span>Falhas OTA</span>
              </div>
            </div>
          ) : null}
        </div>

        <div className="pp-hub-map-chrome__section">
          <div className="pp-hub-map-chrome__section-toggle-row">
            <PpSectionHintLabel
              label={
                diagnostics.linkModeActive ? PP_HELP.hub.linkModeTitle : PP_HELP.hub.edgeModesTitle
              }
              hint={PP_HELP.hub.edgeModesHint}
              className="pp-hub-map-chrome__section-label"
            />
            <PpIconButton
              aria-label={legendOpen ? "Recolher conexões" : "Expandir conexões"}
              aria-expanded={legendOpen}
              onClick={() => setLegendOpen((value) => !value)}
            >
              {legendOpen ? (
                <ChevronDown size={16} aria-hidden="true" />
              ) : (
                <ChevronRight size={16} aria-hidden="true" />
              )}
            </PpIconButton>
          </div>
          {legendOpen ? (
            <div className="pp-hub-map-chrome__section-body">
              <HubCanvasLegend
                linkModeActive={Boolean(diagnostics.linkModeActive)}
                hideTitle
              />
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
