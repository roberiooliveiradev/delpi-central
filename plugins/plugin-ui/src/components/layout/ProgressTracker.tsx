import {
  useId,
  useState,
  type KeyboardEvent,
  type ReactNode,
} from "react";

import { delpiUiClass } from "../../utils/delpiUiClass";

export type ProgressTrackerStepState =
  | "complete"
  | "current"
  | "available"
  | "locked"
  | "error";

export type ProgressTrackerDensity = "default" | "compact";

export type ProgressTrackerStep = {
  id: string;
  label: string;
  state: ProgressTrackerStepState;
  /** Extra accessible hint (e.g. "bloqueada"). */
  statusLabel?: string;
};

export type ProgressTrackerClassNames = {
  root: string;
  rootDensity: (density: ProgressTrackerDensity) => string;
  list: string;
  item: string;
  itemState: (state: ProgressTrackerStepState) => string;
  marker: string;
  label: string;
  connector: string;
  compactSummary: string;
  compactToggle: string;
  compactPanel: string;
  compactList: string;
  compactItem: string;
  compactItemState: (state: ProgressTrackerStepState) => string;
  compactStatus: string;
};

export type ProgressTrackerProps = {
  steps: ProgressTrackerStep[];
  currentStepId: string;
  interactive?: boolean;
  onStepChange?: (stepId: string) => void;
  ariaLabel?: string;
  density?: ProgressTrackerDensity;
  compactSummary?: string;
  className?: string;
  classNames: ProgressTrackerClassNames;
};

const STATE_STATUS: Record<ProgressTrackerStepState, string> = {
  complete: "concluída",
  current: "atual",
  available: "disponível",
  locked: "bloqueada",
  error: "com erro",
};

export function progressTrackerBemClasses(prefix: string): ProgressTrackerClassNames {
  const base = `${prefix}-progress-tracker`;
  const ui = "delpi-ui-progress-tracker";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);

  return {
    root: pair(base, ui),
    rootDensity: (density) => pair(`${base}--${density}`, `${ui}--${density}`),
    list: pair(`${base}__list`, `${ui}__list`),
    item: pair(`${base}__item`, `${ui}__item`),
    itemState: (state) => pair(`${base}__item--${state}`, `${ui}__item--${state}`),
    marker: pair(`${base}__marker`, `${ui}__marker`),
    label: pair(`${base}__label`, `${ui}__label`),
    connector: pair(`${base}__connector`, `${ui}__connector`),
    compactSummary: pair(`${base}__compact-summary`, `${ui}__compact-summary`),
    compactToggle: pair(`${base}__compact-toggle`, `${ui}__compact-toggle`),
    compactPanel: pair(`${base}__compact-panel`, `${ui}__compact-panel`),
    compactList: pair(`${base}__compact-list`, `${ui}__compact-list`),
    compactItem: pair(`${base}__compact-item`, `${ui}__compact-item`),
    compactItemState: (state) =>
      pair(`${base}__compact-item--${state}`, `${ui}__compact-item--${state}`),
    compactStatus: pair(`${base}__compact-status`, `${ui}__compact-status`),
  };
}

function isSelectable(state: ProgressTrackerStepState, interactive: boolean): boolean {
  if (!interactive) return false;
  return state === "complete" || state === "available" || state === "current" || state === "error";
}

function markerGlyph(state: ProgressTrackerStepState): string {
  if (state === "complete") return "✓";
  if (state === "error") return "!";
  if (state === "current") return "●";
  return "○";
}

/**
 * Linear journey progress tracker (not loading).
 * CSS: `styles/progress-tracker.css`.
 */
