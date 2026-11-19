import { useState } from "react";
import { Download, Factory, Layers3, PackageCheck, SearchX, Truck, ArrowUpRight } from "lucide-react";

import { SectionError } from "./SectionError";
import type {
  PendingSupplierItem,
  PendingSupplierPage,
  ThirdPartyMaterialsQuery,
} from "../types/thirdPartyMaterials";
import type { SectionErrorState } from "../types/api";
import { formatInteger, formatQuantity } from "../utils/formatters";

type Props = {
  data: PendingSupplierPage | null;
  loading: boolean;
  error: SectionErrorState | null;
  onRetry: () => void;
  query: ThirdPartyMaterialsQuery | null;
  page: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onDrillDown: (item: PendingSupplierItem) => void;
  onExport?: (format: "csv" | "xlsx") => Promise<void>;
};

export function PendingSuppliersView({
  data, loading, error, onRetry, query, page, pageSize, onPageChange,
  onDrillDown, onExport,
}: Props) {
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState("");
  const summary = data?.summary;
  const totalPages = Math.max(data?.total_pages ?? 1, 1);

  async function handleExport(format: "csv" | "xlsx") {
    if (!onExport) return;
    setExportError("");
    setExporting(true);
    try {
      await onExport(format);
    } catch (reason) {
      setExportError(reason instanceof Error ? reason.message : "Falha ao exportar o relatório.");
    } finally {
      setExporting(false);
    }
  }

  if (!query) {
    return <section className="mt-pending-shell mt-pending-shell--empty">Selecione uma filial para visualizar as pendências dos fornecedores.</section>;
  }

  return (
    <section className="mt-pending" aria-label="Consolidado de pendências por fornecedor">
      <div className="mt-pending-hero">
        <div>
          <p className="mt-pending-eyebrow">MATERIAIS EM PODER DA DELPI · FORNECEDORES</p>
          <h2>Consolidado de pendências</h2>
          <p className="mt-pending-subtitle">Saldo aberto por fornecedor, loja e produto. Cada remessa é considerada apenas uma vez, mesmo quando há múltiplas devoluções.</p>
        </div>
        <div className="mt-pending-export">
          {onExport ? (
            <>
              <button className="mt-btn mt-btn--secondary" type="button" disabled={exporting || loading || !data?.total} onClick={() => void handleExport("csv")}>
                <Download size={16} aria-hidden="true" /> CSV
              </button>
              <button className="mt-btn mt-btn--primary" type="button" disabled={exporting || loading || !data?.total} onClick={() => void handleExport("xlsx")}>
                <Download size={16} aria-hidden="true" /> {exporting ? "Exportando…" : "Excel"}
              </button>
            </>
          ) : null}
        </div>
      </div>

      <div className="mt-pending-stats">
        <div className="mt-pending-stat"><span className="mt-pending-stat__icon"><Factory size={18} /></span><span>Fornecedores</span><strong>{formatInteger(summary?.supplier_count)}</strong></div>
        <div className="mt-pending-stat"><span className="mt-pending-stat__icon"><Layers3 size={18} /></span><span>Produtos pendentes</span><strong>{formatInteger(summary?.product_count)}</strong></div>
        <div className="mt-pending-stat"><span className="mt-pending-stat__icon"><Truck size={18} /></span><span>Remessas abertas</span><strong>{formatInteger(summary?.shipment_count)}</strong></div>
        <div className="mt-pending-stat"><span className="mt-pending-stat__icon"><PackageCheck size={18} /></span><span>Saldo pendente</span><strong>{summary?.mixed_units ? "Múltiplas UMs" : formatQuantity(summary?.pending_quantity, summary?.unit)}</strong></div>
      </div>

      {error ? <SectionError title={error.title} message={error.message} onRetry={error.retryable ? onRetry : undefined} /> : null}
      {exportError ? <SectionError title="Exportação" message={exportError} /> : null}

      <div className="mt-pending-panel">
        <div className="mt-pending-panel__header">
          <div><h3>Pendências por fornecedor</h3><p>Ordenado pelo saldo aberto, com acesso ao detalhamento das remessas.</p></div>
          <span className="mt-pending-records">{formatInteger(data?.total)} produtos</span>
        </div>
        <div className="mt-pending-table-wrap">
          <table className="mt-pending-table">
            <thead><tr><th>Fornecedor</th><th>Produto</th><th>Remessas</th><th>Recebido</th><th>Devolvido</th><th>Saldo pendente</th><th><span className="mt-pending-sr-only">Detalhar</span></th></tr></thead>
            <tbody>
              {(data?.items ?? []).map((item) => (
                <tr key={item.supplier_code + "|" + item.supplier_store + "|" + item.product_code}>
                  <td><strong>{item.supplier_name || item.supplier_code}</strong><small>{item.supplier_code} / {item.supplier_store}</small></td>
                  <td><strong>{item.product_code}</strong><small>{item.product_description}</small></td>
                  <td className="mt-pending-num">{formatInteger(item.shipment_count)}</td>
                  <td className="mt-pending-num">{formatQuantity(item.received_quantity, item.unit)}</td>
                  <td className="mt-pending-num">{formatQuantity(item.returned_quantity, item.unit)}</td>
                  <td className="mt-pending-num"><span className="mt-pending-balance">{formatQuantity(item.pending_quantity, item.unit)}</span></td>
                  <td><button type="button" className="mt-pending-drill" onClick={() => onDrillDown(item)} aria-label={`Ver remessas do produto ${item.product_code} do fornecedor ${item.supplier_name || item.supplier_code}`} title="Ver remessas"><ArrowUpRight size={18} /></button></td>
                </tr>
              ))}
              {!loading && !error && !data?.items.length ? <tr><td colSpan={7} className="mt-pending-empty"><SearchX size={22} aria-hidden="true" /> Nenhuma pendência de fornecedor encontrada para os filtros selecionados.</td></tr> : null}
              {loading ? <tr><td colSpan={7} className="mt-pending-empty" role="status">Carregando pendências…</td></tr> : null}
            </tbody>
          </table>
        </div>
        <div className="mt-pending-footer">
          <span>Página {page} de {totalPages} · {pageSize} registros por página</span>
          <div className="mt-pending-pages">
            <button type="button" className="mt-btn mt-btn--secondary" disabled={page <= 1 || loading} onClick={() => onPageChange(Math.max(page - 1, 1))}>Anterior</button>
            <button type="button" className="mt-btn mt-btn--secondary" disabled={page >= totalPages || loading} onClick={() => onPageChange(Math.min(page + 1, totalPages))}>Próxima</button>
          </div>
        </div>
      </div>
    </section>
  );
}
