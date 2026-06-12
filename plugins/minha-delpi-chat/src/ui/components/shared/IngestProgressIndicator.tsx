import {
  ingestProgressFractionLabel,
  ingestProgressPercentLabel,
  resolveIngestProgressPercent,
  type IngestProgressInput,
} from "../../../content/ingestProgress";
import "./IngestProgressIndicator.css";

export type IngestProgressIndicatorProps = IngestProgressInput & {
  /** Rótulo principal (ex.: fase ou status vindo do JSON de domínio). */
  label: string;
  showPercent?: boolean;
  showFraction?: boolean;
  compact?: boolean;
  className?: string;
};

function joinClassNames(...parts: Array<string | false | undefined>): string {
  return parts.filter(Boolean).join(" ");
}

export function IngestProgressIndicator({
  label,
  percent,
  done,
  total,
  showPercent = true,
  showFraction = true,
  compact = false,
  className,
}: IngestProgressIndicatorProps) {
  const resolvedPercent = resolveIngestProgressPercent({ percent, done, total });
  const suffixParts: string[] = [];

  if (showFraction && typeof done === "number" && typeof total === "number" && total > 0) {
    suffixParts.push(ingestProgressFractionLabel(done, total));
  }

  if (showPercent && resolvedPercent != null) {
    suffixParts.push(ingestProgressPercentLabel(resolvedPercent));
  }

  const displayLabel = suffixParts.length > 0 ? `${label} — ${suffixParts.join(" · ")}` : label;

  return (
    <div
      className={joinClassNames(
        "mdc-ingest-progress",
        compact && "mdc-ingest-progress--compact",
        className,
      )}
      role="status"
      aria-live="polite"
      aria-busy="true"
    >
      <p className="mdc-ingest-progress__label">{displayLabel}</p>
      {resolvedPercent != null ? (
        <progress
          className="mdc-ingest-progress__bar"
          max={100}
          value={resolvedPercent}
          aria-valuenow={resolvedPercent}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      ) : (
        <div
          className="mdc-ingest-progress__bar mdc-ingest-progress__bar--indeterminate"
          role="progressbar"
          aria-valuetext={label}
        />
      )}
    </div>
  );
}
