import { useEffect, useMemo, useState } from "react";

import { getProductStructure } from "../api/productApi";
import type { CommercialProduct } from "../types/commercial";
import type { ProductStructureData } from "../types/productStructure";
import { hasRenderableProductStructure } from "../utils/productStructureTree";

export type CommercialProductStructureEntry = {
  product: CommercialProduct;
  structure: ProductStructureData;
};

export function useCommercialProductStructures(
  products: CommercialProduct[] | undefined
) {
  const productCodes = useMemo(() => {
    const seen = new Set<string>();
    const entries: CommercialProduct[] = [];

    for (const product of products ?? []) {
      const code = product.code?.trim();
      if (!code || seen.has(code)) continue;
      seen.add(code);
      entries.push(product);
    }

    return entries;
  }, [products]);

  const codesKey = productCodes.map((product) => product.code).join("|");

  const [structuresByCode, setStructuresByCode] = useState<
    Record<string, ProductStructureData | null>
  >({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (productCodes.length === 0) {
      setStructuresByCode({});
      setLoading(false);
      return;
    }

    const controller = new AbortController();

    async function loadStructures() {
      setLoading(true);

      const results = await Promise.allSettled(
        productCodes.map(async (product) => {
          const code = product.code.trim();
          const structure = await getProductStructure(code, controller.signal);
          return { code, structure };
        })
      );

      if (controller.signal.aborted) return;

      const next: Record<string, ProductStructureData | null> = {};
      for (const result of results) {
        if (result.status !== "fulfilled") continue;
        next[result.value.code] = result.value.structure;
      }

      setStructuresByCode(next);
      setLoading(false);
    }

    void loadStructures();

    return () => controller.abort();
  }, [codesKey]);

  const entries = useMemo(() => {
    return productCodes.flatMap((product) => {
      const structure = structuresByCode[product.code.trim()];
      if (!structure || !hasRenderableProductStructure(structure)) return [];

      return [{ product, structure }];
    });
  }, [productCodes, structuresByCode]);

  return {
    loading,
    entries,
    hasAny: entries.length > 0,
    shouldRender: loading || entries.length > 0,
  };
}
