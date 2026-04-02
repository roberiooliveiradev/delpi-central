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
      <div className="si-indicator-filter">
        <label htmlFor="indicator-search">Buscar indicador</label>
        <input
          id="indicator-search"
          type="text"
          value={search}
          onChange={(event) => onSearchChange(event.target.value)}
          placeholder="Ex.: OEE, EBITDA, Turnover..."
        />
      </div>

      <div className="si-indicator-filter">
        <label htmlFor="indicator-department">Departamento</label>
        <select
          id="indicator-department"
          value={department}
          onChange={(event) => onDepartmentChange(event.target.value)}
        >
          {departments.map((item) => (
            <option key={item.value} value={item.value}>
              {item.label}
            </option>
          ))}
        </select>
      </div>

      <div className="si-indicator-filter">
        <label htmlFor="indicator-status">Status</label>
        <select
          id="indicator-status"
          value={status}
          onChange={(event) => onStatusChange(event.target.value)}
        >
          {statuses.map((item) => (
            <option key={item.value} value={item.value}>
              {item.label}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}