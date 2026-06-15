import { BRANCHES, KAIZEN_STATUSES, SAVINGS_TYPES } from "../constants/kaizen";

type KaizenRecordFiltersProps = {
  branch: string;
  status: string;
  savingsType: string;
  title: string;
  onBranchChange: (value: string) => void;
  onStatusChange: (value: string) => void;
  onSavingsTypeChange: (value: string) => void;
  onTitleChange: (value: string) => void;
};

export function KaizenRecordFilters({
  branch,
  status,
  savingsType,
  title,
  onBranchChange,
  onStatusChange,
  onSavingsTypeChange,
  onTitleChange,
}: KaizenRecordFiltersProps) {
  return (
    <section className="kz-filters-row" aria-label="Filtros de kaizen">
      <div className="kz-filter-box">
        <label htmlFor="kz-filter-branch">Filial</label>
        <select
          id="kz-filter-branch"
          value={branch}
          onChange={(event) => onBranchChange(event.target.value)}
        >
          <option value="">Todas</option>
          {BRANCHES.map((item) => (
            <option key={item.code} value={item.code}>
              {item.label}
            </option>
          ))}
        </select>
      </div>

      <div className="kz-filter-box">
        <label htmlFor="kz-filter-status">Status</label>
        <select
          id="kz-filter-status"
          value={status}
          onChange={(event) => onStatusChange(event.target.value)}
        >
          <option value="">Todos</option>
          {KAIZEN_STATUSES.map((item) => (
            <option key={item.value} value={item.value}>
              {item.label}
            </option>
          ))}
        </select>
      </div>

      <div className="kz-filter-box">
        <label htmlFor="kz-filter-savings-type">Tipo de economia</label>
        <select
          id="kz-filter-savings-type"
          value={savingsType}
          onChange={(event) => onSavingsTypeChange(event.target.value)}
        >
          <option value="">Todos</option>
          {SAVINGS_TYPES.map((item) => (
            <option key={item.value} value={item.value}>
              {item.label}
            </option>
          ))}
        </select>
      </div>

      <div className="kz-filter-box">
        <label htmlFor="kz-filter-title">Título</label>
        <input
          id="kz-filter-title"
          type="text"
          value={title}
          placeholder="Buscar por título"
          onChange={(event) => onTitleChange(event.target.value)}
        />
      </div>
    </section>
  );
}
