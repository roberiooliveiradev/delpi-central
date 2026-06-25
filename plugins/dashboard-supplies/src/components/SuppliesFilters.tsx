type SuppliesFiltersProps = {
  dateStart: string;
  dateEnd: string;
  branch: string;
  location: string;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onBranchChange: (value: string) => void;
  onLocationChange: (value: string) => void;
  showPeriodFilters?: boolean;
  showLocationFilter?: boolean;
  className?: string;
};

export function SuppliesFilters({
  dateStart,
  dateEnd,
  branch,
  location,
  onDateStartChange,
  onDateEndChange,
  onBranchChange,
  onLocationChange,
  showPeriodFilters = true,
  showLocationFilter = true,
  className = "",
}: SuppliesFiltersProps) {
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
      {showLocationFilter ? (
        <div className="ds-filter-box">
          <label htmlFor="ds-location">Localização (estoque)</label>
          <input
            id="ds-location"
            type="text"
            value={location}
            placeholder="Todas"
            onChange={(e) => onLocationChange(e.target.value)}
          />
        </div>
      ) : null}
    </section>
  );
}
