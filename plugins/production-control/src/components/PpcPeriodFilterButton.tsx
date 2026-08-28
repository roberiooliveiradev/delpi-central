import { useEffect, useId, useRef, useState } from "react";
import { AnchoredPanelPortal } from "@delpi/plugin-ui/index";
import { CalendarDays } from "lucide-react";

import { copy } from "../content/copy";

type Props = {
  startDate: string | null;
  endDate: string | null;
  /** Datas exibidas no painel quando a URL não tem filtro (ex.: período da API). */
  defaultStartDate?: string | null;
  defaultEndDate?: string | null;
  onApply: (next: { startDate: string; endDate: string } | null) => void;
};

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;

function isIsoDate(value: string): boolean {
  return ISO_DATE.test(value.trim());
}

/**
 * Gatilho sutil no período do header — abre painel ancorado (não expõe inputs na barra).
 */
export function PpcPeriodFilterButton({
  startDate,
  endDate,
  defaultStartDate,
  defaultEndDate,
  onApply,
}: Props) {
  const [open, setOpen] = useState(false);
  const [draftStart, setDraftStart] = useState("");
  const [draftEnd, setDraftEnd] = useState("");
  const [error, setError] = useState<string | null>(null);
  const rootRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const startId = useId();
  const endId = useId();
  const hasCustom = Boolean(startDate && endDate);

  useEffect(() => {
    if (!open) return;
    setDraftStart(startDate || defaultStartDate || "");
    setDraftEnd(endDate || defaultEndDate || "");
    setError(null);
  }, [open, startDate, endDate, defaultStartDate, defaultEndDate]);

  const apply = () => {
    const from = draftStart.trim();
    const to = draftEnd.trim();
    if (!isIsoDate(from) || !isIsoDate(to)) {
      setError(copy.periodFilter.invalid);
      return;
    }
    if (from > to) {
      setError(copy.periodFilter.inverted);
      return;
    }
    setError(null);
    setOpen(false);
    onApply({ startDate: from, endDate: to });
  };

  const clear = () => {
    setError(null);
    setOpen(false);
    onApply(null);
  };

  return (
    <div
      ref={rootRef}
      className={`ppc-period-filter${open ? " ppc-period-filter--open" : ""}${
        hasCustom ? " ppc-period-filter--active" : ""
      }`}
    >
      <button
        type="button"
        className="ppc-period-filter__trigger"
        aria-label={open ? copy.periodFilter.closeAria : copy.periodFilter.openAria}
        aria-haspopup="dialog"
        aria-expanded={open}
        title={copy.periodFilter.openAria}
        onClick={() => setOpen((current) => !current)}
      >
        <CalendarDays size={14} strokeWidth={1.75} aria-hidden />
      </button>

      <AnchoredPanelPortal
        open={open}
        anchorRef={rootRef}
        panelRef={panelRef}
        className="ppc-period-filter__panel"
        variant="bare"
        role="dialog"
        aria-label={copy.periodFilter.title}
        preferredPlacement="bottom"
        horizontalAlign="start"
        gap={8}
        portalScopeClassName="dashboard-production-control"
        onDismiss={() => setOpen(false)}
      >
        <p className="ppc-period-filter__title">{copy.periodFilter.title}</p>
        <div className="ppc-period-filter__fields">
          <label className="ppc-period-filter__field" htmlFor={startId}>
            <span>{copy.periodFilter.from}</span>
            <input
              id={startId}
              type="date"
              value={draftStart}
              onChange={(event) => setDraftStart(event.target.value)}
            />
          </label>
          <label className="ppc-period-filter__field" htmlFor={endId}>
            <span>{copy.periodFilter.to}</span>
            <input
              id={endId}
              type="date"
              value={draftEnd}
              onChange={(event) => setDraftEnd(event.target.value)}
            />
          </label>
        </div>
        {error ? (
          <p className="ppc-period-filter__error" role="alert">
            {error}
          </p>
        ) : null}
        <div className="ppc-period-filter__actions">
          <button type="button" className="ppc-period-filter__btn ppc-period-filter__btn--ghost" onClick={clear}>
            {copy.periodFilter.reset}
          </button>
          <button type="button" className="ppc-period-filter__btn ppc-period-filter__btn--primary" onClick={apply}>
            {copy.periodFilter.apply}
          </button>
        </div>
      </AnchoredPanelPortal>
    </div>
  );
}
