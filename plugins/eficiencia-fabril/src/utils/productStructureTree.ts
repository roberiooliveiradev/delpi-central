import type { ProductStructureData, ProductStructureNode } from "../types/productionOeeDetail";
import type { RichTreeNode } from "../types/richTree";
import { formatDecimal } from "./format";

function readNodeField(node: ProductStructureNode, ...keys: string[]): string {
  for (const key of keys) {
    const value = node[key as keyof ProductStructureNode];
    if (value == null || value === "") continue;
    return String(value);
  }
  return "";
}

function readNodeQuantity(node: ProductStructureNode): number | null {
  const value = node.quantity;
  if (value == null || Number.isNaN(Number(value))) return null;
  return Number(value);
}

function formatStructureMeta(node: ProductStructureNode): string {
  const quantity = readNodeQuantity(node);
  const unit = readNodeField(node, "unit", "B1_UM") || "un.";

  if (quantity == null) return "";
  return `${formatDecimal(quantity)} ${unit}`.trim();
}

function mapRootNode(
  root: ProductStructureNode,
  items: ProductStructureNode[]
): RichTreeNode {
  const code = readNodeField(root, "code", "product_code", "B1_COD") || "—";

  return {
    id: `root-${code}`,
    label: code,
    subtitle: readNodeField(root, "description", "B1_DESC") || undefined,
    badge: readNodeField(root, "type", "B1_TIPO") || undefined,
    metaCaption: formatStructureMeta(root) || undefined,
    children: items.map((item, index) =>
      mapStructureNode(item, index, `root-${code}`)
    ),
  };
}

function mapStructureNode(
  node: ProductStructureNode,
  index: number,
  parentKey: string
): RichTreeNode {
  const code = readNodeField(node, "code", "product_code", "B1_COD") || "—";
  const description = readNodeField(node, "description", "B1_DESC");
  const type = readNodeField(node, "type", "B1_TIPO");
  const children = node.components ?? node.items ?? [];

  return {
    id: `${parentKey}-${code}-${index}`,
    label: code,
    subtitle: description || undefined,
    badge: type || undefined,
    metaCaption: formatStructureMeta(node) || undefined,
    children: children.map((child, childIndex) =>
      mapStructureNode(child, childIndex, `${parentKey}-${code}`)
    ),
  };
}

export function buildProductStructureTree(
  structure: ProductStructureData | null | undefined
): RichTreeNode | null {
  if (!structure) return null;

  const items = structure.items ?? [];

  if (structure.root) {
    return mapRootNode(structure.root, items);
  }

  if (items.length === 0) return null;

  if (items.length === 1) {
    return mapStructureNode(items[0], 0, "item");
  }

  return {
    id: "structure-root",
    label: "Componentes",
    subtitle: `${items.length} itens de primeiro nível`,
    children: items.map((item, index) => mapStructureNode(item, index, "item")),
  };
}

export function countRichTreeNodes(node: RichTreeNode): number {
  const children = node.children ?? [];
  return 1 + children.reduce((total, child) => total + countRichTreeNodes(child), 0);
}
