type SuppliesFiltersProps = {
  dateStart: string;
  dateEnd: string;
  branch: string;
  location: string;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onBranchChange: (value: string) => void;
  onLocationChange: (value: string) => void;
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
  className = "",
}: SuppliesFiltersProps) {
  return (
    <section className={`ds-filters-row ${className}`.trim()}>
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
      <div className="ds-filter-box">
        <label htmlFor="ds-location">Localização (estoque / IDD)</label>
        <input
          id="ds-location"
          type="text"
          value={location}
          placeholder="Todas"
          onChange={(e) => onLocationChange(e.target.value)}
        />
      </div>
    </section>
  );
}
