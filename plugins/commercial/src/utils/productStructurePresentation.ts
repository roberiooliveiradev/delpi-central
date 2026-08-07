import type { ProductStructureData, ProductStructureNode } from "../types/productionExtras";

export type StructureTypeBadgeVariant = "neutral" | "info" | "success" | "warning" | "danger";

export function hasRenderableProductStructure(
  structure: ProductStructureData | null | undefined,
): boolean {
  if (!structure) return false;
  if (structure.root) return true;
  return (structure.items?.length ?? 0) > 0;
}

export function structureRoots(structure: ProductStructureData): ProductStructureNode[] {
  if (structure.root) {
    return [
      {
        ...structure.root,
        components: structure.items ?? structure.root.components ?? [],
      },
    ];
  }
  return structure.items ?? [];
}

export function structureNodeCode(node: ProductStructureNode): string {
  return String(node.code || node.product_code || "—").trim() || "—";
}

export function structureNodeChildren(node: ProductStructureNode): ProductStructureNode[] {
  return node.components ?? node.items ?? [];
}

export function structureNodeTypeLabel(node: ProductStructureNode): string | null {
  const type = String(node.type ?? "").trim().toUpperCase();
  return type || null;
}

/** Variante do StatusBadge do kit por tipo TOTVS (PA / PI / MP). */
export function structureNodeTypeBadgeVariant(type: string | null): StructureTypeBadgeVariant {
  const normalized = (type ?? "").trim().toUpperCase();
  if (normalized === "PA") return "info";
  if (normalized === "PI") return "warning";
  if (normalized === "MP") return "neutral";
  return "neutral";
}

export function countStructureNodes(nodes: ProductStructureNode[]): number {
  return nodes.reduce((total, node) => {
    return total + 1 + countStructureNodes(structureNodeChildren(node));
  }, 0);
}
