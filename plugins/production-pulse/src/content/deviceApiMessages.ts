/**
 * Códigos de conectividade de device — espelho de
 * `production-pulse-api/production_pulse_app/content/device_api_messages.json`
 * (`deviceConnectivity.codes`). Mensagens PT ficam só na API.
 */
export const DEVICE_CONNECTIVITY_ERROR_CODES = [
  "timeout",
  "network_error",
  "http_error",
  "invalid_response",
  "device_error",
  "missing_ip",
  "driver_not_implemented",
] as const;

export type DeviceConnectivityErrorCode = (typeof DEVICE_CONNECTIVITY_ERROR_CODES)[number];
