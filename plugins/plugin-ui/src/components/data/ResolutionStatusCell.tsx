import { useEffect, useMemo, useRef, useState, type KeyboardEvent, type MouseEvent } from "react";

import { delpiUiClass, withBemModifier } from "../../utils/delpiUiClass";
import { ActionButton } from "../actions/ActionButton";

export type ResolutionStatus = "open" | "resolved" | "not_applicable";

export type ResolutionStatusCellLabels = {
  /** "Resolver" */
  resolve: string;
  /** "Reabrir" */
  reopen: string;
  /** "Resolvida" */
  resolved: string;
  /** "Resolvida em {date} por {user}" */
  resolvedOn: string;
  /** "Explicada" */
  notApplicable: string;
  /** "Salvando…" */
  sending: string;
  /** "Marcar como resolvida" — primary action label of `variant="full"`. */
  markResolved: string;
};

export type ResolutionStatusCellClassNames = {
  root: string;
  status: string;
  statusIcon: string;
  statusText: string;
  /** Visually hidden text for assistive technology. */
  srOnly: string;
  /** "Resolvida em … por …" line of `variant="full"`. */
  detail: string;
  actions: string;
  button: string;
};

export type ResolutionStatusCellProps = {
  status: ResolutionStatus;
  /** ISO timestamp of the resolution. */
  resolvedAt?: string | null;
  /** Display name of who resolved. */
  resolvedBy?: string | null;
  /**
   * Resolve action. When it returns a promise the cell shows `sending` until it
   * settles, even without `pending`. A rejection only restores the previous
   * state: surfacing the error to the user is the consumer's responsibility.
   */
  onResolve?: () => void | Promise<void>;
  /** Reopen action; same promise semantics as `onResolve`. */
  onReopen?: () => void | Promise<void>;
  /** Request in flight, controlled by the consumer. */
  pending?: boolean;
  disabled?: boolean;
  /**
   * `cell` (table), `compact` (mobile card) or `full` (detail footer).
   * Default `cell`.
   */
  variant?: "cell" | "compact" | "full";
  /** Names the record for assistive technology: `Resolver {contextLabel}`. */
  contextLabel?: string;
  /** Default: `dd/MM` (`cell`/`compact`) or `dd/MM/yyyy HH:mm` (`full`). */
  dateFormatter?: (iso: string) => string;
  labels?: Partial<ResolutionStatusCellLabels>;
  /** BEM dual-class prefix. Default `ds`. */
  prefix?: string;
  className?: string;
  classNames?: Partial<ResolutionStatusCellClassNames>;
};

export const DEFAULT_RESOLUTION_STATUS_CELL_LABELS: ResolutionStatusCellLabels = {
  resolve: "Resolver",
  reopen: "Reabrir",
  resolved: "Resolvida",
  resolvedOn: "Resolvida em {date} por {user}",
  notApplicable: "Explicada",
  sending: "Salvando…",
  markResolved: "Marcar como resolvida",
};

export function resolutionStatusCellBemClasses(prefix: string): ResolutionStatusCellClassNames {
  const ui = "delpi-ui-resolution-status-cell";
  const base = `${prefix}-resolution-status-cell`;
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    root: pair(base, ui),
    status: pair(`${base}__status`, `${ui}__status`),
    statusIcon: pair(`${base}__status-icon`, `${ui}__status-icon`),
    statusText: pair(`${base}__status-text`, `${ui}__status-text`),
    srOnly: pair(`${base}__sr-only`, `${ui}__sr-only`),
    detail: pair(`${base}__detail`, `${ui}__detail`),
    actions: pair(`${base}__actions`, `${ui}__actions`),
    button: pair(`${base}__button`, `${ui}__button`),
  };
}

function pad(value: number): string {
  return String(value).padStart(2, "0");
}

