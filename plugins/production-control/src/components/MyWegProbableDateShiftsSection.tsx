import { HelpTooltip } from "@delpi/plugin-ui/index";
import { CalendarArrowDown, CalendarArrowUp, CalendarRange } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { copy } from "../content/copy";
import { helpTooltips } from "../content/helpTooltips";
import type { MyWegProbableDateShift } from "../types";
import { formatDecimalString } from "../utils/formatDecimalString";
import {
  calendarDaysBetween,
  countProbableShiftKinds,
  filterProbableDateShifts,
  formatProductKeyForDisplay,
  normalizeProbableDateShifts,
  sortProbableDateShiftsByNearestRemessa,
  type MyWegProbableShiftFilter,
} from "../utils/mywegProbableDateShifts";

type Props = {
  shifts: MyWegProbableDateShift[] | undefined | null;
  /** Muda com o par de coletas / payload para resetar filtro e paginação local. */
  resetKey: string;
};

const texts = copy.mywegNeeds.evolution.probableShifts;
const INITIAL_VISIBLE = 10;

function formatRemessaBr(value: string | null | undefined): string {
  const text = (value ?? "").trim();
  if (!text) return "—";
  if (/^\d{4}-\d{2}-\d{2}/.test(text)) {
    const [y, m, d] = text.slice(0, 10).split("-");
    return `${d}/${m}/${y}`;
  }
  return text;
}

function kindLabel(kind: string): string {
  switch (kind) {
    case "possible_advancement":
      return texts.kindAdvancement;
    case "possible_postponement":
      return texts.kindPostponement;
    case "same_date_redistribution":
      return texts.kindSameDate;
    default:
      return texts.kindUnknown;
  }
}

function kindClass(kind: string): string {
  switch (kind) {
    case "possible_advancement":
      return "ppc-myweg-needs__shift-kind ppc-myweg-needs__shift-kind--advance";
    case "possible_postponement":
      return "ppc-myweg-needs__shift-kind ppc-myweg-needs__shift-kind--postpone";
    default:
      return "ppc-myweg-needs__shift-kind";
  }
}

function KindIcon({ kind }: { kind: string }) {
  if (kind === "possible_advancement") {
    return <CalendarArrowDown size={14} strokeWidth={1.9} aria-hidden />;
  }
  if (kind === "possible_postponement") {
    return <CalendarArrowUp size={14} strokeWidth={1.9} aria-hidden />;
  }
  return <CalendarRange size={14} strokeWidth={1.9} aria-hidden />;
}

function deltaDaysLabel(fromRemessa: string, toRemessa: string): string {
  const days = calendarDaysBetween(fromRemessa, toRemessa);
  if (days == null) return texts.daysUnknown;
  if (days === 0) return texts.daysSame;
  if (days < 0) return texts.daysBefore(Math.abs(days));
  return texts.daysAfter(days);
}

