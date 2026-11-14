/** Card único de solicitação PRC — reutilizado em Cards e Kanban.
 * Renderiza os mesmos campos da tabela (mesmos `render` do catálogo),
 * respeitando ordem/visibilidade. Identidade (Nº) permanece acessível.
 * Não executa workflow; só abre o detalhe interno. */

import type { DataTableColumn } from "../../lmps/components/dataTableUi";
import { EngineeringInteractiveDataCard } from "../../../ui/engineeringUi";
import type { PrcRequestSummary } from "../api/productRegistrationApi";
import { PRC_COPY, prcShortId } from "../prcCopy";
import {
  prcQueueCardFieldTone,
  type PrcQueueFieldKey,
  isPrcQueueFieldKey,
} from "../prcQueueFieldCatalog";

/** Identidade (`id`) sempre à frente; demais campos na ordem/visibilidade
 * do menu Colunas. `omitKeys` remove Status no Kanban (já no título). */
export function buildPrcCardColumns(
  allColumns: DataTableColumn<PrcRequestSummary>[],
  visibleColumns: DataTableColumn<PrcRequestSummary>[],
  options?: { omitKeys?: readonly string[] },
): DataTableColumn<PrcRequestSummary>[] {
  const omit = new Set(options?.omitKeys ?? []);
  const idColumn = allColumns.find((column) => column.key === "id");
  const rest = visibleColumns.filter(
    (column) => column.key !== "id" && !omit.has(column.key),
  );
  if (!idColumn || omit.has("id")) return rest;
  return [idColumn, ...rest];
}

export type PrcRequestCardProps = {
  row: PrcRequestSummary;
  columns: DataTableColumn<PrcRequestSummary>[];
  onOpen: (row: PrcRequestSummary) => void;
  className?: string;
};

export function PrcRequestCard({
  row,
  columns,
  onOpen,
  className,
}: PrcRequestCardProps) {
  return (
    <EngineeringInteractiveDataCard
      className={["engineering-prc__request-card", className]
        .filter(Boolean)
        .join(" ")}
      interactive
      ariaLabel={`Solicitação ${prcShortId(row.id)}`}
      onActivate={() => onOpen(row)}
      openHint={PRC_COPY.openRequest}
      fields={columns.map((column) => {
        const key = column.key;
        const tone = isPrcQueueFieldKey(key)
          ? prcQueueCardFieldTone(key as PrcQueueFieldKey)
          : column.key === "id"
            ? "title"
            : "meta";
        return {
          id: column.key,
          label: column.header,
          value: column.render(row),
          valueTone: tone,
          present: true as const,
        };
      })}
    />
  );
}
