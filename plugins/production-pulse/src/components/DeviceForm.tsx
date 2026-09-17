import { useEffect, useMemo, useState } from "react";
import {
  Check,
  Clipboard,
  Eye,
  EyeOff,
  KeyRound,
  Loader2,
  Wifi,
} from "lucide-react";

import {
  PpFormGrid,
  PpHintAction,
  PpIconButton,
  PpNativeInlineTextField,
  PpNativeSelectField,
  PpNativeSwitchField,
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
import {
  canCopyDeviceApiToken,
  canRevealDeviceApiToken,
  generateDeviceApiToken,
  resolveDeviceApiTokenFieldStatus,
} from "../utils/deviceApiToken";

type DeviceFormProps = {
  device: DeviceFormValues;
  drivers: DriverCatalogItem[];
  allowedBranches: string[];
  readOnlyBranch?: boolean;
  /** Loaded controller/IP for edit — detects hardware re-provision. */
  identityBaseline?: { controllerCode: string; ipAddress: string } | null;
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

function tokenStatusLabel(
  status: ReturnType<typeof resolveDeviceApiTokenFieldStatus>,
): string {
  if (status === "configured") return PP_HELP.form.apiTokenStatusConfigured;
  if (status === "missing") return PP_HELP.form.apiTokenStatusMissing;
  return PP_HELP.form.apiTokenStatusPendingSave;
}

function tokenFieldHint(
  status: ReturnType<typeof resolveDeviceApiTokenFieldStatus>,
): string {
  if (status === "configured") return PP_HELP.form.apiTokenSetHint;
  if (status === "missing") return PP_HELP.form.apiTokenMissingHint;
  if (status === "pending_save") return PP_HELP.form.apiTokenPendingSaveHint;
  return PP_HELP.form.apiToken;
}

export function DeviceForm({
  device,
  drivers,
  allowedBranches,
  readOnlyBranch,
  identityBaseline,
  errors,
  onChange,
  onTestConnection,
  testingConnection,
}: DeviceFormProps) {
  const branchOptions = resolveBranchOptions(allowedBranches);
  const selectedDriver = drivers.find((item) => item.key === device.driverKey);
  const [tokenVisible, setTokenVisible] = useState(false);
  const [copyState, setCopyState] = useState<"idle" | "copied" | "failed">("idle");

  const tokenStatus = resolveDeviceApiTokenFieldStatus({
    apiToken: device.apiToken,
    apiTokenSet: device.apiTokenSet,
  });
  const canReveal = canRevealDeviceApiToken(device.apiToken);
  const canCopy = canCopyDeviceApiToken(device.apiToken);

  useEffect(() => {
    if (!canReveal) {
      setTokenVisible(false);
    }
  }, [canReveal]);

  const identityDirty = useMemo(() => {
    if (!identityBaseline) return false;
    const codeChanged =
      device.controllerCode.trim() !== identityBaseline.controllerCode.trim();
    const ipChanged = device.ipAddress.trim() !== identityBaseline.ipAddress.trim();
    return codeChanged || ipChanged;
  }, [device.controllerCode, device.ipAddress, identityBaseline]);

  const tokenPlaceholder =
    tokenStatus === "configured"
      ? "•••••••• (configurado — deixe em branco para manter)"
      : tokenStatus === "missing"
        ? "Será gerado automaticamente ao salvar"
        : "Novo token — copie antes de salvar";

  const onCopyToken = async () => {
    if (!canCopy) return;
    const value = device.apiToken.trim();
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(value);
      } else {
        const area = document.createElement("textarea");
        area.value = value;
        area.setAttribute("readonly", "");
        area.style.position = "fixed";
        area.style.left = "-9999px";
        document.body.appendChild(area);
        area.select();
        const ok = document.execCommand("copy");
        document.body.removeChild(area);
        if (!ok) throw new Error("copy_failed");
      }
      setCopyState("copied");
      window.setTimeout(() => setCopyState("idle"), 1600);
    } catch {
      setCopyState("failed");
      window.setTimeout(() => setCopyState("idle"), 2200);
    }
  };

  const onGenerateToken = () => {
    onChange({ apiToken: generateDeviceApiToken() });
    setTokenVisible(true);
  };

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
              <PpHintAction
                hint={
                  testingConnection
                    ? PP_HELP.form.testConnectionLoading
                    : PP_HELP.form.testConnection
                }
                ariaLabel="Ajuda: Testar conexão"
              >
                <PpIconButton
                  className="pp-test-connection-btn"
                  disabled={testingConnection || !device.ipAddress.trim()}
                  aria-label={
                    testingConnection
                      ? PP_HELP.form.testConnectionLoading
                      : PP_HELP.form.testConnectionAction
                  }
                  onClick={onTestConnection}
                >
                  {testingConnection ? (
                    <Loader2 size={16} aria-hidden className="pp-spin" />
                  ) : (
                    <Wifi size={16} aria-hidden />
                  )}
                </PpIconButton>
              </PpHintAction>
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
          label={`Token do dispositivo · ${tokenStatusLabel(tokenStatus)}`}
          hint={tokenFieldHint(tokenStatus)}
          span
          className="pp-form-grid__span-full"
          type={tokenVisible ? "text" : "password"}
          value={device.apiToken}
          placeholder={tokenPlaceholder}
          onChange={(value) => onChange({ apiToken: value })}
          afterControl={
            <>
              {ppFieldError(errors?.apiToken)}
              {tokenStatus === "missing" ? ppFieldHint(PP_HELP.form.apiTokenMissingHint) : null}
              {identityDirty ? ppFieldHint(PP_HELP.form.apiTokenIdentityDirtyHint) : null}
              {!canCopy ? ppFieldHint(PP_HELP.form.apiTokenCopyDisabledHint) : null}
            </>
          }
          trailing={
            <div className="pp-field__icon-actions" role="group" aria-label="Ações do token">
              <PpHintAction
                hint={PP_HELP.form.apiTokenShowHelp}
                ariaLabel="Ajuda: Mostrar token"
              >
                <PpIconButton
                  disabled={!canReveal}
                  aria-label={
                    tokenVisible
                      ? PP_HELP.form.apiTokenHideAction
                      : PP_HELP.form.apiTokenShowAction
                  }
                  onClick={() => setTokenVisible((v) => !v)}
                >
                  {tokenVisible ? (
                    <EyeOff size={16} aria-hidden />
                  ) : (
                    <Eye size={16} aria-hidden />
                  )}
                </PpIconButton>
              </PpHintAction>
              <PpHintAction
                hint={PP_HELP.form.apiTokenCopyHelp}
                ariaLabel="Ajuda: Copiar token"
              >
                <PpIconButton
                  disabled={!canCopy}
                  aria-label={
                    copyState === "copied"
                      ? PP_HELP.form.apiTokenCopyDone
                      : copyState === "failed"
                        ? PP_HELP.form.apiTokenCopyFailed
                        : PP_HELP.form.apiTokenCopyAction
                  }
                  onClick={() => void onCopyToken()}
                >
                  {copyState === "copied" ? (
                    <Check size={16} aria-hidden />
                  ) : (
                    <Clipboard size={16} aria-hidden />
                  )}
                </PpIconButton>
              </PpHintAction>
              <PpHintAction
                hint={PP_HELP.form.apiTokenGenerateHelp}
                ariaLabel="Ajuda: Gerar token"
              >
                <PpIconButton
                  aria-label={PP_HELP.form.generateApiTokenAction}
                  onClick={onGenerateToken}
                >
                  <KeyRound size={16} aria-hidden />
                </PpIconButton>
              </PpHintAction>
            </div>
          }
        />

        <PpNativeSelectField
          id="pp-device-driver"
          label="Tipo de driver"
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
