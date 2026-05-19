type ProductionFiltersProps = {
  dateStart: string;
  dateEnd: string;
  branch: string;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onBranchChange: (value: string) => void;
  className?: string;
};

export function ProductionFilters({
  dateStart,
  dateEnd,
  branch,
  onDateStartChange,
  onDateEndChange,
  onBranchChange,
  className = "",
}: ProductionFiltersProps) {
  return (
    <section className={`dp-filters-row ${className}`.trim()}>
      <div className="dp-filter-box">
        <label htmlFor="dp-date-start">Data inicial</label>
        <input
          id="dp-date-start"
          type="date"
          value={dateStart}
          onChange={(e) => onDateStartChange(e.target.value)}
        />
      </div>
      <div className="dp-filter-box">
        <label htmlFor="dp-date-end">Data final</label>
        <input
          id="dp-date-end"
          type="date"
          value={dateEnd}
          onChange={(e) => onDateEndChange(e.target.value)}
        />
      </div>
      <div className="dp-filter-box">
        <label htmlFor="dp-branch">Filial</label>
        <select
          id="dp-branch"
          value={branch}
          onChange={(e) => onBranchChange(e.target.value)}
        >
          <option value="">Consolidado (média)</option>
          <option value="01">01 — Matriz</option>
          <option value="02">02 — Filial</option>
        </select>
      </div>
    </section>
  );
}
