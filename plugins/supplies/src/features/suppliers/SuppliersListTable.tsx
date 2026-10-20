import { useMemo } from "react";

import { SuppliesSupplierIdentity } from "../../app/SuppliesDirectoryIdentity";
import {
  SuppliesCompactPagination,
  SuppliesDataTable,
  SuppliesStatusBadge,
  type DataTableColumn,
} from "../../app/suppliesUi";
import { SP_HELP } from "../../content/helpTooltips";
import { formatTaxIdMasked } from "./query";
import {
  SUPPLIERS_PAGE_SIZE_OPTIONS,
  type SupplierListItem,
  type SuppliersQuery,
} from "./types";

type SuppliersListTableProps = {
  items: SupplierListItem[];
  query: SuppliersQuery;
  total: number;
  totalPages: number;
  onPatchQuery: (patch: Partial<SuppliersQuery>) => void;
  onSelectRow: (item: SupplierListItem) => void;
};

export function SuppliersListTable({
  items,
  query,
  total,
  totalPages,
  onPatchQuery,
  onSelectRow,
}: SuppliersListTableProps) {
  const columns = useMemo<DataTableColumn<SupplierListItem>[]>(
    () => [
      {
        key: "supplier",
        header: "Fornecedor",
        headerHint: SP_HELP.suppliersColSupplier,
        render: (item) => (
          <SuppliesSupplierIdentity
            name={item.supplier_name}
            code={item.supplier_id}
            store={item.supplier_store}
          />
        ),
      },
      {
        key: "tax_id",
        header: "Documento",
        headerHint: SP_HELP.suppliersColTaxId,
        render: (item) => formatTaxIdMasked(item.tax_id, item.tax_id_masked),
      },
      {
        key: "supplier_short_name",
        header: "Nome fantasia",
        render: (item) => item.supplier_short_name || "—",
      },
      {
        key: "state",
        header: "UF",
        render: (item) => item.state || "—",
      },
      {
        key: "blocked",
        header: "Situação",
        headerHint: SP_HELP.suppliersColBlocked,
        render: (item) => (
          <SuppliesStatusBadge
            variant={item.blocked ? "danger" : "success"}
            label={item.blocked ? "Bloqueado" : "Ativo"}
          />
        ),
      },
    ],
    [],
  );

  return (
    <div className="sp-suppliers__table-stack">
      <SuppliesDataTable<SupplierListItem>
        columns={columns}
        rows={items}
        rowKey={(item) => item.supplier_id}
        onRowClick={onSelectRow}
        layout="section"
      />
      <SuppliesCompactPagination
        page={query.page}
        pageSize={query.page_size}
        total={total}
        totalPages={totalPages}
        pageSizeOptions={SUPPLIERS_PAGE_SIZE_OPTIONS}
        onPageChange={(page) => onPatchQuery({ page })}
        onPageSizeChange={(pageSize) =>
          onPatchQuery({ page_size: pageSize, page: 1 })
        }
      />
    </div>
  );
}
