type QualityFiltersProps = {
  dateStart: string;
  dateEnd: string;
  branch: string;
  branches?: string[];
  branchesLoading?: boolean;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onBranchChange: (value: string) => void;
  idPrefix?: string;
  className?: string;
};

export function QualityFilters({
  dateStart,
  dateEnd,
  branch,
  branches = [],
  branchesLoading = false,
  onDateStartChange,
  onDateEndChange,
  onBranchChange,
  idPrefix = "dq",
  className,
}: QualityFiltersProps) {
  const branchOptions =
    branches.length > 0 ? branches : branch ? [branch] : [];

  return (
    <section className={["dq-filters-row", className].filter(Boolean).join(" ")}>
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
          disabled={branchesLoading}
        >
          <option value="">Todas</option>
          {branchOptions.map((code) => (
            <option key={code} value={code}>
              {code}
            </option>
          ))}
        </select>
      </div>
    </section>
  );
}
