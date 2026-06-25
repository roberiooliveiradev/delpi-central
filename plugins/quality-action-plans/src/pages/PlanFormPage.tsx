import { useState } from "react";
import { Save } from "lucide-react";

import { createActionPlan, upsertRnc8dReport } from "../api/actionPlansApi";
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
  PAC_SOURCE_TYPES,
  PLAN_SEVERITIES,
  PLAN_STATUSES,
} from "../constants/actionPlans";
import { emptyPlanFormValues, formValuesToPayload, type PlanFormValues } from "../types/planForm";
import { emptyRnc8dPayload } from "../types/rnc8d";

const CUSTOMER_TEMPLATE_OPTIONS = [
  { value: "generic", label: "Padrão PAC" },
  { value: "rnc_8d", label: "Relatório 8D (materiais adquiridos)" },
];

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
      if (values.customer_template === "rnc_8d") {
        await upsertRnc8dReport(plan.id, {
          client_nc_registry: values.client_nc_registry.trim() || undefined,
          customer_name: values.customer_name.trim() || undefined,
          product_code: values.product_code.trim() || undefined,
          batch_number: values.batch_number.trim() || undefined,
          reported_problem: values.reported_problem.trim() || undefined,
          template_payload: emptyRnc8dPayload(),
        });
      }
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
              onChange={(nonconformity_scope) =>
                setValues((current) => ({
                  ...current,
                  nonconformity_scope,
                  customer_template:
                    nonconformity_scope === "internal" ? "generic" : current.customer_template,
                }))
              }
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
            <SelectField
              id="pac-template"
              label="Template do relatório"
              options={
                values.nonconformity_scope === "internal"
                  ? CUSTOMER_TEMPLATE_OPTIONS.filter((item) => item.value === "generic")
                  : CUSTOMER_TEMPLATE_OPTIONS
              }
              value={values.customer_template}
              onChange={(customer_template) => updateField("customer_template", customer_template)}
              searchable={false}
            />
            {values.customer_template === "rnc_8d" ? (
              <TextField
                id="pac-nc-registry"
                label="Registro NC do cliente"
                value={values.client_nc_registry}
                onChange={(client_nc_registry) => updateField("client_nc_registry", client_nc_registry)}
              />
            ) : null}
          </div>
        </SectionCard>

        <SectionCard title="Origem do relato">
          <div className="pac-form-grid">
            <SelectField
              id="pac-source-type"
              label="Canal (source_type)"
              options={[{ value: "", label: "Não informado" }, ...PAC_SOURCE_TYPES.map((item) => ({ value: item.value, label: item.label }))]}
              value={values.source_type}
              onChange={(source_type) => updateField("source_type", source_type)}
              searchable
            />
            <TextField
              id="pac-source-reference"
              label="Referência do canal"
              value={values.source_reference}
              onChange={(source_reference) => updateField("source_reference", source_reference)}
              placeholder="ID do e-mail, nome do arquivo, ticket…"
              fullWidth
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
            />
            <TextField
              id="pac-problem-category"
              label="Categoria do problema"
              value={values.problem_category}
              onChange={(problem_category) => updateField("problem_category", problem_category)}
            />
            <TextField
              id="pac-symptom-tags"
              label="Tags de sintoma"
              value={values.symptom_tags_text}
              onChange={(symptom_tags_text) => updateField("symptom_tags_text", symptom_tags_text)}
              placeholder="oxidacao, trinca, dimensional"
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
