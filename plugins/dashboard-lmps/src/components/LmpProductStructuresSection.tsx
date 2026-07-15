import { Boxes } from "lucide-react";

import { LMPS_HELP_TOOLTIPS } from "../content/helpTooltips";
import { StructureLegend } from "./StructureLegend";
import { DetailCard } from "./DetailCard";
import { ProductStructureTree } from "./ProductStructureTree";
import type { LmpProductStructureEntry } from "../hooks/useLmpProductStructures";

type LmpProductStructuresSectionProps = {
  entries: LmpProductStructureEntry[];
  loading?: boolean;
};

function parseProductTitle(description?: string | null): string {
  const trimmed = description?.trim() ?? "";
  if (!trimmed) return "—";

  const match = trimmed.match(/^(.*)\s+\(([^)]+)\)\s*$/);
  if (!match) return trimmed;

  const title = match[1].trim();
  return title || trimmed;
}

export function LmpProductStructuresSection({
  entries,
  loading = false,
}: LmpProductStructuresSectionProps) {
  if (!loading && entries.length === 0) {
    return null;
  }

  return (
    <DetailCard
      title="Estrutura do produto"
      titleHint={LMPS_HELP_TOOLTIPS.detail.productStructureSection}
      hint="BOM / estrutura analítica com níveis aninhados"
      icon={<Boxes size={20} aria-hidden />}
    >
      <StructureLegend />

      {loading && entries.length === 0 ? (
        <p className="lmps-detail__empty">Carregando estruturas dos produtos…</p>
      ) : null}

      <div className="lmps-product-structure-list">
        {entries.map(({ product, structure }) => (
          <section
            key={product.code}
            className="lmps-product-structure-block"
            aria-label={`Estrutura do produto ${product.code}`}
          >
            <header className="lmps-product-structure-block__header">
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
