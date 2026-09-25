import type { ReactNode } from "react";
import { X } from "lucide-react";

import { ticketActionPresentation } from "../presentation/ticketActionPresentation";
import type { TicketWorkspaceActionId } from "../presentation/ticketWorkspaceActions";

export function TicketActionCard({
  actionId,
  children,
  footer,
  onCancel,
  disabled,
}: {
  actionId: TicketWorkspaceActionId;
  children: ReactNode;
  footer?: ReactNode;
  onCancel: () => void;
  disabled?: boolean;
}) {
  const presentation = ticketActionPresentation(actionId);
  const Icon = presentation.icon;

  return (
    <section
      className="helpdesk-action-card"
      data-action-variant={presentation.variant}
      aria-labelledby={`helpdesk-action-card-title-${actionId}`}
    >
      <header className="helpdesk-action-card__header">
        <div className="helpdesk-action-card__title-row">
          <span className="helpdesk-action-card__icon" aria-hidden>
            <Icon size={18} />
          </span>
          <div className="helpdesk-action-card__titles">
            <h3 id={`helpdesk-action-card-title-${actionId}`} className="helpdesk-action-card__title">
              {presentation.label}
            </h3>
            {presentation.helperText ? (
              <p className="helpdesk-action-card__helper">{presentation.helperText}</p>
            ) : null}
          </div>
          <button
            type="button"
            className="helpdesk-action-card__close"
            aria-label="Cancelar ação"
            disabled={disabled}
            onClick={onCancel}
          >
            <X size={18} aria-hidden />
          </button>
        </div>
      </header>
      <div className="helpdesk-action-card__body">{children}</div>
      {footer ? <footer className="helpdesk-action-card__footer">{footer}</footer> : null}
    </section>
  );
}
