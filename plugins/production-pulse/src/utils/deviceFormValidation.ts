import type { AnchorType, BindingFormValues, DeviceFormValues } from "../types/form";

const IPV4_RE =
  /^(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)$/;

export type DeviceFormErrors = Partial<Record<keyof DeviceFormValues, string>> & {
  binding?: Partial<Record<keyof BindingFormValues, string>>;
  form?: string;
};

export function validateIpv4(value: string): boolean {
  return IPV4_RE.test(value.trim());
}

export const POLL_INTERVAL_MIN_SECONDS = 0.5;
export const POLL_INTERVAL_MAX_SECONDS = 300;

export function clampPollInterval(value: number): number {
  return Math.min(POLL_INTERVAL_MAX_SECONDS, Math.max(POLL_INTERVAL_MIN_SECONDS, value));
}

export function validateDeviceForm(
  device: DeviceFormValues,
  binding: BindingFormValues,
  options: { requireBinding?: boolean } = {},
): DeviceFormErrors {
  const errors: DeviceFormErrors = {};

  const name = device.name.trim();
  if (!name) errors.name = "Nome é obrigatório.";
  else if (name.length > 120) errors.name = "Nome deve ter no máximo 120 caracteres.";

  if (!device.branch) errors.branch = "Filial é obrigatória.";

  const ip = device.ipAddress.trim();
  if (!ip) errors.ipAddress = "Endereço IP é obrigatório.";
  else if (!validateIpv4(ip)) errors.ipAddress = "IP inválido.";

  if (!device.driverKey.trim()) errors.driverKey = "Driver é obrigatório.";

  if (!Number.isFinite(device.pollIntervalSeconds)) {
    errors.pollIntervalSeconds = "Intervalo inválido.";
  } else if (
    device.pollIntervalSeconds < POLL_INTERVAL_MIN_SECONDS ||
    device.pollIntervalSeconds > POLL_INTERVAL_MAX_SECONDS
  ) {
    errors.pollIntervalSeconds = "Intervalo deve estar entre 0,5 e 300 segundos.";
  }

  const bindingErrors = validateBindingForm(binding, options.requireBinding);
  if (Object.keys(bindingErrors).length > 0) {
    errors.binding = bindingErrors;
  }

  return errors;
}

export function validateBindingForm(
  binding: BindingFormValues,
  required = false,
): Partial<Record<keyof BindingFormValues, string>> {
  if (!required && !hasBindingInput(binding)) {
    return {};
  }

  const errors: Partial<Record<keyof BindingFormValues, string>> = {};

  if (binding.anchorType === "work_center") {
    if (!binding.workCenterCode.trim()) {
      errors.workCenterCode = "Centro de trabalho é obrigatório para posto PCP.";
    }
  } else if (binding.anchorType === "machine") {
    if (!binding.machineLabel.trim()) errors.machineLabel = "Nome da máquina é obrigatório.";
  } else if (binding.anchorType === "equipment") {
    if (!binding.equipmentLabel.trim()) errors.equipmentLabel = "Nome do equipamento é obrigatório.";
  } else if (binding.anchorType === "area") {
    if (!binding.areaLabel.trim()) errors.areaLabel = "Nome da área é obrigatório.";
  }

  return errors;
}

export function hasBindingInput(binding: BindingFormValues): boolean {
  return Boolean(
    binding.workCenterCode.trim() ||
      binding.machineLabel.trim() ||
      binding.equipmentLabel.trim() ||
      binding.areaLabel.trim() ||
      binding.resourceCode.trim() ||
      binding.toolCode.trim() ||
      binding.notes.trim() ||
      binding.anchorType !== "equipment",
  );
}

export function bindingToApiBody(binding: BindingFormValues): Record<string, string | null> {
  return {
    anchorType: binding.anchorType,
    workCenterCode: binding.workCenterCode.trim() || null,
    workCenterName: binding.workCenterName.trim() || null,
    machineCode: null,
    machineLabel: binding.machineLabel.trim() || null,
    equipmentLabel: binding.equipmentLabel.trim() || null,
    areaLabel: binding.areaLabel.trim() || null,
    resourceCode: binding.resourceCode.trim() || null,
    toolCode: binding.toolCode.trim() || null,
    notes: binding.notes.trim() || null,
  };
}

export function anchorPrimaryLabelField(anchorType: AnchorType): keyof BindingFormValues {
  if (anchorType === "work_center") return "workCenterCode";
  if (anchorType === "machine") return "machineLabel";
  if (anchorType === "area") return "areaLabel";
  if (anchorType === "standalone") return "notes";
  return "equipmentLabel";
}

export function formatPrimaryMetricFromProbe(
  metrics: Record<string, number | string> | undefined,
): string | null {
  if (!metrics) return null;
  const keys = Object.keys(metrics);
  if (keys.length === 0) return null;
  const key = keys.includes("counter") ? "counter" : keys[0];
  const raw = metrics[key];
  if (raw === undefined || raw === null) return null;
  const formatted = typeof raw === "number" ? new Intl.NumberFormat("pt-BR").format(raw) : String(raw);
  if (key === "counter") return `Golpes: ${formatted}`;
  if (key === "rpm") return `Rotação: ${formatted} rpm`;
  if (key === "temperature_c") return `Temperatura: ${formatted} °C`;
  return `${key}: ${formatted}`;
}
