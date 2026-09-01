import type { DeviceBinding } from "../../types/device";
import { PP_HELP } from "../../content/helpTooltips";
import { PpSectionCard } from "../../app/productionPulseUi";
import { anchorTypeLabel } from "../../utils/deviceDisplay";

type DeviceBindingCardProps = {
  binding: DeviceBinding | null;
};

export function DeviceBindingCard({ binding }: DeviceBindingCardProps) {
  return (
    <PpSectionCard title="Amarração" hint={PP_HELP.detail.bindingCard}>
      {!binding ? (
        <p className="pp-detail-muted">Nenhuma amarração ativa.</p>
      ) : (
        <dl className="pp-detail-dl">
          <div>
            <dt>Local</dt>
            <dd>{binding.placementLabel || "—"}</dd>
          </div>
          <div>
            <dt>Tipo</dt>
            <dd>{anchorTypeLabel(binding.anchorType)}</dd>
          </div>
          {binding.workCenterCode ? (
            <div>
              <dt>Centro de trabalho</dt>
              <dd>
                {binding.workCenterCode}
                {binding.workCenterName ? ` · ${binding.workCenterName}` : ""}
              </dd>
            </div>
          ) : null}
          <div>
            <dt>Recurso</dt>
            <dd>{binding.resourceCode || "—"}</dd>
          </div>
          <div>
            <dt>Ferramenta</dt>
            <dd>{binding.toolCode || "—"}</dd>
          </div>
          {binding.machineLabel ? (
            <div>
              <dt>Máquina</dt>
              <dd>{binding.machineLabel}</dd>
            </div>
          ) : null}
          {binding.equipmentLabel ? (
            <div>
              <dt>Equipamento</dt>
              <dd>{binding.equipmentLabel}</dd>
            </div>
          ) : null}
          {binding.areaLabel ? (
            <div>
              <dt>Área</dt>
              <dd>{binding.areaLabel}</dd>
            </div>
          ) : null}
          {binding.notes ? (
            <div>
              <dt>Observações</dt>
              <dd>{binding.notes}</dd>
            </div>
          ) : null}
        </dl>
      )}
    </PpSectionCard>
  );
}
