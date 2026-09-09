import { useEffect, useMemo, useState } from "react";

import {
  createDevice,
  fetchDevice,
  fetchDriverCatalog,
  replaceDevice,
  testDeviceProbe,
  testExistingDevice,
  upsertDeviceBinding,
} from "../api/productionPulseApi";
import {
  PpActionButton,
  PpFormActions,
  PpPageHero,
  PpSectionCard,
  PpStateBox,
  ppShellIcon,
} from "../app/productionPulseUi";
import { ProductionPulsePagePath } from "../components/ProductionPulsePagePath";
import { DeviceBindingSection } from "../components/DeviceBindingSection";
import { DeviceForm } from "../components/DeviceForm";
import {
  productionPulseDeviceDetailPath,
  productionPulseDeviceEditPath,
  productionPulseFirmwareLinksPath,
} from "../constants/routes";
import type { ProductionPulsePermissionFlags } from "../constants/permissions";
import { PP_HELP } from "../content/helpTooltips";
import { resolveDeviceActionMessage, resolveProbeErrorMessage } from "../utils/apiErrors";
import type { BindingFormValues, DeviceFormValues, ProbeResult } from "../types/form";
import {
  DEFAULT_BINDING_VALUES,
  DEFAULT_DEVICE_FORM_VALUES,
} from "../types/form";
import {
  hasBindingInput,
  validateDeviceForm,
  type DeviceFormErrors,
} from "../utils/deviceFormValidation";
import { isCompactViewport, isMobileViewport } from "../utils/viewportLayout";
import { useViewportBucket } from "../hooks/useViewportBucket";
import { navigateProductionPulse } from "../utils/navigation";
import type { DeviceBinding } from "../types/device";

type ProbeNoticeVariant = "error" | "warning" | "success" | "info";

type DeviceFormPageProps = {
  mode: "create" | "edit";
  deviceId?: string;
  initialBranch?: string;
  permissions: ProductionPulsePermissionFlags;
  /** When true, omit page chrome and call onDone instead of navigating home. */
  embedded?: boolean;
  onDone?: (branch: string) => void;
  onCancel?: () => void;
  /** Optional floating notice host (Admin Hub). */
  onProbeNotice?: (message: string, variant?: ProbeNoticeVariant) => void;
};

function bindingFromApi(binding: DeviceBinding | null | undefined): BindingFormValues {
  if (!binding) return { ...DEFAULT_BINDING_VALUES };
  return {
    anchorType: binding.anchorType as BindingFormValues["anchorType"],
    workCenterCode: binding.workCenterCode ?? "",
    workCenterName: binding.workCenterName ?? "",
    machineLabel: binding.machineLabel ?? "",
    equipmentLabel: binding.equipmentLabel ?? "",
    areaLabel: binding.areaLabel ?? "",
    resourceCode: binding.resourceCode ?? "",
    toolCode: binding.toolCode ?? "",
    notes: binding.notes ?? "",
  };
}

