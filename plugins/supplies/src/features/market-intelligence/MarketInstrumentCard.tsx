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

import { Check } from "lucide-react";

import { SuppliesStatusBadge } from "../../app/suppliesUi";

export type MarketInstrumentCardProps = {
  code: string;
  label: string;
  /** Native quotation unit (e.g. ``US$/t``) — rendered verbatim,
   * never normalized into another unit. */
  unit: string | null;
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
        <span className="sp-market-instrument-card__label">{label}</span>
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
        {unit ? (
          <span className="sp-market-instrument-card__unit">{unit}</span>
        ) : null}
        {!dataAccessAllowed ? (
          <SuppliesStatusBadge label={pendingLabel} variant="neutral" />
        ) : selected ? (
          <span className="sp-market-instrument-card__selected-text">
            {selectedLabel}
          </span>
        ) : null}
      </span>
    </button>
  );
}
