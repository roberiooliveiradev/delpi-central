import type { ProductStructureNode } from "../types/production";

export type FlatProductStructureRow = {
  key: string;
  level: number;
  code: string;
  description: string;
  type: string;
  quantity: number | null;
};

function readNodeField(node: ProductStructureNode, ...keys: string[]): string {
  for (const key of keys) {
    const value = node[key];
    if (value == null || value === "") continue;
    return String(value);
  }
  return "—";
}

function readNodeQuantity(node: ProductStructureNode): number | null {
  const value = node.quantity;
  if (value == null || Number.isNaN(Number(value))) return null;
  return Number(value);
}

function walkNodes(
  nodes: ProductStructureNode[],
  level: number,
  rows: FlatProductStructureRow[]
) {
  nodes.forEach((node, index) => {
    const code = readNodeField(node, "code", "product_code", "B1_COD");
    rows.push({
      key: `${level}-${code}-${index}`,
      level,
      code,
      description: readNodeField(node, "description", "B1_DESC"),
      type: readNodeField(node, "type", "B1_TIPO"),
      quantity: readNodeQuantity(node),
    });

    const children = node.components ?? node.items ?? [];
    if (children.length > 0) {
      walkNodes(children, level + 1, rows);
    }
  });
}

export function flattenProductStructure(
  root?: ProductStructureNode | null,
  items: ProductStructureNode[] = []
): FlatProductStructureRow[] {
  const rows: FlatProductStructureRow[] = [];

  if (root) {
    rows.push({
      key: "root",
      level: 0,
      code: readNodeField(root, "code", "product_code", "B1_COD"),
      description: readNodeField(root, "description", "B1_DESC"),
      type: readNodeField(root, "type", "B1_TIPO"),
      quantity: readNodeQuantity(root),
    });
  }

  walkNodes(items, root ? 1 : 0, rows);
  return rows;
}
