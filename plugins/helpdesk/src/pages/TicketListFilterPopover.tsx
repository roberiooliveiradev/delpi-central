import { ListFilter } from "lucide-react";
import { AnchoredPanelPortal } from "@delpi/plugin-ui/index";
import { useRef, useState, type ReactNode } from "react";

import { helpTooltips } from "../content/helpTooltips";
import type { TicketListFilterGroup } from "../presentation/ticketListViewModel";
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
}: {
  group: TicketListFilterGroup;
  onChange: (next: TicketListFilterGroup) => void;
  onClear: () => void;
  onApply: () => void;
  urgencies: CatalogOption[];
  categories: CatalogOption[];
  assignees: CatalogOption[];
}) {
  const [open, setOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);

  return (
    <div className="helpdesk-anchored-popover helpdesk-anchored-popover--wide" ref={wrapperRef}>
      <button
        type="button"
        className="helpdesk-anchored-popover__trigger delpi-ui-table-toolbar-action"
        aria-label="Filtros avançados"
        aria-expanded={open}
        onClick={() => setOpen((current) => !current)}
      >
        <ListFilter size={16} aria-hidden />
        Filtros
      </button>
      <AnchoredPanelPortal
        open={open}
        anchorRef={wrapperRef}
        panelRef={panelRef}
        className="helpdesk-anchored-popover__panel helpdesk-anchored-popover__panel--wide"
        variant="bare"
        role="dialog"
        aria-label="Filtros avançados"
        preferredPlacement="bottom"
        horizontalAlign="end"
        gap={6}
        portalScopeClassName="dashboard-helpdesk"
        onDismiss={() => setOpen(false)}
      >
        <div className="helpdesk-anchored-popover__header">
          <strong className="helpdesk-anchored-popover__title">Filtros avançados</strong>
          <p className="helpdesk-anchored-popover__hint">{helpTooltips.filterBuilder.panel}</p>
        </div>
        <div className="helpdesk-anchored-popover__body">
          <TicketListFilterBuilder
            group={group}
            onChange={onChange}
            urgencies={urgencies}
            categories={categories}
            assignees={assignees}
            onClear={onClear}
            onApply={() => {
              onApply();
              setOpen(false);
            }}
          />
        </div>
      </AnchoredPanelPortal>
    </div>
  );
}

export type TicketListFilterPopoverTriggerProps = {
  children?: ReactNode;
};
