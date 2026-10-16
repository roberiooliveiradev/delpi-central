import { useId, useState } from "react";
import type { ReactNode } from "react";
import { AlertTriangle, ChevronDown } from "lucide-react";

/**
 * EvidenceDetails — compact, subordinate provenance/evidence surface for
 * a conversational answer: visible source summary + a labelled disclosure
 * revealing semantic label/value items and optional limitations.
 *
 * Render-only: every value arrives already user-facing from the consumer.
 * It never interprets epistemic class, never infers confidence, materiality,
 * freshness or authorization, and carries no provider/backend knowledge.
 *
 * CSS: `styles/evidence-details.css` (`.delpi-ui-evidence-details*`).
 */

export type EvidenceDetailItem = {
  label: string;
  value: ReactNode;
  /** Span the full row width instead of the two-column grid. */
  wide?: boolean;
};

export type EvidenceDetailsProps = {
  /** Always-visible provenance line, e.g. "Fonte · Cadastro DELPI ·
   *  consultado em …". Absent → no summary line rendered. */
  sourceSummary?: ReactNode;
  /** Semantic label/value pairs inside the disclosure. */
  items?: readonly EvidenceDetailItem[];
  /** Verbatim limitation content supplied by the consumer. */
  limitations?: readonly ReactNode[];
  /** Heading above the limitations list. */
  limitationsLabel?: string;
  /** Rendered only when the consumer supplies an explicit materiality
   *  signal — the component never infers it from `limitations`. */
  materialLimitationLabel?: ReactNode;
  /** Disclosure button text. */
  disclosureLabel?: string;
  defaultExpanded?: boolean;
  className?: string;
};

export function EvidenceDetails({
  sourceSummary,
  items,
  limitations,
  limitationsLabel = "Limitações",
  materialLimitationLabel,
  disclosureLabel = "Detalhes da evidência",
  defaultExpanded,
  className,
}: EvidenceDetailsProps) {
  const regionId = useId();
  const [expanded, setExpanded] = useState(Boolean(defaultExpanded));

  const hasDetails =
    (items?.length ?? 0) > 0 || (limitations?.length ?? 0) > 0;

  return (
    <div
      className={`delpi-ui-evidence-details${className ? ` ${className}` : ""}`}
    >
      {sourceSummary ? (
        <p className="delpi-ui-evidence-details__source">{sourceSummary}</p>
      ) : null}

      {materialLimitationLabel ? (
        <p className="delpi-ui-evidence-details__material">
          <AlertTriangle size={13} aria-hidden="true" />
          <span>{materialLimitationLabel}</span>
        </p>
      ) : null}

      {hasDetails ? (
        <>
          <button
            type="button"
            className="delpi-ui-evidence-details__disclosure"
            aria-expanded={expanded}
            aria-controls={regionId}
            onClick={() => setExpanded((previous) => !previous)}
          >
            <span>{disclosureLabel}</span>
            <ChevronDown
              size={13}
              className="delpi-ui-evidence-details__chevron"
              aria-hidden="true"
            />
          </button>
          <div
            id={regionId}
            className="delpi-ui-evidence-details__detail"
            hidden={!expanded}
          >
            {items && items.length > 0 ? (
              <dl className="delpi-ui-evidence-details__grid">
                {items.map((item) => (
                  <div
                    key={item.label}
                    className={`delpi-ui-evidence-details__item${
                      item.wide
                        ? " delpi-ui-evidence-details__item--wide"
                        : ""
                    }`}
                  >
                    <dt className="delpi-ui-evidence-details__item-label">
                      {item.label}
                    </dt>
                    <dd className="delpi-ui-evidence-details__item-value">
                      {item.value}
                    </dd>
                  </div>
                ))}
              </dl>
            ) : null}

            {limitations && limitations.length > 0 ? (
              <div className="delpi-ui-evidence-details__limitations">
                <span className="delpi-ui-evidence-details__limitations-label">
                  {limitationsLabel}
                </span>
                <ul className="delpi-ui-evidence-details__limitations-list">
                  {limitations.map((limitation, index) => (
                    <li key={index}>{limitation}</li>
                  ))}
                </ul>
              </div>
            ) : null}
          </div>
        </>
      ) : null}
    </div>
  );
}
