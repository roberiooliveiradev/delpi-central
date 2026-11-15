/** Card de produto acompanhado — modo Cards da listagem U1.
 * Renderiza os mesmos campos da tabela (mesmos `render` do catálogo),
 * respeitando ordem/visibilidade. Identidade (código oficial)
 * permanece acessível mesmo quando oculta nas preferências.
 * Somente leitura — abre a ficha técnica do produto. */

import type { DataTableColumn } from "../../lmps/components/dataTableUi";
import { EngineeringInteractiveDataCard } from "../../../ui/engineeringUi";
import type { PrcProductSummary } from "../api/productRegistrationApi";
import { PRC_PRODUCTS_COPY } from "../prcCopy";
import {
  isPrcProductFieldKey,
  prcProductCardFieldTone,
} from "../prcProductsFieldCatalog";

/** Código oficial sempre à frente; demais campos na ordem/visibilidade
 * do menu Colunas. */
export function buildPrcProductCardColumns(
  allColumns: DataTableColumn<PrcProductSummary>[],
  visibleColumns: DataTableColumn<PrcProductSummary>[],
): DataTableColumn<PrcProductSummary>[] {
  const codeColumn = allColumns.find(
    (column) => column.key === "officialCode",
  );
  const rest = visibleColumns.filter(
    (column) => column.key !== "officialCode",
  );
  if (!codeColumn) return rest;
  return [codeColumn, ...rest];
}

export type PrcProductCardProps = {
  row: PrcProductSummary;
  columns: DataTableColumn<PrcProductSummary>[];
  onOpen: (row: PrcProductSummary) => void;
  className?: string;
};

export function PrcProductCard({
  row,
  columns,
  onOpen,
  className,
}: PrcProductCardProps) {
  return (
    <EngineeringInteractiveDataCard
      className={["engineering-prc__request-card", className]
        .filter(Boolean)
        .join(" ")}
      interactive
      ariaLabel={`Produto ${row.officialCode}`}
      onActivate={() => onOpen(row)}
      openHint={PRC_PRODUCTS_COPY.openProduct}
      fields={columns.map((column) => ({
        id: column.key,
        label: column.header,
        value: column.render(row),
        valueTone: isPrcProductFieldKey(column.key)
          ? prcProductCardFieldTone(column.key)
          : "meta",
        present: true as const,
      }))}
    />
  );
}
