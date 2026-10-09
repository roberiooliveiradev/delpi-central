import { useId, useState } from "react";
import type { ReactNode } from "react";
import {
  AlertTriangle,
  Ban,
  CheckCircle2,
  ChevronDown,
  CircleDashed,
  CircleMinus,
  Database,
  Loader2,
  ShieldX,
  XCircle,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import type { StatusBadgeVariant } from "../feedback/StatusBadge";

/**
 * ActivityViewer — composable, provider-neutral presentation of an
 * observed activity (steps, sources, outcome) behind a compact,
 * expandable summary line.
 *
 * The component is render-only: every step, source and outcome is
 * explicit data supplied by the consumer. It never fabricates events,
 * timestamps, tool names or provenance, and carries no transport,
 * polling or orchestration logic. Unknown/absent data renders nothing.
 */

export type ActivityState =
  | "pending"
  | "running"
  | "completed"
  | "partial"
  | "blocked"
  | "denied"
  | "failed"
  | "cancelled"
  | "no_data";

export type ActivityStepView = {
  id: string;
  label: string;
  /** Optional short detail rendered under the label. */
  description?: string;
  state: ActivityState;
  /** Display label of the capability exercised — only when the
   *  consumer legitimately knows it. Never inferred from tool names. */
  capabilityLabel?: string;
  /** Display label of the owning specialist/source — only when the
   *  consumer legitimately knows it. */
  sourceLabel?: string;
  /** Pre-formatted, honest timestamp — the component never derives it. */
  timestampLabel?: string;
};

export type ActivitySourceView = {
  id: string;
  label: string;
  /** Honest observed status of the source, e.g. "consultada",
   *  "dados recebidos" — caller-owned vocabulary, never promoted to
   *  GROUNDED/verified by this component. */
  statusLabel?: string;
  /** Optional detail line (e.g. observation time). */
  detail?: string;
  /** Legitimate URL supplied by the caller. Absent → plain text,
   *  never a fabricated link. */
  href?: string;
};

export type ActivityOutcomeView = {
  label: string;
  tone?: StatusBadgeVariant;
  /** When true the outcome stays visible even while the detail
   *  region is collapsed — material warnings must never be buried
   *  inside a closed accordion. */
  persistent?: boolean;
};

export type ActivityViewerProps = {
  title: string;
  state: ActivityState;
  steps?: readonly ActivityStepView[];
  sources?: readonly ActivitySourceView[];
  outcome?: ActivityOutcomeView;
  /** Pre-formatted duration supplied by the caller — never measured. */
  durationLabel?: string;
  /** Secondary muted text appended to the summary line. */
  summaryDetail?: string;
  /** Force enable/disable the disclosure. Default: enabled only when
   *  there is something to expand. */
  expandable?: boolean;
  defaultExpanded?: boolean;
  /** Additional legitimate detail content inside the disclosure. */
  children?: ReactNode;
  className?: string;
};

const STATE_ICON: Record<ActivityState, LucideIcon> = {
  pending: CircleDashed,
  running: Loader2,
  completed: CheckCircle2,
  partial: AlertTriangle,
  blocked: AlertTriangle,
  denied: ShieldX,
  failed: XCircle,
  cancelled: Ban,
  no_data: CircleMinus,
};

const STATE_TONE: Record<ActivityState, string> = {
  pending: "neutral",
  running: "info",
  completed: "success",
  partial: "warning",
  blocked: "warning",
  denied: "danger",
  failed: "danger",
  cancelled: "neutral",
  no_data: "neutral",
};

function ActivityStepIcon({ state }: { state: ActivityState }) {
  const Icon = STATE_ICON[state];
  return (
    <span
      className={`delpi-ui-activity-viewer__step-icon delpi-ui-activity-viewer__step-icon--${STATE_TONE[state]}`}
      data-state={state}
      aria-hidden="true"
    >
      <Icon size={14} />
    </span>
  );
}

export function ActivityViewer({
  title,
  state,
  steps,
  sources,
  outcome,
  durationLabel,
  summaryDetail,
  expandable,
  defaultExpanded,
  children,
  className,
}: ActivityViewerProps) {
  const regionId = useId();
  const [expanded, setExpanded] = useState(Boolean(defaultExpanded));

  const hasDetails =
    (steps?.length ?? 0) > 0 ||
    (sources?.length ?? 0) > 0 ||
    Boolean(children) ||
    (Boolean(outcome) && !outcome?.persistent);
  const isExpandable = (expandable ?? true) && hasDetails;

  const SummaryIcon = STATE_ICON[state];
  const tone = STATE_TONE[state];

  const summaryBody = (
    <>
      <span
        className={`delpi-ui-activity-viewer__icon delpi-ui-activity-viewer__icon--${tone}`}
        data-state={state}
        aria-hidden="true"
      >
        <SummaryIcon size={15} />
      </span>
      <span className="delpi-ui-activity-viewer__title">{title}</span>
      {summaryDetail ? (
        <span className="delpi-ui-activity-viewer__summary-detail">
          {summaryDetail}
        </span>
      ) : null}
      {durationLabel ? (
        <span className="delpi-ui-activity-viewer__duration">
          {durationLabel}
        </span>
      ) : null}
      {isExpandable ? (
        <ChevronDown
          size={14}
          className="delpi-ui-activity-viewer__chevron"
          aria-hidden="true"
        />
      ) : null}
    </>
  );

  return (
    <div
      className={`delpi-ui-activity-viewer delpi-ui-activity-viewer--${tone}${
        className ? ` ${className}` : ""
      }`}
      data-state={state}
      aria-busy={state === "running" ? true : undefined}
      role={
        state === "running" || state === "pending" ? "status" : undefined
      }
    >
      {isExpandable ? (
        <button
          type="button"
          className="delpi-ui-activity-viewer__summary"
          aria-expanded={expanded}
          aria-controls={regionId}
          onClick={() => setExpanded((previous) => !previous)}
        >
          {summaryBody}
        </button>
      ) : (
        <div className="delpi-ui-activity-viewer__summary delpi-ui-activity-viewer__summary--static">
          {summaryBody}
        </div>
      )}

      {outcome?.persistent ? (
        <p
          className={`delpi-ui-activity-viewer__outcome delpi-ui-activity-viewer__outcome--${outcome.tone ?? tone}`}
          role={tone === "danger" || outcome.tone === "danger" ? "alert" : undefined}
        >
          {outcome.label}
        </p>
      ) : null}

      {isExpandable ? (
        <div
          id={regionId}
          role="region"
          aria-label={title}
          className="delpi-ui-activity-viewer__detail"
          hidden={!expanded}
        >
          {steps && steps.length > 0 ? (
            <ol className="delpi-ui-activity-viewer__steps">
              {steps.map((step) => (
                <li
                  key={step.id}
                  className="delpi-ui-activity-viewer__step"
                  data-state={step.state}
                >
                  <ActivityStepIcon state={step.state} />
                  <div className="delpi-ui-activity-viewer__step-body">
                    <span className="delpi-ui-activity-viewer__step-label">
                      {step.label}
                    </span>
                    {step.description ? (
                      <span className="delpi-ui-activity-viewer__step-description">
                        {step.description}
                      </span>
                    ) : null}
                    {step.capabilityLabel ||
                    step.sourceLabel ||
                    step.timestampLabel ? (
                      <span className="delpi-ui-activity-viewer__step-meta">
                        {step.capabilityLabel ? (
                          <span>{step.capabilityLabel}</span>
                        ) : null}
                        {step.sourceLabel ? (
                          <span>{step.sourceLabel}</span>
                        ) : null}
                        {step.timestampLabel ? (
                          <span>{step.timestampLabel}</span>
                        ) : null}
                      </span>
                    ) : null}
                  </div>
                </li>
              ))}
            </ol>
          ) : null}

          {sources && sources.length > 0 ? (
            <ul className="delpi-ui-activity-viewer__sources">
              {sources.map((source) => (
                <li
                  key={source.id}
                  className="delpi-ui-activity-viewer__source"
                >
                  <Database
                    size={13}
                    aria-hidden="true"
                    className="delpi-ui-activity-viewer__source-icon"
                  />
                  <span className="delpi-ui-activity-viewer__source-body">
                    {source.href ? (
                      <a
                        href={source.href}
                        className="delpi-ui-activity-viewer__source-link"
                        rel="noreferrer"
                      >
                        {source.label}
                      </a>
                    ) : (
                      <span className="delpi-ui-activity-viewer__source-label">
                        {source.label}
                      </span>
                    )}
                    {source.statusLabel ? (
                      <span className="delpi-ui-activity-viewer__source-status">
                        {source.statusLabel}
                      </span>
                    ) : null}
                    {source.detail ? (
                      <span className="delpi-ui-activity-viewer__source-detail">
                        {source.detail}
                      </span>
                    ) : null}
                  </span>
                </li>
              ))}
            </ul>
          ) : null}

          {outcome && !outcome.persistent ? (
            <p
              className={`delpi-ui-activity-viewer__outcome delpi-ui-activity-viewer__outcome--${outcome.tone ?? tone}`}
            >
              {outcome.label}
            </p>
          ) : null}

          {children}
        </div>
      ) : null}
    </div>
  );
}
