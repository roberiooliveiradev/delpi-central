import { useEffect, useRef, useState } from "react";
import { ActionButton, AnchoredPanelPortal, HintAction } from "@delpi/plugin-ui/index";

import { helpTooltips } from "../content/helpTooltips";
import {
  HelpdeskAssigneePicker,
  type HelpdeskAssigneeValue,
} from "../components/HelpdeskAssigneePicker";

export function HelpdeskAssignPopover({
  assignedDisplayName,
  assignedUserId,
  value,
  onChange,
  onConfirm,
  saving,
  canAssign = true,
  variant = "block",
}: {
  assignedDisplayName: string;
  assignedUserId?: number | null;
  value: HelpdeskAssigneeValue | null;
  onChange: (user: HelpdeskAssigneeValue | null) => void;
  onConfirm: () => void;
  saving: boolean;
  /** Backend AuthZ disclosure only — never invents assign authority. */
  canAssign?: boolean;
  /** `inline` embeds into the ticket summary rail. */
  variant?: "block" | "inline";
}) {
  const [open, setOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const hasAssignee = Boolean(assignedUserId);
  const label = (assignedDisplayName || "").trim() || "Sem técnico";
  const actionLabel = hasAssignee ? "Alterar" : "Atribuir";
  const inline = variant === "inline";

  useEffect(() => {
    if (!canAssign && open) setOpen(false);
  }, [canAssign, open]);

  const action = canAssign ? (
    <div className="helpdesk-anchored-popover helpdesk-anchored-popover--wide" ref={wrapperRef}>
      <button
        type="button"
        className="helpdesk-anchored-popover__trigger delpi-ui-table-toolbar-action"
        aria-label={actionLabel}
        aria-expanded={open}
        onClick={() => setOpen((current) => !current)}
      >
        {actionLabel}
      </button>
      <AnchoredPanelPortal
        open={open}
        anchorRef={wrapperRef}
        panelRef={panelRef}
        className="helpdesk-anchored-popover__panel helpdesk-anchored-popover__panel--wide"
        variant="bare"
        role="dialog"
        aria-label={hasAssignee ? "Reatribuir técnico" : "Atribuir técnico"}
        preferredPlacement="bottom"
        horizontalAlign="end"
        gap={6}
        portalScopeClassName="dashboard-helpdesk"
        onDismiss={() => setOpen(false)}
      >
          <div className="helpdesk-anchored-popover__header">
            <strong className="helpdesk-anchored-popover__title">
              {hasAssignee ? "Reatribuir técnico" : "Atribuir técnico"}
            </strong>
          </div>
          <div className="helpdesk-anchored-popover__body helpdesk-assign-popover__body">
            <HelpdeskAssigneePicker
              label={hasAssignee ? "Novo técnico" : "Técnico"}
              hint={helpTooltips.detailUi.assignee}
              value={value}
              onChange={onChange}
            />
            <HintAction
              hint={helpTooltips.detailUi.assigneeAction}
              ariaLabel="Ajuda: Confirmar atribuição"
            >
              <ActionButton
                variant="primary"
                type="button"
                disabled={
                  saving ||
                  !value?.id ||
                  Number(value.id) === Number(assignedUserId || 0)
                }
                onClick={() => {
                  onConfirm();
                  setOpen(false);
                }}
              >
                {saving ? "Salvando…" : hasAssignee ? "Reatribuir" : "Atribuir"}
              </ActionButton>
            </HintAction>
          </div>
      </AnchoredPanelPortal>
    </div>
  ) : null;

  if (inline) {
    return (
      <div
        className="helpdesk-assign-summary helpdesk-assign-summary--inline"
        aria-label="Técnico atribuído"
      >
        <span className="helpdesk-ticket-summary-rail__label">Técnico</span>
        <span className="helpdesk-ticket-summary-rail__value">{label}</span>
        {action}
      </div>
    );
  }

  return (
    <div className="helpdesk-assign-summary" aria-label="Técnico atribuído">
      <div className="helpdesk-assign-summary__row">
        <div className="helpdesk-assign-summary__meta">
          <span className="helpdesk-assign-summary__label">Técnico</span>
          <span className="helpdesk-assign-summary__value">{label}</span>
        </div>
        {action}
      </div>
    </div>
  );
}
