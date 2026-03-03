// src/components/ProductsTable.tsx

import { DataTable, type DataTableColumn } from "./DataTable";
import type { Product } from "../data/delpiApi";

interface Props {
  products: Product[];
  page: number;
  totalPages: number;
  total: number;
  pageSize: number;
  loading?: boolean;
  setPage: (p: number) => void;
  setPageSize: (n: number) => void;
  filters: {
    code: string;
    description: string;
  };
  setFilters: React.Dispatch<
    React.SetStateAction<{
      code: string;
      description: string;
    }>
  >;
  onRowClick: (code: string) => void;
}

export const ProductsTable: React.FC<Props> = ({
  products,
  page,
  totalPages,
  total,
  pageSize,
  loading,
  setPage,
  setPageSize,
  filters,
  setFilters,
  onRowClick,
}) => {
  const columns: DataTableColumn<Product>[] = [
    { key: "code", header: "Código" },
    { key: "description", header: "Descrição" },
    { key: "group_code", header: "Grupo" },
  ];

  return (
    <DataTable<Product>
      columns={columns}
      data={products}
      loading={loading}
      pagination={{
        page,
        totalPages,
        total,
        pageSize,
      }}
      pageSizeOptions={[10, 20, 50, 100]}
      onPageChange={(p) => setPage(p)}
      onPageSizeChange={(size) => {
        setPageSize(size);
        setPage(1);
      }}
      searchValue={filters.description}
      onSearchChange={(value) => {
        setFilters((prev) => ({
          ...prev,
          description: value,
        }));
        setPage(1);
      }}
      toolbar={
        <input
          placeholder="Buscar por código..."
          value={filters.code}
          onChange={(e) => {
            setFilters((prev) => ({
              ...prev,
              code: e.target.value,
            }));
            setPage(1);
          }}
        />
      }
      getRowId={(row) => row.code}
      actions={(row) => (
        <button onClick={() => onRowClick(row.code)}>
          Detalhes
        </button>
      )}
    />
  );
};