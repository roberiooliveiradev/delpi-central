import { RefreshCw } from "lucide-react";
import type { ReactNode } from "react";
import { HintAction } from "@delpi/plugin-ui/index";

import { helpTooltips } from "../content/helpTooltips";
import type { TicketListViewModel } from "../presentation/ticketListViewModel";
import { HelpdeskIconButton } from "../ui/helpdeskUi";

/**
 * List chrome: view toggle, chips, sort summary, column prefs, refresh.
 * Export / map / bulk stay console.
 */
export function TicketListToolbar({
  viewModel,
  onRefresh,
  leading,
  clearFiltersSlot,
  columnPreferencesSlot,
  sortBuilderSlot,
  filterBuilderToggle,
}: {
  viewModel: TicketListViewModel;
  onRefresh?: () => void;
  leading?: ReactNode;
  clearFiltersSlot?: ReactNode;
  columnPreferencesSlot?: ReactNode;
  sortBuilderSlot?: ReactNode;
  filterBuilderToggle?: ReactNode;
}) {
  const hasChips = viewModel.activeFilterLabels.length > 0 || Boolean(viewModel.primarySortLabel);
  if (
    !hasChips &&
    !onRefresh &&
    !leading &&
    !clearFiltersSlot &&
    !columnPreferencesSlot &&
    !filterBuilderToggle &&
    !sortBuilderSlot
  ) {
    return null;
  }

  return (
    <div className="helpdesk-list-toolbar" role="region" aria-label="Recorte da lista">
      <div className="helpdesk-list-toolbar__leading">
        {leading}
        <div className="helpdesk-list-toolbar__chips">
          {viewModel.activeFilterLabels.map((label) => (
            <HintAction key={label} hint={helpTooltips.listUi.filterChip} ariaLabel={`Ajuda: ${label}`}>
              <span className="helpdesk-list-toolbar__chip" data-kind="filter">
                Filtrado por {label}
              </span>
            </HintAction>
          ))}
          {viewModel.primarySortLabel ? (
            <HintAction hint={helpTooltips.listUi.sortChip} ariaLabel="Ajuda: ordenação">
              <span className="helpdesk-list-toolbar__chip" data-kind="sort">
                {viewModel.primarySortLabel}
              </span>
            </HintAction>
          ) : null}
        </div>
      </div>
      <div className="helpdesk-list-toolbar__actions">
        {clearFiltersSlot}
        {filterBuilderToggle}
        {sortBuilderSlot}
        {columnPreferencesSlot}
        {onRefresh ? (
          <HintAction hint={helpTooltips.listUi.refreshList} ariaLabel="Ajuda: Atualizar lista">
            <HelpdeskIconButton aria-label="Atualizar lista" onClick={onRefresh}>
              <RefreshCw size={16} aria-hidden />
            </HelpdeskIconButton>
          </HintAction>
        ) : null}
      </div>
    </div>
  );
}
