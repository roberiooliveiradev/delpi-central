import type { EficienciaFabrilShift } from "../constants/shifts";
import type { MultiSelectOption } from "./MultiSelectField";
import { MultiSelectField } from "./MultiSelectField";

type FilterBarProps = {
  dateStart: string;
  dateEnd: string;
  ops: string[];
  employees: string[];
  workCenters: string[];
  shifts: EficienciaFabrilShift[];
  opOptions: MultiSelectOption[];
  employeeOptions: MultiSelectOption[];
  workCenterOptions: MultiSelectOption[];
  shiftOptions: MultiSelectOption[];
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onOpsChange: (value: string[]) => void;
  onEmployeesChange: (value: string[]) => void;
  onWorkCentersChange: (value: string[]) => void;
  onShiftsChange: (value: EficienciaFabrilShift[]) => void;
  disabled?: boolean;
};

export function FilterBar({
  dateStart,
  dateEnd,
  ops,
  employees,
  workCenters,
  shifts,
  opOptions,
  employeeOptions,
  workCenterOptions,
  shiftOptions,
  onDateStartChange,
  onDateEndChange,
  onOpsChange,
  onEmployeesChange,
  onWorkCentersChange,
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

        <MultiSelectField
          label="Operador (nome)"
          emptyLabel="Todos"
          searchable
          options={employeeOptions}
          selectedValues={employees}
          onChange={onEmployeesChange}
          disabled={disabled}
        />

        <MultiSelectField
          label="OP"
          emptyLabel="Todas"
          searchable
          options={opOptions}
          selectedValues={ops}
          onChange={onOpsChange}
          disabled={disabled}
        />

        <MultiSelectField
          label="Centro de trabalho"
          emptyLabel="Todos"
          searchable
          options={workCenterOptions}
          selectedValues={workCenters}
          onChange={onWorkCentersChange}
          disabled={disabled}
        />

        <MultiSelectField
          label="Turno"
          emptyLabel="Todos"
          options={shiftOptions}
          selectedValues={shifts}
          onChange={(values) => onShiftsChange(values as EficienciaFabrilShift[])}
          disabled={disabled}
        />
      </div>
    </section>
  );
}
