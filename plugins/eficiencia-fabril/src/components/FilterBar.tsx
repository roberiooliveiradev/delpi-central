import { Search } from "lucide-react";

import type { EficienciaFabrilShift } from "../constants/shifts";
import { FACTORY_SHIFTS } from "../constants/shifts";

type FilterBarProps = {
  dateStart: string;
  dateEnd: string;
  op: string;
  employee: string;
  workCenter: string;
  shift: EficienciaFabrilShift | "";
  hasPendingChanges?: boolean;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onOpChange: (value: string) => void;
  onEmployeeChange: (value: string) => void;
  onWorkCenterChange: (value: string) => void;
  onShiftChange: (value: EficienciaFabrilShift | "") => void;
  onApply: () => void;
  loading?: boolean;
};

export function FilterBar({
  dateStart,
  dateEnd,
  op,
  employee,
  workCenter,
  shift,
  hasPendingChanges = false,
  onDateStartChange,
  onDateEndChange,
  onOpChange,
  onEmployeeChange,
  onWorkCenterChange,
  onShiftChange,
  onApply,
  loading = false,
}: FilterBarProps) {
  return (
    <section className="ef-filter-bar" aria-label="Filtros do dashboard">
      <div className="ef-filter-bar__grid">
        <label className="ef-field">
          <span>Data início</span>
          <input
            type="date"
            value={dateStart}
            onChange={(event) => onDateStartChange(event.target.value)}
          />
        </label>

        <label className="ef-field">
          <span>Data fim</span>
          <input
            type="date"
            value={dateEnd}
            onChange={(event) => onDateEndChange(event.target.value)}
          />
        </label>

        <label className="ef-field">
          <span>Operador (nome)</span>
          <input
            type="text"
            value={employee}
            placeholder="Ex.: CRISTIANE"
            onChange={(event) => onEmployeeChange(event.target.value)}
          />
        </label>

        <label className="ef-field">
          <span>OP</span>
          <input
            type="text"
            value={op}
            placeholder="Ex.: 24549301007"
            onChange={(event) => onOpChange(event.target.value)}
          />
        </label>

        <label className="ef-field">
          <span>Centro de trabalho</span>
          <input
            type="text"
            value={workCenter}
            placeholder="Ex.: CT-01A"
            onChange={(event) => onWorkCenterChange(event.target.value)}
          />
        </label>

        <label className="ef-field">
          <span>Turno</span>
          <select
            value={shift}
            onChange={(event) =>
              onShiftChange(event.target.value as EficienciaFabrilShift | "")
            }
          >
            <option value="">Todos</option>
            {FACTORY_SHIFTS.map((item) => (
              <option key={item.id} value={item.id}>
                {item.label} ({item.start} – {item.end})
              </option>
            ))}
          </select>
        </label>

      </div>

      <button
        type="button"
        className="ef-btn ef-btn--primary"
        onClick={onApply}
        disabled={loading}
      >
        <Search size={16} aria-hidden />
        {loading
          ? "Carregando…"
          : hasPendingChanges
            ? "Aplicar filtros *"
            : "Aplicar filtros"}
      </button>
    </section>
  );
}
