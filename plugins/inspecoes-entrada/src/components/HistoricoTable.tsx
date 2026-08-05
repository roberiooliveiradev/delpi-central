import type { InspecoesEntradaHistoricoItem } from "../types/inspecoesEntradaHistorico";
import { formatDatePt, formatNumber, formatText } from "../utils/format";
import { historicoRowKey } from "../utils/historicoRowKey";
import { resolveResultBadge } from "../utils/resultBadge";
import { DataTable, IE_TABLE, type DataTableColumn } from "./dataTableUi";
import { ResultBadge } from "./ResultBadge";

type HistoricoTableProps = {
  items: InspecoesEntradaHistoricoItem[];
  onViewDetails: (item: InspecoesEntradaHistoricoItem) => void;
};

export function HistoricoTable({ items, onViewDetails }: HistoricoTableProps) {
  const columns: DataTableColumn<InspecoesEntradaHistoricoItem>[] = [
    {
      key: "report_date",
      header: "Data laudo",
      render: (item) => formatDatePt(item.report_date),
    },
    {
      key: "report_time",
      header: "Hora laudo",
      render: (item) => formatText(item.report_time),
    },
    {
      key: "invoice_number",
      header: "NF",
      className: "ie-cell-mono",
      render: (item) => formatText(item.invoice_number),
    },
    {
      key: "supplier_name",
      header: "Fornecedor",
      className: IE_TABLE.colWide,
      render: (item) => formatText(item.supplier_name),
    },
    {
      key: "product_code",
      header: "Produto",
      className: "ie-cell-mono",
      render: (item) => formatText(item.product_code),
    },
    {
      key: "quantity",
      header: "Quantidade",
      align: "right",
      className: IE_TABLE.colNumeric,
      render: (item) => formatNumber(item.quantity),
    },
    {
      key: "unit",
      header: "UM",
      render: (item) => formatText(item.unit),
    },
    {
      key: "result",
      header: "Resultado",
      render: (item) => <ResultBadge badge={resolveResultBadge(item.result)} />,
    },
    {
      key: "inspector_name",
      header: "Ensaiador",
      render: (item) => formatText(item.inspector_name),
    },
    {
      key: "tests_count",
      header: "Ensaios",
      align: "right",
      className: IE_TABLE.colNumeric,
      render: (item) => formatNumber(item.tests_count),
    },
    {
      key: "failed_tests_count",
      header: "Reprovados",
      align: "right",
      className: IE_TABLE.colNumeric,
      render: (item) => formatNumber(item.failed_tests_count),
    },
    {
      key: "actions",
      header: "",
      className: IE_TABLE.colActions,
      interactive: true,
      render: (item) => (
        <div className={IE_TABLE.actions}>
          <button
            type="button"
            className="ie-btn ie-btn--ghost ie-btn--sm"
            onClick={() => onViewDetails(item)}
          >
            Ver detalhes
          </button>
        </div>
      ),
    },
  ];

  return (
    <DataTable
      columns={columns}
      rows={items}
      rowKey={(item, index) => historicoRowKey(item, index)}
      layout="section"
      emptyMessage="Nenhuma inspeção encontrada para os filtros selecionados."
    />
  );
}
