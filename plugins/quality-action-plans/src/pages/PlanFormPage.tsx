import { useState } from "react";
import { Save } from "lucide-react";

import { createActionPlan } from "../api/actionPlansApi";
import { PageHeader } from "../components/PageHeader";
import { StateAlert } from "../components/StateAlert";
import {
  detailPath,
  listPath,
  PAC_BRANCH_OPTIONS,
  PLAN_SEVERITIES,
  PLAN_STATUSES,
} from "../constants/actionPlans";
import { emptyPlanFormValues, formValuesToPayload, type PlanFormValues } from "../types/planForm";

type Props = {
  onNavigate: (path: string) => void;
};

export function PlanFormPage({ onNavigate }: Props) {
  const [values, setValues] = useState<PlanFormValues>(emptyPlanFormValues);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function updateField<K extends keyof PlanFormValues>(key: K, value: PlanFormValues[K]) {
    setValues((current) => ({ ...current, [key]: value }));
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);

    try {
      const payload = formValuesToPayload(values);
      if (!payload.title) {
        throw new Error("Informe o título do plano.");
      }
      const plan = await createActionPlan(payload);
      onNavigate(detailPath(plan.id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao criar plano.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <PageHeader
        title="Novo plano de ação"
        subtitle="Registre um problema de qualidade para acompanhamento PAC."
        actions={
          <button type="button" className="pac-ghost-btn" onClick={() => onNavigate(listPath())}>
            Cancelar
          </button>
        }
      />

      <form className="pac-card pac-form" onSubmit={(event) => void handleSubmit(event)}>
        {error ? <StateAlert variant="error">{error}</StateAlert> : null}

        <div className="pac-form-grid">
          <div className="pac-filter-box pac-filter-box--full">
            <label htmlFor="pac-title">Título *</label>
            <input
              id="pac-title"
              value={values.title}
              onChange={(event) => updateField("title", event.target.value)}
              required
            />
          </div>

          <div className="pac-filter-box">
            <label htmlFor="pac-branch">Filial *</label>
            <select
              id="pac-branch"
              value={values.branch_code}
              onChange={(event) => updateField("branch_code", event.target.value)}
            >
              {PAC_BRANCH_OPTIONS.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </div>

          <div className="pac-filter-box">
            <label htmlFor="pac-severity">Severidade</label>
            <select
              id="pac-severity"
              value={values.severity}
              onChange={(event) => updateField("severity", event.target.value)}
            >
              {PLAN_SEVERITIES.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </div>

          <div className="pac-filter-box">
            <label htmlFor="pac-status">Status inicial</label>
            <select
              id="pac-status"
              value={values.status}
              onChange={(event) => updateField("status", event.target.value)}
            >
              {PLAN_STATUSES.filter((item) => item.value === "draft" || item.value === "triage").map(
                (item) => (
                  <option key={item.value} value={item.value}>
                    {item.label}
                  </option>
                ),
              )}
            </select>
          </div>

          <div className="pac-filter-box">
            <label htmlFor="pac-customer">Cliente</label>
            <input
              id="pac-customer"
              value={values.customer_name}
              onChange={(event) => updateField("customer_name", event.target.value)}
            />
          </div>

          <div className="pac-filter-box">
            <label htmlFor="pac-product">Produto</label>
            <input
              id="pac-product"
              value={values.product_code}
              onChange={(event) => updateField("product_code", event.target.value)}
            />
          </div>

          <div className="pac-filter-box">
            <label htmlFor="pac-batch">Lote</label>
            <input
              id="pac-batch"
              value={values.batch_number}
              onChange={(event) => updateField("batch_number", event.target.value)}
            />
          </div>

          <div className="pac-filter-box">
            <label htmlFor="pac-department">Área</label>
            <input
              id="pac-department"
              value={values.department}
              onChange={(event) => updateField("department", event.target.value)}
            />
          </div>

          <div className="pac-filter-box">
            <label htmlFor="pac-failure">Modo de falha</label>
            <input
              id="pac-failure"
              value={values.failure_mode}
              onChange={(event) => updateField("failure_mode", event.target.value)}
            />
          </div>

          <div className="pac-filter-box pac-filter-box--full">
            <label htmlFor="pac-problem">Relato do problema</label>
            <textarea
              id="pac-problem"
              rows={4}
              value={values.reported_problem}
              onChange={(event) => updateField("reported_problem", event.target.value)}
            />
          </div>
        </div>

        <div className="pac-form-actions">
          <button type="submit" className="pac-primary-btn" disabled={saving}>
            <Save size={16} aria-hidden="true" />
            {saving ? "Salvando…" : "Criar plano"}
          </button>
        </div>
      </form>
    </>
  );
}
