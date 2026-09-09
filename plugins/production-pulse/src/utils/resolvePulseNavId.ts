import type { ProductionPulseRoute } from "../constants/routes";

export type ProductionPulseNavId = "panel" | "firmwares" | "firmwareLinks" | "operator";

export function resolvePulseNavId(route: ProductionPulseRoute): ProductionPulseNavId | null {
  switch (route.kind) {
    case "panel":
    case "deviceNew":
    case "deviceEdit":
    case "deviceDetail":
      return "panel";
    case "firmwares":
    case "firmwareDetail":
      return "firmwares";
    case "firmwareLinks":
    case "firmwareJobs":
      return "firmwareLinks";
    case "operatorHub":
    case "operatorPicker":
    case "operatorDevice":
      return "operator";
    default:
      return null;
  }
}
