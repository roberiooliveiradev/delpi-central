// src/components/ProductsTable.tsx

import { DataTable } from "./DataTable"
import type { Product } from "../data/delpiApi"

type Props = {
  products: Product[]
  loading: boolean
  page: number
  totalPages: number
  total: number
  pageSize: number

  filters: {
    code?: string
    group?: string
    description?: string
  }

  setFilters: (f: any) => void

  setPage: (p: number) => void
  setPageSize: (n: number) => void

  sort?: {
    sort?: string
    direction?: "asc" | "desc"
  }

  setSort?: (s: any) => void

  onRowClick: (code: string) => void
}

export function ProductsTable({
  products,
  loading,
  page,
  totalPages,
  total,
  pageSize,
  filters,
  setFilters,
  setPage,
  setPageSize,
  sort,
  setSort,
  onRowClick
}: Props) {

  const columns = [
    {
      key: "code",
      header: "Código",
      sortable: true
    },
    {
      key: "description",
      header: "Descrição",
      sortable: true
    },
    {
      key: "group_code",
      header: "Grupo",
      sortable: true
    }
  ]

  return (
    <div>

      {/* 🔎 FILTROS */}

      <div style={{
        display: "flex",
        gap: 12,
        marginBottom: 12
      }}>

        <input
          placeholder="Código"
          value={filters.code ?? ""}
          onChange={(e) =>
            setFilters({
              ...filters,
              code: e.target.value
            })
          }
        />

        <input
          placeholder="Descrição"
          value={filters.description ?? ""}
          onChange={(e) =>
            setFilters({
              ...filters,
              description: e.target.value
            })
          }
        />

        <input
          placeholder="Grupo"
          value={filters.group ?? ""}
          onChange={(e) =>
            setFilters({
              ...filters,
              group: e.target.value
            })
          }
        />

      </div>

      <DataTable<Product>
        columns={columns}
        data={products}
        loading={loading}

        sort={sort}
        onSortChange={(s) => {
          setSort?.(s)
        }}

        pagination={{
          page,
          totalPages,
          total,
          pageSize
        }}

        onPageChange={setPage}
        onPageSizeChange={setPageSize}

        getRowId={(p) => p.code}

        actions={(row) => (
          <button onClick={() => onRowClick(row.code)}>
            Ver
          </button>
        )}
      />

    </div>
  )
}