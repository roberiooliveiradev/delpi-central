import { useEffect, useId, useRef, useState } from "react";
import { ClipboardList, ListFilter } from "lucide-react";
import { useClickOutside } from "@delpi/plugin-ui/index";

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
  const panelId = useId();

  useClickOutside([wrapperRef], open, () => setOpen(false));

  useEffect(() => {
    if (!open) return;
    function handleKey(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [open]);

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
        aria-controls={panelId}
        onClick={() => setOpen((current) => !current)}
      >
        <ListFilter size={16} aria-hidden />
        <span>Filtro</span>
      </button>
      {open ? (
        <div
          id={panelId}
          className="helpdesk-anchored-popover__panel helpdesk-timeline-filter__panel"
          role="group"
          aria-label="Mostrar na linha do tempo"
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
        </div>
      ) : null}
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
  const panelId = useId();

  useClickOutside([wrapperRef], open, () => setOpen(false));

  useEffect(() => {
    if (!open) return;
    function handleKey(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [open]);

  if (tasks.length === 0) return null;

  return (
    <div className="helpdesk-timeline-tools helpdesk-anchored-popover" ref={wrapperRef}>
      <button
        type="button"
        className="helpdesk-timeline-tools__btn"
        aria-label="Ver lista de afazeres"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((current) => !current)}
      >
        <ClipboardList size={16} aria-hidden />
        <span>Afazeres ({tasks.length})</span>
      </button>
      {open ? (
        <div
          id={panelId}
          className="helpdesk-anchored-popover__panel helpdesk-task-list__panel"
          role="list"
          aria-label="Lista de afazeres do chamado"
        >
          {tasks.map((task) => (
            <div key={task.id} className="helpdesk-task-list__item" role="listitem" data-action-variant="task">
              <p className="helpdesk-task-list__content">{task.content || "Tarefa"}</p>
              {task.author ? (
                <p className="helpdesk-task-list__meta">{task.author}</p>
              ) : null}
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}
