import { SP_HELP } from "../../content/helpTooltips";
import type { PurchaseRequestTableColumnKey } from "./purchaseRequestsTableConfig";

export function purchaseRequestsColumnHelp(
  key: PurchaseRequestTableColumnKey,
): string | undefined {
  switch (key) {
    case "requester":
      return SP_HELP.purchaseRequestsColRequester;
    case "cost_center":
      return SP_HELP.purchaseRequestsColCc;
    case "opened":
      return SP_HELP.purchaseRequestsColOpened;
    case "stage":
      return SP_HELP.purchaseRequestsColStage;
    default:
      return undefined;
  }
}
