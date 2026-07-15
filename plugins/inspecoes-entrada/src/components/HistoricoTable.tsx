import { dataTableBemClasses } from "@delpi/plugin-ui/index";
import type { InspecoesEntradaHistoricoItem } from "../types/inspecoesEntradaHistorico";
import { formatDatePt, formatNumber, formatText } from "../utils/format";
import { resolveResultBadge } from "../utils/resultBadge";
import { ResultBadge } from "./ResultBadge";

const IE_TABLE = dataTableBemClasses("ie");

type HistoricoTableProps = {
  items: InspecoesEntradaHistoricoItem[];
  onViewDetails: (item: InspecoesEntradaHistoricoItem) => void;
};

export function HistoricoTable({ items, onViewDetails }: HistoricoTableProps) {
  return (
    <div className={IE_TABLE.wrap}>
      <table className="ie-table">
        <thead>
          <tr>
            <th>Data laudo</th>
            <th>Hora laudo</th>
            <th>NF</th>
            <th>Fornecedor</th>
            <th>Produto</th>
            <th>Quantidade</th>
            <th>UM</th>
            <th>Resultado</th>
            <th>Ensaiador</th>
            <th>Ensaios</th>
            <th>Reprovados</th>
            <th aria-label="Ações" />
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.inspection_id}>
              <td>{formatDatePt(item.report_date)}</td>
              <td>{formatText(item.report_time)}</td>
              <td className="ie-cell-mono">{formatText(item.invoice_number)}</td>
              <td>{formatText(item.supplier_name)}</td>
              <td className="ie-cell-mono">{formatText(item.product_code)}</td>
              <td>{formatNumber(item.quantity)}</td>
              <td>{formatText(item.unit)}</td>
              <td>
                <ResultBadge badge={resolveResultBadge(item.result)} />
              </td>
              <td>{formatText(item.inspector_name)}</td>
              <td>{formatNumber(item.tests_count)}</td>
              <td>{formatNumber(item.failed_tests_count)}</td>
              <td className="ie-table__actions">
                <button
                  type="button"
                  className="ie-btn ie-btn--ghost ie-btn--sm"
                  onClick={() => onViewDetails(item)}
                >
                  Ver detalhes
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
