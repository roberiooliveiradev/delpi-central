import { NativeSwitchControl } from "@delpi/plugin-ui/index";

import {
  PpActionButton,
  PpFieldLabel,
  PpFormGrid,
} from "../app/productionPulseUi";
import { PP_HELP } from "../content/helpTooltips";
import { getPpSectionIntro } from "../content/sectionIntros";
import type { DeviceFormValues, DriverCatalogItem } from "../types/form";
import { branchLabel, resolveBranchOptions } from "../constants/branches";

type DeviceFormProps = {
  device: DeviceFormValues;
  drivers: DriverCatalogItem[];
  allowedBranches: string[];
  readOnlyBranch?: boolean;
  errors?: Partial<Record<keyof DeviceFormValues, string>>;
  onChange: (patch: Partial<DeviceFormValues>) => void;
  onTestConnection?: () => void;
  testingConnection?: boolean;
};

function driverPreview(driver: DriverCatalogItem | undefined): string {
  if (!driver?.metrics?.length) return "—";
  return driver.metrics
    .map((metric) => metric.labelPt ?? metric.key)
    .slice(0, 3)
    .join(" · ");
}

export function DeviceForm({
  device,
  drivers,
  allowedBranches,
  readOnlyBranch,
  errors,
  onChange,
  onTestConnection,
  testingConnection,
}: DeviceFormProps) {
  const branchOptions = resolveBranchOptions(allowedBranches);
  const selectedDriver = drivers.find((item) => item.key === device.driverKey);

  return (
    <div className="pp-device-form">
      <p className="pp-section-intro">{getPpSectionIntro("form.device")}</p>
      <PpFormGrid className="pp-form-grid--single">
        <label className="pp-field">
          <PpFieldLabel label="Nome do dispositivo" hint={PP_HELP.form.name} />
          <input
            value={device.name}
            onChange={(event) => onChange({ name: event.target.value })}
            placeholder="ESP ventilador setor A"
          />
          {errors?.name ? <span className="pp-field-error">{errors.name}</span> : null}
        </label>

        <label className="pp-field">
          <PpFieldLabel label="Filial" hint={PP_HELP.form.filial} />
          <select
            value={device.branch}
            disabled={readOnlyBranch}
            onChange={(event) => onChange({ branch: event.target.value })}
          >
            {branchOptions.map((item) => (
              <option key={item.id} value={item.id}>
                {branchLabel(item.id)} ({item.id})
              </option>
            ))}
          </select>
          {errors?.branch ? <span className="pp-field-error">{errors.branch}</span> : null}
        </label>

        <div className="pp-field pp-field--ip-row">
          <label className="pp-field">
            <PpFieldLabel label="Endereço IP" hint={PP_HELP.form.ip} />
            <input
              value={device.ipAddress}
              onChange={(event) => onChange({ ipAddress: event.target.value })}
              placeholder="192.168.20.2"
            />
            {errors?.ipAddress ? <span className="pp-field-error">{errors.ipAddress}</span> : null}
          </label>
          {onTestConnection ? (
            <PpActionButton
              variant="ghost"
              className="pp-test-connection-btn"
              disabled={testingConnection || !device.ipAddress.trim()}
              onClick={onTestConnection}
            >
              {testingConnection ? "Testando…" : "Testar conexão"}
            </PpActionButton>
          ) : null}
        </div>

        <label className="pp-field">
          <PpFieldLabel label="Driver" hint={PP_HELP.form.driver} />
          <select
            value={device.driverKey}
            onChange={(event) => onChange({ driverKey: event.target.value })}
          >
            {drivers.map((driver) => (
              <option key={driver.key} value={driver.key}>
                {driver.labelPt}
              </option>
            ))}
          </select>
          <span className="pp-field-hint">{PP_HELP.form.driverPreview}</span>
          <span className="pp-driver-preview">Preview: {driverPreview(selectedDriver)}</span>
          {errors?.driverKey ? <span className="pp-field-error">{errors.driverKey}</span> : null}
        </label>

        <label className="pp-field">
          <PpFieldLabel label="Intervalo poll (s)" hint={PP_HELP.form.pollInterval} />
          <input
            type="number"
            min={5}
            max={300}
            value={device.pollIntervalSeconds}
            onChange={(event) =>
              onChange({ pollIntervalSeconds: Number.parseInt(event.target.value, 10) || 30 })
            }
          />
          {errors?.pollIntervalSeconds ? (
            <span className="pp-field-error">{errors.pollIntervalSeconds}</span>
          ) : null}
        </label>

        <label className="pp-field pp-field--switch">
          <PpFieldLabel label="Dispositivo ativo" hint={PP_HELP.form.enabled} />
          <NativeSwitchControl
            checked={device.enabled}
            aria-label="Dispositivo ativo"
            onChange={(checked) => onChange({ enabled: checked })}
          />
        </label>
      </PpFormGrid>
    </div>
  );
}
