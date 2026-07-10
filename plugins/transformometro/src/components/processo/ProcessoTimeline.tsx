import { useMemo, useState } from "react";
import {
  CircleDot,
  ClipboardList,
  FileText,
  GitBranch,
  Layers,
  Link2,
  Ruler,
} from "lucide-react";

import { FieldLabel, HelpTooltip } from "@delpi/plugin-ui/index";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import type { ProcessoAuditLogEntry } from "../../utils/processoTimeline";
import {
  buildProcessoTimeline,
  filterProcessoTimelineEntries,
  PROCESSO_TIMELINE_FILTER_OPTIONS,
  type ProcessoTimelineCategory,
  type ProcessoTimelineEntry,
  type ProcessoTimelineFilter,
} from "../../utils/processoTimeline";
import { formatDateTime } from "../../utils/format";

type Props = {
  entries: ProcessoAuditLogEntry[];
  loading?: boolean;
};

const CATEGORY_ICONS = {
  processo: FileText,
  instancia: Layers,
  revisao: GitBranch,
  medicao: Ruler,
  investimento: ClipboardList,
  vinculo: Link2,
} as const satisfies Record<ProcessoTimelineCategory, typeof FileText>;

function TimelineItem({ entry }: { entry: ProcessoTimelineEntry }) {
  const Icon = CATEGORY_ICONS[entry.category] ?? FileText;

  return (
    <li className="tm-timeline-entry">
      <span className={`tm-timeline-entry__marker tm-timeline-entry__marker--${entry.category}`}>
        <Icon size={14} strokeWidth={2} aria-hidden="true" />
      </span>
      <div className="tm-timeline-entry__body">
        <div className="tm-timeline-entry__header">
          <strong>{entry.title}</strong>
          <time className="tm-timeline-entry__time" dateTime={entry.occurredAt}>
            {formatDateTime(entry.occurredAt)}
          </time>
        </div>
        {entry.detail ? <p className="tm-timeline-entry__detail">{entry.detail}</p> : null}
        {entry.meta ? <p className="tm-timeline-entry__meta">{entry.meta}</p> : null}
      </div>
    </li>
  );
}

export function ProcessoTimeline({ entries, loading = false }: Props) {
  const [filter, setFilter] = useState<ProcessoTimelineFilter>("all");
  const timeline = useMemo(() => buildProcessoTimeline(entries), [entries]);
  const visibleEntries = useMemo(
    () => filterProcessoTimelineEntries(timeline, filter),
    [timeline, filter]
  );

  return (
    <section className="ds-card ds-editable-section">
      <div className="ds-editable-section__header">
        <div>
          <h2 className="ds-section-title tm-timeline__title">
            Linha do tempo
            <HelpTooltip content={TM_HELP_TOOLTIPS.processos.timeline} ariaLabel="Ajuda: Linha do tempo" />
          </h2>
          <p className="ds-hint">
            Alterações do processo, mapeamento WBS, diagramas, instâncias, revisões, medições, investimentos e
            recursos vinculados.
          </p>
        </div>
      </div>

      <p className="tm-timeline-filters__label">
        <FieldLabel className="tm-field__label" label="Filtrar eventos" hint={TM_HELP_TOOLTIPS.processos.timelineFilter} />
      </p>
      <div className="tm-timeline-filters" role="tablist" aria-label="Filtrar linha do tempo">
        {PROCESSO_TIMELINE_FILTER_OPTIONS.map((option) => (
          <button
            key={option.value}
            type="button"
            role="tab"
            aria-selected={filter === option.value}
            className={
              filter === option.value
                ? "tm-timeline-filters__chip tm-timeline-filters__chip--active"
                : "tm-timeline-filters__chip"
            }
            onClick={() => setFilter(option.value)}
          >
            {option.label}
          </button>
        ))}
      </div>

      {loading ? (
        <p className="ds-state-box">Carregando histórico…</p>
      ) : visibleEntries.length ? (
        <ol className="tm-timeline-track">
          {visibleEntries.map((entry) => (
            <TimelineItem key={entry.id} entry={entry} />
          ))}
        </ol>
      ) : (
        <div className="ds-state-box">
          <CircleDot size={18} aria-hidden="true" />
          <span>{entries.length ? "Nenhum evento neste filtro." : "Nenhuma alteração registrada ainda."}</span>
        </div>
      )}
    </section>
  );
}
