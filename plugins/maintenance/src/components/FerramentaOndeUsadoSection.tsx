import { useCallback, useEffect, useMemo, useState } from "react";

import { DM_HELP } from "../content/helpTooltips";
import { MAINTENANCE_LIST_LAYOUT_KEYS } from "../content/listLayoutKeys";
import { OndeUsadoListCard } from "./listCards/MaintenanceListCards";
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
        headerHint: DM_HELP.miniAplicadores.ondeUsadoNivel,
        sortable: true,
        sortValue: (item) => item.nivel,
        render: (item) => item.nivel,
        align: "center",
      },
      {
        key: "codigo",
        header: "Código",
        headerHint: DM_HELP.miniAplicadores.ondeUsadoCodigo,
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
        headerHint: DM_HELP.miniAplicadores.ondeUsadoDescricao,
        sortable: true,
        sortValue: (item) => item.descricao,
        render: (item) => item.descricao,
      },
      {
        key: "tipo",
        header: "Tipo",
        headerHint: DM_HELP.miniAplicadores.ondeUsadoTipo,
        sortable: true,
        sortValue: (item) => item.tipo,
        render: (item) => item.tipo || "—",
        align: "center",
      },
      {
        key: "unidade",
        header: "Un.",
        headerHint: DM_HELP.miniAplicadores.ondeUsadoUnidade,
        sortable: true,
        sortValue: (item) => item.unidade,
        render: (item) => item.unidade || "—",
        align: "center",
      },
      {
        key: "quantidade",
        header: "Quantidade",
        headerHint: DM_HELP.miniAplicadores.ondeUsadoQuantidade,
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
        titleHint={DM_HELP.miniAplicadores.ondeUsado}
        countBadgeLabel="produto(s)"
        columns={columns}
        rows={items}
        loading={loading}
        emptyMessage="Esta ferramenta não aparece como componente de nenhum produto na BOM."
        getRowKey={(item, index) => `${item.codigo}-${item.nivel}-${index}`}
        viewLayoutPreferencesKey={MAINTENANCE_LIST_LAYOUT_KEYS.ondeUsado}
        renderCard={(item) => <OndeUsadoListCard item={item} />}
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
