import type {
  IntermediateProductionOrderRow,
  ProductStructureData,
  ProductStructureNode,
  ProductionOrderDetail,
} from "../types/production";

function readNodeCode(node: ProductStructureNode): string {
  const value = node.code ?? node.product_code ?? node.B1_COD;
  return value == null ? "" : String(value).trim();
}

function walkStructureLevels(
  nodes: ProductStructureNode[],
  level: number,
  index: Map<string, number>
) {
  for (const node of nodes) {
    const code = readNodeCode(node);
    if (code && !index.has(code)) {
      index.set(code, level);
    }

    const children = node.components ?? node.items ?? [];
    if (children.length > 0) {
      walkStructureLevels(children, level + 1, index);
    }
  }
}

export function buildStructureLevelIndex(
  structure: ProductStructureData | null | undefined
): Map<string, number> {
  const index = new Map<string, number>();

  if (!structure) return index;

  if (structure.root) {
    const rootCode = readNodeCode(structure.root);
    if (rootCode) index.set(rootCode, 0);
  }

  const startLevel = structure.root ? 1 : 0;
  walkStructureLevels(structure.items ?? [], startLevel, index);
  return index;
}

export function mapLinkedOrdersToIntermediateRows(
  orders: ProductionOrderDetail[] = [],
  structure?: ProductStructureData | null
): IntermediateProductionOrderRow[] {
  const levelByCode = buildStructureLevelIndex(structure);

  return orders.map((order) => ({
    key: `${order.branch}-${order.production_order}-${order.product_code}`,
    level: levelByCode.get(order.product_code) ?? 1,
    product_code: order.product_code,
    description: order.product_description,
    product_type: order.product_type,
    branch: order.branch,
    production_order: order.production_order,
    order_number: order.order_number,
    order_item: order.order_item,
    due_date: order.due_date,
    finish_date: order.finish_date,
    days_diff: order.days_diff,
    otd_status: order.otd_status,
    planned_qty: order.planned_qty,
    produced_qty: order.produced_qty,
    production_started: (order.produced_qty ?? 0) > 0 || Boolean(order.finish_date),
  }));
}

export function summarizeIntermediateOtd(
  rows: IntermediateProductionOrderRow[]
): {
  total: number;
  on_time: number;
  late: number;
  open: number;
} {
  return rows.reduce(
    (summary, row) => {
      summary.total += 1;
      if (row.otd_status === "on_time") summary.on_time += 1;
      if (row.otd_status === "late") summary.late += 1;
      if (row.otd_status === "open") summary.open += 1;
      return summary;
    },
    { total: 0, on_time: 0, late: 0, open: 0 }
  );
}
