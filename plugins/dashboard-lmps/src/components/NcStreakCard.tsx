import { HelpTooltip } from "@delpi/plugin-ui/index";
import { ShieldCheck } from "lucide-react";

import type { LmpNonconformityStreak } from "../types/lmpNonconformity";
import { LMPS_HELP_TOOLTIPS } from "../content/helpTooltips";
import { LMPS_ROUTES } from "../constants/routes";
import { navigateLmps } from "../utils/navigation";

function formatDays(value: number): string {
  return String(Math.max(0, Math.trunc(value))).padStart(2, "0");
}

type NcStreakCardProps = {
  streak: LmpNonconformityStreak | null;
  loading?: boolean;
  error?: string | null;
};

export function NcStreakCard({ streak, loading, error }: NcStreakCardProps) {
  const current = streak?.current_days_without_nc ?? 0;
  const record = streak?.record_days_without_nc ?? 0;

  return (
    <section
      className={`lmps-nc-streak${loading ? " lmps-nc-streak--loading" : ""}`}
      aria-busy={loading || undefined}
      aria-label="Dias sem não conformidade em LMPs"
    >
      <div className="lmps-nc-streak__icon" aria-hidden>
        <ShieldCheck size={28} />
      </div>
      <div className="lmps-nc-streak__body">
        <p className="lmps-nc-streak__eyebrow">
          Estamos há:
          <HelpTooltip
            content={LMPS_HELP_TOOLTIPS.kpis.ncStreak}
            ariaLabel="Ajuda: dias sem NC em LMPs"
          />
        </p>
        {error ? (
          <p className="lmps-nc-streak__error">{error}</p>
        ) : (
          <>
            <p className="lmps-nc-streak__current">
              <span className="lmps-nc-streak__days">{formatDays(current)}</span>
              <span className="lmps-nc-streak__unit">dias</span>
            </p>
            <p className="lmps-nc-streak__label">Sem NC em LMP&apos;s</p>
            <p className="lmps-nc-streak__record">
              Nosso recorde é{" "}
              <strong>{record.toLocaleString("pt-BR")} dias</strong>
            </p>
          </>
        )}
      </div>
      <button
        type="button"
        className="lmps-ghost-btn lmps-nc-streak__link"
        onClick={() => navigateLmps(LMPS_ROUTES.nonconformities)}
      >
        Ver NCs
      </button>
    </section>
  );
}
