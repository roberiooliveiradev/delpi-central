import { useEffect, useMemo, useState } from "react";

import { fetchDeviceReadings } from "../../api/productionPulseApi";
import { PpActionButton, PpReadingsAreaChart, PpSectionCard } from "../../app/productionPulseUi";
import type { DeviceListItem } from "../../types/device";
import type { DeviceReading, LivePollResult } from "../../types/detail";
import { PP_HELP } from "../../content/helpTooltips";
import { productionPulseDeviceDetailPath } from "../../constants/routes";
import { navigateProductionPulse } from "../../utils/navigation";
import { isoHoursAgo, primaryMetricKey, readingsToChartPoints } from "../../utils/detailDisplay";
import { DeviceBindingCard } from "./DeviceBindingCard";
import { DeviceChipHealthCard } from "./DeviceChipHealthCard";
import { DeviceMetricHero } from "./DeviceMetricHero";

type DeviceOverviewTabProps = {
  device: DeviceListItem;
  liveSnapshot: LivePollResult | null;
  refreshing: boolean;
  canCommand: boolean;
  onRefreshLive: () => void;
  onPollNow: () => void;
  onReset: () => void;
};

export function DeviceOverviewTab({
  device,
  liveSnapshot,
  refreshing,
  canCommand,
  onRefreshLive,
  onPollNow,
  onReset,
}: DeviceOverviewTabProps) {
  const [miniReadings, setMiniReadings] = useState<DeviceReading[]>([]);
  const metricKey = primaryMetricKey(liveSnapshot?.metrics ?? device.lastMetrics, device.capabilities);

  useEffect(() => {
    const controller = new AbortController();
    fetchDeviceReadings(device.id, {
      page: 1,
      pageSize: 48,
      from: isoHoursAgo(24),
      signal: controller.signal,
    })
      .then((payload) => setMiniReadings(payload.items))
      .catch(() => setMiniReadings([]));
    return () => controller.abort();
  }, [device.id, liveSnapshot?.recordedAt]);

  const deltaPoints = useMemo(
    () => (metricKey ? readingsToChartPoints(miniReadings, metricKey, "delta") : []),
    [metricKey, miniReadings],
  );

  return (
    <div className="pp-detail-overview">
      <div className="pp-detail-overview__top">
        <DeviceMetricHero
          device={device}
          liveSnapshot={liveSnapshot}
          refreshing={refreshing}
          canCommand={canCommand}
          onRefreshLive={onRefreshLive}
          onPollNow={onPollNow}
          onReset={onReset}
        />
        <DeviceBindingCard binding={device.binding} deviceName={device.name} />
      </div>

      <DeviceChipHealthCard
        health={
          liveSnapshot
            ? {
                firmwareVersion: liveSnapshot.firmwareVersion,
                uptimeMs: liveSnapshot.uptimeMs,
                freeHeap: liveSnapshot.freeHeap,
                rssi: liveSnapshot.rssi,
                wifiConnected: liveSnapshot.wifiConnected,
              }
            : null
        }
      />

      <PpSectionCard title="Mini histórico (24h)" hint={PP_HELP.detail.chartDelta}>
        <PpReadingsAreaChart points={deltaPoints} height={240} variant="mini" />
        <div className="pp-detail-overview__link-row">
          <PpActionButton
            variant="ghost"
            onClick={() => navigateProductionPulse(productionPulseDeviceDetailPath(device.id, "history"))}
          >
            Ver histórico completo →
          </PpActionButton>
        </div>
      </PpSectionCard>
    </div>
  );
}
