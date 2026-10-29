import { useMemo } from "react";

import type { ProductStructureData } from "../types/productStructure";
import { buildProductStructureTree } from "../utils/productStructureTree";
import { RichTree } from "./RichTree";

type ProductStructureTreeProps = {
  structure: ProductStructureData | null;
  emptyMessage?: string;
};

export function ProductStructureTree({
  structure,
  emptyMessage = "Estrutura não disponível para este produto.",
}: ProductStructureTreeProps) {
  const root = useMemo(() => buildProductStructureTree(structure), [structure]);

  if (!root) {
    return <p className="lmps-detail__empty">{emptyMessage}</p>;
  }

  return (
    <RichTree
      root={root}
      expandDepth={1}
      footerLabel={(nodeCount) => `${nodeCount} componente(s) na estrutura`}
    />
  );
}
