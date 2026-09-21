import { Columns3, RefreshCw } from "lucide-react";

import type { TicketListViewModel } from "../presentation/ticketListViewModel";
import { HelpdeskIconButton } from "../ui/helpdeskUi";

/**
 * List chrome slots for GLPI-parity listing (chips, sort summary, column prefs, refresh).
 * Export / map / bulk actions stay console — slots are typed but not rendered until H13.
 */
export function TicketListToolbar({
  viewModel,
  onRefresh,
  onOpenColumnPreferences,
}: {
  viewModel: TicketListViewModel;
  onRefresh?: () => void;
  onOpenColumnPreferences?: () => void;
}) {
  const hasChips = viewModel.activeFilterLabels.length > 0 || Boolean(viewModel.primarySortLabel);
  if (!hasChips && !onRefresh && !onOpenColumnPreferences) return null;

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
        {onOpenColumnPreferences ? (
          <HelpdeskIconButton
            aria-label="Selecionar colunas da lista"
            title="Selecionar colunas da lista"
            onClick={onOpenColumnPreferences}
          >
            <Columns3 size={16} aria-hidden />
          </HelpdeskIconButton>
        ) : null}
        {onRefresh ? (
          <HelpdeskIconButton aria-label="Atualizar lista" title="Atualizar lista" onClick={onRefresh}>
            <RefreshCw size={16} aria-hidden />
          </HelpdeskIconButton>
        ) : null}
      </div>
    </div>
  );
}
