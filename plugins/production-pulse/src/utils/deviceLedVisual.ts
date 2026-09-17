/** Canonical LED operational states from chip GET /api/status (`ledState`). */
export type DeviceLedState =
  | "offline"
  | "connecting"
  | "wifi_ok_never_contacted"
  | "backend_ok"
  | "wifi_ok_stale"
  | "ota_in_progress"
  | "auth_error";

export type DeviceLedPattern = "solid" | "blink_slow" | "blink_fast" | "blink_ota";

export type DeviceLedVisual = {
  ledState: DeviceLedState;
  colorClass: string;
  pattern: DeviceLedPattern;
  label: string;
};

const LED_VISUALS: Record<DeviceLedState, Omit<DeviceLedVisual, "ledState">> = {
  offline: {
    colorClass: "pp-led--red",
    pattern: "solid",
    label: "Sem Wi‑Fi",
  },
  connecting: {
    colorClass: "pp-led--red",
    pattern: "blink_slow",
    label: "Conectando Wi‑Fi",
  },
  wifi_ok_never_contacted: {
    colorClass: "pp-led--blue",
    pattern: "solid",
    label: "Wi‑Fi OK · sem Pulse",
  },
  backend_ok: {
    colorClass: "pp-led--green",
    pattern: "solid",
    label: "Pulse autenticado",
  },
  wifi_ok_stale: {
    colorClass: "pp-led--blue",
    pattern: "blink_slow",
    label: "Wi‑Fi OK · Pulse stale",
  },
  ota_in_progress: {
    colorClass: "pp-led--yellow",
    pattern: "blink_ota",
    label: "OTA em andamento",
  },
  auth_error: {
    colorClass: "pp-led--red",
    pattern: "blink_fast",
    label: "Falha de autenticação",
  },
};

const KNOWN_STATES = new Set<string>(Object.keys(LED_VISUALS));

export function isDeviceLedState(value: unknown): value is DeviceLedState {
  return typeof value === "string" && KNOWN_STATES.has(value);
}

/** Map chip `ledState` to fixed RGB visual (not theme V1/V2). */
export function resolveLedVisual(ledState: unknown): DeviceLedVisual | null {
  if (!isDeviceLedState(ledState)) return null;
  const visual = LED_VISUALS[ledState];
  return { ledState, ...visual };
}

/**
 * Prefer chip LED when Pulse connectivity is online (or unknown online-ish).
 * disabled / no_binding / offline keep Pulse badge (avoid stale LED while unreachable).
 */
export function preferLedVisualForConnectivity(
  status: string | null | undefined,
  ledState: unknown,
): DeviceLedVisual | null {
  if (status === "disabled" || status === "no_binding" || status === "offline") {
    return null;
  }
  return resolveLedVisual(ledState);
}
