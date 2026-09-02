import validationContent from "./device_validation_content.json";

export const POLL_INTERVAL_MIN_MS = validationContent.limits.pollIntervalMs.min;
export const POLL_INTERVAL_MAX_MS = validationContent.limits.pollIntervalMs.max;
export const POLL_INTERVAL_DEFAULT_MS = validationContent.limits.pollIntervalMs.default;
export const LIVE_UI_REFRESH_MIN_MS = validationContent.limits.liveUiRefreshMs.min;
export const NAME_MAX_LENGTH = validationContent.limits.nameMaxLength;
export const VALID_BRANCHES = validationContent.validBranches;
export const IPV4_REGEX = new RegExp(validationContent.patterns.ipv4);

/** Códigos de validação usados pelo formulário — mensagens espelham `device_api_messages.validationErrors`. */
export const DEVICE_FORM_VALIDATION_ERROR_CODES = [
  "name_required",
  "name_too_long",
  "branch_required",
  "ip_address_required",
  "invalid_ipv4",
  "driver_key_required",
  "poll_interval_out_of_range",
  "work_center_code_required",
  "machine_label_required",
  "equipment_label_required",
  "area_label_required",
] as const;

export type DeviceFormValidationErrorCode =
  (typeof DEVICE_FORM_VALIDATION_ERROR_CODES)[number];

export function formatValidationMessage(
  code: string,
  params: Record<string, string | number> = {},
): string {
  const template = DEVICE_FORM_VALIDATION_MESSAGES[code as DeviceFormValidationErrorCode];
  if (!template) return code;
  return template.replace(/\{(\w+)\}/g, (_match, key: string) => {
    const value = params[key];
    return value === undefined || value === null ? `{${key}}` : String(value);
  });
}

export const DEVICE_FORM_VALIDATION_MESSAGES: Record<DeviceFormValidationErrorCode, string> = {
  name_required: "Informe o nome do dispositivo.",
  name_too_long: "O nome do dispositivo deve ter no máximo 120 caracteres.",
  branch_required: "Informe a filial.",
  ip_address_required: "Informe o endereço IP do dispositivo.",
  invalid_ipv4: "Informe um endereço IPv4 válido.",
  driver_key_required: "Selecione o driver (protocolo) do dispositivo.",
  poll_interval_out_of_range:
    "O intervalo de leitura deve estar entre {min} e {max} milissegundos.",
  work_center_code_required: "Informe o centro de trabalho para amarração por posto.",
  machine_label_required: "Informe o rótulo da máquina para amarração por máquina.",
  equipment_label_required: "Informe o rótulo do equipamento para amarração por equipamento.",
  area_label_required: "Informe o rótulo da área para amarração por área.",
};

export function validateIpv4(value: string): boolean {
  return IPV4_REGEX.test(value.trim());
}

export function clampPollIntervalMs(value: number): number {
  return Math.min(POLL_INTERVAL_MAX_MS, Math.max(POLL_INTERVAL_MIN_MS, Math.round(value)));
}
