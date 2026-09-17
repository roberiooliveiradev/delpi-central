import type { ProductionPulseRoute } from "../constants/routes";

/**
 * Stable key for shell ViewTransition — Admin↔Operador and operator steps fade in.
 * Branch switches stay on the same hub key (canvas soft-refresh handles that).
 */
export function resolvePulseContentTransitionKey(route: ProductionPulseRoute): string {
  switch (route.kind) {
    case "firmwareLinks":
    case "firmwares":
    case "firmwareJobs":
    case "panel":
      return "admin:hub";
    case "operatorHub":
      return `operator:hub:${route.branch}`;
    case "operatorPicker":
      return `operator:picker:${route.branch}:${route.placementKey}`;
    case "operatorDevice":
      return `operator:device:${route.branch}:${route.deviceId}`;
    case "deviceNew":
    case "deviceEdit":
    case "deviceDetail":
    case "firmwareNew":
    case "firmwareDetail":
      return `admin:legacy:${route.kind}`;
    case "unknown":
      return "unknown";
    default: {
      const _exhaustive: never = route;
      return String(_exhaustive);
    }
  }
}
