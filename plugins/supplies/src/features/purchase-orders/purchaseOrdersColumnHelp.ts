import { SP_HELP } from "../../content/helpTooltips";
import type { PurchaseOrderTableColumnKey } from "./purchaseOrdersTableConfig";

export function purchaseOrdersColumnHelp(
  key: PurchaseOrderTableColumnKey,
): string | undefined {
  switch (key) {
    case "supplier":
      return SP_HELP.purchaseOrdersColSupplier;
    case "open_quantity":
      return SP_HELP.purchaseOrdersColOpenQty;
    case "delivery":
      return SP_HELP.purchaseOrdersColDelivery;
    case "status":
      return SP_HELP.purchaseOrdersColStatus;
    case "open_value":
      return SP_HELP.purchaseOrdersColOpenValue;
    default:
      return undefined;
  }
}
