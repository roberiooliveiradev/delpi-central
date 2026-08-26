import { useCallback, useEffect, useMemo, useState } from "react";
import { createDashboardSegmentToggle } from "@delpi/plugin-ui/index";

import { MaintenanceSectionHintLabel } from "../app/maintenanceUi";
import { DM_HELP } from "../content/helpTooltips";
import { fetchComponentes, type ComponenteItem } from "../data/api/maintenanceApi";
import { useServerTable } from "../hooks/useServerTable";
import { ComponentesEstoqueTree } from "./ComponentesEstoqueTree";
import { ComponenteEstoqueBadges, ComponenteEstoqueCell } from "./ComponenteEstoqueBadges";
import { DataTableSection, type DataTableColumn } from "./dataTableUi";

const DmSegmentToggle = createDashboardSegmentToggle("dm");

type ComponentesView = "table" | "tree";

type ComponentesEstoqueSectionProps = {
  filial: string;
  codigoFerramenta: string;
  getAccessToken?: () => string | undefined;
  estruturaItems?: ComponenteItem[];
};

function buildComponentesColumns(): DataTableColumn<ComponenteItem>[] {
  return [
    {
      key: "nivel",
      header: "Nível",
      headerHint: DM_HELP.miniAplicadores.componentesNivel,
      sortable: true,
      sortValue: (item) => item.nivel,
      render: (item) => item.nivel,
      align: "center",
    },
    {
      key: "codigo",
      header: "Código",
      headerHint: DM_HELP.miniAplicadores.componentesCodigo,
      sortable: true,
      sortValue: (item) => item.codigo,
      render: (item) => (
        <span
          className="dm-datatable__cell-indent"
          style={{ paddingLeft: `${item.nivel * 12}px` }}
        >
          {item.codigo}
        </span>
      ),
    },
    {
      key: "descricao",
      header: "Descrição",
      headerHint: DM_HELP.miniAplicadores.componentesDescricao,
      sortable: true,
      sortValue: (item) => item.descricao,
      render: (item) => item.descricao,
    },
    {
      key: "unidade",
      header: "Un.",
      headerHint: DM_HELP.miniAplicadores.componentesUnidade,
      sortable: true,
      sortValue: (item) => item.unidade,
      render: (item) => item.unidade,
      align: "center",
    },
    {
      key: "estoque01",
      header: "Estoque 01",
      headerHint: DM_HELP.miniAplicadores.estoque01,
      sortable: true,
      sortValue: (item) => item.estoque_local_01,
      render: (item) => <ComponenteEstoqueCell local="01" value={item.estoque_local_01} />,
      align: "right",
    },
    {
      key: "estoque99",
      header: "Estoque 99",
      headerHint: DM_HELP.miniAplicadores.estoque99,
      sortable: true,
      sortValue: (item) => item.estoque_local_99,
      render: (item) => <ComponenteEstoqueCell local="99" value={item.estoque_local_99} />,
      align: "right",
    },
  ];
}

export function ComponentesEstoqueSection({
  filial,
  codigoFerramenta,
  getAccessToken,
  estruturaItems = [],
}: ComponentesEstoqueSectionProps) {
  const [view, setView] = useState<ComponentesView>("table");
  const componentesTable = useServerTable({ defaultSortKey: "nivel" });
  const [componentes, setComponentes] = useState<ComponenteItem[]>([]);
  const [componentesTotal, setComponentesTotal] = useState(0);
  const [componentesLoading, setComponentesLoading] = useState(false);

  const columns = useMemo(() => buildComponentesColumns(), []);

  const loadComponentesTable = useCallback(async () => {
    if (!codigoFerramenta) return;
    setComponentesLoading(true);
    try {
      const data = await fetchComponentes(
        codigoFerramenta,
        filial,
        {
          page: componentesTable.query.page,
          pageSize: componentesTable.query.pageSize,
          sortKey: componentesTable.query.sortKey,
          sortDirection: componentesTable.query.sortDirection,
        },
        getAccessToken,
      );
      setComponentes(data.items ?? []);
      setComponentesTotal(data.total ?? 0);
    } catch {
      setComponentes([]);
      setComponentesTotal(0);
    } finally {
      setComponentesLoading(false);
    }
  }, [codigoFerramenta, componentesTable.query, filial, getAccessToken]);

  useEffect(() => {
    componentesTable.resetPage();
  }, [codigoFerramenta, componentesTable.resetPage]);

  useEffect(() => {
    if (view === "table") {
      void loadComponentesTable();
    }
  }, [loadComponentesTable, view]);

  const viewToggle = (
    <DmSegmentToggle
      ariaLabel="Modo de visualização dos componentes"
      idPrefix="dm-componentes-view"
      value={view}
      onChange={setView}
      options={[
        { value: "table", label: "Tabela" },
        { value: "tree", label: "Árvore" },
      ]}
    />
  );

  if (view === "tree") {
    return (
      <section className="dm-card dm-table-section">
        <div className="dm-section-header">
          <div className="dm-section-header__title-group">
            <h3 className="dm-section-header__title">
              <MaintenanceSectionHintLabel
                label="Componentes e estoque"
                hint={DM_HELP.miniAplicadores.componentesArvore}
              />
            </h3>
          </div>
          <div className="dm-section-header__meta">
            <span className="dm-badge">{estruturaItems.length} item(ns)</span>
            {viewToggle}
          </div>
        </div>
        <ComponentesEstoqueTree items={estruturaItems} />
      </section>
    );
  }

  return (
    <DataTableSection
      columnPreferencesKey="maintenance:ComponentesEstoqueSection:componentes-e-estoque:v1"
      title="Componentes e estoque"
      titleHint={DM_HELP.miniAplicadores.componentesEstoque}
      countBadgeLabel="item(ns)"
      actions={viewToggle}
      columns={columns}
      rows={componentes}
      loading={componentesLoading}
      emptyMessage="Nenhum componente amarrado a esta ferramenta."
      getRowKey={(item, index) => `${item.codigo}-${item.nivel}-${index ?? 0}`}
      serverTable={{
        page: componentesTable.query.page,
        pageSize: componentesTable.query.pageSize,
        total: componentesTotal,
        onPageChange: componentesTable.setPage,
        sortKey: componentesTable.query.sortKey,
        sortDirection: componentesTable.query.sortDirection,
        onSortChange: componentesTable.handleSortChange,
      }}
    />
  );
}
