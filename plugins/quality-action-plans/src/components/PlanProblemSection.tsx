import type { ReactNode } from "react";
import { Search } from "lucide-react";
import { useCallback, useState } from "react";

import {
  searchDelpiProducts,
  type DelpiProductLookupItem,
} from "../api/delpiLookupApi";
import { CreatableMultiSelectField } from "./ui/CreatableMultiSelectField";
import { DelpiAsyncLookupField } from "./ui/DelpiAsyncLookupField";
import { DelpiCustomerSearchModal } from "./ui/DelpiCustomerSearchModal";
import { FormActions } from "./ui/FormActions";
import { SectionSaveButton } from "./ui/SectionSaveButton";
import { ReadOnlyField } from "./ui/ReadOnlyField";
import { SelectField } from "./ui/SelectField";
import { TextAreaField } from "./ui/TextAreaField";
import { TextField } from "./ui/TextField";
import {
  PAC_BRANCH_OPTIONS,
  PAC_NONCONFORMITY_SCOPES,
  PAC_SOURCE_TYPES,
  PLAN_SEVERITIES,
} from "../constants/actionPlans";
import { RNC8D_SHARED_FIELD_LABELS } from "../constants/rnc8dSharedFields";
import { PAC_HELP_TOOLTIPS } from "../content/helpTooltips";
import { serializeTaggedList } from "../utils/taggedList";

export type PlanIdentificationFormState = {
  title: string;
  customer_code: string;
  customer_store: string;
  customer_name: string;
  product_code: string;
  product_description: string;
  batch_number: string;
  department: string;
  failure_modes: string[];
  problem_categories: string[];
  symptom_tags: string[];
  reported_problem: string;
  severity: string;
  branch_code: string;
  nonconformity_scope: string;
  client_nc_registry: string;
  source_type: string;
  source_reference: string;
};

type PlanProblemSectionProps = {
  showRnc8dFlow: boolean;
  identificationForm: PlanIdentificationFormState;
  onIdentificationChange: (
    updater: (current: PlanIdentificationFormState) => PlanIdentificationFormState,
  ) => void;
  saving: string | null;
  onSaveIdentification: () => void;
  dirtyIdentification?: boolean;
  identificationSaveKey?: string;
  materialSection?: ReactNode;
};

function formatProductLabel(item: DelpiProductLookupItem): string {
  return item.description ? `${item.code} — ${item.description}` : item.code;
}

