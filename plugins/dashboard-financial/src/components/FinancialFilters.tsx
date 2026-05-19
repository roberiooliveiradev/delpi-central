type FinancialFiltersProps = {
  dateStart: string;
  dateEnd: string;
  branch: string;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onBranchChange: (value: string) => void;
  showPeriodFilters?: boolean;
  className?: string;
};

export function FinancialFilters({
  dateStart,
  dateEnd,
  branch,
  onDateStartChange,
  onDateEndChange,
  onBranchChange,
  showPeriodFilters = true,
  className = "",
}: FinancialFiltersProps) {
  return (
    <section className={`ds-filters-row ${className}`.trim()}>
      {showPeriodFilters ? (
        <>
          <div className="ds-filter-box">
            <label htmlFor="ds-date-start">Data inicial</label>
            <input
              id="ds-date-start"
              type="date"
              value={dateStart}
              onChange={(e) => onDateStartChange(e.target.value)}
            />
          </div>
          <div className="ds-filter-box">
            <label htmlFor="ds-date-end">Data final</label>
            <input
              id="ds-date-end"
              type="date"
              value={dateEnd}
              onChange={(e) => onDateEndChange(e.target.value)}
            />
          </div>
        </>
      ) : null}
      <div className="ds-filter-box">
        <label htmlFor="ds-branch">Filial</label>
        <select
          id="ds-branch"
          value={branch}
          onChange={(e) => onBranchChange(e.target.value)}
        >
          <option value="">Consolidado</option>
          <option value="01">01 — Matriz</option>
          <option value="02">02 — Filial</option>
        </select>
      </div>
    </section>
  );
}
