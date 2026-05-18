import type { NonconformityType } from "../types/nonconformity";

type NonconformityFiltersProps = {
  dateStart: string;
  dateEnd: string;
  branch: string;
  type: NonconformityType;
  status: string;
  itemCode: string;
  description: string;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onBranchChange: (value: string) => void;
  onTypeChange: (value: NonconformityType) => void;
  onStatusChange: (value: string) => void;
  onItemCodeChange: (value: string) => void;
  onDescriptionChange: (value: string) => void;
};

export function NonconformityFilters({
  dateStart,
  dateEnd,
  branch,
  type,
  status,
  itemCode,
  description,
  onDateStartChange,
  onDateEndChange,
  onBranchChange,
  onTypeChange,
  onStatusChange,
  onItemCodeChange,
  onDescriptionChange,
}: NonconformityFiltersProps) {
  return (
    <section className="dq-filters-row dq-filters-row--extended">
      <div className="dq-filter-box">
        <label htmlFor="nc-date-start">Data inicial</label>
        <input
          id="nc-date-start"
          type="date"
          value={dateStart}
          onChange={(e) => onDateStartChange(e.target.value)}
        />
      </div>

      <div className="dq-filter-box">
        <label htmlFor="nc-date-end">Data final</label>
        <input
          id="nc-date-end"
          type="date"
          value={dateEnd}
          onChange={(e) => onDateEndChange(e.target.value)}
        />
      </div>

      <div className="dq-filter-box">
        <label htmlFor="nc-branch">Filial</label>
        <select
          id="nc-branch"
          value={branch}
          onChange={(e) => onBranchChange(e.target.value)}
        >
          <option value="">Todas</option>
          <option value="01">01</option>
          <option value="02">02</option>
        </select>
      </div>

      <div className="dq-filter-box">
        <label htmlFor="nc-type">Tipo</label>
        <select
          id="nc-type"
          value={type}
          onChange={(e) => onTypeChange(e.target.value as NonconformityType)}
        >
          <option value="all">Todas</option>
          <option value="internal">Interna</option>
          <option value="external">Externa</option>
        </select>
      </div>

      <div className="dq-filter-box">
        <label htmlFor="nc-status">Status</label>
        <input
          id="nc-status"
          type="text"
          value={status}
          placeholder="Filtro de status"
          onChange={(e) => onStatusChange(e.target.value)}
        />
      </div>

      <div className="dq-filter-box">
        <label htmlFor="nc-item">Item</label>
        <input
          id="nc-item"
          type="text"
          value={itemCode}
          placeholder="Código do item"
          onChange={(e) => onItemCodeChange(e.target.value)}
        />
      </div>

      <div className="dq-filter-box dq-filter-box--wide">
        <label htmlFor="nc-description">Descrição</label>
        <input
          id="nc-description"
          type="text"
          value={description}
          placeholder="Buscar na descrição"
          onChange={(e) => onDescriptionChange(e.target.value)}
        />
      </div>
    </section>
  );
}
