import { ListFilter } from "lucide-react";
import { useClickOutside } from "@delpi/plugin-ui/index";
import { useId, useRef, useState, useEffect, type ReactNode } from "react";

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
  const panelId = useId();

  // SelectField/MultiSelect abrem painel no body — useClickOutside ignora overlays aninhados.
  useClickOutside([wrapperRef], open, () => setOpen(false));

  useEffect(() => {
    if (!open) return;
    function handleKey(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [open]);

  return (
    <div className="helpdesk-anchored-popover helpdesk-anchored-popover--wide" ref={wrapperRef}>
      <button
        type="button"
        className="helpdesk-anchored-popover__trigger delpi-ui-table-toolbar-action"
        aria-label="Filtros avançados"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((current) => !current)}
      >
        <ListFilter size={16} aria-hidden />
        Filtros
      </button>
      {open ? (
        <div
          id={panelId}
          className="helpdesk-anchored-popover__panel"
          role="dialog"
          aria-label="Filtros avançados"
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
        </div>
      ) : null}
    </div>
  );
}

export type TicketListFilterPopoverTriggerProps = {
  children?: ReactNode;
};
