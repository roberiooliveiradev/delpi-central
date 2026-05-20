type LmpFiltersProps = {
  listingType: string;
  status: string;
  onListingTypeChange: (value: string) => void;
  onStatusChange: (value: string) => void;
};

export function LmpFilters({
  listingType,
  status,
  onListingTypeChange,
  onStatusChange,
}: LmpFiltersProps) {
  return (
    <section className="ds-filters-row ds-filters-row--extended">
      <div className="ds-filter-box">
        <label htmlFor="de-listing-type">Tipo</label>
        <select
          id="de-listing-type"
          value={listingType}
          onChange={(e) => onListingTypeChange(e.target.value)}
        >
          <option value="Todos">Todos</option>
          <option value="LMP">LMP</option>
          <option value="Amostra">Amostra</option>
          <option value="Outro">Outro</option>
        </select>
      </div>
      <div className="ds-filter-box">
        <label htmlFor="de-lmp-status">Status</label>
        <select
          id="de-lmp-status"
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
  );
}
