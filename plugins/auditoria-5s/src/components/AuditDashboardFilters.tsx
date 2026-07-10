import { RefreshCw } from "lucide-react";

import type { AuditArea } from "../api/audit5sApi";
import { SENSOS, SHIFTS } from "../constants/audit5s";
import type { ChartGranularity } from "../types/auditDashboard";
import { FilterBarShell, FilterInputField, FilterSelectField } from "./filtersUi";

const STATUS_OPTIONS = [
  { value: "closed", label: "Encerradas" },
  { value: "nc_in_progress", label: "NC em andamento" },
  { value: "evaluation_complete", label: "Pendente NC's" },
  { value: "draft", label: "Em avaliação" },
  { value: "", label: "Todas" },
];

const GRANULARITY_OPTIONS: { value: ChartGranularity; label: string }[] = [
  { value: "day", label: "Dia" },
  { value: "week", label: "Semana" },
  { value: "month", label: "Mês" },
];

type Props = {
  areas: AuditArea[];
  dateStart: string;
  dateEnd: string;
  areaId: string;
  shift: string;
  auditStatus: string;
  sensoOrder: string;
  granularity: ChartGranularity;
  loading: boolean;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onAreaIdChange: (value: string) => void;
  onShiftChange: (value: string) => void;
  onAuditStatusChange: (value: string) => void;
  onSensoOrderChange: (value: string) => void;
  onGranularityChange: (value: ChartGranularity) => void;
  onReload: () => void;
};

export function AuditDashboardFilters({
  areas,
  dateStart,
  dateEnd,
  areaId,
  shift,
  auditStatus,
  sensoOrder,
  granularity,
  loading,
  onDateStartChange,
  onDateEndChange,
  onAreaIdChange,
  onShiftChange,
  onAuditStatusChange,
  onSensoOrderChange,
  onGranularityChange,
  onReload,
}: Props) {
  const areaOptions = areas.map((area) => ({ value: area.id, label: area.name }));
  const sensoOptions = SENSOS.map((senso) => ({
    value: String(senso.order),
    label: `${senso.order} — ${senso.name}`,
  }));

  return (
    <FilterBarShell>
      <FilterInputField
        id="a5s-filter-date-start"
        label="Data inicial"
        type="date"
        value={dateStart}
        onChange={onDateStartChange}
      />
      <FilterInputField
        id="a5s-filter-date-end"
        label="Data final"
        type="date"
        value={dateEnd}
        onChange={onDateEndChange}
      />
      <FilterSelectField
        id="a5s-filter-area"
        label="Área"
        value={areaId}
        onChange={onAreaIdChange}
        options={areaOptions}
        placeholderOption="Todas"
      />
      <FilterSelectField
        id="a5s-filter-shift"
        label="Turno"
        value={shift}
        onChange={onShiftChange}
        options={SHIFTS}
        placeholderOption="Todos"
      />
      <FilterSelectField
        id="a5s-filter-senso"
        label="Senso"
        value={sensoOrder}
        onChange={onSensoOrderChange}
        options={sensoOptions}
        placeholderOption="Todos (nota geral)"
      />
      <FilterSelectField
        id="a5s-filter-status"
        label="Status auditoria"
        value={auditStatus}
        onChange={onAuditStatusChange}
        options={STATUS_OPTIONS}
      />
      <FilterSelectField
        id="a5s-filter-granularity"
        label="Granularidade"
        value={granularity}
        onChange={(value) => onGranularityChange(value as ChartGranularity)}
        options={GRANULARITY_OPTIONS}
      />
      <div className="a5s-analytics-filters__actions">
        <button
          type="button"
          className="a5s-btn a5s-btn--ghost"
          disabled={loading}
          onClick={onReload}
        >
          <RefreshCw size={16} aria-hidden className={loading ? "a5s-spin" : undefined} />
          Atualizar
        </button>
      </div>
    </FilterBarShell>
  );
}