/** Default date formats; empty string for unparseable input. */
export function formatResolutionDate(iso: string, withTime: boolean): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  const day = `${pad(date.getDate())}/${pad(date.getMonth() + 1)}`;
  if (!withTime) return day;
  return `${day}/${date.getFullYear()} ${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function withContext(text: string, contextLabel?: string): string {
  return contextLabel ? `${text} ${contextLabel}` : text;
}

/**
 * Resolved / not-resolved control for a record: "Resolver" while open,
 * "✓ dd/MM" plus "Reabrir" once resolved. Presentation only — the consumer
 * owns the state, persistence and authorization.
 */
export function ResolutionStatusCell({
  status,
  resolvedAt,
  resolvedBy,
  onResolve,
  onReopen,
  pending = false,
  disabled = false,
  variant = "cell",
  contextLabel,
  dateFormatter,
  labels: labelsOverride,
  prefix = "ds",
  className,
  classNames: classNamesOverride,
}: ResolutionStatusCellProps) {
  const base = useMemo(() => resolutionStatusCellBemClasses(prefix), [prefix]);
  const classNames = { ...base, ...classNamesOverride };
  const labels = { ...DEFAULT_RESOLUTION_STATUS_CELL_LABELS, ...labelsOverride };

  const [inFlight, setInFlight] = useState(false);
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  const busy = pending || inFlight;
  const full = variant === "full";

  const run = (action: (() => void | Promise<void>) | undefined) => {
    if (!action || busy || disabled) return;
    let result: void | Promise<void>;
    try {
      result = action();
    } catch {
      // A synchronous failure leaves the state unchanged; the consumer reports it.
      return;
    }
    if (result && typeof (result as Promise<void>).then === "function") {
      setInFlight(true);
      (result as Promise<void>).then(
        () => {
          if (mounted.current) setInFlight(false);
        },
        () => {
          if (mounted.current) setInFlight(false);
        },
      );
    }
  };

  const stopRowActivation = (event: MouseEvent<HTMLElement>) => {
    event.stopPropagation();
  };
  const stopRowKeys = (event: KeyboardEvent<HTMLElement>) => {
    if (event.key === "Enter" || event.key === " ") event.stopPropagation();
  };

  const formatDate = (iso: string): string =>
    dateFormatter ? dateFormatter(iso) : formatResolutionDate(iso, full);

  const dateText = resolvedAt ? formatDate(resolvedAt) : "";
  const resolvedOnText = (() => {
    if (resolvedBy) {
      return labels.resolvedOn.replace("{date}", dateText).replace("{user}", resolvedBy);
    }
    return dateText ? `${labels.resolved} — ${dateText}` : labels.resolved;
  })();

  const rootClass = [withBemModifier(classNames.root, variant), className]
    .filter(Boolean)
    .join(" ");

  // The visible text already names the action; the context is only appended
  // while the label is stable (a "Salvando…" button keeps its visible name).
  const actionAriaLabel = (text: string): string | undefined =>
    contextLabel && !busy ? withContext(text, contextLabel) : undefined;

  let body;
  if (status === "not_applicable") {
    body = <span className={classNames.statusText}>{labels.notApplicable}</span>;
  } else if (status === "resolved") {
    body = (
      <>
        <span className={classNames.status} title={resolvedOnText}>
          <span className={classNames.statusIcon} aria-hidden="true">
            ✓
          </span>
          <span className={classNames.srOnly}>{labels.resolved}</span>
          {full ? null : dateText ? <span className={classNames.statusText}>{dateText}</span> : null}
        </span>
        {full ? <span className={classNames.detail}>{resolvedOnText}</span> : null}
        {onReopen ? (
          <span className={classNames.actions}>
            <ActionButton
              variant={full ? "default" : "link"}
              className={classNames.button}
              disabled={disabled || busy}
              aria-label={actionAriaLabel(labels.reopen)}
              onClick={() => run(onReopen)}
            >
              {busy ? labels.sending : labels.reopen}
            </ActionButton>
          </span>
        ) : null}
      </>
    );
  } else {
    body = onResolve ? (
      <span className={classNames.actions}>
        <ActionButton
          variant={full ? "primary" : "default"}
          className={classNames.button}
          disabled={disabled || busy}
          aria-label={actionAriaLabel(full ? labels.markResolved : labels.resolve)}
          onClick={() => run(onResolve)}
        >
          {busy ? labels.sending : full ? labels.markResolved : labels.resolve}
        </ActionButton>
      </span>
    ) : null;
  }

  return (
    <div
      className={rootClass}
      data-status={status}
      data-variant={variant}
      aria-busy={busy || undefined}
      onClick={stopRowActivation}
      onKeyDown={stopRowKeys}
    >
      {body}
    </div>
  );
}

export type DashboardResolutionStatusCellProps = Omit<ResolutionStatusCellProps, "prefix">;

export function createDashboardResolutionStatusCell(config: { prefix: string }) {
  return function DashboardResolutionStatusCell(props: DashboardResolutionStatusCellProps) {
    return <ResolutionStatusCell prefix={config.prefix} {...props} />;
  };
}
