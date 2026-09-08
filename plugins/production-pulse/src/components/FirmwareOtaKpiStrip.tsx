import { AlertTriangle, CheckCircle2, Cpu, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";

import {
  fetchFirmwareUpdateSummary,
  type FirmwareUpdateSummary,
} from "../api/productionPulseApi";
import { PpSimpleKpiCard } from "../app/productionPulseUi";
import { PP_HELP } from "../content/helpTooltips";

type FirmwareOtaKpiStripProps = {
  branch: string;
  enabled?: boolean;
};

export function FirmwareOtaKpiStrip({ branch, enabled = true }: FirmwareOtaKpiStripProps) {
  const [summary, setSummary] = useState<FirmwareUpdateSummary | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!enabled || !branch) {
      setSummary(null);
      return;
    }
    const controller = new AbortController();
    setLoading(true);
    void fetchFirmwareUpdateSummary(branch)
      .then((data) => {
        if (!controller.signal.aborted) setSummary(data);
      })
      .catch(() => {
        if (!controller.signal.aborted) setSummary(null);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [branch, enabled]);

  if (!enabled) return null;

  if (loading && !summary) {
    return (
      <section className="pp-kpi-strip" aria-label="Indicadores OTA">
        <div className="pp-kpi-skeleton" aria-hidden="true" />
        <div className="pp-kpi-skeleton" aria-hidden="true" />
        <div className="pp-kpi-skeleton" aria-hidden="true" />
        <div className="pp-kpi-skeleton" aria-hidden="true" />
      </section>
    );
  }

  const data = summary ?? { total: 0, updated: 0, updating: 0, failed: 0 };

  return (
    <section className="pp-kpi-strip" aria-label="Indicadores OTA" title={PP_HELP.ota.openJobs}>
      <PpSimpleKpiCard
        title="Frota OTA"
        titleHint={PP_HELP.ota.openCatalog}
        value={String(data.total)}
        icon={<Cpu size={20} aria-hidden="true" />}
      />
      <PpSimpleKpiCard
        title="Atualizados"
        titleHint={PP_HELP.ota.deviceVersionCard}
        value={String(data.updated)}
        icon={<CheckCircle2 size={20} aria-hidden="true" />}
        iconTone="success"
      />
      <PpSimpleKpiCard
        title="Em update"
        titleHint={PP_HELP.ota.jobsHero}
        value={String(data.updating)}
        icon={<RefreshCw size={20} aria-hidden="true" />}
      />
      <PpSimpleKpiCard
        title="Falhas OTA"
        titleHint={PP_HELP.ota.deviceJobFailed}
        value={String(data.failed)}
        icon={<AlertTriangle size={20} aria-hidden="true" />}
        iconTone="warning"
      />
    </section>
  );
}
