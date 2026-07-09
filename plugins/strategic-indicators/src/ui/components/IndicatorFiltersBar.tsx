import "./IndicatorFiltersBar.css";

import {
  IndicatorFilterInputField,
  IndicatorFilterSelectField,
} from "./siFiltersUi";

type IndicatorFiltersBarProps = {
  search: string;
  department: string;
  status: string;
  departments: { value: string; label: string }[];
  statuses: { value: string; label: string }[];
  onSearchChange: (value: string) => void;
  onDepartmentChange: (value: string) => void;
  onStatusChange: (value: string) => void;
};

export function IndicatorFiltersBar({
  search,
  department,
  status,
  departments,
  statuses,
  onSearchChange,
  onDepartmentChange,
  onStatusChange,
}: IndicatorFiltersBarProps) {
  return (
    <div className="si-indicator-filters">
      <IndicatorFilterInputField
        id="indicator-search"
        label="Buscar indicador"
        type="search"
        value={search}
        onChange={onSearchChange}
        placeholder="Ex.: OEE, EBITDA, Turnover..."
      />
      <IndicatorFilterSelectField
        id="indicator-department"
        label="Departamento"
        value={department}
        onChange={onDepartmentChange}
        options={departments}
      />
      <IndicatorFilterSelectField
        id="indicator-status"
        label="Status"
        value={status}
        onChange={onStatusChange}
        options={statuses}
      />
    </div>
  );
}
