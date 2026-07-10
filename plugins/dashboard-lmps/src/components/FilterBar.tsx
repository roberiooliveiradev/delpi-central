import type { ReactNode } from "react";
import { ListFilter } from "lucide-react";

import { DASHBOARD_SI_DEPARTMENT_ID } from "../constants/siDepartmentId";
import { LMPS_HELP_TOOLTIPS } from "../content/helpTooltips";
import {
  LMPS_BRANCH_OPTIONS,
  LMPS_LISTING_TYPE_OPTIONS,
  LMPS_STATUS_OPTIONS,
} from "../constants/filterOptions";
import { HelpTooltip } from "@delpi/plugin-ui/index";
import { DepartmentIddBadge } from "./DepartmentIddBadge";
import { MultiSelectField } from "./MultiSelectField";
import { FilterInputField, FiltersRow } from "./dashboardFiltersUi";
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
  exportActions?: ReactNode;
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
  exportActions,
  disabled = false,
}: FilterBarProps) {
  return (
    <>
      <header className="lmps-page-header">
        <div>
          <p className="lmps-eyebrow">DELPI • Analytics</p>
          <div className="lmps-page-header__title-row">
            <h1>Acompanhamento de LMPs</h1>
            <DepartmentIddBadge
              departmentId={DASHBOARD_SI_DEPARTMENT_ID}
              filters={{ competence, dateStart, dateEnd, branches }}
              classPrefix="lmps"
            />
          </div>
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
          {exportActions ? (
            <div className="lmps-header-action lmps-no-print">{exportActions}</div>
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

      <FiltersRow>
        <FilterInputField
          id="lmps-competence"
          label="Competência"
          hint={LMPS_HELP_TOOLTIPS.filters.competence}
          type="month"
          value={competence}
          disabled={disabled}
          onChange={onCompetenceChange}
        />
        <FilterInputField
          label="Data inicial"
          hint={LMPS_HELP_TOOLTIPS.filters.dateStart}
          type="date"
          value={dateStart}
          disabled={disabled}
          onChange={onDateStartChange}
        />
        <FilterInputField
          label="Data final"
          hint={LMPS_HELP_TOOLTIPS.filters.dateEnd}
          type="date"
          value={dateEnd}
          disabled={disabled}
          onChange={onDateEndChange}
        />

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
      </FiltersRow>
    </>
  );
}
