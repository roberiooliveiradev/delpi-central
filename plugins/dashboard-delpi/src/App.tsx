// src/App.tsx

import { useMemo, useState } from "react";
import { DelpiApi } from "./data/delpiApi";
import { useProductsDashboard } from "./hooks/useProductsDashboard";
import { ProductsTable } from "./components/ProductTable";
import { Modal } from "./components/Modal";

interface Props {
  token: string;
}

function App({ token }: Props) {
  const api = useMemo(() => new DelpiApi(token), [token]);

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
  } = useProductsDashboard(api);

  const [selectedProduct, setSelectedProduct] = useState<any>(null);
  const [loadingProduct, setLoadingProduct] = useState(false);

  const handleRowClick = async (code: string) => {
    try {
      setLoadingProduct(true);
      const res = await api.getProduct(code);
      setSelectedProduct(res.data.produto);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingProduct(false);
    }
  };

  return (
    <div style={{ padding: 24 }}>
      <h1>Dashboard DELPI</h1>

      <ProductsTable
        products={products}
        page={page}
        totalPages={totalPages}
        total={total}
        pageSize={pageSize}
        loading={loading}
        setPage={setPage}
        setPageSize={setPageSize}
        filters={filters}
        setFilters={setFilters}
        onRowClick={handleRowClick}
      />

      <Modal
        open={!!selectedProduct || loadingProduct}
        title="Detalhes do Produto"
        size="md"
        onClose={() => setSelectedProduct(null)}
      >
        {loadingProduct ? (
          <div>Carregando produto...</div>
        ) : selectedProduct ? (
          <div style={{ display: "grid", gap: 12 }}>
            <div>
              <strong>Código:</strong> {selectedProduct.code}
            </div>

            <div>
              <strong>Descrição:</strong> {selectedProduct.description}
            </div>

            <div>
              <strong>Grupo:</strong> {selectedProduct.group_code}
            </div>

            {selectedProduct.type && (
              <div>
                <strong>Tipo:</strong> {selectedProduct.type}
              </div>
            )}

            {selectedProduct.unit && (
              <div>
                <strong>Unidade:</strong> {selectedProduct.unit}
              </div>
            )}
          </div>
        ) : null}
      </Modal>
    </div>
  );
}

export default App;