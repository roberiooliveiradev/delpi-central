import { printDelpiDocumentSpec } from "@delpi/plugin-ui/index";

import type { Shipment } from "../types/thirdPartyMaterials";
import { buildShipmentDelpiDocumentSpec } from "./shipmentPdfSpec";

export { buildShipmentDelpiDocumentSpec } from "./shipmentPdfSpec";

export function exportShipmentPdf(shipment: Shipment): boolean {
  return printDelpiDocumentSpec(buildShipmentDelpiDocumentSpec(shipment));
}
