import type { CommercialProductStructureEntry } from "../hooks/useCommercialProductStructures";
import type {
  ProductStructureData,
  ProductStructureNode,
} from "../types/productStructure";
import { formatDecimal } from "../utils/format";
import { parseProductTitle } from "../utils/commercialProductsPresentation";
import type { TableExportPayload } from "./types";

function readNodeField(node: ProductStructureNode, ...keys: string[]): string {
  for (const key of keys) {
    const value = node[key];
    if (value == null || value === "") continue;
    return String(value);
  }

  return "";
}

function formatStructureQuantity(node: ProductStructureNode): string {
  const quantity = node.quantity;
  if (quantity == null || Number.isNaN(Number(quantity))) return "—";

  const unit = readNodeField(node, "unit", "B1_UM") || "un.";
  return `${formatDecimal(Number(quantity))} ${unit}`.trim();
}

function flattenStructureNode(
  node: ProductStructureNode,
  rootProduct: string,
  level: number,
  rows: Record<string, unknown>[],
): void {
  const code = readNodeField(node, "code", "product_code", "B1_COD") || "—";
  const description = readNodeField(node, "description", "B1_DESC") || "—";
  const type = readNodeField(node, "type", "B1_TIPO") || "—";

  rows.push({
    root_product: rootProduct,
    level,
    code,
    description,
    type,
    quantity: formatStructureQuantity(node),
  });

  const children = node.components ?? node.items ?? [];
  children.forEach((child) => {
    flattenStructureNode(child, rootProduct, level + 1, rows);
  });
}

function flattenStructureData(
  rootProduct: string,
  structure: ProductStructureData,
): Record<string, unknown>[] {
  const rows: Record<string, unknown>[] = [];

  if (structure.root) {
    flattenStructureNode(structure.root, rootProduct, 0, rows);
    return rows;
  }

  for (const item of structure.items ?? []) {
    flattenStructureNode(item, rootProduct, 0, rows);
  }

  return rows;
}

export function buildProductStructuresPayload(
  entries: CommercialProductStructureEntry[],
): TableExportPayload {
  const rows = entries.flatMap(({ product, structure }) => {
    const rootProduct = `${product.code} — ${parseProductTitle(product.description)}`;
    return flattenStructureData(rootProduct, structure);
  });

  return {
    title: "Estrutura BOM",
    columns: [
      { key: "root_product", label: "Produto raiz" },
      { key: "level", label: "Nível" },
      { key: "code", label: "Código" },
      { key: "description", label: "Descrição" },
      { key: "type", label: "Tipo" },
      { key: "quantity", label: "Quantidade" },
    ],
    rows,
  };
}
