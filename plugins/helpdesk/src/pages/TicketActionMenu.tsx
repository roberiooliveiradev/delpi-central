import { useEffect, useId, useRef, useState } from "react";
import { ChevronDown } from "lucide-react";
import { useClickOutside } from "@delpi/plugin-ui/index";

import type { TicketWorkspaceAction, TicketWorkspaceActionId } from "../presentation/ticketWorkspaceActions";

export function TicketActionMenu({
  actions,
  activeId,
  onChange,
  disabled,
}: {
  actions: readonly TicketWorkspaceAction[];
  activeId: TicketWorkspaceActionId | null;
  onChange: (id: TicketWorkspaceActionId) => void;
  disabled?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const panelId = useId();
  const active = actions.find((item) => item.id === activeId) ?? actions[0] ?? null;

  useClickOutside([wrapperRef], open, () => setOpen(false));

  useEffect(() => {
    if (!open) return;
    function handleKey(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [open]);

  if (!active || actions.length === 0) return null;

  if (actions.length === 1) {
    return (
      <div className="helpdesk-action-menu helpdesk-action-menu--single" aria-label="Ação do chamado">
        <span className="helpdesk-action-menu__label">{active.label}</span>
      </div>
    );
  }

  return (
    <div className="helpdesk-action-menu helpdesk-anchored-popover" ref={wrapperRef}>
      <button
        type="button"
        className="helpdesk-action-menu__trigger"
        aria-label={`Ação: ${active.label}`}
        aria-expanded={open}
        aria-controls={panelId}
        disabled={disabled}
        onClick={() => setOpen((current) => !current)}
      >
        <span>{active.label}</span>
        <ChevronDown size={16} aria-hidden />
      </button>
      {open ? (
        <div
          id={panelId}
          className="helpdesk-anchored-popover__panel helpdesk-action-menu__panel"
          role="menu"
          aria-label="Ações do chamado"
        >
          {actions.map((action) => (
            <button
              key={action.id}
              type="button"
              role="menuitem"
              className={[
                "helpdesk-action-menu__item",
                action.id === active.id ? "helpdesk-action-menu__item--active" : null,
              ]
                .filter(Boolean)
                .join(" ")}
              onClick={() => {
                onChange(action.id);
                setOpen(false);
              }}
            >
              {action.label}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}
