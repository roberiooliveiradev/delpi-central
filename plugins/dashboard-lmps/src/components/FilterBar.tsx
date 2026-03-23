import { Filter, ListFilter } from "lucide-react";

type FilterBarProps = {
  dateStart: string;
  dateEnd: string;
  branch: string;
  status: string;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onBranchChange: (value: string) => void;
  onStatusChange: (value: string) => void;
  onRefresh: () => void;
};

export function FilterBar({
  dateStart,
  dateEnd,
  branch,
  status,
  onDateStartChange,
  onDateEndChange,
  onBranchChange,
  onStatusChange,
  onRefresh
}: FilterBarProps) {
  return (
    <>
      <header className="lmps-page-header">
        <div>
          <p className="lmps-eyebrow">DELPI • Analytics</p>
          <h1>Acompanhamento de LMPs</h1>
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
            alt="Data inicial"
            value={dateStart}
            onChange={(e) => onDateStartChange(e.target.value)}
          />
        </div>

        <div className="lmps-filter-box">
          <label>Data final</label>
          <input
            type="date"
            alt="Data final"
            value={dateEnd}
            onChange={(e) => onDateEndChange(e.target.value)}
          />
        </div>

        <div className="lmps-filter-box">
          <label>Filial</label>
          <select
            value={branch}
            onChange={(e) => onBranchChange(e.target.value)}
          >
            <option value="">Todas</option>
            <option value="01">01</option>
            <option value="02">02</option>
          </select>
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
            <option value="Retornada">Retornada</option>
          </select>
        </div>
      </section>
    </>
  );
}