type CommercialFiltersProps = {
  dateStart: string;
  dateEnd: string;
  branch: string;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onBranchChange: (value: string) => void;
  className?: string;
};

export function CommercialFilters({
  dateStart,
  dateEnd,
  branch,
  onDateStartChange,
  onDateEndChange,
  onBranchChange,
  className = "",
}: CommercialFiltersProps) {
  return (
    <section className={`dc-filters-row ${className}`.trim()}>
      <div className="dc-filter-box">
        <label htmlFor="dc-date-start">Data inicial</label>
        <input
          id="dc-date-start"
          type="date"
          value={dateStart}
          onChange={(e) => onDateStartChange(e.target.value)}
        />
      </div>
      <div className="dc-filter-box">
        <label htmlFor="dc-date-end">Data final</label>
        <input
          id="dc-date-end"
          type="date"
          value={dateEnd}
          onChange={(e) => onDateEndChange(e.target.value)}
        />
      </div>
      <div className="dc-filter-box">
        <label htmlFor="dc-branch">Filial (indicadores)</label>
        <select
          id="dc-branch"
          value={branch}
          onChange={(e) => onBranchChange(e.target.value)}
        >
          <option value="">Todas</option>
          <option value="01">01 — Matriz</option>
          <option value="02">02 — Filial</option>
        </select>
      </div>
    </section>
  );
}
