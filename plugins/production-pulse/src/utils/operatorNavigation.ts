import { productionPulseOperatorPath } from "../constants/routes";
import { navigateProductionPulse } from "./navigation";

/** Volta ao hub de locais — nunca ao picker (auto-redirect com 1 device). */
export function navigateOperatorPlacementHub(branch: string): void {
  navigateProductionPulse(productionPulseOperatorPath(branch));
}
