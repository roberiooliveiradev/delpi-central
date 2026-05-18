type Audit5sFiltersProps = {
  dateStart: string;
  dateEnd: string;
  branch: string;
  branches?: string[];
  branchesLoading?: boolean;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onBranchChange: (value: string) => void;
};

export function Audit5sFilters({
  dateStart,
  dateEnd,
  branch,
  branches = [],
  branchesLoading = false,
  onDateStartChange,
  onDateEndChange,
  onBranchChange,
}: Audit5sFiltersProps) {
  const branchOptions =
    branches.length > 0 ? branches : branch ? [branch] : [];

  return (
    <section className="dq-filters-row">
      <div className="dq-filter-box">
        <label htmlFor="a5s-date-start">Data inicial</label>
        <input
          id="a5s-date-start"
          type="date"
          value={dateStart}
          onChange={(e) => onDateStartChange(e.target.value)}
        />
      </div>

      <div className="dq-filter-box">
        <label htmlFor="a5s-date-end">Data final</label>
        <input
          id="a5s-date-end"
          type="date"
          value={dateEnd}
          onChange={(e) => onDateEndChange(e.target.value)}
        />
      </div>

      <div className="dq-filter-box">
        <label htmlFor="a5s-branch">Filial</label>
        <select
          id="a5s-branch"
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
