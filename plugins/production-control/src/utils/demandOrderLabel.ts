import { copy } from "../content/copy";
import type { DemandLine } from "../types";

/** Linha MyWEG de planejamento (não pedido Protheus). */
export function isMywegDemandLine(line: Pick<DemandLine, "source" | "planning">): boolean {
  return line.source === "myweg" || line.planning === true;
}

/** Rótulo da coluna Pedido na tabela / Excel — sem ID técnico MyWEG. */
export function demandOrderTableLabel(line: Pick<DemandLine, "source" | "planning" | "sales_order" | "line_item">): string {
  if (isMywegDemandLine(line)) {
    return copy.demand.mywegNeedLabel;
  }
  return `${line.sales_order}/${line.line_item}`;
}

/** Identificador técnico MyWEG (record_id) — só detalhe / auditoria. */
export function demandMywegRecordId(line: Pick<DemandLine, "line_item">): string {
  return String(line.line_item || "").trim();
}
