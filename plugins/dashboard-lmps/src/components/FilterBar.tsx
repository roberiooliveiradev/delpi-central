import { Download, ListFilter } from "lucide-react";

import { LMPS_HELP_TOOLTIPS } from "../content/helpTooltips";
import {
  LMPS_BRANCH_OPTIONS,
  LMPS_LISTING_TYPE_OPTIONS,
  LMPS_STATUS_OPTIONS,
} from "../constants/filterOptions";
import { FieldLabel, HelpTooltip } from "./HelpTooltip";
import { MultiSelectField } from "./MultiSelectField";
import { OPERATIONAL_UNIT_FIELD_LABEL } from "../utils/operationalUnitLabels";

type FilterBarProps = {
  competence: string;
  dateStart: string;
  dateEnd: string;
  branches: string[];
  listingTypes: string[];
  statuses: string[];
  onCompetenceChange: (value: string) => void;
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
  competence,
  dateStart,
  dateEnd,
  branches,
  listingTypes,
  statuses,
  onCompetenceChange,
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
          <span className="lmps-page-subtitle lmps-page-subtitle--with-help">
            Indicadores de prazo, nível, status e lead time útil
            <HelpTooltip
              content={LMPS_HELP_TOOLTIPS.actions.pageSubtitle}
              ariaLabel="Ajuda: escopo do dashboard"
              className="lmps-page-subtitle__help"
            />
          </span>
        </div>

        <div className="lmps-header-actions">
          {onExport ? (
            <div className="lmps-header-action">
              <button
                className="lmps-ghost-btn"
                type="button"
                onClick={onExport}
                disabled={exportDisabled}
              >
                <Download size={16} />
                Exportar CSV
              </button>
              <HelpTooltip
                content={LMPS_HELP_TOOLTIPS.actions.exportCsv}
                ariaLabel="Ajuda: exportar CSV"
                className="lmps-header-action__help"
              />
            </div>
          ) : null}
          <div className="lmps-header-action">
            <button className="lmps-primary-btn" type="button" onClick={onRefresh}>
              <ListFilter size={16} />
              Atualizar
            </button>
            <HelpTooltip
              content={LMPS_HELP_TOOLTIPS.actions.refresh}
              ariaLabel="Ajuda: atualizar dashboard"
              className="lmps-header-action__help"
            />
          </div>
        </div>
      </header>

      <section className="lmps-filters-row" aria-label="Filtros do dashboard">
        <label className="lmps-filter-box lmps-field">
          <FieldLabel label="Competência" hint={LMPS_HELP_TOOLTIPS.filters.competence} />
          <input
            id="lmps-competence"
            type="month"
            value={competence}
            disabled={disabled}
            onChange={(event) => onCompetenceChange(event.target.value)}
          />
        </label>

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
          label={OPERATIONAL_UNIT_FIELD_LABEL}
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
