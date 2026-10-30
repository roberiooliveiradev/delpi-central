import { useMemo } from "react";

import type { ProductStructureData } from "../types/productStructure";
import type { RichTreeNode } from "../types/richTree";
import { buildProductStructureTree } from "../utils/productStructureTree";
import { RichTree } from "./RichTree";

type ProductStructureTreeProps = {
  structure: ProductStructureData | null;
  emptyMessage?: string;
  /** Nós com `navCode` viram botões que abrem a ficha do componente. */
  onNodeNavigate?: (node: RichTreeNode) => void;
  footerLabel?: (nodeCount: number) => string;
};

export function ProductStructureTree({
  structure,
  emptyMessage = "Estrutura não disponível para este produto.",
  onNodeNavigate,
  footerLabel = (nodeCount) => `${nodeCount} componente(s) na estrutura`,
}: ProductStructureTreeProps) {
  const root = useMemo(() => buildProductStructureTree(structure), [structure]);

  if (!root) {
    return <p className="lmps-detail__empty">{emptyMessage}</p>;
  }

  return (
    <RichTree
      root={root}
      expandDepth={1}
      footerLabel={footerLabel}
      onNodeNavigate={onNodeNavigate}
    />
  );
}
