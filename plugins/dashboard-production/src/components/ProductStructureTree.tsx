import { useMemo } from "react";

import type { ProductStructureData } from "../types/production";
import { buildProductStructureTree } from "../utils/productStructureTree";
import { RichTree } from "./RichTree";
import { STATE_BOX_EMPTY } from "../ui/stateChrome";

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
    return <div className={STATE_BOX_EMPTY}>{emptyMessage}</div>;
  }

  return (
    <RichTree
      root={root}
      expandDepth={1}
      footerLabel={(nodeCount) => `${nodeCount} componente(s) na estrutura`}
    />
  );
}
