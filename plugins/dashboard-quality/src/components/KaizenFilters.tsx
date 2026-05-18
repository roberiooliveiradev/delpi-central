type KaizenFiltersProps = {
  dateStart: string;
  dateEnd: string;
  branch: string;
  branches?: string[];
  branchesLoading?: boolean;
  title: string;
  status: string;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onBranchChange: (value: string) => void;
  onTitleChange: (value: string) => void;
  onStatusChange: (value: string) => void;
};

export function KaizenFilters({
  dateStart,
  dateEnd,
  branch,
  branches = [],
  branchesLoading = false,
  title,
  status,
  onDateStartChange,
  onDateEndChange,
  onBranchChange,
  onTitleChange,
  onStatusChange,
}: KaizenFiltersProps) {
  const branchOptions =
    branches.length > 0 ? branches : branch ? [branch] : [];

  return (
    <section className="dq-filters-row dq-filters-row--extended">
      <div className="dq-filter-box">
        <label htmlFor="kz-date-start">Data inicial</label>
        <input
          id="kz-date-start"
          type="date"
          value={dateStart}
          onChange={(e) => onDateStartChange(e.target.value)}
        />
      </div>

      <div className="dq-filter-box">
        <label htmlFor="kz-date-end">Data final</label>
        <input
          id="kz-date-end"
          type="date"
          value={dateEnd}
          onChange={(e) => onDateEndChange(e.target.value)}
        />
      </div>

      <div className="dq-filter-box">
        <label htmlFor="kz-branch">Filial</label>
        <select
          id="kz-branch"
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

      <div className="dq-filter-box">
        <label htmlFor="kz-title">Título</label>
        <input
          id="kz-title"
          type="text"
          value={title}
          placeholder="Buscar por título"
          onChange={(e) => onTitleChange(e.target.value)}
        />
      </div>

      <div className="dq-filter-box">
        <label htmlFor="kz-status">Status</label>
        <input
          id="kz-status"
          type="text"
          value={status}
          placeholder="Filtro de status"
          onChange={(e) => onStatusChange(e.target.value)}
        />
      </div>
    </section>
  );
}
