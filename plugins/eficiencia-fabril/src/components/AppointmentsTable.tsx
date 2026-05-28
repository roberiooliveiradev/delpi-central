import { FileSpreadsheet } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import type { EficienciaFabrilListFilterParams } from "../api/fetchAllEficienciaFabrilItems";
import { VERIFY_EFFICIENCY_THRESHOLD_PCT } from "../constants/businessRules";
import type { EficienciaFabrilItem } from "../types/eficienciaFabril";
import { formatDisplayDate } from "../utils/dates";
import { exportAppointmentsExcel } from "../utils/exportAppointmentsExcel";
import { formatCurrency, formatNumber, formatPercent } from "../utils/format";

type AppointmentsTableProps = {
  items: EficienciaFabrilItem[];
  page: number;
  totalPages: number;
  total: number;
  listFilterParams: EficienciaFabrilListFilterParams;
  onPageChange: (page: number) => void;
  onExportError?: (message: string) => void;
  disabled?: boolean;
};

export function AppointmentsTable({
  items,
  page,
  totalPages,
  total,
  listFilterParams,
  onPageChange,
  onExportError,
  disabled = false,
}: AppointmentsTableProps) {
  const [exporting, setExporting] = useState(false);
  const exportAbortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    return () => exportAbortRef.current?.abort();
  }, []);

  const handleExportExcel = useCallback(async () => {
    if (exporting || total <= 0) return;

    exportAbortRef.current?.abort();
    const controller = new AbortController();
    exportAbortRef.current = controller;

    setExporting(true);
    try {
      await exportAppointmentsExcel(listFilterParams, controller.signal);
    } catch (err) {
      if (controller.signal.aborted) return;
      const message =
        err instanceof Error ? err.message : "Não foi possível exportar o Excel.";
      onExportError?.(message);
    } finally {
      if (exportAbortRef.current === controller) {
        setExporting(false);
      }
    }
  }, [exporting, listFilterParams, onExportError, total]);

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
                <td colSpan={11} className="ef-table__empty">
                  Nenhum apontamento para os filtros selecionados.
                </td>
              </tr>
            ) : (
              items.map((item, index) => (
                <tr
                  key={`${item.op}-${item.data_producao}-${index}`}
                  className={
                    (item.eficiencia_percentual ?? 0) > VERIFY_EFFICIENCY_THRESHOLD_PCT
                      ? "ef-row ef-row--verify"
                      : "ef-row"
                  }
                >
                  <td>{formatDisplayDate(item.data_producao)}</td>
                  <td>{item.hora_inicio ?? "—"}</td>
                  <td>{item.hora_final ?? "—"}</td>
                  <td>{formatNumber(item.qtd_apontada, 3)}</td>
                  <td>{item.filial ?? "—"}</td>
                  <td>{item.op ?? "—"}</td>
                  <td>{item.centro_trabalho ?? "—"}</td>
                  <td>{item.nome_operador ?? item.login_operador ?? "—"}</td>
                  <td>{formatPercent(item.eficiencia_percentual)}</td>
                  <td>{formatCurrency(item.resultado_mod)}</td>
                  <td>
                    {(item.eficiencia_percentual ?? 0) > VERIFY_EFFICIENCY_THRESHOLD_PCT ? (
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
