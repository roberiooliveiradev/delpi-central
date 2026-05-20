type HrFiltersProps = {
  dateStart: string;
  dateEnd: string;
  branch: string;
  branchOptions: string[];
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onBranchChange: (value: string) => void;
};

export function HrFilters({
  dateStart,
  dateEnd,
  branch,
  branchOptions,
  onDateStartChange,
  onDateEndChange,
  onBranchChange,
}: HrFiltersProps) {
  return (
    <section className="dh-filters-row" aria-label="Filtros do dashboard de RH">
      <div className="dh-filter-box">
        <label htmlFor="hr-filter-start">Início</label>
        <input
          id="hr-filter-start"
          type="date"
          value={dateStart}
          onChange={(event) => onDateStartChange(event.target.value)}
        />
      </div>
      <div className="dh-filter-box">
        <label htmlFor="hr-filter-end">Fim</label>
        <input
          id="hr-filter-end"
          type="date"
          value={dateEnd}
          onChange={(event) => onDateEndChange(event.target.value)}
        />
      </div>
      <div className="dh-filter-box">
        <label htmlFor="hr-filter-branch">Filial</label>
        <select
          id="hr-filter-branch"
          value={branch}
          onChange={(event) => onBranchChange(event.target.value)}
        >
          <option value="">Todas</option>
          {branchOptions.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </div>
    </section>
  );
}
