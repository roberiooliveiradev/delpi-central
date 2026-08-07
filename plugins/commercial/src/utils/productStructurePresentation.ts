import type { ProductStructureData, ProductStructureNode } from "../types/productionExtras";

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
