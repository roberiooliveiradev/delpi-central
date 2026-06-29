import type { ReactNode } from "react";
import { Save } from "lucide-react";
import { useCallback, useMemo } from "react";

import {
  searchDelpiCustomers,
  searchDelpiProducts,
  type DelpiCustomerLookupItem,
  type DelpiProductLookupItem,
} from "../api/delpiLookupApi";
import { ScopeBadge, SeverityBadge, StatusBadge } from "./StatusBadge";
import { CreatableMultiSelectField } from "./ui/CreatableMultiSelectField";
import { DelpiAsyncLookupField } from "./ui/DelpiAsyncLookupField";
import { FormActions } from "./ui/FormActions";
import { SelectField } from "./ui/SelectField";
import { TextAreaField } from "./ui/TextAreaField";
import { TextField } from "./ui/TextField";
import {
  branchLabel,
  PAC_BRANCH_OPTIONS,
  PAC_NONCONFORMITY_SCOPES,
  PAC_SOURCE_TYPES,
  PLAN_SEVERITIES,
  PLAN_STATUSES,
} from "../constants/actionPlans";
import { RNC8D_SHARED_FIELD_LABELS } from "../constants/rnc8dSharedFields";
import { PAC_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { PlanStatus } from "../types/actionPlan";
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
  planStatus: PlanStatus;
  planBranchCode?: string | null;
  planScope?: string | null;
  planSeverity?: string | null;
  isTerminalPlan: boolean;
  identificationForm: PlanIdentificationFormState;
  onIdentificationChange: (
    updater: (current: PlanIdentificationFormState) => PlanIdentificationFormState,
  ) => void;
  statusValue: string;
  onStatusChange: (value: string) => void;
  reopenReason: string;
  onReopenReasonChange: (value: string) => void;
  reopenTargetStatus: string;
  onReopenTargetStatusChange: (value: string) => void;
  reopenStatusOptions: { value: string; label: string }[];
  saving: string | null;
  onSaveStatus: () => void;
  onReopen: () => void;
  onSaveIdentification: () => void;
  materialSection?: ReactNode;
};

function formatCustomerLabel(item: DelpiCustomerLookupItem): string {
  const store = item.store ? ` / loja ${item.store}` : "";
  return `${item.code}${store} — ${item.name}`;
}

function formatProductLabel(item: DelpiProductLookupItem): string {
  return item.description ? `${item.code} — ${item.description}` : item.code;
}

export function PlanProblemSection({
  showRnc8dFlow,
  planStatus,
  planBranchCode,
  planScope,
  planSeverity,
  isTerminalPlan,
  identificationForm,
  onIdentificationChange,
  statusValue,
  onStatusChange,
  reopenReason,
  onReopenReasonChange,
  reopenTargetStatus,
  onReopenTargetStatusChange,
  reopenStatusOptions,
  saving,
  onSaveStatus,
  onReopen,
  onSaveIdentification,
  materialSection,
}: PlanProblemSectionProps) {
  const statusOptions = useMemo(
    () => PLAN_STATUSES.map((item) => ({ value: item.value, label: item.label })),
    [],
  );

  const searchCustomers = useCallback(async (query: string, signal: AbortSignal) => {
    const looksLikeCode = /^[0-9A-Za-z./-]+$/.test(query.trim());
    const items = await searchDelpiCustomers(
      looksLikeCode ? { code: query, signal } : { name: query, signal },
    );
    return items.map((item) => ({
      value: item.code,
      label: formatCustomerLabel(item),
      meta: { code: item.code, store: item.store, name: item.name },
    }));
  }, []);

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
      <div className="pac-plan-status-bar">
        <dl className="pac-dl pac-dl--compact">
          <div>
            <dt>Status atual</dt>
            <dd>
              <StatusBadge status={planStatus} />
            </dd>
          </div>
          <div>
            <dt>Filial</dt>
            <dd>{branchLabel(planBranchCode)}</dd>
          </div>
          <div>
            <dt>Escopo</dt>
            <dd>
              <ScopeBadge scope={planScope} />
            </dd>
          </div>
          <div>
            <dt>Severidade</dt>
            <dd>
              <SeverityBadge severity={planSeverity ?? "medium"} />
            </dd>
          </div>
        </dl>
        <div className="pac-inline-form pac-plan-status-bar__actions">
          {isTerminalPlan ? (
            <>
              <TextAreaField
                id="pac-reopen-reason"
                label="Motivo da reabertura"
                hint={PAC_HELP_TOOLTIPS.detail.reopenReason}
                value={reopenReason}
                onChange={onReopenReasonChange}
                placeholder="Descreva por que o plano precisa ser reaberto…"
                rows={3}
                fullWidth
              />
              <SelectField
                id="pac-plan-reopen-status"
                label="Retomar em"
                hint={PAC_HELP_TOOLTIPS.detail.reopenTargetStatus}
                options={reopenStatusOptions}
                value={reopenTargetStatus}
                onChange={onReopenTargetStatusChange}
                searchable={false}
              />
              <button
                type="button"
                className="pac-primary-btn"
                disabled={saving === "reopen" || reopenReason.trim().length < 5}
                onClick={onReopen}
              >
                <Save size={16} />
                {saving === "reopen" ? "Reabrindo…" : "Reabrir plano"}
              </button>
            </>
          ) : (
            <>
              <SelectField
                id="pac-plan-status"
                label="Atualizar status"
                hint={PAC_HELP_TOOLTIPS.detail.updateStatus}
                options={statusOptions}
                value={statusValue}
                onChange={onStatusChange}
                searchable
              />
              <button
                type="button"
                className="pac-primary-btn"
                disabled={saving === "status"}
                onClick={onSaveStatus}
              >
                <Save size={16} />
                {saving === "status" ? "Salvando…" : "Salvar status"}
              </button>
            </>
          )}
        </div>
      </div>

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
      <div className="pac-form-grid">
        <DelpiAsyncLookupField
          id="pac-detail-customer-code"
          label="Código do cliente (Delpi)"
          hint={PAC_HELP_TOOLTIPS.detail.customer}
          value={identificationForm.customer_code}
          onChange={(customer_code) => setField("customer_code", customer_code)}
          searchOptions={searchCustomers}
          onSelect={(option) => {
            onIdentificationChange((current) => ({
              ...current,
              customer_code: option.meta?.code ?? option.value,
              customer_store: option.meta?.store ?? current.customer_store,
              customer_name: option.meta?.name ?? current.customer_name,
            }));
          }}
        />
        <TextField
          id="pac-detail-customer-store"
          label="Loja"
          value={identificationForm.customer_store}
          onChange={(customer_store) => setField("customer_store", customer_store)}
        />
        <TextField
          id="pac-detail-customer-name"
          label="Nome do cliente"
          hint={PAC_HELP_TOOLTIPS.detail.customer}
          value={identificationForm.customer_name}
          onChange={(customer_name) => setField("customer_name", customer_name)}
        />
      </div>

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
        <button
          type="button"
          className="pac-primary-btn"
          disabled={saving === "identification"}
          onClick={onSaveIdentification}
        >
          <Save size={16} />
          {saving === "identification" ? "Salvando…" : "Salvar identificação"}
        </button>
      </FormActions>
    </>
  );
}

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
