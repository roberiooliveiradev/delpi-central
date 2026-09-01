import { Cpu, Link2Off, Wifi, WifiOff } from "lucide-react";

import { PpSimpleKpiCard } from "../app/productionPulseUi";
import { PP_HELP } from "../content/helpTooltips";
import type { DeviceSummary } from "../types/device";

type DeviceKpiStripProps = {
  summary: DeviceSummary | null;
  loading?: boolean;
};

function skeletonCard(key: string) {
  return <div key={key} className="pp-kpi-skeleton" aria-hidden="true" />;
}

export function DeviceKpiStrip({ summary, loading }: DeviceKpiStripProps) {
  if (loading && !summary) {
    return (
      <section className="pp-kpi-strip" aria-label="Indicadores">
        {skeletonCard("a")}
        {skeletonCard("b")}
        {skeletonCard("c")}
        {skeletonCard("d")}
      </section>
    );
  }

  const data = summary ?? { total: 0, online: 0, offline: 0, withoutBinding: 0 };

  return (
    <section className="pp-kpi-strip" aria-label="Indicadores">
      <PpSimpleKpiCard
        title="Total"
        titleHint={PP_HELP.panel.kpiTotal}
        value={String(data.total)}
        icon={<Cpu size={20} aria-hidden="true" />}
      />
      <PpSimpleKpiCard
        title="Online"
        titleHint={PP_HELP.panel.kpiOnline}
        value={String(data.online)}
        icon={<Wifi size={20} aria-hidden="true" />}
        iconTone="success"
      />
      <PpSimpleKpiCard
        title="Offline"
        titleHint={PP_HELP.panel.kpiOffline}
        value={String(data.offline)}
        icon={<WifiOff size={20} aria-hidden="true" />}
        iconTone="warning"
      />
      <PpSimpleKpiCard
        title="Sem amarração"
        titleHint={PP_HELP.panel.kpiWithoutBinding}
        value={String(data.withoutBinding)}
        icon={<Link2Off size={20} aria-hidden="true" />}
      />
    </section>
  );
}
