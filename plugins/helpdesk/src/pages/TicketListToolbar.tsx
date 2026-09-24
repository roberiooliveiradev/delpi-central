import type { ReactNode } from "react";
import { HintAction } from "@delpi/plugin-ui/index";

import { helpTooltips } from "../content/helpTooltips";
import type { TicketListViewModel } from "../presentation/ticketListViewModel";

/**
 * Segunda faixa da lista: view toggle + chips de filtro ativos (sem sort chip redundante).
 */
export function TicketListToolbar({
  viewModel,
  leading,
  trailing,
}: {
  viewModel: TicketListViewModel;
  leading?: ReactNode;
  trailing?: ReactNode;
}) {
  const filterChips = viewModel.activeFilterLabels;
  if (!leading && !trailing && filterChips.length === 0) return null;

  return (
    <div className="helpdesk-list-toolbar" role="region" aria-label="Recorte da lista">
      <div className="helpdesk-list-toolbar__leading">
        {leading}
        {filterChips.length > 0 ? (
          <div className="helpdesk-list-toolbar__chips">
            {filterChips.map((label) => (
              <HintAction key={label} hint={helpTooltips.listUi.filterChip} ariaLabel={`Ajuda: ${label}`}>
                <span className="helpdesk-list-toolbar__chip" data-kind="filter">
                  {label}
                </span>
              </HintAction>
            ))}
          </div>
        ) : null}
      </div>
      {trailing ? <div className="helpdesk-list-toolbar__actions">{trailing}</div> : null}
    </div>
  );
}
