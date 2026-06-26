import { useMemo, useState } from "react";
import {
  CheckCircle2,
  CircleDot,
  ClipboardList,
  FileText,
  Paperclip,
  Search,
} from "lucide-react";

import type { ActionPlanDetail } from "../types/actionPlan";
import { formatDateTime } from "../utils/format";
import {
  buildPlanTimeline,
  filterTimelineEntries,
  TIMELINE_FILTER_OPTIONS,
  type PlanTimelineEntry,
  type TimelineCategory,
  type TimelineFilter,
} from "../utils/planTimeline";
import { PAC_HELP_TOOLTIPS } from "../content/helpTooltips";
import { SectionCard } from "./ui/SectionCard";
import { FieldLabel } from "./ui/HelpTooltip";

type Props = {
  detail: ActionPlanDetail;
};

function categoryIcon(category: TimelineCategory) {
  switch (category) {
    case "actions":
      return ClipboardList;
    case "evidence":
      return Paperclip;
    case "effectiveness":
      return CheckCircle2;
    case "analysis":
      return Search;
    default:
      return FileText;
  }
}

function TimelineItem({ entry }: { entry: PlanTimelineEntry }) {
  const Icon = categoryIcon(entry.category);

  return (
    <li className="pac-timeline-entry">
      <span className={`pac-timeline-entry__marker pac-timeline-entry__marker--${entry.category}`}>
        <Icon size={14} strokeWidth={2} aria-hidden="true" />
      </span>
      <div className="pac-timeline-entry__body">
        <div className="pac-timeline-entry__header">
          <strong>{entry.title}</strong>
          <time className="pac-muted" dateTime={entry.occurredAt}>
            {formatDateTime(entry.occurredAt)}
          </time>
        </div>
        {entry.detail ? <p className="pac-timeline-entry__detail">{entry.detail}</p> : null}
        {entry.meta ? <p className="pac-muted pac-timeline-entry__meta">{entry.meta}</p> : null}
      </div>
    </li>
  );
}

export function PlanTimeline({ detail }: Props) {
  const [filter, setFilter] = useState<TimelineFilter>("all");
  const entries = useMemo(() => buildPlanTimeline(detail), [detail]);
  const visibleEntries = useMemo(
    () => filterTimelineEntries(entries, filter),
    [entries, filter],
  );

  return (
    <SectionCard
      title="Linha do tempo"
      hint={PAC_HELP_TOOLTIPS.sections.timeline}
      subtitle="Status, ações, evidências e eficácia em ordem cronológica."
    >
      <p className="pac-timeline-filters__label">
        <FieldLabel label="Filtrar eventos" hint={PAC_HELP_TOOLTIPS.detail.timelineFilter} />
      </p>
      <div className="pac-timeline-filters" role="tablist" aria-label="Filtrar linha do tempo">
        {TIMELINE_FILTER_OPTIONS.map((option) => (
          <button
            key={option.value}
            type="button"
            role="tab"
            aria-selected={filter === option.value}
            className={
              filter === option.value
                ? "pac-timeline-filters__chip pac-timeline-filters__chip--active"
                : "pac-timeline-filters__chip"
            }
            onClick={() => setFilter(option.value)}
          >
            {option.label}
          </button>
        ))}
      </div>

      {visibleEntries.length ? (
        <ol className="pac-timeline-track">
          {visibleEntries.map((entry) => (
            <TimelineItem key={entry.id} entry={entry} />
          ))}
        </ol>
      ) : (
        <div className="pac-state-box">
          <CircleDot size={18} aria-hidden="true" />
          <span>Nenhum evento neste filtro.</span>
        </div>
      )}
    </SectionCard>
  );
}
