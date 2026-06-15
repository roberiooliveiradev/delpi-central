import { Download, ListFilter } from "lucide-react";

import { LMPS_HELP_TOOLTIPS } from "../content/helpTooltips";
import {
  LMPS_BRANCH_OPTIONS,
  LMPS_LISTING_TYPE_OPTIONS,
  LMPS_STATUS_OPTIONS,
} from "../constants/filterOptions";
import { FieldLabel } from "./HelpTooltip";
import { MultiSelectField } from "./MultiSelectField";

type FilterBarProps = {
  dateStart: string;
  dateEnd: string;
  branches: string[];
  listingTypes: string[];
  statuses: string[];
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onBranchesChange: (value: string[]) => void;
  onListingTypesChange: (value: string[]) => void;
  onStatusesChange: (value: string[]) => void;
  onRefresh: () => void;
  onExport?: () => void;
  exportDisabled?: boolean;
  disabled?: boolean;
};

export function FilterBar({
  dateStart,
  dateEnd,
  branches,
  listingTypes,
  statuses,
  onDateStartChange,
  onDateEndChange,
  onBranchesChange,
  onListingTypesChange,
  onStatusesChange,
  onRefresh,
  onExport,
  exportDisabled = false,
  disabled = false,
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
          {onExport ? (
            <button
              className="lmps-ghost-btn"
              type="button"
              onClick={onExport}
              disabled={exportDisabled}
            >
              <Download size={16} />
              Exportar CSV
            </button>
          ) : null}
          <button className="lmps-primary-btn" type="button" onClick={onRefresh}>
            <ListFilter size={16} />
            Atualizar
          </button>
        </div>
      </header>

      <section className="lmps-filters-row" aria-label="Filtros do dashboard">
        <label className="lmps-filter-box lmps-field">
          <FieldLabel label="Data inicial" hint={LMPS_HELP_TOOLTIPS.filters.dateStart} />
          <input
            type="date"
            value={dateStart}
            disabled={disabled}
            onChange={(event) => onDateStartChange(event.target.value)}
          />
        </label>

        <label className="lmps-filter-box lmps-field">
          <FieldLabel label="Data final" hint={LMPS_HELP_TOOLTIPS.filters.dateEnd} />
          <input
            type="date"
            value={dateEnd}
            disabled={disabled}
            onChange={(event) => onDateEndChange(event.target.value)}
          />
        </label>

        <MultiSelectField
          label="Filial"
          labelHint={LMPS_HELP_TOOLTIPS.filters.branch}
          emptyLabel="Todas"
          searchable
          options={LMPS_BRANCH_OPTIONS}
          selectedValues={branches}
          onChange={onBranchesChange}
          disabled={disabled}
        />

        <MultiSelectField
          label="Tipo"
          labelHint={LMPS_HELP_TOOLTIPS.filters.listingType}
          emptyLabel="Todos"
          searchable
          options={LMPS_LISTING_TYPE_OPTIONS}
          selectedValues={listingTypes}
          onChange={onListingTypesChange}
          disabled={disabled}
        />

        <MultiSelectField
          label="Status"
          labelHint={LMPS_HELP_TOOLTIPS.filters.status}
          emptyLabel="Todos"
          searchable
          options={LMPS_STATUS_OPTIONS}
          selectedValues={statuses}
          onChange={onStatusesChange}
          disabled={disabled}
        />
      </section>
    </>
  );
}
