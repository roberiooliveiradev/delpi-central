import type { KaizenRevision, KaizenRevisionChangeType } from "../../types/kaizen";

const CHANGE_TYPE_LABELS: Record<KaizenRevisionChangeType, string> = {
  baseline: "Baseline",
  implantacao: "Implantação",
  melhoria: "Melhoria",
  correcao: "Correção",
  descontinuacao: "Descontinuação",
  restauracao: "Restauração",
};

const CHANGE_TYPE_TONE: Record<KaizenRevisionChangeType, string> = {
  baseline: "muted",
  implantacao: "success",
  melhoria: "info",
  correcao: "warning",
  descontinuacao: "danger",
  restauracao: "info",
};

function formatDate(value: string | null): string {
  if (!value) return "—";
  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString("pt-BR");
}

type KaizenRevisionTimelineProps = {
  revisions: KaizenRevision[];
};

export function KaizenRevisionTimeline({ revisions }: KaizenRevisionTimelineProps) {
  if (revisions.length === 0) {
    return <p className="kz-empty-hint">Nenhuma revisão registrada.</p>;
  }

  return (
    <ol className="kz-timeline">
      {revisions.map((revision) => {
        const tone = CHANGE_TYPE_TONE[revision.change_type] ?? "muted";
        const current = revision.effective_until == null;
        return (
          <li key={revision.id} className="kz-timeline__item">
            <div className="kz-timeline__marker" aria-hidden="true" />
            <div className="kz-timeline__body">
              <div className="kz-timeline__head">
                <span className="kz-timeline__version">v{revision.revision_number}</span>
                <span className={`kz-badge kz-badge--${tone}`}>
                  {CHANGE_TYPE_LABELS[revision.change_type] ?? revision.change_type}
                </span>
                {current ? <span className="kz-badge kz-badge--current">Vigente</span> : null}
              </div>
              {revision.change_summary ? (
                <p className="kz-timeline__summary">{revision.change_summary}</p>
              ) : null}
              {revision.change_reason ? (
                <p className="kz-timeline__reason">{revision.change_reason}</p>
              ) : null}
              <p className="kz-timeline__dates">
                Vigência: {formatDate(revision.effective_from)}
                {" → "}
                {revision.effective_until ? formatDate(revision.effective_until) : "atual"}
              </p>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
