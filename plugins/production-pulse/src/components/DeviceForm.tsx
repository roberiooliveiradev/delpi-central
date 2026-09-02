import {
  PpActionButton,
  PpFormGrid,
  PpNativeInlineTextField,
  PpNativeSelectField,
  PpNativeSwitchField,
  PpNativeTextAreaField,
  PpNativeTextField,
  ppFieldError,
  ppFieldHint,
} from "../app/productionPulseUi";
import { PP_HELP } from "../content/helpTooltips";
import {
  DEBOUNCE_MS_DEFAULT,
  DEBOUNCE_MS_MAX,
  DEBOUNCE_MS_MIN,
  POLL_INTERVAL_DEFAULT_MS,
  POLL_INTERVAL_MAX_MS,
  POLL_INTERVAL_MIN_MS,
} from "../content/deviceValidationContent";
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

function generateDeviceApiToken(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID().replace(/-/g, "");
  }
  return `tok${Date.now().toString(16)}${Math.random().toString(16).slice(2, 10)}`;
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
      <PpFormGrid className="pp-form-grid--pair">
        <PpNativeTextField
          id="pp-device-name"
          label="Nome do dispositivo"
          hint={PP_HELP.form.name}
          value={device.name}
          placeholder="ESP ventilador setor A"
          onChange={(value) => onChange({ name: value })}
          afterControl={ppFieldError(errors?.name)}
        />

        <PpNativeSelectField
          id="pp-device-branch"
          label="Filial"
          hint={PP_HELP.form.filial}
          value={device.branch}
          disabled={readOnlyBranch}
          options={branchOptions.map((item) => ({
            value: item.id,
            label: `${branchLabel(item.id)} (${item.id})`,
          }))}
          onChange={(value) => onChange({ branch: value })}
          afterControl={ppFieldError(errors?.branch)}
        />

        <PpNativeInlineTextField
          id="pp-device-ip"
          label="Endereço IP"
          hint={PP_HELP.form.ip}
          span
          className="pp-form-grid__span-full pp-field--ip-row"
          value={device.ipAddress}
          placeholder="192.168.20.2"
          onChange={(value) => onChange({ ipAddress: value })}
          afterControl={ppFieldError(errors?.ipAddress)}
          trailing={
            onTestConnection ? (
              <PpActionButton
                variant="ghost"
                className="pp-test-connection-btn"
                disabled={testingConnection || !device.ipAddress.trim()}
                onClick={onTestConnection}
              >
                {testingConnection ? PP_HELP.form.testConnectionLoading : PP_HELP.form.testConnectionAction}
              </PpActionButton>
            ) : null
          }
        />

        <PpNativeTextField
          id="pp-device-controller-code"
          label="Código do controlador"
          hint={PP_HELP.form.controllerCode}
          value={device.controllerCode}
          placeholder="ESP-00A1B2C3"
          onChange={(value) => onChange({ controllerCode: value })}
          afterControl={ppFieldError(errors?.controllerCode)}
        />

        <PpNativeTextField
          id="pp-device-wifi-ssid"
          label="SSID Wi-Fi"
          hint={PP_HELP.form.wifiSsid}
          value={device.wifiSsid}
          placeholder="Rede da planta"
          onChange={(value) => onChange({ wifiSsid: value })}
          afterControl={ppFieldError(errors?.wifiSsid)}
        />

        <PpNativeTextField
          id="pp-device-wifi-password"
          label="Senha Wi-Fi"
          hint={PP_HELP.form.wifiPassword}
          type="password"
          value={device.wifiPassword}
          placeholder="Deixe em branco para manter"
          onChange={(value) => onChange({ wifiPassword: value })}
          afterControl={ppFieldError(errors?.wifiPassword)}
        />

        <PpNativeTextField
          id="pp-device-debounce"
          label="Debounce (ms)"
          hint={PP_HELP.form.debounceMs}
          type="number"
          min={DEBOUNCE_MS_MIN}
          max={DEBOUNCE_MS_MAX}
          step={1}
          inputMode="numeric"
          value={device.debounceMs}
          placeholder={String(DEBOUNCE_MS_DEFAULT)}
          onChange={(value) => onChange({ debounceMs: value })}
          afterControl={ppFieldError(errors?.debounceMs)}
        />

        <PpNativeInlineTextField
          id="pp-device-api-token"
          label="Token do dispositivo"
          hint={
            device.apiTokenSet && !device.apiToken.trim()
              ? PP_HELP.form.apiTokenSetHint
              : PP_HELP.form.apiToken
          }
          span
          className="pp-form-grid__span-full"
          type="password"
          value={device.apiToken}
          placeholder="Deixe em branco para manter"
          onChange={(value) => onChange({ apiToken: value })}
          afterControl={ppFieldError(errors?.apiToken)}
          trailing={
            <PpActionButton
              variant="ghost"
              type="button"
              onClick={() => onChange({ apiToken: generateDeviceApiToken() })}
            >
              {PP_HELP.form.generateApiTokenAction}
            </PpActionButton>
          }
        />

        <PpNativeTextAreaField
          id="pp-device-firmware-source"
          label="Código .ino"
          hint={PP_HELP.form.firmwareSource}
          className="pp-firmware-source-field"
          controlClassName="pp-firmware-source-field__control"
          rows={14}
          value={device.firmwareSource}
          placeholder="// Cole o sketch Arduino completo deste dispositivo"
          onChange={(value) => onChange({ firmwareSource: value })}
          afterControl={ppFieldError(errors?.firmwareSource)}
        />

        <PpNativeSelectField
          id="pp-device-driver"
          label="Driver"
          hint={PP_HELP.form.driver}
          span
          value={device.driverKey}
          options={drivers.map((driver) => ({
            value: driver.key,
            label: driver.labelPt,
          }))}
          onChange={(value) => onChange({ driverKey: value })}
          afterControl={
            <>
              {ppFieldHint(PP_HELP.form.driverPreview)}
              <span className="pp-driver-preview">Preview: {driverPreview(selectedDriver)}</span>
              {ppFieldError(errors?.driverKey)}
            </>
          }
        />

        <PpNativeTextField
          id="pp-device-poll-interval"
          label="Intervalo poll (ms)"
          hint={PP_HELP.form.pollInterval}
          type="number"
          min={POLL_INTERVAL_MIN_MS}
          max={POLL_INTERVAL_MAX_MS}
          step={1}
          inputMode="numeric"
          value={String(device.pollIntervalMs)}
          onChange={(value) =>
            onChange({
              pollIntervalMs: Number.parseInt(value, 10) || POLL_INTERVAL_DEFAULT_MS,
            })
          }
          afterControl={ppFieldError(errors?.pollIntervalMs)}
        />

        <PpNativeSwitchField
          id="pp-device-enabled"
          label="Dispositivo ativo"
          hint={PP_HELP.form.enabled}
          checked={device.enabled}
          onChange={(checked) => onChange({ enabled: checked })}
        />
      </PpFormGrid>
    </div>
  );
}
