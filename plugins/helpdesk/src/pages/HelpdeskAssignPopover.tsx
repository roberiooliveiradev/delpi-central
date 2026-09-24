import { useEffect, useId, useRef, useState } from "react";
import { ActionButton, HintAction } from "@delpi/plugin-ui/index";

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
}: {
  assignedDisplayName: string;
  assignedUserId?: number | null;
  value: HelpdeskAssigneeValue | null;
  onChange: (user: HelpdeskAssigneeValue | null) => void;
  onConfirm: () => void;
  saving: boolean;
}) {
  const [open, setOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const panelId = useId();
  const hasAssignee = Boolean(assignedUserId);
  const label = (assignedDisplayName || "").trim() || "Sem técnico";
  const actionLabel = hasAssignee ? "Alterar" : "Atribuir";

  useEffect(() => {
    if (!open) return;
    function handlePointer(event: MouseEvent) {
      if (wrapperRef.current?.contains(event.target as Node)) return;
      setOpen(false);
    }
    function handleKey(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", handlePointer);
    document.addEventListener("keydown", handleKey);
    return () => {
      document.removeEventListener("mousedown", handlePointer);
      document.removeEventListener("keydown", handleKey);
    };
  }, [open]);

  return (
    <div className="helpdesk-assign-summary" aria-label="Técnico atribuído">
      <div className="helpdesk-assign-summary__row">
        <div className="helpdesk-assign-summary__meta">
          <span className="helpdesk-assign-summary__label">Técnico</span>
          <span className="helpdesk-assign-summary__value">{label}</span>
        </div>
        <div className="helpdesk-anchored-popover helpdesk-anchored-popover--wide" ref={wrapperRef}>
          <button
            type="button"
            className="helpdesk-anchored-popover__trigger delpi-ui-table-toolbar-action"
            aria-label={actionLabel}
            aria-expanded={open}
            aria-controls={panelId}
            onClick={() => setOpen((current) => !current)}
          >
            {actionLabel}
          </button>
          {open ? (
            <div
              id={panelId}
              className="helpdesk-anchored-popover__panel"
              role="dialog"
              aria-label={hasAssignee ? "Reatribuir técnico" : "Atribuir técnico"}
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
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
