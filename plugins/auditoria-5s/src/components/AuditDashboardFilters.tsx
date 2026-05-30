import { RefreshCw } from "lucide-react";

import type { AuditArea } from "../api/audit5sApi";
import { SENSOS, SHIFTS } from "../constants/audit5s";
import type { ChartGranularity } from "../types/auditDashboard";

const STATUS_OPTIONS = [
  { value: "closed", label: "Encerradas" },
  { value: "nc_in_progress", label: "NC em andamento" },
  { value: "evaluation_complete", label: "Avaliação concluída" },
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
  return (
    <section className="a5s-analytics-filters">
      <div className="a5s-analytics-filters__grid">
        <label>
          Data inicial
          <input type="date" value={dateStart} onChange={(e) => onDateStartChange(e.target.value)} />
        </label>
        <label>
          Data final
          <input type="date" value={dateEnd} onChange={(e) => onDateEndChange(e.target.value)} />
        </label>
        <label>
          Área
          <select value={areaId} onChange={(e) => onAreaIdChange(e.target.value)}>
            <option value="">Todas</option>
            {areas.map((area) => (
              <option key={area.id} value={area.id}>
                {area.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Turno
          <select value={shift} onChange={(e) => onShiftChange(e.target.value)}>
            <option value="">Todos</option>
            {SHIFTS.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
        </label>
        <label>
          Senso
          <select value={sensoOrder} onChange={(e) => onSensoOrderChange(e.target.value)}>
            <option value="">Todos (nota geral)</option>
            {SENSOS.map((senso) => (
              <option key={senso.order} value={String(senso.order)}>
                {senso.order} — {senso.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Status auditoria
          <select value={auditStatus} onChange={(e) => onAuditStatusChange(e.target.value)}>
            {STATUS_OPTIONS.map((option) => (
              <option key={option.value || "all"} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <label>
          Granularidade
          <select
            value={granularity}
            onChange={(e) => onGranularityChange(e.target.value as ChartGranularity)}
          >
            {GRANULARITY_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
      </div>
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
    </section>
  );
}
