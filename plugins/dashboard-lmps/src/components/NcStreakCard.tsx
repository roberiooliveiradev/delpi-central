import { ShieldCheck } from "lucide-react";

import { KpiCard } from "./KpiCard";
import type { LmpNonconformityStreak } from "../types/lmpNonconformity";
import { LMPS_HELP_TOOLTIPS } from "../content/helpTooltips";
import { LMPS_ROUTES } from "../constants/routes";
import { GHOST_BTN } from "../ui/ghostChrome";
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
    <KpiCard
      title="Dias sem NC"
      titleHint={LMPS_HELP_TOOLTIPS.kpis.ncStreak}
      value={error ? "—" : `${formatDays(current)} dias`}
      subtitle={
        error
          ? error
          : `Sem NC em LMP's · Recorde: ${record.toLocaleString("pt-BR")} dias`
      }
      icon={<ShieldCheck size={22} />}
      loading={Boolean(loading) && !error}
      footer={
        <div className="delpi-ui-kpi-footer">
          <button
            type="button"
            className={GHOST_BTN}
            onClick={() => navigateLmps(LMPS_ROUTES.nonconformities)}
          >
            Ver NCs
          </button>
        </div>
      }
    />
  );
}
