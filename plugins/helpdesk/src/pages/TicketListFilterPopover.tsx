import { ListFilter } from "lucide-react";

import { helpTooltips } from "../content/helpTooltips";
import type { TicketListFilterGroup } from "../presentation/ticketListViewModel";
import { HelpdeskListToolbarPopover } from "../ui/helpdeskUi";
import { TicketListFilterBuilder } from "./TicketListFilterBuilder";

type CatalogOption = { id: number; name: string };

export function TicketListFilterPopover({
  group,
  onChange,
  onClear,
  onApply,
  urgencies,
  categories,
  assignees,
  requesters,
}: {
  group: TicketListFilterGroup;
  onChange: (next: TicketListFilterGroup) => void;
  onClear: () => void;
  onApply: () => void;
  urgencies: CatalogOption[];
  categories: CatalogOption[];
  assignees: CatalogOption[];
  requesters: CatalogOption[];
}) {
  return (
    <HelpdeskListToolbarPopover
      label="Filtros"
      icon={<ListFilter size={16} aria-hidden />}
      ariaLabel="Filtros avançados"
      panelAriaLabel="Filtros avançados"
      panelTitle="Filtros avançados"
      panelHint={helpTooltips.filterBuilder.panel}
      wide
    >
      {(close) => (
        <TicketListFilterBuilder
          group={group}
          onChange={onChange}
          urgencies={urgencies}
          categories={categories}
          assignees={assignees}
          requesters={requesters}
          onClear={onClear}
          onApply={() => {
            onApply();
            close();
          }}
        />
      )}
    </HelpdeskListToolbarPopover>
  );
}
