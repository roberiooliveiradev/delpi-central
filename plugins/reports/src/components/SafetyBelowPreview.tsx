import { useCallback, useEffect, useState } from "react";
import { AlertTriangle, CheckCircle2, PackageSearch, RefreshCw } from "lucide-react";

import { previewSafetyStockBelow } from "../api/reportsApi";
import type { SafetyBelowPreviewData } from "../types/reports";
import { formatBranchUnitLabel } from "../utils/format";

type Props = { branch: string };
const STATUS: Record<string, { label: string; status: string }> = {
  sufficient: { label: "Atende em quantidade", status: "success" },
  partial: { label: "Cobertura parcial", status: "warning" },
  none: { label: "Não atende", status: "danger" },
};

function quantity(value: number, unit: string): string {
  return new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 4 }).format(value)
    + (unit ? " " + unit : "");
}

function dateLabel(value: string | null): string {
  if (!value) return "Sem data";
  const parsed = /^(\d{4})-(\d{2})-(\d{2})/.exec(value);
  return parsed ? [parsed[3], parsed[2], parsed[1]].join("/") : value;
}

export function SafetyBelowPreview({ branch }: Props) {
  const [data, setData] = useState<SafetyBelowPreviewData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [revision, setRevision] = useState(0);
  const reload = useCallback(() => setRevision((value) => value + 1), []);

  useEffect(() => {
    const controller = new AbortController();
    async function fetchData() {
      setLoading(true);
      setError("");
      try {
        const result = await previewSafetyStockBelow(branch, controller.signal);
        if (!controller.signal.aborted) setData(result);
      } catch (reason) {
        if (!controller.signal.aborted) {
          setData(null);
          setError(reason instanceof Error ? reason.message : "Erro no relatório.");
        }
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }
    if (branch === "01" || branch === "02") void fetchData();
    return () => controller.abort();
  }, [branch, revision]);

  const stats = [
    { label: "Em alerta", value: data?.meta.alertCount ?? 0, icon: PackageSearch },
    { label: "Sem cobertura", value: data?.meta.uncoveredCount ?? 0, icon: AlertTriangle },
    { label: "Cobertura parcial", value: data?.meta.partialCount ?? 0, icon: AlertTriangle },
    { label: "Cobertos em quantidade", value: data?.meta.coveredCount ?? 0, icon: CheckCircle2 },
  ];

  return (
    <section className="rp-card rp-safety-preview">
      <div className="rp-card__header">
        <div>
          <p className="rp-safety-preview__eyebrow">Pré-visualização · GLPI #1178</p>
          <h2 className="rp-card__title">Estoque abaixo da segurança</h2>
          <p className="rp-card__hint">
            {formatBranchUnitLabel(branch)} · saldo 01 + 98 + 99 · abaixo do
            estoque de segurança. O relatório por e-mail usa a mesma base.
          </p>
        </div>
        <button type="button" className="rp-btn rp-btn--secondary"
          onClick={reload} disabled={loading}>
          <RefreshCw size={16} aria-hidden="true" />
          {loading ? "Consultando…" : "Atualizar"}
        </button>
      </div>

      {error ? <p role="alert" className="rp-banner rp-banner--error">{error}</p> : null}
      <div className="rp-safety-preview__stats">
        {stats.map(({ label, value, icon: Icon }) => (
          <div className="rp-safety-preview__stat" key={label}>
            <Icon size={17} aria-hidden="true" />
            <span>{label}</span>
            <strong>{loading && !data ? "…" : value}</strong>
          </div>
        ))}
      </div>

      <p className="rp-safety-preview__legend">
        A indicação de atendimento compara <strong>quantidades</strong> após pedidos elegíveis.
        Entrega vencida ou sem data não é garantia de recebimento.
        Pedidos em outros armazéns ou com unidade incompatível são informativos.
      </p>

      <div className="rp-safety-preview__scroll">
        <table className="rp-safety-preview__table">
          <thead><tr>
            <th>Produto</th><th>Saldo</th><th>Segurança</th><th>Déficit</th>
            <th>Pedidos em aberto</th><th>Cobertura</th>
          </tr></thead>
          <tbody>
            {(data?.items ?? []).map((item) => {
              const status = STATUS[item.coverage_status] || STATUS.none;
              return (
                <tr key={item.branch + ":" + item.product_code}>
                  <td><strong>{item.product_code}</strong>
                    <small>{item.product_description}</small>
                  </td>
                  <td className="rp-safety-preview__numeric">
                    {quantity(item.available_stock, item.unit)}
                  </td>
                  <td className="rp-safety-preview__numeric">
                    {quantity(item.safety_stock, item.unit)}
                  </td>
                  <td className="rp-safety-preview__numeric">
                    <strong>{quantity(item.deficit_quantity, item.unit)}</strong>
                  </td>
                  <td>
                    {item.purchase_orders.length ? (
                      <div className="rp-safety-preview__orders">
                        {item.purchase_orders.map((order, i) => (
                          <div key={order.order_number + ":" + order.order_item + ":" + i}>
                            <strong>PC {order.order_number}/{order.order_item}</strong>
                            <span>Qtd. {quantity(
                              order.open_quantity_primary_unit ?? order.open_quantity,
                              order.coverage_eligible ? item.unit : order.order_unit,
                            )} · {dateLabel(order.expected_delivery_date)}</span>
                            {order.delivery_status === "overdue" ? (
                              <small>Previsão vencida</small>
                            ) : null}
                            {!order.coverage_eligible ? (
                              <small>Não elegível à cobertura</small>
                            ) : null}
                          </div>
                        ))}
                      </div>
                    ) : <span className="rp-muted">Sem pedido</span>}
                  </td>
                  <td>
                    <span className={"rp-safety-preview__badge rp-safety-preview__badge--" + status.status}>
                      {status.label}
                    </span>
                    <small>Saldo + PCs: {quantity(item.projected_stock_after_orders, item.unit)}</small>
                    {item.warnings.map((warning) => (
                      <small className="rp-safety-preview__warning" key={warning}>{warning}</small>
                    ))}
                  </td>
                </tr>
              );
            })}
            {!loading && data && data.items.length === 0 ? (
              <tr><td colSpan={6} className="rp-safety-preview__empty">
                Nenhum produto abaixo do estoque de segurança nesta filial.
              </td></tr>
            ) : null}
            {loading && !data ? (
              <tr><td colSpan={6} className="rp-safety-preview__empty">
                Consultando estoque e pedidos em aberto…
              </td></tr>
            ) : null}
          </tbody>
        </table>
      </div>
      <p className="rp-safety-preview__foot">
        {data ? "Atualizado em " + dateLabel(data.meta.asOfDate) +
          " · " + data.total + " produtos encontrados" : ""}
      </p>
    </section>
  );
}
