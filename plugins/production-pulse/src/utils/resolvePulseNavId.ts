import type { ProductionPulseRoute } from "../constants/routes";

export type ProductionPulseNavId = "panel" | "hub" | "operator";

export function resolvePulseNavId(route: ProductionPulseRoute): ProductionPulseNavId | null {
  switch (route.kind) {
    case "panel":
    case "deviceNew":
    case "deviceEdit":
    case "deviceDetail":
      return "panel";
    case "firmwares":
    case "firmwareNew":
    case "firmwareDetail":
    case "firmwareLinks":
    case "firmwareJobs":
      return "hub";
    case "operatorHub":
    case "operatorPicker":
    case "operatorDevice":
      return "operator";
    default:
      return null;
  }
}
