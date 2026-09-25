import { useEffect, useId, useRef, useState } from "react";
import { ChevronDown } from "lucide-react";
import { useClickOutside } from "@delpi/plugin-ui/index";

import { ticketActionPresentation } from "../presentation/ticketActionPresentation";
import type { TicketWorkspaceAction, TicketWorkspaceActionId } from "../presentation/ticketWorkspaceActions";

export function TicketActionMenu({
  actions,
  activeId,
  onChange,
  disabled,
  idleLabel = "Responder",
}: {
  actions: readonly TicketWorkspaceAction[];
  activeId: TicketWorkspaceActionId | null;
  onChange: (id: TicketWorkspaceActionId) => void;
  disabled?: boolean;
  /** Label when no action is open (idle). */
  idleLabel?: string;
}) {
  const [open, setOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const panelId = useId();
  const selected = actions.find((item) => item.id === activeId) ?? null;
  const triggerPresentation = selected
    ? ticketActionPresentation(selected.id)
    : actions[0]
      ? ticketActionPresentation(actions[0].id)
      : null;
  const TriggerIcon = triggerPresentation?.icon;
  const triggerLabel = selected?.label ?? idleLabel;

  useClickOutside([wrapperRef], open, () => setOpen(false));

  useEffect(() => {
    if (!open) return;
    function handleKey(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [open]);

  if (actions.length === 0) return null;

  return (
    <div
      className="helpdesk-action-menu helpdesk-anchored-popover"
      ref={wrapperRef}
      data-action-idle={selected ? "false" : "true"}
    >
      <button
        type="button"
        className="helpdesk-action-menu__trigger"
        aria-label={selected ? `Ação ativa: ${selected.label}` : "Escolher ação do chamado"}
        aria-expanded={open}
        aria-controls={panelId}
        aria-haspopup="menu"
        disabled={disabled}
        data-action-variant={triggerPresentation?.variant}
        onClick={() => setOpen((current) => !current)}
      >
        {TriggerIcon ? (
          <span className="helpdesk-action-menu__trigger-icon" aria-hidden>
            <TriggerIcon size={16} />
          </span>
        ) : null}
        <span>{triggerLabel}</span>
        <ChevronDown size={16} aria-hidden />
      </button>
      {open ? (
        <div
          id={panelId}
          className="helpdesk-anchored-popover__panel helpdesk-action-menu__panel"
          role="menu"
          aria-label="Ações do chamado"
        >
          {actions.map((action) => {
            const presentation = ticketActionPresentation(action.id);
            const Icon = presentation.icon;
            return (
              <button
                key={action.id}
                type="button"
                role="menuitem"
                className={[
                  "helpdesk-action-menu__item",
                  action.id === activeId ? "helpdesk-action-menu__item--active" : null,
                ]
                  .filter(Boolean)
                  .join(" ")}
                data-action-variant={presentation.variant}
                onClick={() => {
                  onChange(action.id);
                  setOpen(false);
                }}
              >
                <span className="helpdesk-action-menu__item-icon" aria-hidden>
                  <Icon size={16} />
                </span>
                <span>{action.label}</span>
              </button>
            );
          })}
        </div>
      ) : null}
    </div>
  );
}
