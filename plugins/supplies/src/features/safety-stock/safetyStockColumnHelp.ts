import { SP_HELP } from "../../content/helpTooltips";
import type { SafetyStockTableColumnKey } from "./safetyStockTableConfig";

/**
 * Ajuda contextual por cabeçalho (headerHint do DataTable do kit).
 * Textos vivem em SP_HELP — explicam o campo, nunca redefinem cálculo.
 */
export function safetyStockColumnHelp(
  key: SafetyStockTableColumnKey,
): string | undefined {
  switch (key) {
    case "product_code":
      return SP_HELP.safetyStockColProduct;
    case "product_description":
      return SP_HELP.safetyStockColDescription;
    case "branch":
      return SP_HELP.safetyStockColBranch;
    case "product_type":
      return SP_HELP.safetyStockColType;
    case "product_group":
      return SP_HELP.safetyStockColGroup;
    case "unit":
      return SP_HELP.safetyStockColUnit;
    case "safety_stock":
      return SP_HELP.safetyStockSafetyStock;
    case "primary_stock":
      return SP_HELP.safetyStockPrimaryStock;
    case "work_in_process_stock":
      return SP_HELP.safetyStockWorkInProcess;
    case "deficit_quantity":
      return SP_HELP.safetyStockDeficit;
    case "status":
      return SP_HELP.safetyStockStatus;
    default:
      return undefined;
  }
}
