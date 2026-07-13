import type { HistoricoFilters } from "../hooks/useInspecoesProcessoHistorico";

type HistoricoFiltersProps = {
  filters: HistoricoFilters;
  loading: boolean;
  onChange: (patch: Partial<HistoricoFilters>) => void;
  onSearch: () => void;
  onClear: () => void;
};

export function HistoricoFiltersBar({
  filters,
  loading,
  onChange,
  onSearch,
  onClear,
}: HistoricoFiltersProps) {
  return (
    <form
      className="ip-filters"
      aria-label="Filtros do histórico"
      onSubmit={(event) => {
        event.preventDefault();
        onSearch();
      }}
    >
      <div className="ip-filters__grid ip-filters__grid--compact">
        <label className="ip-field">
          <span className="ip-field__label">Ordem de produção</span>
          <input
            className="ip-input"
            type="search"
            value={filters.ordem_producao}
            onChange={(event) => onChange({ ordem_producao: event.target.value })}
            placeholder="Ex.: 10565201002"
            autoComplete="off"
          />
        </label>

        <label className="ip-field">
          <span className="ip-field__label">Código do produto</span>
          <input
            className="ip-input"
            type="search"
            value={filters.codigo_produto}
            onChange={(event) => onChange({ codigo_produto: event.target.value })}
            placeholder="Ex.: 50233817"
            autoComplete="off"
          />
        </label>
      </div>

      <p className="ip-auditoria-hint">
        Consulta limitada aos últimos 12 meses. Informe ordem de produção ou código do
        produto.
      </p>

      <div className="ip-filters__actions">
        <button type="submit" className="ip-button ip-button--primary" disabled={loading}>
          Buscar
        </button>
        <button type="button" className="ip-button" onClick={onClear} disabled={loading}>
          Limpar filtros
        </button>
      </div>
    </form>
  );
}
