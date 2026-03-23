// src/App.tsx
import { useMemo, useState } from "react"
import { DelpiApi } from "./data/delpiApi"
import { useProductsDashboard } from "./hooks/useProductsDashboard"
import { ProductsTable } from "./components/ProductTable"
import { Modal } from "./components/Modal"

interface Props {
  getAccessToken?: () => string | undefined
}

function formatLabel(key: string) {
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, l => l.toUpperCase())
}

function App({ getAccessToken }: Props) {
  const token = getAccessToken?.() ?? ""

  const api = useMemo(() => new DelpiApi(token), [token])

  const {
    products,
    loading,
    page,
    pageSize,
    total,
    totalPages,
    setPage,
    setPageSize,
    filters,
    setFilters,
    sort,
    setSort
  } = useProductsDashboard(api)

  const [selectedProduct, setSelectedProduct] = useState<any>(null)
  const [loadingProduct, setLoadingProduct] = useState(false)

  const handleRowClick = async (code: string) => {
    try {
      setLoadingProduct(true)
      const res = await api.getProduct(code)
      setSelectedProduct(res.data.produto)
    } catch (err) {
      console.error(err)
    } finally {
      setLoadingProduct(false)
    }
  }

  return (
    <div style={{ padding: 24 }}>
      <h1>Dashboard DELPI  - PROVANDO QUE O FRONTEND NÃO ATUALIZA NA PRODUÇÃO! DEMORA HORAS!</h1>

      <ProductsTable
        products={products}
        page={page}
        totalPages={totalPages}
        total={total}
        pageSize={pageSize}
        loading={loading}
        filters={filters}
        setFilters={setFilters}
        sort={sort}
        setSort={setSort}
        setPage={setPage}
        setPageSize={setPageSize}
        onRowClick={handleRowClick}
      />

      <Modal
        open={!!selectedProduct || loadingProduct}
        title="Detalhes do Produto"
        size="lg"
        onClose={() => setSelectedProduct(null)}
      >
        {loadingProduct ? (
          <div>Carregando produto...</div>
        ) : selectedProduct ? (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(2,1fr)",
              gap: 12
            }}
          >
            {Object.entries(selectedProduct)
              .sort(([a], [b]) => a.localeCompare(b))
              .map(([key, value]) => {
                if (value === "" || value === null) return null

                return (
                  <div key={key}>
                    <strong>{formatLabel(key)}:</strong> {String(value)}
                  </div>
                )
              })}
          </div>
        ) : null}
      </Modal>
    </div>
  )
}

export default App