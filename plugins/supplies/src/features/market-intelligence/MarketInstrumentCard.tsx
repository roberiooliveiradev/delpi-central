/** Selectable market instrument card (PROC-0076 R4, D-04).
 *
 * Local feature component — the kit has no selectable-card primitive
 * (``InteractiveDataCard`` is a navigation card). Semantics: a real
 * ``<button aria-pressed>`` so selection is keyboard/AT operable and
 * announced as a toggle; the check indicator is redundant with text
 * and border state (never color-only).
 *
 * D-04 separation: ``selectable`` reflects catalog presence in the
 * UI; ``dataAccessAllowed`` reflects source display rights. A card
 * stays selectable while its source is pending — selection prepares
 * the view, never authorizes reading protected quotes.
 */

import { Boxes, Check } from "lucide-react";

import { formatMarketUnit } from "./marketUnits";

export type MarketInstrumentCardProps = {
  code: string;
  label: string;
  /** Native quotation unit (code or label — always rendered through
   * ``formatMarketUnit``, never normalized into another unit). */
  unit: string | null;
  /** Short context line (quote basis, latest reference date). */
  context?: string | null;
  selected: boolean;
  /** Catalog UI selectability (instrument exists for selection). */
  selectable: boolean;
  /** Source display rights — false renders the pending-source
   * status without blocking selection (D-04). */
  dataAccessAllowed: boolean;
  /** Short status text when data access is not allowed. */
  pendingLabel: string;
  selectedLabel: string;
  onToggle: (code: string) => void;
};

export function MarketInstrumentCard({
  code,
  label,
  unit,
  context,
  selected,
  selectable,
  dataAccessAllowed,
  pendingLabel,
  selectedLabel,
  onToggle,
}: MarketInstrumentCardProps) {
  const classNames = [
    "sp-market-instrument-card",
    selected ? "sp-market-instrument-card--selected" : "",
    !dataAccessAllowed
      ? "sp-market-instrument-card--pending"
      : "",
  ]
    .filter(Boolean)
    .join(" ");

  const unitLabel = formatMarketUnit(unit);

  return (
    <button
      type="button"
      className={classNames}
      aria-pressed={selected}
      disabled={!selectable}
      data-instrument={code}
      onClick={() => onToggle(code)}
    >
      <span className="sp-market-instrument-card__top">
        <span className="sp-market-instrument-card__heading">
          <span
            className="sp-market-instrument-card__icon"
            aria-hidden="true"
          >
            <Boxes size={16} strokeWidth={1.75} />
          </span>
          <span className="sp-market-instrument-card__label">
            {label}
          </span>
        </span>
        <span
          className="sp-market-instrument-card__check"
          aria-hidden="true"
        >
          {selected ? (
            <Check size={14} strokeWidth={2.5} />
          ) : null}
        </span>
      </span>
      <span className="sp-market-instrument-card__meta">
        {unitLabel ? (
          <span className="sp-market-instrument-card__unit">
            {unitLabel}
          </span>
        ) : null}
        {context ? (
          <span className="sp-market-instrument-card__context">
            {context}
          </span>
        ) : null}
        {!dataAccessAllowed ? (
          <span className="sp-market-instrument-card__pending">
            {pendingLabel}
          </span>
        ) : selected ? (
          <span className="sp-market-instrument-card__selected-text">
            {selectedLabel}
          </span>
        ) : null}
      </span>
    </button>
  );
}
