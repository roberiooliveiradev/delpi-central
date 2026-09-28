import { useRef, useState } from "react";
import { ClipboardList, ListFilter } from "lucide-react";
import { AnchoredPanelPortal } from "@delpi/plugin-ui/index";

import {
  TIMELINE_VISIBILITY_OPTIONS,
  type TimelineVisibilityKind,
  type TimelineVisibilityState,
} from "../presentation/timelineVisibility";

export function TicketTimelineFilterPopover({
  value,
  onChange,
}: {
  value: TimelineVisibilityState;
  onChange: (next: TimelineVisibilityState) => void;
}) {
  const [open, setOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);

  function toggle(kind: TimelineVisibilityKind) {
    onChange({ ...value, [kind]: !value[kind] });
  }

  return (
    <div className="helpdesk-timeline-tools helpdesk-anchored-popover" ref={wrapperRef}>
      <button
        type="button"
        className="helpdesk-timeline-tools__btn"
        aria-label="Filtro da linha do tempo"
        aria-expanded={open}
        onClick={() => setOpen((current) => !current)}
      >
        <ListFilter size={16} aria-hidden />
        <span>Filtro</span>
      </button>
      <AnchoredPanelPortal
        open={open}
        anchorRef={wrapperRef}
        panelRef={panelRef}
        className="helpdesk-anchored-popover__panel helpdesk-timeline-filter__panel"
        variant="bare"
        role="group"
        aria-label="Mostrar na linha do tempo"
        preferredPlacement="bottom"
        horizontalAlign="end"
        gap={6}
        portalScopeClassName="dashboard-helpdesk"
        onDismiss={() => setOpen(false)}
      >
        <p className="helpdesk-timeline-filter__title">Mostrar na linha do tempo</p>
        <ul className="helpdesk-timeline-filter__list">
          {TIMELINE_VISIBILITY_OPTIONS.map((option) => (
            <li key={option.id}>
              <label
                className="helpdesk-timeline-filter__option"
                data-action-variant={option.variant}
              >
                <input
                  type="checkbox"
                  checked={value[option.id]}
                  onChange={() => toggle(option.id)}
                />
                <span>{option.label}</span>
              </label>
            </li>
          ))}
        </ul>
      </AnchoredPanelPortal>
    </div>
  );
}

export function TicketTaskListPopover({
  tasks,
}: {
  tasks: readonly { id: number; content: string; author: string }[];
}) {
  const [open, setOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);

  if (tasks.length === 0) return null;

  return (
    <div className="helpdesk-timeline-tools helpdesk-anchored-popover" ref={wrapperRef}>
      <button
        type="button"
        className="helpdesk-timeline-tools__btn"
        aria-label="Ver lista de afazeres"
        aria-expanded={open}
        onClick={() => setOpen((current) => !current)}
      >
        <ClipboardList size={16} aria-hidden />
        <span>Afazeres ({tasks.length})</span>
      </button>
      <AnchoredPanelPortal
        open={open}
        anchorRef={wrapperRef}
        panelRef={panelRef}
        className="helpdesk-anchored-popover__panel helpdesk-task-list__panel"
        variant="bare"
        role="list"
        aria-label="Lista de afazeres do chamado"
        preferredPlacement="bottom"
        horizontalAlign="end"
        gap={6}
        portalScopeClassName="dashboard-helpdesk"
        onDismiss={() => setOpen(false)}
      >
        {tasks.map((task) => (
          <div key={task.id} className="helpdesk-task-list__item" role="listitem" data-action-variant="task">
            <p className="helpdesk-task-list__content">{task.content || "Tarefa"}</p>
            {task.author ? (
              <p className="helpdesk-task-list__meta">{task.author}</p>
            ) : null}
          </div>
        ))}
      </AnchoredPanelPortal>
    </div>
  );
}
