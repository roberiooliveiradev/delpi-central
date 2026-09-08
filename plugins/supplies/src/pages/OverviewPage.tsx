import { useEffect, useMemo, useState } from "react";
import { HelpTooltip } from "@delpi/plugin-ui/index";
import { BarChart3 } from "lucide-react";

import { getOverview, type OverviewKpiCard, type OverviewResponse } from "../api/overview";
import { navigatePluginView } from "../app/pluginNavigation";
import { buildPluginPath } from "../app/pluginRoutes";
import { useSuppliesSession } from "../app/SuppliesSessionContext";
import { SuppliesKpiCard } from "../app/suppliesKpiCard";
import {
  SuppliesEmptyState,
  SuppliesPagePath,
  SuppliesStateBanner,
} from "../app/suppliesUi";
import { SP_HELP } from "../content/helpTooltips";
import {
  firstDayOfMonthIso,
  OVERVIEW_CONTENT,
  temporalNatureLabel,
  todayIso,
} from "../features/overview/overviewContent";

type OverviewPageProps = {
  basePath: string;
};

function formatMeta(meta: number | null, unit: string | null): string | null {
  if (meta == null) return null;
  if (unit === "%") return `${meta.toFixed(1)}%`;
  if (unit === "R$") {
    return `R$ ${meta.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }
  return String(meta);
}

export function OverviewPage({ basePath }: OverviewPageProps) {
  const session = useSuppliesSession();
  const units = session.allowedUnits;
  const [branch, setBranch] = useState<string>("");
  const [from, setFrom] = useState(firstDayOfMonthIso);
  const [to, setTo] = useState(todayIso);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<OverviewResponse | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    getOverview(
      {
        branch: branch || undefined,
        from,
        to,
      },
      controller.signal,
    )
      .then((payload) => setData(payload))
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setData(null);
        setError(err instanceof Error ? err.message : OVERVIEW_CONTENT.error);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [branch, from, to, reloadKey]);

  const kpis = data?.kpis ?? [];
  const availableCount = useMemo(
    () => kpis.filter((kpi) => kpi.status === "available").length,
    [kpis],
  );
  const hasPartial = (data?.partialFailures.length ?? 0) > 0;

  const homeHref = buildPluginPath("home", basePath);

  return (
    <div className="sp-page-stack sp-overview">
      <SuppliesPagePath
        back={{
          label: "Início",
          href: homeHref,
          onNavigate: (event) => {
            event.preventDefault();
            navigatePluginView("home", { basePath });
          },
        }}
        items={[]}
        current={OVERVIEW_CONTENT.title}
      />

      <header className="sp-overview__hero">
        <p className="sp-overview__eyebrow">{OVERVIEW_CONTENT.eyebrow}</p>
        <h1>
          {OVERVIEW_CONTENT.title}{" "}
          <HelpTooltip
            content={SP_HELP.overviewTemporal}
            ariaLabel={OVERVIEW_CONTENT.helpAriaLabel}
          />
        </h1>
        <p className="sp-overview__description">{OVERVIEW_CONTENT.description}</p>
      </header>

      <div className="sp-overview__filters">
        <label>
          <span>{OVERVIEW_CONTENT.branchLabel}</span>
          <select value={branch} onChange={(event) => setBranch(event.target.value)}>
            <option value="">{OVERVIEW_CONTENT.branchAll}</option>
            {units.map((unit) => (
              <option key={unit} value={unit}>
                {unit}
              </option>
            ))}
          </select>
        </label>
        <label>
          <span>{OVERVIEW_CONTENT.periodFromLabel}</span>
          <input type="date" value={from} onChange={(event) => setFrom(event.target.value)} />
        </label>
        <label>
          <span>{OVERVIEW_CONTENT.periodToLabel}</span>
          <input type="date" value={to} onChange={(event) => setTo(event.target.value)} />
        </label>
        <button
          type="button"
          className="sp-home__chip"
          onClick={() => setReloadKey((value) => value + 1)}
        >
          {OVERVIEW_CONTENT.reloadLabel}
        </button>
      </div>

      {loading ? <SuppliesStateBanner>{OVERVIEW_CONTENT.loading}</SuppliesStateBanner> : null}
      {error ? <SuppliesStateBanner variant="error">{error}</SuppliesStateBanner> : null}
      {!loading && !error && hasPartial ? (
        <SuppliesStateBanner>{OVERVIEW_CONTENT.partialNote}</SuppliesStateBanner>
      ) : null}

      {!loading && !error && availableCount === 0 ? (
        <SuppliesEmptyState
          title={OVERVIEW_CONTENT.empty}
          message={OVERVIEW_CONTENT.description}
        />
      ) : null}

      {!loading && !error && kpis.length > 0 ? (
        <ul className="sp-overview__grid">
          {kpis.map((kpi) => (
            <li key={kpi.id}>
              <OverviewKpiItem kpi={kpi} />
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}

function OverviewKpiItem({ kpi }: { kpi: OverviewKpiCard }) {
  const unavailable = kpi.status === "unavailable";
  const nature = temporalNatureLabel(kpi.temporalNature);
  return (
    <SuppliesKpiCard
      title={kpi.title}
      titleHint={kpi.description}
      value={unavailable ? OVERVIEW_CONTENT.unavailable : kpi.displayValue ?? "—"}
      contextLabel={`${nature} · ${kpi.periodLabel}`}
      goalLabel={formatMeta(kpi.meta, kpi.unit)}
      subtitle={unavailable ? OVERVIEW_CONTENT.partialNote : undefined}
      icon={<BarChart3 size={18} strokeWidth={1.75} aria-hidden="true" />}
      className={unavailable ? "sp-overview__kpi--unavailable" : undefined}
    />
  );
}
