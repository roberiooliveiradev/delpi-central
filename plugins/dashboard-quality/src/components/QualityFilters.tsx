type QualityFiltersProps = {
  dateStart: string;
  dateEnd: string;
  branch: string;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onBranchChange: (value: string) => void;
  idPrefix?: string;
};

export function QualityFilters({
  dateStart,
  dateEnd,
  branch,
  onDateStartChange,
  onDateEndChange,
  onBranchChange,
  idPrefix = "dq",
}: QualityFiltersProps) {
  return (
    <section className="dq-filters-row">
      <div className="dq-filter-box">
        <label htmlFor={`${idPrefix}-date-start`}>Data inicial</label>
        <input
          id={`${idPrefix}-date-start`}
          type="date"
          value={dateStart}
          onChange={(e) => onDateStartChange(e.target.value)}
        />
      </div>

      <div className="dq-filter-box">
        <label htmlFor={`${idPrefix}-date-end`}>Data final</label>
        <input
          id={`${idPrefix}-date-end`}
          type="date"
          value={dateEnd}
          onChange={(e) => onDateEndChange(e.target.value)}
        />
      </div>

      <div className="dq-filter-box">
        <label htmlFor={`${idPrefix}-branch`}>Filial</label>
        <select
          id={`${idPrefix}-branch`}
          value={branch}
          onChange={(e) => onBranchChange(e.target.value)}
        >
          <option value="">Todas</option>
          <option value="01">01</option>
          <option value="02">02</option>
        </select>
      </div>
    </section>
  );
}
