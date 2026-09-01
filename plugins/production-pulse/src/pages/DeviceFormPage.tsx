import { useEffect, useState } from "react";

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
  PpBackLink,
  PpFormActions,
  PpPageHero,
  PpSectionCard,
  PpStateBox,
  ppShellIcon,
} from "../app/productionPulseUi";
import { DeviceBindingSection } from "../components/DeviceBindingSection";
import { DeviceForm } from "../components/DeviceForm";
import { TestConnectionModal } from "../components/modals/TestConnectionModal";
import { PRODUCTION_PULSE_BASE_PATH } from "../constants/routes";
import type { ProductionPulsePermissionFlags } from "../constants/permissions";
import { PP_HELP } from "../content/helpTooltips";
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
import { useViewportBucket } from "../hooks/useViewportBucket";
import { navigateProductionPulse } from "../utils/navigation";
import { buildPanelPath } from "../utils/panelFilterUrl";
import type { DeviceBinding } from "../types/device";

type DeviceFormPageProps = {
  mode: "create" | "edit";
  deviceId?: string;
  initialBranch?: string;
  permissions: ProductionPulsePermissionFlags;
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
}: DeviceFormPageProps) {
  const viewport = useViewportBucket();
  const isMobile = viewport === "mobile";

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

  const [testOpen, setTestOpen] = useState(false);
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
          driverKey: row.driverKey,
          pollIntervalSeconds: row.pollIntervalSeconds,
          enabled: row.enabled,
        });
        setBinding(bindingFromApi(row.binding));
      })
      .catch((err: Error) => setFormError(err.message))
      .finally(() => setLoading(false));
  }, [deviceId, mode]);

  const canManage = permissions.canManageDevices;

  const goBack = () => {
    navigateProductionPulse(buildPanelPath({ branch: device.branch, page: 1, view: "list", groupBy: "work_center", anchorType: "", role: "", status: "", search: "" }));
  };

  const runTestConnection = async () => {
    setTestOpen(true);
    setTestLoading(true);
    setTestResult(null);
    setTestError(null);
    try {
      const result =
        mode === "edit" && deviceId
          ? await testExistingDevice(deviceId)
          : await testDeviceProbe(device);
      setTestResult(result);
      if (!result.online) {
        setTestError(result.error ?? PP_HELP.modals.testFail);
      }
    } catch (err) {
      setTestError(err instanceof Error ? err.message : PP_HELP.modals.testFail);
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
    try {
      const saved =
        mode === "edit" && deviceId
          ? await replaceDevice(deviceId, device)
          : await createDevice(device);

      if (hasBindingInput(binding)) {
        await upsertDeviceBinding(saved.id, binding);
        navigateProductionPulse(`${PRODUCTION_PULSE_BASE_PATH}?branch=${encodeURIComponent(saved.branch)}`);
      } else {
        navigateProductionPulse(`${PRODUCTION_PULSE_BASE_PATH}?branch=${encodeURIComponent(saved.branch)}`);
      }
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
    <div className="pp-page-stack pp-form-page">
      <PpPageHero
        title={mode === "create" ? "Novo dispositivo" : "Editar dispositivo"}
        description="Cadastro do hardware e onde o sensor está instalado."
        badge={ppShellIcon}
        nav={<PpBackLink onClick={goBack}>Voltar ao painel</PpBackLink>}
      />

      {formError ? (
        <PpStateBox variant="error" title="Não foi possível continuar" message={formError} />
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

      <div className={`pp-form-footer${isMobile ? " pp-form-footer--sticky" : ""}`}>
        <PpFormActions>
          <PpActionButton variant="ghost" onClick={goBack} disabled={saving}>
            Cancelar
          </PpActionButton>
          <PpActionButton variant="primary" onClick={() => void onSave()} disabled={saving}>
            {saving ? "Salvando…" : "Salvar"}
          </PpActionButton>
        </PpFormActions>
      </div>

      <TestConnectionModal
        open={testOpen}
        loading={testLoading}
        result={testResult}
        error={testError}
        onClose={() => setTestOpen(false)}
      />
    </div>
  );
}
