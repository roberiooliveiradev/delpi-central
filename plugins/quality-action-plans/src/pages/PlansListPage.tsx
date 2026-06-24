import { useCallback, useEffect, useState } from "react";

import { fetchActionPlans } from "../api/actionPlansApi";
import { AppNav } from "../components/AppNav";
import { PageHeader } from "../components/PageHeader";
import { PlansTable } from "../components/PlansTable";
import { StateAlert } from "../components/StateAlert";
import { PLAN_SEVERITIES, PLAN_STATUSES } from "../constants/actionPlans";
import type { ActionPlanSummary } from "../types/actionPlan";

type Props = {
  onNavigate: (path: string) => void;
};

export function PlansListPage({ onNavigate }: Props) {
  const [items, setItems] = useState<ActionPlanSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState("");
  const [severity, setSeverity] = useState("");
  const [customerName, setCustomerName] = useState("");
  const [productCode, setProductCode] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchActionPlans({
        status: status || undefined,
        severity: severity || undefined,
        customer_name: customerName || undefined,
        product_code: productCode || undefined,
        page_size: 100,
      });
      setItems(data.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao listar planos.");
    } finally {
      setLoading(false);
    }
  }, [customerName, productCode, severity, status]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <>
      <PageHeader
        title="Planos de ação"
        subtitle="Listagem consolidada para acompanhamento da liderança."
      />
      <AppNav active="list" onNavigate={onNavigate} />
      {error ? <StateAlert variant="error">{error}</StateAlert> : null}
      <div className="pac-filters-row">
        <div className="pac-filter-box">
          <label htmlFor="pac-filter-status">Status</label>
          <select
            id="pac-filter-status"
            value={status}
            onChange={(event) => setStatus(event.target.value)}
          >
            <option value="">Todos</option>
            {PLAN_STATUSES.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
        </div>
        <div className="pac-filter-box">
          <label htmlFor="pac-filter-severity">Severidade</label>
          <select
            id="pac-filter-severity"
            value={severity}
            onChange={(event) => setSeverity(event.target.value)}
          >
            <option value="">Todas</option>
            {PLAN_SEVERITIES.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
        </div>
        <div className="pac-filter-box">
          <label htmlFor="pac-filter-customer">Cliente</label>
          <input
            id="pac-filter-customer"
            value={customerName}
            onChange={(event) => setCustomerName(event.target.value)}
            placeholder="Filtrar por cliente"
          />
        </div>
        <div className="pac-filter-box">
          <label htmlFor="pac-filter-product">Produto</label>
          <input
            id="pac-filter-product"
            value={productCode}
            onChange={(event) => setProductCode(event.target.value)}
            placeholder="Código do produto"
          />
        </div>
        <div className="pac-filter-box pac-filter-box--action">
          <span className="pac-filter-box__spacer" aria-hidden />
          <button type="button" className="pac-primary-btn" onClick={() => void load()}>
            Atualizar
          </button>
        </div>
      </div>
      <section className="pac-card">
        <PlansTable items={items} loading={loading} onNavigate={onNavigate} />
      </section>
    </>
  );
}
