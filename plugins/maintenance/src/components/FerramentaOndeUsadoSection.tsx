import { useCallback, useEffect, useMemo, useState } from "react";

import { fetchOndeUsado, type OndeUsadoItem } from "../data/api/maintenanceApi";
import { useServerTable } from "../hooks/useServerTable";
import { DataTableSection, type DataTableColumn } from "./data";

type FerramentaOndeUsadoSectionProps = {
  filial: string;
  codigoFerramenta: string;
  getAccessToken?: () => string | undefined;
};

export function FerramentaOndeUsadoSection({
  filial,
  codigoFerramenta,
  getAccessToken,
}: FerramentaOndeUsadoSectionProps) {
  const ondeUsadoTable = useServerTable({ defaultSortKey: "nivel" });
  const [items, setItems] = useState<OndeUsadoItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const columns = useMemo<DataTableColumn<OndeUsadoItem>[]>(
    () => [
      {
        key: "nivel",
        header: "Nível",
        sortable: true,
        sortValue: (item) => item.nivel,
        render: (item) => item.nivel,
        align: "center",
      },
      {
        key: "codigo",
        header: "Código",
        sortable: true,
        sortValue: (item) => item.codigo,
        render: (item) => (
          <span className="dm-datatable__cell-indent" style={{ paddingLeft: `${item.nivel * 12}px` }}>
            {item.codigo}
          </span>
        ),
      },
      {
        key: "descricao",
        header: "Descrição",
        sortable: true,
        sortValue: (item) => item.descricao,
        render: (item) => item.descricao,
      },
      {
        key: "tipo",
        header: "Tipo",
        sortable: true,
        sortValue: (item) => item.tipo,
        render: (item) => item.tipo || "—",
        align: "center",
      },
      {
        key: "unidade",
        header: "Un.",
        sortable: true,
        sortValue: (item) => item.unidade,
        render: (item) => item.unidade || "—",
        align: "center",
      },
      {
        key: "quantidade",
        header: "Quantidade",
        sortable: true,
        sortValue: (item) => item.quantidade,
        render: (item) => item.quantidade.toLocaleString("pt-BR"),
        align: "right",
      },
    ],
    [],
  );

  const loadOndeUsado = useCallback(async () => {
    if (!codigoFerramenta) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchOndeUsado(
        codigoFerramenta,
        filial,
        {
          page: ondeUsadoTable.query.page,
          pageSize: ondeUsadoTable.query.pageSize,
          sortKey: ondeUsadoTable.query.sortKey,
          sortDirection: ondeUsadoTable.query.sortDirection,
        },
        getAccessToken,
      );
      setItems(data.items ?? []);
      setTotal(data.total ?? 0);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar onde é usado.");
      setItems([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [codigoFerramenta, filial, getAccessToken, ondeUsadoTable.query]);

  useEffect(() => {
    ondeUsadoTable.resetPage();
  }, [codigoFerramenta, ondeUsadoTable.resetPage]);

  useEffect(() => {
    void loadOndeUsado();
  }, [loadOndeUsado]);

  return (
    <>
      {error ? <p className="dm-inline-error">{error}</p> : null}
      <DataTableSection
        columnPreferencesKey="maintenance:FerramentaOndeUsadoSection:onde-usado:v1"
        title="Onde é usado"
        titleHint="Produtos pai (PA/PI) que utilizam esta ferramenta na estrutura vigente."
        countBadgeLabel="produto(s)"
        columns={columns}
        rows={items}
        loading={loading}
        emptyMessage="Esta ferramenta não aparece como componente de nenhum produto na BOM."
        getRowKey={(item, index) => `${item.codigo}-${item.nivel}-${index}`}
        serverTable={{
          page: ondeUsadoTable.query.page,
          pageSize: ondeUsadoTable.query.pageSize,
          total,
          onPageChange: ondeUsadoTable.setPage,
          sortKey: ondeUsadoTable.query.sortKey,
          sortDirection: ondeUsadoTable.query.sortDirection,
          onSortChange: ondeUsadoTable.handleSortChange,
        }}
      />
    </>
  );
}
