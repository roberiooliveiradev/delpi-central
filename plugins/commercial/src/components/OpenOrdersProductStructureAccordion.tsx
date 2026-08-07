import { SectionCard } from "@delpi/plugin-ui/index";
import { useMemo } from "react";

import {
  cmSectionCardClassNames,
  cmSectionLabels,
} from "../app/commercialUi";
import { CM_HELP } from "../content/helpTooltips";
import type { ProductStructureData } from "../types/productionExtras";
import { structureRoots } from "../utils/productStructurePresentation";
import { ProductStructureTree } from "./ProductStructureTree";

type OpenOrdersProductStructureAccordionProps = {
  structure: ProductStructureData | null;
  error: string | null;
  productCode: string;
};

export function OpenOrdersProductStructureAccordion({
  structure,
  error,
  productCode,
}: OpenOrdersProductStructureAccordionProps) {
  const roots = useMemo(() => (structure ? structureRoots(structure) : []), [structure]);

  if (error && !structure) {
    return null;
  }
  if (roots.length === 0) {
    return null;
  }

  return (
    <SectionCard
      title="Estrutura do produto"
      hint={CM_HELP.openOrders.detail.bom}
      classNames={cmSectionCardClassNames}
      labels={cmSectionLabels}
      collapsible
      defaultOpen={false}
    >
      <ProductStructureTree nodes={roots} caption={`BOM de ${productCode}`} expandDepth={1} />
    </SectionCard>
  );
}