export function PlanProblemSection({
  showRnc8dFlow,
  identificationForm,
  onIdentificationChange,
  saving,
  onSaveIdentification,
  dirtyIdentification = false,
  identificationSaveKey = "identification",
  materialSection,
}: PlanProblemSectionProps) {
  const [customerSearchOpen, setCustomerSearchOpen] = useState(false);

  const searchProducts = useCallback(async (query: string, signal: AbortSignal) => {
    const looksLikeCode = /^[0-9A-Za-z./-]+$/.test(query.trim());
    const items = await searchDelpiProducts(
      looksLikeCode ? { code: query, signal } : { description: query, signal },
    );
    return items.map((item) => ({
      value: item.code,
      label: formatProductLabel(item),
      meta: { code: item.code, description: item.description },
    }));
  }, []);

  const setField = <K extends keyof PlanIdentificationFormState>(
    key: K,
    value: PlanIdentificationFormState[K],
  ) => {
    onIdentificationChange((current) => ({ ...current, [key]: value }));
  };

  return (
    <>
      <h3 className="pac-subsection-title">Identificação geral</h3>
      <div className="pac-form-grid">
        <TextField
          id="pac-detail-title"
          label="Título"
          hint={PAC_HELP_TOOLTIPS.detail.title}
          value={identificationForm.title}
          onChange={(title) => setField("title", title)}
          fullWidth
        />
        <SelectField
          id="pac-detail-branch"
          label="Filial"
          hint={PAC_HELP_TOOLTIPS.filters.branch}
          options={PAC_BRANCH_OPTIONS.map((item) => ({ value: item.value, label: item.label }))}
          value={identificationForm.branch_code}
          onChange={(branch_code) => setField("branch_code", branch_code)}
          searchable={false}
        />
        <SelectField
          id="pac-detail-scope"
          label="Escopo NC"
          hint={PAC_HELP_TOOLTIPS.filters.scope}
          options={PAC_NONCONFORMITY_SCOPES.map((item) => ({
            value: item.value,
            label: item.label,
          }))}
          value={identificationForm.nonconformity_scope}
          onChange={(nonconformity_scope) => setField("nonconformity_scope", nonconformity_scope)}
          searchable={false}
        />
        <SelectField
          id="pac-detail-severity"
          label="Severidade"
          hint={PAC_HELP_TOOLTIPS.filters.severity}
          options={PLAN_SEVERITIES.map((item) => ({ value: item.value, label: item.label }))}
          value={identificationForm.severity}
          onChange={(severity) => setField("severity", severity)}
          searchable
        />
      </div>

      <h3 className="pac-subsection-title">Cliente</h3>
      <div className="pac-customer-section">
        <div className="pac-customer-section__toolbar">
          <button
            type="button"
            className="pac-ghost-btn"
            onClick={() => setCustomerSearchOpen(true)}
          >
            <Search size={16} aria-hidden="true" />
            Pesquisar cliente na Delpi
          </button>
          {identificationForm.customer_code ||
          identificationForm.customer_store ||
          identificationForm.customer_name ? (
            <button
              type="button"
              className="pac-ghost-btn pac-ghost-btn--danger"
              onClick={() =>
                onIdentificationChange((current) => ({
                  ...current,
                  customer_code: "",
                  customer_store: "",
                  customer_name: "",
                }))
              }
            >
              Limpar cliente
            </button>
          ) : null}
        </div>
        <div className="pac-form-grid">
          <ReadOnlyField
            id="pac-detail-customer-code"
            label="Código do cliente (Delpi)"
            hint={PAC_HELP_TOOLTIPS.detail.customer}
            value={identificationForm.customer_code}
            appearance="field"
          />
          <ReadOnlyField
            id="pac-detail-customer-store"
            label="Loja"
            value={identificationForm.customer_store}
            appearance="field"
          />
          <TextField
            id="pac-detail-customer-name"
            label="Nome do cliente"
            hint={PAC_HELP_TOOLTIPS.detail.customer}
            value={identificationForm.customer_name}
            onChange={(customer_name) => setField("customer_name", customer_name)}
          />
        </div>
      </div>

      <DelpiCustomerSearchModal
        open={customerSearchOpen}
        onClose={() => setCustomerSearchOpen(false)}
        initialFilters={{
          code: identificationForm.customer_code,
          store: identificationForm.customer_store,
          name: identificationForm.customer_name,
        }}
        onSelect={(customer) => {
          onIdentificationChange((current) => ({
            ...current,
            customer_code: customer.code,
            customer_store: customer.store,
            customer_name: customer.name,
          }));
        }}
      />

      <h3 className="pac-subsection-title">Material</h3>
      <div className="pac-form-grid">
        <DelpiAsyncLookupField
          id="pac-detail-product"
          label={
            showRnc8dFlow ? RNC8D_SHARED_FIELD_LABELS.productCode : "Código produto"
          }
          hint={PAC_HELP_TOOLTIPS.detail.productCode}
          value={identificationForm.product_code}
          onChange={(product_code) => setField("product_code", product_code)}
          searchOptions={searchProducts}
          onSelect={(option) => {
            onIdentificationChange((current) => ({
              ...current,
              product_code: option.meta?.code ?? option.value,
              product_description: option.meta?.description ?? current.product_description,
            }));
          }}
        />
        <TextField
          id="pac-detail-product-desc"
          label={
            showRnc8dFlow
              ? RNC8D_SHARED_FIELD_LABELS.productDescription
              : "Descrição produto"
          }
          hint={PAC_HELP_TOOLTIPS.detail.productDescription}
          value={identificationForm.product_description}
          onChange={(product_description) => setField("product_description", product_description)}
        />
        <TextField
          id="pac-detail-batch"
          label={showRnc8dFlow ? RNC8D_SHARED_FIELD_LABELS.supplierBatch : "Lote"}
          hint={PAC_HELP_TOOLTIPS.detail.supplierBatch}
          value={identificationForm.batch_number}
          onChange={(batch_number) => setField("batch_number", batch_number)}
        />
        <TextField
          id="pac-detail-department"
          label="Área"
          hint={PAC_HELP_TOOLTIPS.detail.department}
          value={identificationForm.department}
          onChange={(department) => setField("department", department)}
        />
      </div>

      <h3 className="pac-subsection-title">Classificação do problema</h3>
      <div className="pac-form-grid">
        <CreatableMultiSelectField
          id="pac-detail-failure"
          label="Modo de falha"
          hint={PAC_HELP_TOOLTIPS.detail.failureMode}
          selectedValues={identificationForm.failure_modes}
          onChange={(failure_modes) => setField("failure_modes", failure_modes)}
          emptyLabel="Adicionar modos de falha…"
        />
        <CreatableMultiSelectField
          id="pac-detail-problem-category"
          label="Categoria do problema"
          hint={PAC_HELP_TOOLTIPS.detail.problemCategory}
          selectedValues={identificationForm.problem_categories}
          onChange={(problem_categories) => setField("problem_categories", problem_categories)}
          emptyLabel="Adicionar categorias…"
        />
        <CreatableMultiSelectField
          id="pac-detail-symptom-tags"
          label="Tags de sintoma"
          hint={PAC_HELP_TOOLTIPS.detail.symptomTags}
          selectedValues={identificationForm.symptom_tags}
          onChange={(symptom_tags) => setField("symptom_tags", symptom_tags)}
          emptyLabel="Adicionar tags…"
        />
      </div>

      <h3 className="pac-subsection-title">Origem e registro</h3>
      <div className="pac-form-grid">
        <SelectField
          id="pac-detail-source-type"
          label="Canal (source_type)"
          hint={PAC_HELP_TOOLTIPS.form.source}
          options={[
            { value: "", label: "Não informado" },
            ...PAC_SOURCE_TYPES.map((item) => ({ value: item.value, label: item.label })),
          ]}
          value={identificationForm.source_type}
          onChange={(source_type) => setField("source_type", source_type)}
          searchable
        />
        <TextField
          id="pac-detail-source-reference"
          label="Referência do canal"
          hint={PAC_HELP_TOOLTIPS.detail.sourceReference}
          value={identificationForm.source_reference}
          onChange={(source_reference) => setField("source_reference", source_reference)}
        />
        {showRnc8dFlow ? (
          <TextField
            id="pac-detail-nc-registry"
            label={RNC8D_SHARED_FIELD_LABELS.clientNcRegistry}
            hint={PAC_HELP_TOOLTIPS.detail.clientNcRegistry}
            value={identificationForm.client_nc_registry}
            onChange={(client_nc_registry) => setField("client_nc_registry", client_nc_registry)}
          />
        ) : null}
      </div>

      {materialSection}

      <TextAreaField
        id="pac-detail-problem"
        label={RNC8D_SHARED_FIELD_LABELS.reportedProblem}
        hint={PAC_HELP_TOOLTIPS.form.description}
        value={identificationForm.reported_problem}
        onChange={(reported_problem) => setField("reported_problem", reported_problem)}
        fullWidth
      />
      <FormActions align="end">
        <SectionSaveButton
          saveKey={identificationSaveKey}
          saving={saving}
          onSave={onSaveIdentification}
          dirty={dirtyIdentification}
          label={
            showRnc8dFlow ? "Salvar problema e cabeçalho 8D" : "Salvar identificação"
          }
        />
      </FormActions>
    </>
  );
}

// Utilitário de payload compartilhado com PlanFormPage.
// eslint-disable-next-line react-refresh/only-export-components
export function buildIdentificationUpdatePayload(form: PlanIdentificationFormState) {
  return {
    title: form.title.trim() || undefined,
    customer_code: form.customer_code.trim() || undefined,
    customer_store: form.customer_store.trim() || undefined,
    customer_name: form.customer_name.trim() || undefined,
    product_code: form.product_code.trim() || undefined,
    product_description: form.product_description.trim() || undefined,
    batch_number: form.batch_number.trim() || undefined,
    department: form.department.trim() || undefined,
    failure_mode: serializeTaggedList(form.failure_modes),
    problem_category: serializeTaggedList(form.problem_categories),
    symptom_tags: form.symptom_tags.length ? form.symptom_tags : undefined,
    reported_problem: form.reported_problem.trim() || undefined,
    severity: form.severity,
    branch_code: form.branch_code,
    nonconformity_scope: form.nonconformity_scope,
    client_nc_registry: form.client_nc_registry.trim() || undefined,
    source_type: form.source_type.trim() || undefined,
    source_reference: form.source_reference.trim() || undefined,
  };
}
