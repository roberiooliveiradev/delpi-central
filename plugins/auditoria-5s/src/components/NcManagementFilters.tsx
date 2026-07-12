import { RefreshCw } from "lucide-react";

import type { AuditArea } from "../api/audit5sApi";
import { NC_STATUS_OPTIONS } from "../constants/audit5s";
import { formatPersonName } from "../utils/formatPersonName";

const STATUS_OPTIONS = [
  { value: "", label: "Todos os status" },
  ...NC_STATUS_OPTIONS.map((item) => ({ value: item.value, label: item.label })),
];

type Props = {
  areas: AuditArea[];
  dateStart: string;
  dateEnd: string;
  areaId: string;
  status: string;
  responsible: string;
  responsibleOptions: string[];
  overdueOnly: boolean;
  loading: boolean;
  lastUpdatedLabel?: string;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onAreaIdChange: (value: string) => void;
  onStatusChange: (value: string) => void;
  onResponsibleChange: (value: string) => void;
  onOverdueOnlyChange: (value: boolean) => void;
  onReload: () => void;
};

export function NcManagementFilters({
  areas,
  dateStart,
  dateEnd,
  areaId,
  status,
  responsible,
  responsibleOptions,
  overdueOnly,
  loading,
  lastUpdatedLabel,
  onDateStartChange,
  onDateEndChange,
  onAreaIdChange,
  onStatusChange,
  onResponsibleChange,
  onOverdueOnlyChange,
  onReload,
}: Props) {
  return (
    <section className="a5s-nc-board-filters" aria-label="Filtros da gestão de NCs">
      <div className="a5s-nc-board-filters__period">
        <input
          type="date"
          value={dateStart}
          aria-label="Data inicial"
          onChange={(event) => onDateStartChange(event.target.value)}
        />
        <span aria-hidden>—</span>
        <input
          type="date"
          value={dateEnd}
          aria-label="Data final"
          onChange={(event) => onDateEndChange(event.target.value)}
        />
      </div>

      <select
        className="a5s-nc-board-filters__select"
        value={areaId}
        aria-label="Área"
        onChange={(event) => onAreaIdChange(event.target.value)}
      >
        <option value="">Todas as áreas</option>
        {areas.map((area) => (
          <option key={area.id} value={area.id}>
            {area.name}
          </option>
        ))}
      </select>

      <select
        className="a5s-nc-board-filters__select a5s-nc-board-filters__select--responsible"
        value={responsible}
        aria-label="Responsável"
        onChange={(event) => onResponsibleChange(event.target.value)}
      >
        <option value="">Todos os responsáveis</option>
        {responsibleOptions.map((name) => (
          <option key={name} value={name}>
            {formatPersonName(name) || name}
          </option>
        ))}
      </select>

      <select
        className="a5s-nc-board-filters__select"
        value={status}
        aria-label="Status"
        onChange={(event) => onStatusChange(event.target.value)}
      >
        {STATUS_OPTIONS.map((option) => (
          <option key={option.value || "all"} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>

      <button
        type="button"
        className={`a5s-nc-board-filters__chip${overdueOnly ? " is-active" : ""}`}
        aria-pressed={overdueOnly}
        onClick={() => onOverdueOnlyChange(!overdueOnly)}
      >
        Atrasadas
      </button>

      <div className="a5s-nc-board-filters__aside">
        {lastUpdatedLabel ? (
          <span className="a5s-nc-board-filters__meta" aria-live="polite">
            {lastUpdatedLabel}
          </span>
        ) : null}
        <button
          type="button"
          className="a5s-nc-board-filters__refresh"
          disabled={loading}
          aria-label="Atualizar lista"
          onClick={onReload}
        >
          <RefreshCw size={16} aria-hidden />
        </button>
      </div>
    </section>
  );
}
