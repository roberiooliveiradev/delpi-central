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
  loading?: boolean;
};

export function OpenOrdersProductStructureAccordion({
  structure,
  error,
  productCode,
  loading = false,
}: OpenOrdersProductStructureAccordionProps) {
  const roots = useMemo(() => (structure ? structureRoots(structure) : []), [structure]);

  if (loading && !structure && !error) {
    return (
      <SectionCard
        title="Estrutura do produto"
        hint={CM_HELP.openOrders.detail.bom}
        classNames={cmSectionCardClassNames}
        labels={cmSectionLabels}
        collapsible
        defaultOpen={false}
      >
        <p className="cm-open-orders-detail__muted">Carregando BOM…</p>
      </SectionCard>
    );
  }

  if (error && !structure) {
    return (
      <SectionCard
        title="Estrutura do produto"
        hint={CM_HELP.openOrders.detail.bom}
        classNames={cmSectionCardClassNames}
        labels={cmSectionLabels}
        collapsible
        defaultOpen
      >
        <p role="alert">{error}</p>
      </SectionCard>
    );
  }

  if (roots.length === 0) {
    return (
      <SectionCard
        title="Estrutura do produto"
        hint={CM_HELP.openOrders.detail.bom}
        classNames={cmSectionCardClassNames}
        labels={cmSectionLabels}
        collapsible
        defaultOpen={false}
      >
        <p className="cm-open-orders-detail__muted">
          Nenhuma estrutura (BOM) disponível para {productCode || "este produto"}.
        </p>
      </SectionCard>
    );
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
