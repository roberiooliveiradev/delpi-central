import { AlertTriangle, Link2, PackageCheck, RefreshCw } from "lucide-react";

import { PpSimpleKpiCard } from "../app/productionPulseUi";
import { PP_HELP } from "../content/helpTooltips";
import type { HubOtaKpis } from "../utils/hubOtaKpis";

type HubOtaKpiStripProps = {
  kpis: HubOtaKpis;
  loading?: boolean;
};

function skeletonCard(key: string) {
  return <div key={key} className="pp-kpi-skeleton" aria-hidden="true" />;
}

export function HubOtaKpiStrip({ kpis, loading }: HubOtaKpiStripProps) {
  if (loading) {
    return (
      <section className="pp-kpi-strip" aria-label="Indicadores OTA">
        {skeletonCard("a")}
        {skeletonCard("b")}
        {skeletonCard("c")}
        {skeletonCard("d")}
      </section>
    );
  }

  return (
    <section className="pp-kpi-strip" aria-label="Indicadores OTA">
      <PpSimpleKpiCard
        title="Firmwares publicados"
        titleHint={PP_HELP.hub.kpiPublished}
        value={String(kpis.publishedFirmwares)}
        icon={<PackageCheck size={20} aria-hidden="true" />}
      />
      <PpSimpleKpiCard
        title="Vinculados"
        titleHint={PP_HELP.hub.kpiLinked}
        value={String(kpis.linkedDevices)}
        subtitle={`${kpis.outdatedDevices} ${PP_HELP.hub.kpiOutdatedSuffix}`}
        icon={<Link2 size={20} aria-hidden="true" />}
        iconTone="success"
      />
      <PpSimpleKpiCard
        title="Em atualização"
        titleHint={PP_HELP.hub.kpiUpdating}
        value={String(kpis.updatingDevices)}
        icon={<RefreshCw size={20} aria-hidden="true" />}
      />
      <PpSimpleKpiCard
        title="Falhas OTA"
        titleHint={PP_HELP.hub.kpiFailed}
        value={String(kpis.failedDevices)}
        icon={<AlertTriangle size={20} aria-hidden="true" />}
        iconTone="warning"
      />
    </section>
  );
}
