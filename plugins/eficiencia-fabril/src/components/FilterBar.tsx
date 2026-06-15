import type { EficienciaFabrilShift } from "../constants/shifts";
import { ShiftMultiSelect } from "./ShiftMultiSelect";

type FilterBarProps = {
  dateStart: string;
  dateEnd: string;
  op: string;
  employee: string;
  workCenter: string;
  shifts: EficienciaFabrilShift[];
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onOpChange: (value: string) => void;
  onEmployeeChange: (value: string) => void;
  onWorkCenterChange: (value: string) => void;
  onShiftsChange: (value: EficienciaFabrilShift[]) => void;
  disabled?: boolean;
};

export function FilterBar({
  dateStart,
  dateEnd,
  op,
  employee,
  workCenter,
  shifts,
  onDateStartChange,
  onDateEndChange,
  onOpChange,
  onEmployeeChange,
  onWorkCenterChange,
  onShiftsChange,
  disabled = false,
}: FilterBarProps) {
  return (
    <section className="ef-filter-bar" aria-label="Filtros do dashboard">
      <div className="ef-filter-bar__grid">
        <label className="ef-field">
          <span>Data início</span>
          <input
            type="date"
            value={dateStart}
            disabled={disabled}
            onChange={(event) => onDateStartChange(event.target.value)}
          />
        </label>

        <label className="ef-field">
          <span>Data fim</span>
          <input
            type="date"
            value={dateEnd}
            disabled={disabled}
            onChange={(event) => onDateEndChange(event.target.value)}
          />
        </label>

        <label className="ef-field">
          <span>Operador (nome)</span>
          <input
            type="text"
            value={employee}
            placeholder="Ex.: CRISTIANE"
            disabled={disabled}
            onChange={(event) => onEmployeeChange(event.target.value)}
          />
        </label>

        <label className="ef-field">
          <span>OP</span>
          <input
            type="text"
            value={op}
            placeholder="Ex.: 24549301007"
            disabled={disabled}
            onChange={(event) => onOpChange(event.target.value)}
          />
        </label>

        <label className="ef-field">
          <span>Centro de trabalho</span>
          <input
            type="text"
            value={workCenter}
            placeholder="Ex.: CT-01A"
            disabled={disabled}
            onChange={(event) => onWorkCenterChange(event.target.value)}
          />
        </label>

        <label className="ef-field">
          <span>Turno</span>
          <ShiftMultiSelect value={shifts} onChange={onShiftsChange} disabled={disabled} />
        </label>
      </div>
    </section>
  );
}
