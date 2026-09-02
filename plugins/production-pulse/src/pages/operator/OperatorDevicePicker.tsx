import { useEffect, useState } from "react";

import { fetchOperatorPlacementDevices } from "../../api/productionPulseApi";
import { PpActionButton, PpStateBox } from "../../app/productionPulseUi";
import { OperatorBrandBar } from "../../components/operator/OperatorBrandBar";
import { OperatorDevicePickCard } from "../../components/operator/OperatorDevicePickCard";
import {
  productionPulseOperatorDevicePath,
  productionPulseOperatorPath,
} from "../../constants/routes";
import type { ProductionPulsePermissionFlags } from "../../constants/permissions";
import { PP_HELP } from "../../content/helpTooltips";
import type { OperatorDeviceItem } from "../../types/operator";
import { navigateOperatorPlacementHub } from "../../utils/operatorNavigation";
import { navigateProductionPulse } from "../../utils/navigation";
import { writeLastPlacementKey } from "../../utils/operatorStorage";

type OperatorDevicePickerProps = {
  placementKey: string;
  branch: string;
  permissions: ProductionPulsePermissionFlags;
};

export function OperatorDevicePicker({
  placementKey,
  branch,
  permissions,
}: OperatorDevicePickerProps) {
  const [devices, setDevices] = useState<OperatorDeviceItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const placementLabel = devices[0]?.placementLabel ?? placementKey;

  useEffect(() => {
    writeLastPlacementKey(placementKey);
    const controller = new AbortController();
    setLoading(true);
    fetchOperatorPlacementDevices(placementKey, branch, { signal: controller.signal })
      .then((items) => {
        setDevices(items);
        setLoading(false);
        if (items.length === 1) {
          navigateProductionPulse(
            productionPulseOperatorDevicePath(items[0].id, branch, placementKey),
          );
        }
      })
      .catch((err) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : "Erro ao carregar devices.");
        setLoading(false);
      });
    return () => controller.abort();
  }, [branch, placementKey]);

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
    return (
      <div className="pp-operator-picker">
        <OperatorBrandBar branch={branch} title="Carregando…" subtitle={PP_HELP.operator.pickerTitle} />
        <PpStateBox variant="loading" title="Carregando devices" message="Aguarde…" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="pp-operator-picker">
        <OperatorBrandBar branch={branch} title={placementLabel} subtitle={PP_HELP.operator.pickerTitle} />
        <PpStateBox variant="error" title="Erro" message={error} />
      </div>
    );
  }

  return (
    <div className="pp-operator-picker">
      <OperatorBrandBar
        branch={branch}
        title={placementLabel}
        subtitle={PP_HELP.operator.pickerTitle}
        trailing={
          <PpActionButton
            variant="ghost"
            className="pp-operator-hero-btn"
            onClick={() => navigateOperatorPlacementHub(branch)}
            title={PP_HELP.operator.changePlacement}
          >
            Trocar posto
          </PpActionButton>
        }
      />

      <div className="pp-operator-picker__grid">
        {devices.map((device) => (
          <OperatorDevicePickCard
            key={device.id}
            device={device}
            onSelect={(item) =>
              navigateProductionPulse(productionPulseOperatorDevicePath(item.id, branch, placementKey))
            }
          />
        ))}
      </div>
    </div>
  );
}