export function ProgressTracker({
  steps,
  currentStepId,
  interactive = false,
  onStepChange,
  ariaLabel = "Etapas",
  density = "default",
  compactSummary,
  className,
  classNames,
}: ProgressTrackerProps) {
  const panelId = useId();
  const [compactOpen, setCompactOpen] = useState(false);
  const current = steps.find((s) => s.id === currentStepId) ?? steps[0];

  function selectStep(step: ProgressTrackerStep) {
    if (!isSelectable(step.state, interactive)) return;
    onStepChange?.(step.id);
    if (density === "compact") setCompactOpen(false);
  }

  function onKeyDown(event: KeyboardEvent<HTMLButtonElement>, index: number) {
    if (!interactive) return;
    const selectable = steps
      .map((s, i) => ({ s, i }))
      .filter(({ s }) => isSelectable(s.state, interactive));
    if (!selectable.length) return;
    const pos = selectable.findIndex(({ i }) => i === index);
    if (pos < 0) return;
    if (event.key === "ArrowRight" || event.key === "ArrowDown") {
      event.preventDefault();
      const next = selectable[(pos + 1) % selectable.length];
      selectStep(next.s);
    } else if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
      event.preventDefault();
      const prev = selectable[(pos - 1 + selectable.length) % selectable.length];
      selectStep(prev.s);
    }
  }

  if (density === "compact") {
    const summary =
      compactSummary ||
      `Etapa atual: ${current?.label || "—"}. ${steps.filter((s) => s.state === "complete").length} de ${steps.length} concluídas.`;
    return (
      <div
        className={[classNames.root, classNames.rootDensity("compact"), className]
          .filter(Boolean)
          .join(" ")}
        aria-label={ariaLabel}
      >
        <p className={classNames.compactSummary}>{summary}</p>
        <button
          type="button"
          className={classNames.compactToggle}
          aria-expanded={compactOpen}
          aria-controls={panelId}
          onClick={() => setCompactOpen((v) => !v)}
        >
          {compactOpen ? "Ocultar etapas" : "Ver etapas"}
        </button>
        {compactOpen ? (
          <div id={panelId} className={classNames.compactPanel}>
            <ol className={classNames.compactList}>
              {steps.map((step) => {
                const status = step.statusLabel || STATE_STATUS[step.state];
                const selectable = isSelectable(step.state, interactive);
                return (
                  <li
                    key={step.id}
                    className={[
                      classNames.compactItem,
                      classNames.compactItemState(step.state),
                    ].join(" ")}
                  >
                    <button
                      type="button"
                      disabled={!selectable}
                      aria-current={step.state === "current" ? "step" : undefined}
                      aria-disabled={step.state === "locked" ? true : undefined}
                      onClick={() => selectStep(step)}
                    >
                      <span aria-hidden="true">{markerGlyph(step.state)}</span>{" "}
                      {step.label}
                      <span className={classNames.compactStatus}> {status}</span>
                    </button>
                  </li>
                );
              })}
            </ol>
          </div>
        ) : null}
      </div>
    );
  }

  return (
    <nav
      className={[classNames.root, classNames.rootDensity("default"), className]
        .filter(Boolean)
        .join(" ")}
      aria-label={ariaLabel}
    >
      <ol className={classNames.list}>
        {steps.map((step, index) => {
          const selectable = isSelectable(step.state, interactive);
          const status = step.statusLabel || STATE_STATUS[step.state];
          return (
            <li
              key={step.id}
              className={[classNames.item, classNames.itemState(step.state)].join(" ")}
            >
              {index > 0 ? <span className={classNames.connector} aria-hidden="true" /> : null}
              <button
                type="button"
                className={classNames.label}
                disabled={!selectable}
                aria-current={step.state === "current" ? "step" : undefined}
                aria-disabled={step.state === "locked" ? true : undefined}
                aria-label={`${step.label}, ${status}`}
                onClick={() => selectStep(step)}
                onKeyDown={(e) => onKeyDown(e, index)}
              >
                <span className={classNames.marker} aria-hidden="true">
                  {markerGlyph(step.state)}
                </span>
                <span>{step.label}</span>
              </button>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

export type DashboardProgressTrackerProps = Omit<ProgressTrackerProps, "classNames">;

export function createDashboardProgressTracker(config: { prefix: string }) {
  const classNames = progressTrackerBemClasses(config.prefix);
  return function DashboardProgressTracker(props: DashboardProgressTrackerProps): ReactNode {
    return <ProgressTracker classNames={classNames} {...props} />;
  };
}
