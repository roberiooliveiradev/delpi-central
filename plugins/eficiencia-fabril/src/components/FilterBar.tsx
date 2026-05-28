import { Search } from "lucide-react";

type FilterBarProps = {
  dateStart: string;
  dateEnd: string;
  branch: string;
  op: string;
  employee: string;
  workCenter: string;
  branches: readonly string[];
  hasPendingChanges?: boolean;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onBranchChange: (value: string) => void;
  onOpChange: (value: string) => void;
  onEmployeeChange: (value: string) => void;
  onWorkCenterChange: (value: string) => void;
  onApply: () => void;
  loading?: boolean;
};

export function FilterBar({
  dateStart,
  dateEnd,
  branch,
  op,
  employee,
  workCenter,
  branches,
  hasPendingChanges = false,
  onDateStartChange,
  onDateEndChange,
  onBranchChange,
  onOpChange,
  onEmployeeChange,
  onWorkCenterChange,
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
          <span>Operador (nome)</span>
          <input
            type="text"
            value={employee}
            placeholder="Ex.: CRISTIANE"
            onChange={(event) => onEmployeeChange(event.target.value)}
          />
        </label>

        <label className="ef-field">
          <span>OP</span>
          <input
            type="text"
            value={op}
            placeholder="Ex.: 24549301007"
            onChange={(event) => onOpChange(event.target.value)}
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

      </div>

      <button
        type="button"
        className="ef-btn ef-btn--primary"
        onClick={onApply}
        disabled={loading}
      >
        <Search size={16} aria-hidden />
        {loading
          ? "Carregando…"
          : hasPendingChanges
            ? "Aplicar filtros *"
            : "Aplicar filtros"}
      </button>
    </section>
  );
}
