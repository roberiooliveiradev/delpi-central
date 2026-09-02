import { Plus } from "lucide-react";

import {
  PpActionButton,
  PpFilterInputField,
  PpFilterSelectField,
  PpFiltersRow,
  PpFilterToolbarRowClasses,
  PpSegmentToggle,
} from "../app/productionPulseUi";
import { PP_HELP } from "../content/helpTooltips";
import type { PanelFilters, PanelGroupBy } from "../utils/panelFilterUrl";

type DeviceFiltersBarProps = {
  filters: PanelFilters;
  canManage: boolean;
  onChange: (patch: Partial<PanelFilters>) => void;
  onCreateDevice?: () => void;
};

const ANCHOR_OPTIONS = [
  { value: "", label: "Todos" },
  { value: "work_center", label: "Posto PCP" },
  { value: "machine", label: "Máquina" },
  { value: "equipment", label: "Equipamento" },
  { value: "area", label: "Área" },
  { value: "standalone", label: "Avulso" },
];

const ROLE_OPTIONS = [
  { value: "", label: "Todos" },
  { value: "pulse_counter", label: "Contador" },
  { value: "process_gauge", label: "Sensor" },
];

const STATUS_OPTIONS = [
  { value: "", label: "Todos" },
  { value: "online", label: "Online" },
  { value: "offline", label: "Offline" },
  { value: "no_binding", label: "Sem amarração" },
  { value: "disabled", label: "Desativado" },
];

const GROUP_BY_OPTIONS: Array<{ value: PanelGroupBy; label: string }> = [
  { value: "work_center", label: "Posto (CT)" },
  { value: "machine", label: "Máquina" },
  { value: "equipment", label: "Equipamento" },
  { value: "area", label: "Área" },
];

export function DeviceFiltersBar({
  filters,
  canManage,
  onChange,
  onCreateDevice,
}: DeviceFiltersBarProps) {
  return (
    <PpFiltersRow>
      <PpFilterSelectField
        id="pp-filter-anchor-type"
        label="Tipo"
        hint={PP_HELP.panel.filterAnchorType}
        value={filters.anchorType}
        onChange={(value) => onChange({ anchorType: value as PanelFilters["anchorType"] })}
        options={ANCHOR_OPTIONS}
        placeholderOption="Todos"
      />
      <PpFilterSelectField
        id="pp-filter-status"
        label="Status"
        hint={PP_HELP.panel.filterStatus}
        value={filters.status}
        onChange={(value) => onChange({ status: value as PanelFilters["status"] })}
        options={STATUS_OPTIONS}
        placeholderOption="Todos"
      />
      <PpFilterSelectField
        id="pp-filter-role"
        label="Papel"
        hint={PP_HELP.panel.filterRole}
        value={filters.role}
        onChange={(value) => onChange({ role: value })}
        options={ROLE_OPTIONS}
        placeholderOption="Todos"
      />
      <PpFilterInputField
        id="pp-filter-search"
        label="Busca"
        type="search"
        hint={PP_HELP.panel.filterSearch}
        value={filters.search}
        onChange={(value) => onChange({ search: value })}
        placeholder="Nome, objeto ou IP…"
      />
      <div className={PpFilterToolbarRowClasses.row}>
        <div className={PpFilterToolbarRowClasses.cluster}>
          <PpSegmentToggle
            ariaLabel="Modo de visualização"
            size="sm"
            widthMode="content"
            value={filters.view}
            onChange={(value) => onChange({ view: value as PanelFilters["view"] })}
            options={[
              { value: "list", label: "Lista" },
              { value: "grouped", label: "Agrupado" },
            ]}
          />
          {filters.view === "grouped" ? (
            <PpFilterSelectField
              id="pp-filter-group-by"
              label="Agrupar por"
              hint={PP_HELP.panel.filterGroupBy}
              value={filters.groupBy}
              onChange={(value) => onChange({ groupBy: value as PanelGroupBy })}
              options={GROUP_BY_OPTIONS}
            />
          ) : null}
        </div>
        {canManage ? (
          <PpActionButton
            variant="primary"
            onClick={onCreateDevice}
            className={PpFilterToolbarRowClasses.action}
          >
            <Plus size={16} aria-hidden="true" />
            <span className="pp-filter-new-device__label">Novo dispositivo</span>
          </PpActionButton>
        ) : null}
      </div>
    </PpFiltersRow>
  );
}
