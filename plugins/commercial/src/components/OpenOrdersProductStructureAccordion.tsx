import { SectionCard } from "@delpi/plugin-ui/index";
import { useMemo } from "react";

import {
  cmSectionCardClassNames,
  cmSectionLabels,
} from "../app/commercialUi";
import { CM_HELP } from "../content/helpTooltips";
import type { ProductStructureData, ProductStructureNode } from "../types/productionExtras";
import { formatQuantity } from "../utils/format";

type OpenOrdersProductStructureAccordionProps = {
  structure: ProductStructureData | null;
  error: string | null;
  productCode: string;
};

function nodeCode(node: ProductStructureNode): string {
  return String(node.code || node.product_code || "—").trim() || "—";
}

function StructureTree({ nodes, depth = 0 }: { nodes: ProductStructureNode[]; depth?: number }) {
  if (nodes.length === 0) return null;
  return (
    <ul className="cm-open-orders-detail__bom-list" data-depth={depth}>
      {nodes.map((node, index) => {
        const children = node.components ?? node.items ?? [];
        const qty =
          node.quantity != null && !Number.isNaN(Number(node.quantity))
            ? ` × ${formatQuantity(Number(node.quantity))}${node.unit ? ` ${node.unit}` : ""}`
            : "";
        return (
          <li key={`${nodeCode(node)}-${index}`}>
            <span>
              <strong>{nodeCode(node)}</strong>
              {node.type ? ` [${node.type}]` : ""}
              {node.description ? ` — ${node.description}` : ""}
              {qty}
            </span>
            {children.length > 0 ? <StructureTree nodes={children} depth={depth + 1} /> : null}
          </li>
        );
      })}
    </ul>
  );
}

export function OpenOrdersProductStructureAccordion({
  structure,
  error,
  productCode,
}: OpenOrdersProductStructureAccordionProps) {
  const roots = useMemo(() => {
    if (!structure) return [] as ProductStructureNode[];
    if (structure.root) {
      return [
        {
          ...structure.root,
          components: structure.items ?? structure.root.components ?? [],
        },
      ];
    }
    return structure.items ?? [];
  }, [structure]);

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
      <p className="cm-open-orders-detail__muted">BOM de {productCode}</p>
      <StructureTree nodes={roots} />
    </SectionCard>
  );
}
