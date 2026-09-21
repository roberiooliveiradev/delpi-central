import { RefreshCw } from "lucide-react";
import type { ReactNode } from "react";

import type { TicketListViewModel } from "../presentation/ticketListViewModel";
import { HelpdeskIconButton } from "../ui/helpdeskUi";

/**
 * List chrome: chips, sort summary, column prefs slot, refresh.
 * Export / map / bulk stay console.
 */
export function TicketListToolbar({
  viewModel,
  onRefresh,
  columnPreferencesSlot,
  sortBuilderSlot,
  filterBuilderToggle,
}: {
  viewModel: TicketListViewModel;
  onRefresh?: () => void;
  columnPreferencesSlot?: ReactNode;
  sortBuilderSlot?: ReactNode;
  filterBuilderToggle?: ReactNode;
}) {
  const hasChips = viewModel.activeFilterLabels.length > 0 || Boolean(viewModel.primarySortLabel);
  if (
    !hasChips &&
    !onRefresh &&
    !columnPreferencesSlot &&
    !filterBuilderToggle &&
    !sortBuilderSlot
  ) {
    return null;
  }

  return (
    <div className="helpdesk-list-toolbar" role="region" aria-label="Recorte da lista">
      <div className="helpdesk-list-toolbar__chips">
        {viewModel.activeFilterLabels.map((label) => (
          <span key={label} className="helpdesk-list-toolbar__chip" data-kind="filter">
            Filtrado por {label}
          </span>
        ))}
        {viewModel.primarySortLabel ? (
          <span className="helpdesk-list-toolbar__chip" data-kind="sort">
            {viewModel.primarySortLabel}
          </span>
        ) : null}
      </div>
      <div className="helpdesk-list-toolbar__actions">
        {filterBuilderToggle}
        {sortBuilderSlot}
        {columnPreferencesSlot}
        {onRefresh ? (
          <HelpdeskIconButton aria-label="Atualizar lista" onClick={onRefresh}>
            <RefreshCw size={16} aria-hidden />
          </HelpdeskIconButton>
        ) : null}
      </div>
    </div>
  );
}
