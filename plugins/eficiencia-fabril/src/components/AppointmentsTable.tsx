import { FileSpreadsheet } from "lucide-react";
import { useCallback, useState } from "react";

import { isProductionEfficiencyOutlier } from "../constants/businessRules";
import type { EficienciaFabrilItem } from "../types/eficienciaFabril";
import { formatDisplayDate } from "../utils/dates";
import { exportAppointmentsExcel } from "../utils/exportAppointmentsExcel";
import { formatCurrency, formatNumber, formatPercent } from "../utils/format";

type AppointmentsTableProps = {
  items: EficienciaFabrilItem[];
  exportItems: EficienciaFabrilItem[];
  exportDateStart: string;
  exportDateEnd: string;
  page: number;
  totalPages: number;
  total: number;
  onPageChange: (page: number) => void;
  onExportError?: (message: string) => void;
  disabled?: boolean;
};

export function AppointmentsTable({
  items,
  exportItems,
  exportDateStart,
  exportDateEnd,
  page,
  totalPages,
  total,
  onPageChange,
  onExportError,
  disabled = false,
}: AppointmentsTableProps) {
  const [exporting, setExporting] = useState(false);

  const handleExportExcel = useCallback(async () => {
    if (exporting || total <= 0) return;

    setExporting(true);
    try {
      await exportAppointmentsExcel(exportItems, exportDateStart, exportDateEnd);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Não foi possível exportar o Excel.";
      onExportError?.(message);
    } finally {
      setExporting(false);
    }
  }, [exportDateEnd, exportDateStart, exportItems, exporting, onExportError, total]);

  return (
    <section className="ef-table-card" aria-label="Apontamentos">
      <header className="ef-table-card__header">
        <div>
          <h2>Apontamentos</h2>
          <p>{total.toLocaleString("pt-BR")} registro(s) no período</p>
        </div>
        <div className="ef-table-card__actions">
          <button
            type="button"
            className="ef-btn ef-btn--ghost"
            disabled={disabled || exporting || total <= 0}
            onClick={() => void handleExportExcel()}
            aria-busy={exporting}
          >
            <FileSpreadsheet size={16} aria-hidden />
            {exporting ? "Exportando…" : "Exportar Excel"}
          </button>
          <div className="ef-pagination">
          <button
            type="button"
            className="ef-btn ef-btn--ghost"
            disabled={disabled || page <= 1}
            onClick={() => onPageChange(page - 1)}
          >
            Anterior
          </button>
          <span>
            Página {page} de {Math.max(totalPages, 1)}
          </span>
          <button
            type="button"
            className="ef-btn ef-btn--ghost"
            disabled={disabled || page >= totalPages}
            onClick={() => onPageChange(page + 1)}
          >
            Próxima
          </button>
          </div>
        </div>
      </header>

      <div className="ef-table-wrap">
        <table className="ef-table">
          <thead>
            <tr>
              <th>Data</th>
              <th>Início</th>
              <th>Fim</th>
              <th>Qtd. apontada</th>
              <th>Filial</th>
              <th>OP</th>
              <th>Descrição produto</th>
              <th>CT</th>
              <th>Operador</th>
              <th>Eficiência</th>
              <th>Resultado MOD</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 ? (
              <tr>
                <td colSpan={12} className="ef-table__empty">
                  Nenhum apontamento para os filtros selecionados.
                </td>
              </tr>
            ) : (
              items.map((item, index) => (
                <tr
                  key={`${item.op}-${item.data_producao}-${index}`}
                  className={
                    isProductionEfficiencyOutlier(item.eficiencia_percentual)
                      ? "ef-row ef-row--verify"
                      : "ef-row"
                  }
                >
                  <td data-label="Data">{formatDisplayDate(item.data_producao)}</td>
                  <td data-label="Início">{item.hora_inicio ?? "—"}</td>
                  <td data-label="Fim">{item.hora_final ?? "—"}</td>
                  <td data-label="Qtd. apontada">{formatNumber(item.qtd_apontada, 3)}</td>
                  <td data-label="Filial">{item.filial ?? "—"}</td>
                  <td data-label="OP">{item.op ?? "—"}</td>
                  <td data-label="Descrição produto">
                    {item.descricao_produto?.trim() || item.produto || "—"}
                  </td>
                  <td data-label="CT">{item.centro_trabalho ?? "—"}</td>
                  <td data-label="Operador">
                    {item.nome_operador ?? item.login_operador ?? "—"}
                  </td>
                  <td data-label="Eficiência">{formatPercent(item.eficiencia_percentual)}</td>
                  <td data-label="Resultado MOD">{formatCurrency(item.resultado_mod)}</td>
                  <td data-label="Status">
                    {isProductionEfficiencyOutlier(item.eficiencia_percentual) ? (
                      <span className="ef-badge ef-badge--danger">Verificar</span>
                    ) : (
                      <span className="ef-badge">{item.status_registro ?? "—"}</span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
