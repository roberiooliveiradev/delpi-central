import { useEffect, useState } from "react";

import { fetchOperatorDevice } from "../../api/productionPulseApi";
import { PpStateBox } from "../../app/productionPulseUi";
import { CounterPadSurface } from "../../components/operator/CounterPadSurface";
import { GaugeReadoutSurface } from "../../components/operator/GaugeReadoutSurface";
import type { ProductionPulsePermissionFlags } from "../../constants/permissions";
import type { OperatorDeviceItem } from "../../types/operator";
import { resolveOperatorSurface } from "../../utils/operatorDisplay";

type OperatorDeviceSurfacePageProps = {
  deviceId: string;
  branch: string;
  placementKey?: string;
  permissions: ProductionPulsePermissionFlags;
};

export function OperatorDeviceSurfacePage({
  deviceId,
  branch,
  placementKey,
  permissions,
}: OperatorDeviceSurfacePageProps) {
  const [device, setDevice] = useState<OperatorDeviceItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    fetchOperatorDevice(deviceId)
      .then((row) => {
        setDevice(row);
        setLoading(false);
      })
      .catch((err) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : "Erro ao carregar device.");
        setLoading(false);
      });
    return () => controller.abort();
  }, [deviceId]);

  if (!permissions.canOperator) {
    return (
      <PpStateBox
        variant="error"
        title="Sem permissão"
        message="Você não tem permissão para o modo operador."
      />
    );
  }

  if (loading) {
    return <PpStateBox variant="loading" title="Carregando superfície" message="Aguarde…" />;
  }

  if (error || !device) {
    return (
      <PpStateBox
        variant="error"
        title="Device indisponível"
        message={error ?? "Dispositivo não encontrado."}
      />
    );
  }

  const surface = resolveOperatorSurface(device);
  const placementLabel = device.placementLabel ?? placementKey;

  if (surface === "counter_pad") {
    return (
      <CounterPadSurface
        deviceId={deviceId}
        branch={branch}
        placementKey={placementKey ?? device.placementKey}
        placementLabel={placementLabel}
        initialDevice={device}
      />
    );
  }

  return (
    <GaugeReadoutSurface
      deviceId={deviceId}
      branch={branch}
      placementKey={placementKey ?? device.placementKey}
      placementLabel={placementLabel}
      initialDevice={device}
    />
  );
}
