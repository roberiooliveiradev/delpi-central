import { Search } from "lucide-react";

type FilterBarProps = {
  dateStart: string;
  dateEnd: string;
  branch: string;
  employee: string;
  workCenter: string;
  statusOkOnly: boolean;
  branches: readonly string[];
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onBranchChange: (value: string) => void;
  onEmployeeChange: (value: string) => void;
  onWorkCenterChange: (value: string) => void;
  onStatusOkOnlyChange: (value: boolean) => void;
  onApply: () => void;
  loading?: boolean;
};

export function FilterBar({
  dateStart,
  dateEnd,
  branch,
  employee,
  workCenter,
  statusOkOnly,
  branches,
  onDateStartChange,
  onDateEndChange,
  onBranchChange,
  onEmployeeChange,
  onWorkCenterChange,
  onStatusOkOnlyChange,
  onApply,
  loading = false,
}: FilterBarProps) {
  return (
    <section className="ef-filter-bar" aria-label="Filtros do dashboard">
      <div className="ef-filter-bar__grid">
        <label className="ef-field">
          <span>Data início</span>
          <input
            type="date"
            value={dateStart}
            onChange={(event) => onDateStartChange(event.target.value)}
          />
        </label>

        <label className="ef-field">
          <span>Data fim</span>
          <input
            type="date"
            value={dateEnd}
            onChange={(event) => onDateEndChange(event.target.value)}
          />
        </label>

        <label className="ef-field">
          <span>Filial</span>
          <select
            value={branch}
            onChange={(event) => onBranchChange(event.target.value)}
          >
            <option value="">Todas (01 e 02)</option>
            {branches.map((item) => (
              <option key={item} value={item}>
                Filial {item}
              </option>
            ))}
          </select>
        </label>

        <label className="ef-field">
          <span>Operador (código ou login)</span>
          <input
            type="text"
            value={employee}
            placeholder="Ex.: 000123"
            onChange={(event) => onEmployeeChange(event.target.value)}
          />
        </label>

        <label className="ef-field">
          <span>Centro de trabalho</span>
          <input
            type="text"
            value={workCenter}
            placeholder="Ex.: CT-01A"
            onChange={(event) => onWorkCenterChange(event.target.value)}
          />
        </label>

        <label className="ef-field ef-field--checkbox">
          <input
            type="checkbox"
            checked={statusOkOnly}
            onChange={(event) => onStatusOkOnlyChange(event.target.checked)}
          />
          <span>Somente registros OK</span>
        </label>
      </div>

      <button
        type="button"
        className="ef-btn ef-btn--primary"
        onClick={onApply}
        disabled={loading}
      >
        <Search size={16} aria-hidden />
        {loading ? "Carregando…" : "Aplicar filtros"}
      </button>
    </section>
  );
}