export function MyWegProbableDateShiftsSection({ shifts, resetKey }: Props) {
  const [filter, setFilter] = useState<MyWegProbableShiftFilter>("all");
  const [visibleCount, setVisibleCount] = useState(INITIAL_VISIBLE);

  useEffect(() => {
    setFilter("all");
    setVisibleCount(INITIAL_VISIBLE);
  }, [resetKey]);

  const normalized = useMemo(() => normalizeProbableDateShifts(shifts), [shifts]);
  const counts = useMemo(() => countProbableShiftKinds(normalized), [normalized]);
  const filtered = useMemo(() => {
    return sortProbableDateShiftsByNearestRemessa(
      filterProbableDateShifts(normalized, filter),
    );
  }, [normalized, filter]);

  const visible = filtered.slice(0, visibleCount);
  const hasMore = filtered.length > visibleCount;

  return (
    <section className="ppc-myweg-needs__shifts" aria-label={texts.aria}>
      <header className="ppc-myweg-needs__shifts-header">
        <h3 className="ppc-myweg-needs__shifts-title">
          {texts.title}
          <HelpTooltip content={helpTooltips.mywegNeedsProbableShifts} trigger="icon" />
        </h3>
        <p className="ppc-myweg-needs__shifts-scope">{texts.scopeNote}</p>
        <p className="ppc-myweg-needs__shifts-note">{texts.notAdditive}</p>
      </header>

      <div className="ppc-myweg-needs__shifts-summary" aria-label={texts.title}>
        <article className="ppc-myweg-needs__kpi ppc-myweg-needs__kpi--shift">
          <h3>
            {texts.advancements}
            <HelpTooltip content={helpTooltips.mywegNeedsProbableAdvancement} trigger="icon" />
          </h3>
          <p>{counts.advancements}</p>
        </article>
        <article className="ppc-myweg-needs__kpi ppc-myweg-needs__kpi--shift">
          <h3>
            {texts.postponements}
            <HelpTooltip content={helpTooltips.mywegNeedsProbablePostponement} trigger="icon" />
          </h3>
          <p>{counts.postponements}</p>
        </article>
        <article className="ppc-myweg-needs__kpi ppc-myweg-needs__kpi--shift">
          <h3>
            {texts.total}
            <HelpTooltip content={helpTooltips.mywegNeedsProbableTotal} trigger="icon" />
          </h3>
          <p>{counts.total}</p>
        </article>
      </div>

      {normalized.length === 0 ? (
        <p className="ppc-myweg-needs__evolution-note" role="status">
          {texts.empty}
        </p>
      ) : (
        <>
          <div
            className="ppc-myweg-needs__shifts-filters"
            role="group"
            aria-label={texts.filterAria}
          >
            {(
              [
                ["all", texts.filterAll],
                ["advancement", texts.filterAdvancement],
                ["postponement", texts.filterPostponement],
              ] as const
            ).map(([value, label]) => (
              <button
                key={value}
                type="button"
                className={
                  filter === value
                    ? "ppc-btn ppc-btn--secondary ppc-myweg-needs__shifts-filter--active"
                    : "ppc-btn ppc-btn--secondary"
                }
                aria-pressed={filter === value}
                onClick={() => {
                  setFilter(value);
                  setVisibleCount(INITIAL_VISIBLE);
                }}
              >
                {label}
              </button>
            ))}
            <span className="ppc-myweg-needs__shifts-filtered" role="status">
              {texts.filteredCount(filtered.length, normalized.length)}
            </span>
          </div>

          {filtered.length === 0 ? (
            <p className="ppc-myweg-needs__evolution-note" role="status">
              {texts.empty}
            </p>
          ) : (
            <div className="ppc-myweg-needs__shifts-table-wrap">
              <table className="ppc-myweg-needs__shifts-table">
                <thead>
                  <tr>
                    <th scope="col">{texts.columns.product}</th>
                    <th scope="col">{texts.columns.kind}</th>
                    <th scope="col">{texts.columns.from}</th>
                    <th scope="col">{texts.columns.to}</th>
                    <th scope="col">{texts.columns.quantity}</th>
                    <th scope="col">{texts.columns.deltaDays}</th>
                  </tr>
                </thead>
                <tbody>
                  {visible.map((shift, index) => {
                    const product = formatProductKeyForDisplay(shift.productKey);
                    const qty = formatDecimalString(shift.quantityUn);
                    return (
                      <tr
                        key={`${shift.productKey}|${shift.fromRemessa}|${shift.toRemessa}|${shift.kind}|${shift.quantityUn}|${index}`}
                      >
                        <td>
                          <span className="ppc-myweg-needs__shifts-product">{product.label}</span>
                          {!product.confirmed ? (
                            <span className="ppc-myweg-needs__shifts-identity">
                              {texts.identityUnconfirmed}
                            </span>
                          ) : null}
                        </td>
                        <td>
                          <span className={kindClass(shift.kind)}>
                            <KindIcon kind={shift.kind} />
                            {kindLabel(shift.kind)}
                          </span>
                        </td>
                        <td>{formatRemessaBr(shift.fromRemessa)}</td>
                        <td>{formatRemessaBr(shift.toRemessa)}</td>
                        <td>{texts.quantityUn(qty)}</td>
                        <td>{deltaDaysLabel(shift.fromRemessa, shift.toRemessa)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {hasMore || visibleCount > INITIAL_VISIBLE ? (
            <div className="ppc-myweg-needs__shifts-more">
              {hasMore ? (
                <button
                  type="button"
                  className="ppc-btn ppc-btn--secondary"
                  onClick={() => setVisibleCount((current) => current + INITIAL_VISIBLE)}
                >
                  {texts.showMore}
                </button>
              ) : null}
              {visibleCount > INITIAL_VISIBLE ? (
                <button
                  type="button"
                  className="ppc-btn ppc-btn--secondary"
                  onClick={() => setVisibleCount(INITIAL_VISIBLE)}
                >
                  {texts.showLess}
                </button>
              ) : null}
            </div>
          ) : null}
        </>
      )}
    </section>
  );
}
