import { useRef, useState } from "react";
import { ChevronDown } from "lucide-react";
import { AnchoredPanelPortal } from "@delpi/plugin-ui/index";

import { ticketActionPresentation } from "../presentation/ticketActionPresentation";
import type { TicketWorkspaceAction, TicketWorkspaceActionId } from "../presentation/ticketWorkspaceActions";

const HELPDESK_PORTAL_SCOPE = "dashboard-helpdesk";

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
  const anchorRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const selected = actions.find((item) => item.id === activeId) ?? null;
  const triggerPresentation = selected
    ? ticketActionPresentation(selected.id)
    : actions[0]
      ? ticketActionPresentation(actions[0].id)
      : null;
  const TriggerIcon = triggerPresentation?.icon;
  const triggerLabel = selected?.label ?? idleLabel;

  if (actions.length === 0) return null;

  return (
    <div
      className="helpdesk-action-menu"
      ref={anchorRef}
      data-action-idle={selected ? "false" : "true"}
    >
      <button
        type="button"
        className="helpdesk-action-menu__trigger"
        aria-label={selected ? `Ação ativa: ${selected.label}` : "Escolher ação do chamado"}
        aria-expanded={open}
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
      <AnchoredPanelPortal
        open={open}
        anchorRef={anchorRef}
        panelRef={panelRef}
        className="helpdesk-action-menu__panel"
        variant="bare"
        role="menu"
        aria-label="Ações do chamado"
        preferredPlacement="top"
        horizontalAlign="start"
        gap={6}
        portalScopeClassName={HELPDESK_PORTAL_SCOPE}
        onDismiss={() => setOpen(false)}
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
      </AnchoredPanelPortal>
    </div>
  );
}
