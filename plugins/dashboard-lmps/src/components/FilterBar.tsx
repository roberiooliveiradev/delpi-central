import { Filter, ListFilter } from "lucide-react";

type FilterBarProps = {
  dateStart: string;
  dateEnd: string;
  status: string;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onStatusChange: (value: string) => void;
  onRefresh: () => void;
};

export function FilterBar({
  dateStart,
  dateEnd,
  status,
  onDateStartChange,
  onDateEndChange,
  onStatusChange,
  onRefresh
}: FilterBarProps) {
  return (
    <>
      <header className="lmps-page-header">
        <div>
          <p className="lmps-eyebrow">DELPI • Analytics</p>
          <h1>Dashboard LMPs</h1>
          <span className="lmps-page-subtitle">
            Indicadores de prazo, nível, status e lead time útil
          </span>
        </div>

        <div className="lmps-header-actions">
          <button className="lmps-ghost-btn" type="button">
            <Filter size={16} />
            Filtros
          </button>
          <button className="lmps-primary-btn" type="button" onClick={onRefresh}>
            <ListFilter size={16} />
            Atualizar
          </button>
        </div>
      </header>

      <section className="lmps-filters-row">
        <div className="lmps-filter-box">
          <label>Data inicial</label>
          <input
            type="date"
            value={dateStart}
            onChange={(e) => onDateStartChange(e.target.value)}
          />
        </div>

        <div className="lmps-filter-box">
          <label>Data final</label>
          <input
            type="date"
            value={dateEnd}
            onChange={(e) => onDateEndChange(e.target.value)}
          />
        </div>

        <div className="lmps-filter-box">
          <label>Status</label>
          <select
            value={status}
            onChange={(e) => onStatusChange(e.target.value)}
          >
            <option value="Todos">Todos</option>
            <option value="Pontual">Pontual</option>
            <option value="Atrasado">Atrasado</option>
            <option value="Andamento">Andamento</option>
          </select>
        </div>

        <div className="lmps-filter-box">
          <label>Critério</label>
          <input type="text" value="SLA por nível e dias úteis" readOnly />
        </div>
      </section>
    </>
  );
}