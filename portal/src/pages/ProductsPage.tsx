// src/pages/ProductsPage.tsx

import React, { useState } from "react";
import { useProducts } from "../hooks/useProducts";
import { DataTable, type DataTableColumn } from "../components/DataTable";
import type { Product } from "../data/delpiApi";
import { Eye } from "lucide-react";
import { useAppAlert } from "../components/ConfirmDialogProvider";

export const ProductsPage: React.FC = () => {
  const showAlert = useAppAlert();
  // ===============================
  // Estado da tabela (server-side)
  // ===============================

  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);

  const { items, total, totalPages, loading, error } =
    useProducts(page, pageSize);

  // ===============================
  // Colunas
  // ===============================

  const columns: DataTableColumn<Product>[] = [
    {
      key: "code",
      header: "Código",
      sortable: false, // server-side ainda não implementado
      width: 120,
    },
    {
      key: "description",
      header: "Descrição",
      sortable: false,
    },
    {
      key: "sale_price",
      header: "Preço",
      render: (row) =>
        new Intl.NumberFormat("pt-BR", {
          style: "currency",
          currency: "BRL",
        }).format(row.sale_price ?? 0),
    },
  ];

  if (error) {
    return (
      <div style={{ padding: 24, color: "#ef4444" }}>
        Erro ao carregar produtos: {error}
      </div>
    );
  }

  return (
    <div style={{ padding: 24 }}>
      <h1 style={{ marginBottom: 20 }}>Produtos</h1>

      <DataTable<Product>
        columns={columns}
        data={items}
        loading={loading}
        pagination={{
          page,
          totalPages,
          total,
          pageSize,
        }}
        onPageChange={setPage}
        onPageSizeChange={(size) => {
          setPageSize(size);
          setPage(1);
        }}
        actions={(row) => (
          <button
            className="datatable-action-btn"
            onClick={() =>
              void showAlert({
                title: row.description,
                message: `Código ${row.code}`,
              })
            }
          >
            <Eye size={16} />
          </button>
        )}
        emptyText="Nenhum produto encontrado."
      />
    </div>
  );
};