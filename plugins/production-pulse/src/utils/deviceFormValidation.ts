import type { AnchorType, BindingFormValues, DeviceFormValues } from "../types/form";
import {
  clampPollIntervalMs,
  CONTROLLER_CODE_MAX_LENGTH,
  formatValidationMessage,
  NAME_MAX_LENGTH,
  POLL_INTERVAL_MAX_MS,
  POLL_INTERVAL_MIN_MS,
  validateControllerCode,
  validateIpv4,
} from "../content/deviceValidationContent";

export type DeviceFormErrors = Partial<Record<keyof DeviceFormValues, string>> & {
  binding?: Partial<Record<keyof BindingFormValues, string>>;
  form?: string;
};

export { clampPollIntervalMs, POLL_INTERVAL_MAX_MS, POLL_INTERVAL_MIN_MS, validateIpv4 };

export function validateDeviceForm(
  device: DeviceFormValues,
  binding: BindingFormValues,
  options: { requireBinding?: boolean } = {},
): DeviceFormErrors {
  const errors: DeviceFormErrors = {};

  const name = device.name.trim();
  if (!name) errors.name = formatValidationMessage("name_required");
  else if (name.length > NAME_MAX_LENGTH) {
    errors.name = formatValidationMessage("name_too_long");
  }

  if (!device.branch) errors.branch = formatValidationMessage("branch_required");

  const ip = device.ipAddress.trim();
  if (!ip) errors.ipAddress = formatValidationMessage("ip_address_required");
  else if (!validateIpv4(ip)) errors.ipAddress = formatValidationMessage("invalid_ipv4");

  const controllerCode = (device.controllerCode ?? "").trim();
  if (controllerCode) {
    if (controllerCode.length > CONTROLLER_CODE_MAX_LENGTH) {
      errors.controllerCode = formatValidationMessage("controller_code_too_long", {
        max: CONTROLLER_CODE_MAX_LENGTH,
      });
    } else if (!validateControllerCode(controllerCode)) {
      errors.controllerCode = formatValidationMessage("invalid_controller_code");
    }
  }

  if (!device.driverKey.trim()) errors.driverKey = formatValidationMessage("driver_key_required");

  if (!Number.isFinite(device.pollIntervalMs)) {
    errors.pollIntervalMs = formatValidationMessage("poll_interval_out_of_range", {
      min: POLL_INTERVAL_MIN_MS,
      max: POLL_INTERVAL_MAX_MS,
    });
  } else if (
    device.pollIntervalMs < POLL_INTERVAL_MIN_MS ||
    device.pollIntervalMs > POLL_INTERVAL_MAX_MS
  ) {
    errors.pollIntervalMs = formatValidationMessage("poll_interval_out_of_range", {
      min: POLL_INTERVAL_MIN_MS,
      max: POLL_INTERVAL_MAX_MS,
    });
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
      errors.workCenterCode = formatValidationMessage("work_center_code_required");
    }
  } else if (binding.anchorType === "machine") {
    if (!binding.machineLabel.trim()) {
      errors.machineLabel = formatValidationMessage("machine_label_required");
    }
  } else if (binding.anchorType === "equipment") {
    if (!binding.equipmentLabel.trim()) {
      errors.equipmentLabel = formatValidationMessage("equipment_label_required");
    }
  } else if (binding.anchorType === "area") {
    if (!binding.areaLabel.trim()) {
      errors.areaLabel = formatValidationMessage("area_label_required");
    }
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
