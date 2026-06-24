import { useState } from "react";
import { Save } from "lucide-react";

import { createActionPlan } from "../api/actionPlansApi";
import { PageHeader } from "../components/PageHeader";
import { StateAlert } from "../components/StateAlert";
import { FormActions } from "../components/ui/FormActions";
import { SectionCard } from "../components/ui/SectionCard";
import { SelectField } from "../components/ui/SelectField";
import { TextAreaField } from "../components/ui/TextAreaField";
import { TextField } from "../components/ui/TextField";
import {
  detailPath,
  listPath,
  PAC_BRANCH_OPTIONS,
  PAC_NONCONFORMITY_SCOPES,
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

  const initialStatusOptions = PLAN_STATUSES.filter(
    (item) => item.value === "draft" || item.value === "triage",
  ).map((item) => ({ value: item.value, label: item.label }));

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

      <form className="pac-form" onSubmit={(event) => void handleSubmit(event)}>
        {error ? <StateAlert variant="error">{error}</StateAlert> : null}

        <SectionCard title="Identificação">
          <div className="pac-form-grid">
            <TextField
              id="pac-title"
              label="Título"
              value={values.title}
              onChange={(title) => updateField("title", title)}
              required
              fullWidth
            />
            <SelectField
              id="pac-branch"
              label="Filial"
              options={PAC_BRANCH_OPTIONS.map((item) => ({ value: item.value, label: item.label }))}
              value={values.branch_code}
              onChange={(branch_code) => updateField("branch_code", branch_code)}
              required
              searchable={false}
            />
            <SelectField
              id="pac-scope"
              label="Escopo da não conformidade"
              options={PAC_NONCONFORMITY_SCOPES.map((item) => ({ value: item.value, label: item.label }))}
              value={values.nonconformity_scope}
              onChange={(nonconformity_scope) => updateField("nonconformity_scope", nonconformity_scope)}
              searchable={false}
            />
            <SelectField
              id="pac-severity"
              label="Severidade"
              options={PLAN_SEVERITIES.map((item) => ({ value: item.value, label: item.label }))}
              value={values.severity}
              onChange={(severity) => updateField("severity", severity)}
              searchable
            />
            <SelectField
              id="pac-status"
              label="Status inicial"
              options={initialStatusOptions}
              value={values.status}
              onChange={(status) => updateField("status", status)}
              searchable={false}
            />
          </div>
        </SectionCard>

        <SectionCard title="Contexto">
          <div className="pac-form-grid">
            <TextField
              id="pac-customer"
              label="Cliente"
              value={values.customer_name}
              onChange={(customer_name) => updateField("customer_name", customer_name)}
            />
            <TextField
              id="pac-product"
              label="Produto"
              value={values.product_code}
              onChange={(product_code) => updateField("product_code", product_code)}
            />
            <TextField
              id="pac-batch"
              label="Lote"
              value={values.batch_number}
              onChange={(batch_number) => updateField("batch_number", batch_number)}
            />
            <TextField
              id="pac-department"
              label="Área"
              value={values.department}
              onChange={(department) => updateField("department", department)}
            />
            <TextField
              id="pac-failure"
              label="Modo de falha"
              value={values.failure_mode}
              onChange={(failure_mode) => updateField("failure_mode", failure_mode)}
              fullWidth
            />
          </div>
        </SectionCard>

        <SectionCard title="Descrição do problema">
          <TextAreaField
            id="pac-problem"
            label="Relato do problema"
            value={values.reported_problem}
            onChange={(reported_problem) => updateField("reported_problem", reported_problem)}
            fullWidth
          />
        </SectionCard>

        <FormActions align="end">
          <button type="submit" className="pac-primary-btn" disabled={saving}>
            <Save size={16} aria-hidden="true" />
            {saving ? "Salvando…" : "Criar plano"}
          </button>
        </FormActions>
      </form>
    </>
  );
}
