import { ListFilter, ShieldCheck } from "lucide-react";

type FilterBarProps = {
  dateStart: string;
  dateEnd: string;
  branch: string;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onBranchChange: (value: string) => void;
  onRefresh: () => void;
  refreshing?: boolean;
};

export function FilterBar({
  dateStart,
  dateEnd,
  branch,
  onDateStartChange,
  onDateEndChange,
  onBranchChange,
  onRefresh,
  refreshing = false,
}: FilterBarProps) {
  return (
    <>
      <header className="dq-page-header">
        <div className="dq-page-header__brand">
          <div className="dq-header__icon" aria-hidden="true">
            <ShieldCheck size={28} strokeWidth={1.75} />
          </div>
          <div>
            <p className="dq-eyebrow">DELPI • Qualidade</p>
            <h1>Dashboard Qualidade</h1>
            <span className="dq-page-subtitle">
              PPM, kaizens, auditorias 5S e NC (TOTVS)
            </span>
          </div>
        </div>

        <div className="dq-header-actions">
          <button
            className="dq-primary-btn"
            type="button"
            onClick={onRefresh}
            disabled={refreshing}
          >
            <ListFilter size={16} />
            {refreshing ? "Atualizando…" : "Atualizar"}
          </button>
        </div>
      </header>

      <section className="dq-filters-row">
        <div className="dq-filter-box">
          <label htmlFor="dq-date-start">Data inicial</label>
          <input
            id="dq-date-start"
            type="date"
            value={dateStart}
            onChange={(e) => onDateStartChange(e.target.value)}
          />
        </div>

        <div className="dq-filter-box">
          <label htmlFor="dq-date-end">Data final</label>
          <input
            id="dq-date-end"
            type="date"
            value={dateEnd}
            onChange={(e) => onDateEndChange(e.target.value)}
          />
        </div>

        <div className="dq-filter-box">
          <label htmlFor="dq-branch">Filial</label>
          <select
            id="dq-branch"
            value={branch}
            onChange={(e) => onBranchChange(e.target.value)}
          >
            <option value="">Todas</option>
            <option value="01">01</option>
            <option value="02">02</option>
          </select>
        </div>
      </section>
    </>
  );
}
