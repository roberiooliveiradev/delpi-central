import { Boxes } from "lucide-react";

import { COMMERCIAL_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { CommercialProductStructureEntry } from "../hooks/useCommercialProductStructures";
import { parseProductTitle } from "../utils/commercialProductsPresentation";
import { DetailCard } from "./DetailCard";
import { ProductStructureTree } from "./ProductStructureTree";
import { StructureLegend } from "./StructureLegend";

type CommercialProductStructuresSectionProps = {
  entries: CommercialProductStructureEntry[];
  loading?: boolean;
  exportActions?: React.ReactNode;
};

export function CommercialProductStructuresSection({
  entries,
  loading = false,
  exportActions,
}: CommercialProductStructuresSectionProps) {
  if (!loading && entries.length === 0) {
    return null;
  }

  return (
    <DetailCard
      title="Estrutura do produto"
      titleHint={COMMERCIAL_HELP_TOOLTIPS.detail.productStructureSection}
      hint="BOM / estrutura analítica com níveis aninhados"
      icon={<Boxes size={20} aria-hidden />}
      className="dc-detail-card--full"
      headerActions={exportActions}
    >
      <StructureLegend />

      {loading && entries.length === 0 ? (
        <p className="dc-detail__empty">Carregando estruturas dos produtos…</p>
      ) : null}

      <div className="dc-product-structure-list">
        {entries.map(({ product, structure }) => (
          <section
            key={product.code}
            className="dc-product-structure-block"
            aria-label={`Estrutura do produto ${product.code}`}
          >
            <header className="dc-product-structure-block__header">
              <h3>{product.code}</h3>
              <p>{parseProductTitle(product.description)}</p>
            </header>
            <ProductStructureTree structure={structure} />
          </section>
        ))}
      </div>
    </DetailCard>
  );
}