export function DeviceFormPage({
  mode,
  deviceId,
  initialBranch,
  permissions,
  embedded = false,
  onDone,
  onCancel,
  onProbeNotice,
}: DeviceFormPageProps) {
  const viewport = useViewportBucket();
  const isMobile = isMobileViewport(viewport);
  const isCompact = isCompactViewport(viewport);

  const [device, setDevice] = useState<DeviceFormValues>({
    ...DEFAULT_DEVICE_FORM_VALUES,
    branch: initialBranch ?? DEFAULT_DEVICE_FORM_VALUES.branch,
  });
  const [binding, setBinding] = useState<BindingFormValues>({ ...DEFAULT_BINDING_VALUES });
  const [drivers, setDrivers] = useState<Awaited<ReturnType<typeof fetchDriverCatalog>>>([]);
  const [loading, setLoading] = useState(mode === "edit");
  const [saving, setSaving] = useState(false);
  const [errors, setErrors] = useState<DeviceFormErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [configPushBanner, setConfigPushBanner] = useState<string | null>(null);

  const [testLoading, setTestLoading] = useState(false);
  const [testResult, setTestResult] = useState<ProbeResult | null>(null);
  const [testError, setTestError] = useState<string | null>(null);

  useEffect(() => {
    fetchDriverCatalog()
      .then(setDrivers)
      .catch(() => setDrivers([]));
  }, []);

  useEffect(() => {
    if (mode !== "edit" || !deviceId) return;
    setLoading(true);
    fetchDevice(deviceId)
      .then((row) => {
        setDevice({
          name: row.name,
          branch: row.branch,
          ipAddress: row.ipAddress,
          controllerCode: row.controllerCode ?? "",
          firmwareSource: row.firmwareSource ?? "",
          wifiSsid: row.wifiSsid ?? "",
          wifiPassword: "",
          debounceMs: row.debounceMs != null ? String(row.debounceMs) : "",
          apiToken: "",
          apiTokenSet: Boolean(row.apiTokenSet),
          driverKey: row.driverKey,
          pollIntervalMs: row.pollIntervalMs,
          enabled: row.enabled,
        });
        setBinding(bindingFromApi(row.binding));
      })
      .catch((err: Error) => setFormError(err.message))
      .finally(() => setLoading(false));
  }, [deviceId, mode]);

  const canManage = permissions.canManageDevices;

  const panelBackPath = useMemo(
    () =>
      productionPulseFirmwareLinksPath({
        branch: device.branch,
        panel: "devices",
      }),
    [device.branch],
  );

  const goBack = () => {
    if (onCancel) {
      onCancel();
      return;
    }
    navigateProductionPulse(panelBackPath);
  };

  const formPageTitle = mode === "create" ? "Novo dispositivo" : "Editar dispositivo";

  const runTestConnection = async () => {
    setTestLoading(true);
    setTestResult(null);
    setTestError(null);
    try {
      const result =
        mode === "edit" && deviceId
          ? await testExistingDevice(deviceId)
          : await testDeviceProbe(device);
      setTestResult(result);
      if (result.online) {
        setDevice((prev) => {
          const patch: Partial<DeviceFormValues> = {};
          if (result.controllerCode && !prev.controllerCode.trim()) {
            patch.controllerCode = result.controllerCode;
          }
          const ssid = result.wifiSsid ?? result.deviceConfig?.ssid;
          if (ssid && !prev.wifiSsid.trim()) {
            patch.wifiSsid = ssid;
          }
          const debounce =
            result.debounceMs ?? result.deviceConfig?.debounceMs;
          if (debounce != null && !prev.debounceMs.trim()) {
            patch.debounceMs = String(debounce);
          }
          if (result.apiTokenSet != null || result.deviceConfig?.apiTokenSet != null) {
            patch.apiTokenSet = Boolean(
              result.apiTokenSet ?? result.deviceConfig?.apiTokenSet,
            );
          }
          return Object.keys(patch).length ? { ...prev, ...patch } : prev;
        });
        onProbeNotice?.(PP_HELP.modals.testOk, "success");
      } else {
        const message = resolveProbeErrorMessage(result, PP_HELP.modals.testFail);
        setTestError(message);
        onProbeNotice?.(message, "warning");
      }
    } catch (err) {
      const message = resolveDeviceActionMessage(err, PP_HELP.modals.testFail);
      setTestError(message);
      onProbeNotice?.(message, "error");
    } finally {
      setTestLoading(false);
    }
  };

  const onSave = async () => {
    const nextErrors = validateDeviceForm(device, binding, {
      requireBinding: hasBindingInput(binding),
    });
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) {
      setFormError("Revise os campos destacados antes de salvar.");
      return;
    }

    setSaving(true);
    setFormError(null);
    setConfigPushBanner(null);
    try {
      const saved =
        mode === "edit" && deviceId
          ? await replaceDevice(deviceId, device)
          : await createDevice(device);

      if (hasBindingInput(binding)) {
        await upsertDeviceBinding(saved.id, binding);
      }

      if (saved.deviceConfigPush?.status === "failed") {
        setConfigPushBanner(
          saved.deviceConfigPush.message ?? PP_HELP.form.deviceConfigPushFailed,
        );
        setDevice((prev) => ({
          ...prev,
          wifiPassword: "",
          apiToken: "",
          apiTokenSet: Boolean(saved.apiTokenSet),
          wifiSsid: saved.wifiSsid ?? prev.wifiSsid,
          debounceMs:
            saved.debounceMs != null ? String(saved.debounceMs) : prev.debounceMs,
        }));
        if (mode === "create") {
          navigateProductionPulse(productionPulseDeviceEditPath(saved.id));
        }
        return;
      }

      if (onDone) {
        onDone(saved.branch);
        return;
      }
      navigateProductionPulse(
        productionPulseFirmwareLinksPath({ branch: saved.branch, panel: "devices" }),
      );
    } catch (err) {
      const message = err instanceof Error ? err.message : "Não foi possível salvar o dispositivo.";
      setFormError(message);
      if (message.toLowerCase().includes("ip")) {
        setErrors((current) => ({ ...current, ipAddress: message }));
      }
    } finally {
      setSaving(false);
    }
  };

  if (!canManage) {
    return (
      <div className="pp-page-stack">
        <PpPageHero title="Dispositivo" badge={ppShellIcon} />
        <PpStateBox
          variant="error"
          title="Sem permissão"
          message="Você não tem permissão para cadastrar ou editar dispositivos."
        />
      </div>
    );
  }

  if (loading) {
    return (
      <div className="pp-page-stack">
        <PpPageHero title="Carregando…" badge={ppShellIcon} />
        <PpStateBox variant="loading" title="Carregando dispositivo" message="Aguarde…" />
      </div>
    );
  }

  return (
    <div className={`pp-page-stack pp-form-page${embedded ? " pp-form-page--embedded" : ""}`}>
      {!embedded ? (
        <>
          <ProductionPulsePagePath
            panelHref={panelBackPath}
            current={formPageTitle}
            items={
              mode === "edit" && deviceId && device.name
                ? [
                    {
                      id: "device",
                      label: device.name,
                      href: productionPulseDeviceDetailPath(deviceId),
                    },
                  ]
                : []
            }
          />
          <PpPageHero
            title={formPageTitle}
            description="Cadastro do hardware e onde o sensor está instalado."
            badge={ppShellIcon}
          />
        </>
      ) : null}

      {formError ? (
        <PpStateBox variant="error" title="Não foi possível continuar" message={formError} />
      ) : null}

      {configPushBanner ? (
        <PpStateBox
          variant="error"
          title="Configuração no chip"
          message={configPushBanner}
        />
      ) : null}

      {testLoading ? (
        <PpStateBox
          variant="loading"
          title="Testando conexão…"
          message="Aguarde a resposta do dispositivo."
        />
      ) : null}

      {!testLoading && testResult?.online ? (
        <PpStateBox
          variant="empty"
          title="Conexão OK"
          message="O dispositivo respondeu ao probe."
          action={
            <PpActionButton variant="ghost" onClick={() => setTestResult(null)}>
              Fechar
            </PpActionButton>
          }
        />
      ) : null}

      {!testLoading && testError ? (
        <PpStateBox
          variant="error"
          title="Falha no teste"
          message={testError}
          action={
            <PpActionButton
              variant="ghost"
              onClick={() => {
                setTestError(null);
                setTestResult(null);
              }}
            >
              Fechar
            </PpActionButton>
          }
        />
      ) : null}

      <div className="pp-form-layout">
        <PpSectionCard title="Dispositivo IoT" hint={PP_HELP.form.sectionDevice}>
          <DeviceForm
            device={device}
            drivers={drivers}
            allowedBranches={permissions.allowedBranches}
            readOnlyBranch={mode === "edit"}
            errors={errors}
            onChange={(patch) => setDevice((current) => ({ ...current, ...patch }))}
            onTestConnection={() => void runTestConnection()}
            testingConnection={testLoading}
          />
        </PpSectionCard>

        <PpSectionCard title="Onde está instalado" hint={PP_HELP.form.sectionPlacement}>
          <DeviceBindingSection
            binding={binding}
            branch={device.branch}
            errors={errors.binding}
            stackedAnchor={isMobile}
            onChange={(patch) => setBinding((current) => ({ ...current, ...patch }))}
          />
        </PpSectionCard>
      </div>

      <div className={`pp-form-footer${isCompact ? " pp-form-footer--sticky" : ""}`}>
        <PpFormActions>
          <PpActionButton variant="ghost" onClick={goBack} disabled={saving}>
            Cancelar
          </PpActionButton>
          <PpActionButton variant="primary" onClick={() => void onSave()} disabled={saving}>
            {saving ? "Salvando…" : "Salvar"}
          </PpActionButton>
        </PpFormActions>
      </div>
    </div>
  );
}
