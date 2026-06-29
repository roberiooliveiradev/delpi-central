import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ArrowLeft,
  Download,
  Save,
} from "lucide-react";

import {
  approveEffectivenessReview,
  exportPlanPdf,
  exportRnc8dPdf,
  exportRnc8dSpreadsheet,
  fetchActionPlanDetail,
  fetchPlanAuditLog,
  promoteSolutionPattern,
  recordEffectivenessReview,
  rejectEffectivenessReview,
  reopenPlan,
  submitEffectivenessReview,
  updateActionPlan,
  updatePlanStatus,
  upsertIshikawa,
  upsertRnc8dReport,
} from "../api/actionPlansApi";
import { EvidencePanel } from "../components/EvidencePanel";
import { FiveWhysFlowPanel } from "../components/FiveWhysFlowPanel";
import { PlanActionsPanel } from "../components/PlanActionsPanel";
import { IshikawaFishboneDiagram } from "../components/IshikawaFishboneDiagram";
import { PlanTimeline } from "../components/PlanTimeline";
import { SimilarCasesPanel } from "../components/SimilarCasesPanel";
import { PageHeader } from "../components/PageHeader";
import { Rnc8dDisciplineProgress } from "../components/Rnc8dDisciplineProgress";
import { formatActorDisplay } from "../utils/actorDisplay";
import {
  Rnc8dClosureSection,
  Rnc8dContainmentSection,
  Rnc8dEffectivenessSection,
  Rnc8dHeaderFields,
  Rnc8dNcDescriptionSection,
  Rnc8dPreventiveSection,
  Rnc8dSaveActions,
  Rnc8dTeamSection,
} from "../components/rnc8d/Rnc8dSections";
import { ScopeBadge, SeverityBadge, StatusBadge } from "../components/StatusBadge";
import { SaveStatusBanner } from "../components/SaveStatusBanner";
import { FormActions } from "../components/ui/FormActions";
import { SectionCard } from "../components/ui/SectionCard";
import { SelectField } from "../components/ui/SelectField";
import { StatusPipeline } from "../components/ui/StatusPipeline";
import { TextAreaField } from "../components/ui/TextAreaField";
import { TextField } from "../components/ui/TextField";
import {
  branchLabel,
  dashboardPath,
  EFFECTIVENESS_STATUSES,
  listPath,
  PAC_BRANCH_OPTIONS,
  PAC_NONCONFORMITY_SCOPES,
  PAC_SOURCE_TYPES,
  PLAN_SEVERITIES,
  PLAN_STATUSES,
} from "../constants/actionPlans";
import { RNC8D_SHARED_FIELD_LABELS } from "../constants/rnc8dSharedFields";
import { PAC_HELP_TOOLTIPS } from "../content/helpTooltips";
import type {
  ActionPlanDetail,
  PlanAuditLogEntry,
} from "../types/actionPlan";
import type { Rnc8dReportPayload } from "../types/rnc8d";
import { emptyRnc8dPayload } from "../types/rnc8d";
import { mergeSharedIdentificationIntoRnc8d, sanitizeRnc8dReportPayload } from "../utils/rnc8dPayload";
import { buildTeamMemberSelectOptions } from "../utils/teamMemberOptions";
import { formatDateTime } from "../utils/format";
import {
  emptyIshikawaCausesForm,
  parseIshikawaCausesForm,
  serializeIshikawaCausesForm,
  type IshikawaCausesForm,
} from "../utils/ishikawaCauses";
import {
  emptyFiveWhysForm,
  parseFiveWhysForm,
  type FiveWhysForm,
} from "../utils/fiveWhys";
import { formatSymptomTags, parseSymptomTags } from "../utils/symptomTags";

type Props = {
  planId: string;
  onNavigate: (path: string) => void;
};

const AUDIT_EVENT_LABELS: Record<string, string> = {
  plan_created: "Plano criado",
  plan_updated: "Identificação atualizada",
  plan_closed: "Plano encerrado",
  plan_reopened: "Plano reaberto",
  effectiveness_submitted: "Eficácia submetida",
  effectiveness_approved: "Eficácia aprovada",
  effectiveness_reviewed: "Eficácia registrada",
  effectiveness_approval_rejected: "Submissão rejeitada",
};

export function PlanDetailPage({ planId, onNavigate }: Props) {
  const [detail, setDetail] = useState<ActionPlanDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [statusValue, setStatusValue] = useState("");
  const [ishikawaCausesForm, setIshikawaCausesForm] = useState<IshikawaCausesForm>(
    emptyIshikawaCausesForm(),
  );
  const [ishikawaNotes, setIshikawaNotes] = useState("");
  const [fiveWhysForm, setFiveWhysForm] = useState<FiveWhysForm>(emptyFiveWhysForm());
  const [rnc8dForm, setRnc8dForm] = useState<Rnc8dReportPayload>({});
  const [effectivenessStatus, setEffectivenessStatus] = useState("pending");
  const [effectivenessNotes, setEffectivenessNotes] = useState("");
  const [effectivenessRejectionReason, setEffectivenessRejectionReason] = useState("");
  const [reopenReason, setReopenReason] = useState("");
  const [reopenTargetStatus, setReopenTargetStatus] = useState("in_progress");
  const [saving, setSaving] = useState<string | null>(null);
  const [auditLog, setAuditLog] = useState<PlanAuditLogEntry[]>([]);
  const [identificationForm, setIdentificationForm] = useState({
    title: "",
    customer_name: "",
    product_code: "",
    product_description: "",
    batch_number: "",
    department: "",
    failure_mode: "",
    problem_category: "",
    symptom_tags_text: "",
    reported_problem: "",
    severity: "medium",
    branch_code: "01",
    nonconformity_scope: "external",
    client_nc_registry: "",
    source_type: "",
    source_reference: "",
  });

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchActionPlanDetail(planId);
      setDetail(data);
      setStatusValue(data.plan.status);
      setReopenTargetStatus(
        data.plan.status === "cancelled" ? "triage" : "in_progress",
      );
      setIshikawaCausesForm(parseIshikawaCausesForm(data.ishikawa));
      setIshikawaNotes(data.ishikawa?.notes ?? "");
      setFiveWhysForm(parseFiveWhysForm(data.five_whys));
      setRnc8dForm({
        client_nc_registry: data.plan.client_nc_registry ?? "",
        customer_name: data.plan.customer_name ?? "",
        customer_contact: data.plan.customer_contact ?? "",
        product_code: data.plan.product_code ?? "",
        product_description: data.plan.product_description ?? "",
        batch_number: data.plan.batch_number ?? "",
        reported_problem: data.plan.reported_problem ?? "",
        template_payload: {
          ...emptyRnc8dPayload(),
          ...(data.plan.template_payload ?? {}),
        },
        team_members: data.team_members?.length
          ? data.team_members
          : [{ member_name: "", department: "", is_leader: true }],
      });
      setEffectivenessStatus(
        data.plan.effectiveness_proposed_status
          ?? data.plan.effectiveness_status
          ?? "pending",
      );
      setEffectivenessNotes(data.plan.effectiveness_notes ?? "");
      setEffectivenessRejectionReason("");
      setIdentificationForm({
        title: data.plan.title ?? "",
        customer_name: data.plan.customer_name ?? "",
        product_code: data.plan.product_code ?? "",
        product_description: data.plan.product_description ?? "",
        batch_number: data.plan.batch_number ?? "",
        department: data.plan.department ?? "",
        failure_mode: data.plan.failure_mode ?? "",
        problem_category: data.plan.problem_category ?? "",
        symptom_tags_text: formatSymptomTags(data.plan.symptom_tags),
        reported_problem: data.plan.reported_problem ?? "",
        severity: data.plan.severity ?? "medium",
        branch_code: data.plan.branch_code ?? "01",
        nonconformity_scope: data.plan.nonconformity_scope ?? "external",
        client_nc_registry: data.plan.client_nc_registry ?? "",
        source_type: data.plan.source_type ?? "",
        source_reference: data.plan.source_reference ?? "",
      });
      try {
        const audit = await fetchPlanAuditLog(planId);
        setAuditLog(audit.items);
      } catch {
        setAuditLog([]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar plano.");
    } finally {
      setLoading(false);
    }
  }, [planId]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!success) {
      return undefined;
    }
    const timer = window.setTimeout(() => setSuccess(null), 4500);
    return () => window.clearTimeout(timer);
  }, [success]);

  async function runSave(key: string, action: () => Promise<void>) {
    setSaving(key);
    setError(null);
    setSuccess(null);
    try {
      await action();
      setSuccess("Alterações salvas.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar.");
    } finally {
      setSaving(null);
    }
  }

  const plan = detail?.plan;
  const terminalStatuses = new Set(["completed", "cancelled"]);
  const isTerminalPlan = plan ? terminalStatuses.has(plan.status) : false;
  const statusOptions = PLAN_STATUSES.map((item) => ({ value: item.value, label: item.label }));
  const reopenStatusOptions = PLAN_STATUSES.filter(
    (item) => !terminalStatuses.has(item.value) && item.value !== "draft",
  ).map((item) => ({ value: item.value, label: item.label }));
  const showRnc8dFlow =
    plan?.nonconformity_scope === "external"
    || identificationForm.nonconformity_scope === "external"
    || plan?.customer_template === "rnc_8d";
  const sharedIdentification = useMemo(
    () => ({
      client_nc_registry: identificationForm.client_nc_registry,
      customer_name: identificationForm.customer_name,
      product_code: identificationForm.product_code,
      product_description: identificationForm.product_description,
      batch_number: identificationForm.batch_number,
      reported_problem: identificationForm.reported_problem,
    }),
    [identificationForm],
  );
  const teamMemberOptions = useMemo(
    () =>
      buildTeamMemberSelectOptions(
        rnc8dForm.team_members,
        detail?.actions?.map((action) => action.responsible_name),
      ),
    [rnc8dForm.team_members, detail?.actions],
  );
  const effectivenessApprovalStatus = plan?.effectiveness_approval_status ?? null;
  const isEffectivenessPendingApproval = effectivenessApprovalStatus === "pending_review";
  const isEffectivenessRejected = effectivenessApprovalStatus === "rejected";
  const submittableEffectivenessOptions = EFFECTIVENESS_STATUSES.filter((item) =>
    ["effective", "partially_effective", "ineffective"].includes(item.value),
  );

  async function handleExportRnc8d() {
    setError(null);
    try {
      const registry = plan?.client_nc_registry || plan?.code || planId.slice(0, 8);
      await exportRnc8dSpreadsheet(planId, `RNC_${registry}_8D.xlsx`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao gerar planilha.");
    }
  }

  async function handleExportPlanPdf() {
    setError(null);
    try {
      const registry = plan?.code || planId.slice(0, 8);
      await exportPlanPdf(planId, `PAC_${registry}_resumo.pdf`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao gerar PDF do plano.");
    }
  }

  async function handleExportRnc8dPdf() {
    setError(null);
    try {
      const registry = plan?.client_nc_registry || plan?.code || planId.slice(0, 8);
      await exportRnc8dPdf(planId, `RNC_${registry}_8D.pdf`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao gerar PDF 8D.");
    }
  }

  return (
    <>
      <PageHeader
        title={plan?.title ?? "Detalhe do plano"}
        subtitle={plan?.code ? `Código ${plan.code}` : "Carregando…"}
        actions={
          <>
            <button type="button" className="pac-ghost-btn" onClick={() => onNavigate(listPath())}>
              <ArrowLeft size={16} />
              Voltar à lista
            </button>
            <button type="button" className="pac-ghost-btn" onClick={() => onNavigate(dashboardPath())}>
              Resumo
            </button>
            <button type="button" className="pac-ghost-btn" onClick={() => void handleExportPlanPdf()}>
              <Download size={16} />
              PDF resumo
            </button>
            {showRnc8dFlow ? (
              <>
                <button type="button" className="pac-primary-btn" onClick={() => void handleExportRnc8d()}>
                  <Download size={16} />
                  Excel 8D
                </button>
                <button type="button" className="pac-ghost-btn" onClick={() => void handleExportRnc8dPdf()}>
                  <Download size={16} />
                  PDF 8D
                </button>
              </>
            ) : null}
          </>
        }
      />
      <SaveStatusBanner
        saving={saving ? "Salvando alterações…" : null}
        success={success}
        error={error}
        onDismiss={() => {
          setSuccess(null);
          setError(null);
        }}
      />
      {loading && !detail ? <p className="pac-muted">Carregando detalhe…</p> : null}

      {plan ? (
        <div className="pac-detail-grid">
          <SectionCard
            title={showRnc8dFlow ? "Problema e cabeçalho 8D" : "Problema"}
            hint={PAC_HELP_TOOLTIPS.sections.problem}
            subtitle={
              showRnc8dFlow
                ? "Identificação do plano e complementos da planilha (material, NF e contato)."
                : undefined
            }
          >
            <StatusPipeline
              currentStatus={plan.status}
              hint={PAC_HELP_TOOLTIPS.detail.statusPipeline}
            />
            {showRnc8dFlow && detail ? <Rnc8dDisciplineProgress detail={detail} /> : null}
            <div className="pac-form-grid">
              <TextField
                id="pac-detail-title"
                label="Título"
                hint={PAC_HELP_TOOLTIPS.detail.title}
                value={identificationForm.title}
                onChange={(title) => setIdentificationForm((c) => ({ ...c, title }))}
                fullWidth
              />
              <TextField
                id="pac-detail-customer"
                label="Cliente"
                hint={PAC_HELP_TOOLTIPS.detail.customer}
                value={identificationForm.customer_name}
                onChange={(customer_name) =>
                  setIdentificationForm((c) => ({ ...c, customer_name }))
                }
              />
              <SelectField
                id="pac-detail-branch"
                label="Filial"
                hint={PAC_HELP_TOOLTIPS.filters.branch}
                options={PAC_BRANCH_OPTIONS.map((item) => ({ value: item.value, label: item.label }))}
                value={identificationForm.branch_code}
                onChange={(branch_code) => setIdentificationForm((c) => ({ ...c, branch_code }))}
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
                onChange={(nonconformity_scope) =>
                  setIdentificationForm((c) => ({ ...c, nonconformity_scope }))
                }
                searchable={false}
              />
              <TextField
                id="pac-detail-product"
                label={
                  showRnc8dFlow
                    ? RNC8D_SHARED_FIELD_LABELS.productCode
                    : "Código produto"
                }
                hint={PAC_HELP_TOOLTIPS.detail.productCode}
                value={identificationForm.product_code}
                onChange={(product_code) => setIdentificationForm((c) => ({ ...c, product_code }))}
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
                onChange={(product_description) =>
                  setIdentificationForm((c) => ({ ...c, product_description }))
                }
              />
              <TextField
                id="pac-detail-batch"
                label={
                  showRnc8dFlow ? RNC8D_SHARED_FIELD_LABELS.supplierBatch : "Lote"
                }
                hint={PAC_HELP_TOOLTIPS.detail.supplierBatch}
                value={identificationForm.batch_number}
                onChange={(batch_number) => setIdentificationForm((c) => ({ ...c, batch_number }))}
              />
              <TextField
                id="pac-detail-department"
                label="Área"
                hint={PAC_HELP_TOOLTIPS.detail.department}
                value={identificationForm.department}
                onChange={(department) => setIdentificationForm((c) => ({ ...c, department }))}
              />
              <TextField
                id="pac-detail-failure"
                label="Modo de falha"
                hint={PAC_HELP_TOOLTIPS.detail.failureMode}
                value={identificationForm.failure_mode}
                onChange={(failure_mode) => setIdentificationForm((c) => ({ ...c, failure_mode }))}
              />
              <TextField
                id="pac-detail-problem-category"
                label="Categoria do problema"
                hint={PAC_HELP_TOOLTIPS.detail.problemCategory}
                value={identificationForm.problem_category}
                onChange={(problem_category) =>
                  setIdentificationForm((c) => ({ ...c, problem_category }))
                }
              />
              <TextField
                id="pac-detail-symptom-tags"
                label="Tags de sintoma"
                hint={PAC_HELP_TOOLTIPS.detail.symptomTags}
                value={identificationForm.symptom_tags_text}
                onChange={(symptom_tags_text) =>
                  setIdentificationForm((c) => ({ ...c, symptom_tags_text }))
                }
                placeholder="oxidacao, trinca"
              />
              <SelectField
                id="pac-detail-severity"
                label="Severidade"
                hint={PAC_HELP_TOOLTIPS.filters.severity}
                options={PLAN_SEVERITIES.map((item) => ({ value: item.value, label: item.label }))}
                value={identificationForm.severity}
                onChange={(severity) => setIdentificationForm((c) => ({ ...c, severity }))}
                searchable
              />
              <SelectField
                id="pac-detail-source-type"
                label="Canal (source_type)"
                hint={PAC_HELP_TOOLTIPS.form.source}
                options={[{ value: "", label: "Não informado" }, ...PAC_SOURCE_TYPES.map((item) => ({ value: item.value, label: item.label }))]}
                value={identificationForm.source_type}
                onChange={(source_type) =>
                  setIdentificationForm((c) => ({ ...c, source_type }))
                }
                searchable
              />
              <TextField
                id="pac-detail-source-reference"
                label="Referência do canal"
                hint={PAC_HELP_TOOLTIPS.detail.sourceReference}
                value={identificationForm.source_reference}
                onChange={(source_reference) =>
                  setIdentificationForm((c) => ({ ...c, source_reference }))
                }
              />
              {showRnc8dFlow ? (
                <TextField
                  id="pac-detail-nc-registry"
                  label={RNC8D_SHARED_FIELD_LABELS.clientNcRegistry}
                  hint={PAC_HELP_TOOLTIPS.detail.clientNcRegistry}
                  value={identificationForm.client_nc_registry}
                  onChange={(client_nc_registry) =>
                    setIdentificationForm((c) => ({ ...c, client_nc_registry }))
                  }
                />
              ) : null}
            </div>
            {showRnc8dFlow ? (
              <>
                <h3 className="pac-subsection-title">Material e nota fiscal</h3>
                <Rnc8dHeaderFields value={rnc8dForm} onChange={setRnc8dForm} />
              </>
            ) : null}
            <TextAreaField
              id="pac-detail-problem"
              label={RNC8D_SHARED_FIELD_LABELS.reportedProblem}
              hint={PAC_HELP_TOOLTIPS.form.description}
              value={identificationForm.reported_problem}
              onChange={(reported_problem) =>
                setIdentificationForm((c) => ({ ...c, reported_problem }))
              }
              fullWidth
            />
            <FormActions align="end">
              <button
                type="button"
                className="pac-primary-btn"
                disabled={saving === "identification"}
                onClick={() =>
                  void runSave("identification", async () => {
                    const shared = {
                      client_nc_registry: identificationForm.client_nc_registry,
                      customer_name: identificationForm.customer_name,
                      product_code: identificationForm.product_code,
                      product_description: identificationForm.product_description,
                      batch_number: identificationForm.batch_number,
                      reported_problem: identificationForm.reported_problem,
                    };
                    await updateActionPlan(planId, {
                      title: identificationForm.title.trim() || undefined,
                      customer_name: identificationForm.customer_name.trim() || undefined,
                      product_code: identificationForm.product_code.trim() || undefined,
                      product_description: identificationForm.product_description.trim() || undefined,
                      batch_number: identificationForm.batch_number.trim() || undefined,
                      department: identificationForm.department.trim() || undefined,
                      failure_mode: identificationForm.failure_mode.trim() || undefined,
                      problem_category: identificationForm.problem_category.trim() || undefined,
                      symptom_tags: (() => {
                        const tags = parseSymptomTags(identificationForm.symptom_tags_text);
                        return tags.length ? tags : undefined;
                      })(),
                      reported_problem: identificationForm.reported_problem.trim() || undefined,
                      severity: identificationForm.severity,
                      branch_code: identificationForm.branch_code,
                      nonconformity_scope: identificationForm.nonconformity_scope,
                      client_nc_registry: identificationForm.client_nc_registry.trim() || undefined,
                      source_type: identificationForm.source_type.trim() || undefined,
                      source_reference: identificationForm.source_reference.trim() || undefined,
                    });
                    if (showRnc8dFlow) {
                      await upsertRnc8dReport(
                        planId,
                        sanitizeRnc8dReportPayload(
                          mergeSharedIdentificationIntoRnc8d(rnc8dForm, shared),
                        ),
                      );
                    }
                  })
                }
              >
                <Save size={16} />
                {saving === "identification" ? "Salvando…" : "Salvar identificação"}
              </button>
            </FormActions>
            <dl className="pac-dl pac-dl--compact">
              <div>
                <dt>Status atual</dt>
                <dd>
                  <StatusBadge status={plan.status} />
                </dd>
              </div>
              <div>
                <dt>Filial</dt>
                <dd>{branchLabel(plan.branch_code)}</dd>
              </div>
              <div>
                <dt>Escopo</dt>
                <dd>
                  <ScopeBadge scope={plan.nonconformity_scope} />
                </dd>
              </div>
              <div>
                <dt>Severidade</dt>
                <dd>
                  <SeverityBadge severity={plan.severity} />
                </dd>
              </div>
            </dl>
            <div className="pac-inline-form">
              {isTerminalPlan ? (
                <>
                  <TextAreaField
                    id="pac-reopen-reason"
                    label="Motivo da reabertura"
                    hint={PAC_HELP_TOOLTIPS.detail.reopenReason}
                    value={reopenReason}
                    onChange={setReopenReason}
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
                    onChange={setReopenTargetStatus}
                    searchable={false}
                  />
                  <button
                    type="button"
                    className="pac-primary-btn"
                    disabled={saving === "reopen" || reopenReason.trim().length < 5}
                    onClick={() =>
                      void runSave("reopen", async () => {
                        await reopenPlan(planId, reopenReason, reopenTargetStatus);
                        setReopenReason("");
                      })
                    }
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
                    onChange={setStatusValue}
                    searchable
                  />
                  <button
                    type="button"
                    className="pac-primary-btn"
                    disabled={saving === "status"}
                    onClick={() =>
                      void runSave("status", async () => {
                        await updatePlanStatus(planId, statusValue);
                      })
                    }
                  >
                    <Save size={16} />
                    {saving === "status" ? "Salvando…" : "Salvar status"}
                  </button>
                </>
              )}
            </div>
          </SectionCard>

          <SimilarCasesPanel planId={planId} onNavigate={onNavigate} />

          {showRnc8dFlow ? (
            <>
              <Rnc8dNcDescriptionSection value={rnc8dForm} onChange={setRnc8dForm} />
              <Rnc8dTeamSection value={rnc8dForm} onChange={setRnc8dForm} />
              <Rnc8dContainmentSection value={rnc8dForm} onChange={setRnc8dForm} />

              <SectionCard
                title="4. Estudo da causa do defeito (5 Porquês)"
                hint={PAC_HELP_TOOLTIPS.sections.fiveWhys}
              >
                <FiveWhysFlowPanel
                  planId={planId}
                  form={fiveWhysForm}
                  saving={saving}
                  onChange={setFiveWhysForm}
                  onSave={runSave}
                />
              </SectionCard>

              <SectionCard title="4. Ishikawa (6M)" hint={PAC_HELP_TOOLTIPS.sections.ishikawa}>
                <IshikawaFishboneDiagram
                  problem={plan.reported_problem || plan.title}
                  causes={ishikawaCausesForm}
                  notes={ishikawaNotes}
                  onChange={setIshikawaCausesForm}
                  onNotesChange={setIshikawaNotes}
                  saving={saving === "ishikawa"}
                  onSave={() =>
                    void runSave("ishikawa", async () => {
                      await upsertIshikawa(
                        planId,
                        serializeIshikawaCausesForm(ishikawaCausesForm, ishikawaNotes),
                      );
                    })
                  }
                />
              </SectionCard>

              <SectionCard
                title="5. Ação corretiva proposta"
                hint={PAC_HELP_TOOLTIPS.sections.actions}
              >
                <PlanActionsPanel
                  planId={planId}
                  actions={detail.actions}
                  evidences={detail.evidences ?? []}
                  saving={saving}
                  onSave={runSave}
                  responsibleOptions={teamMemberOptions}
                />
              </SectionCard>

              <Rnc8dEffectivenessSection value={rnc8dForm} onChange={setRnc8dForm} />
            </>
          ) : (
            <>
              <EvidencePanel
                planId={planId}
                evidences={detail.evidences ?? []}
                actions={detail.actions ?? []}
                onChanged={load}
              />

              <SectionCard title="Ishikawa (6M)" hint={PAC_HELP_TOOLTIPS.sections.ishikawa}>
                <IshikawaFishboneDiagram
                  problem={plan.reported_problem || plan.title}
                  causes={ishikawaCausesForm}
                  notes={ishikawaNotes}
                  onChange={setIshikawaCausesForm}
                  onNotesChange={setIshikawaNotes}
                  saving={saving === "ishikawa"}
                  onSave={() =>
                    void runSave("ishikawa", async () => {
                      await upsertIshikawa(
                        planId,
                        serializeIshikawaCausesForm(ishikawaCausesForm, ishikawaNotes),
                      );
                    })
                  }
                />
              </SectionCard>

              <SectionCard title="Estudo de causa — Porquês" hint={PAC_HELP_TOOLTIPS.sections.fiveWhys}>
                <FiveWhysFlowPanel
                  planId={planId}
                  form={fiveWhysForm}
                  saving={saving}
                  onChange={setFiveWhysForm}
                  onSave={runSave}
                />
              </SectionCard>

              <SectionCard title="Ações corretivas e plano" hint={PAC_HELP_TOOLTIPS.sections.actions}>
                <PlanActionsPanel
                  planId={planId}
                  actions={detail.actions}
                  evidences={detail.evidences ?? []}
                  saving={saving}
                  onSave={runSave}
                />
              </SectionCard>
            </>
          )}

          <SectionCard
            title={showRnc8dFlow ? "6. Registro de eficácia (PAC)" : "Eficácia"}
            hint={PAC_HELP_TOOLTIPS.sections.effectiveness}
            subtitle={
              showRnc8dFlow
                ? "Fluxo de aprovação do coordenador — complementa a seção 6 da planilha 8D."
                : undefined
            }
          >
            {isEffectivenessPendingApproval ? (
              <div className="pac-state" style={{ marginBottom: "0.75rem" }}>
                <strong>Aguardando aprovação do coordenador.</strong>
                {plan.effectiveness_proposed_status ? (
                  <span>
                    {" "}
                    Resultado proposto:{" "}
                    {EFFECTIVENESS_STATUSES.find(
                      (item) => item.value === plan.effectiveness_proposed_status,
                    )?.label ?? plan.effectiveness_proposed_status}
                    .
                  </span>
                ) : null}
              </div>
            ) : null}
            {isEffectivenessRejected && plan.effectiveness_rejection_reason ? (
              <div className="pac-state pac-state--error" style={{ marginBottom: "0.75rem" }}>
                <strong>Submissão rejeitada:</strong> {plan.effectiveness_rejection_reason}
              </div>
            ) : null}
            <div className="pac-form-grid">
              <SelectField
                id="pac-effectiveness-status"
                label="Resultado"
                hint={PAC_HELP_TOOLTIPS.detail.effectivenessResult}
                options={(isEffectivenessPendingApproval
                  ? EFFECTIVENESS_STATUSES
                  : submittableEffectivenessOptions
                ).map((item) => ({
                  value: item.value,
                  label: item.label,
                }))}
                value={effectivenessStatus}
                onChange={setEffectivenessStatus}
                searchable={false}
                disabled={isEffectivenessPendingApproval}
              />
              <TextAreaField
                id="pac-effectiveness-notes"
                label="Observações"
                hint={PAC_HELP_TOOLTIPS.detail.effectivenessNotes}
                value={effectivenessNotes}
                onChange={setEffectivenessNotes}
                placeholder="Evidências e conclusão da verificação de eficácia"
                fullWidth
                disabled={isEffectivenessPendingApproval}
              />
            </div>
            {isEffectivenessPendingApproval ? (
              <TextAreaField
                id="pac-effectiveness-rejection-reason"
                label="Motivo da rejeição (coordenador)"
                hint={PAC_HELP_TOOLTIPS.detail.effectivenessRejection}
                value={effectivenessRejectionReason}
                onChange={setEffectivenessRejectionReason}
                placeholder="Descreva o motivo com ao menos 5 caracteres"
                fullWidth
              />
            ) : null}
            <FormActions>
              {!isEffectivenessPendingApproval ? (
                <button
                  type="button"
                  className="pac-primary-btn"
                  disabled={saving === "effectiveness-submit"}
                  onClick={() =>
                    void runSave("effectiveness-submit", async () => {
                      await submitEffectivenessReview(
                        planId,
                        effectivenessStatus,
                        effectivenessNotes.trim() || undefined,
                      );
                    })
                  }
                >
                  {saving === "effectiveness-submit"
                    ? "Salvando…"
                    : "Submeter para aprovação"}
                </button>
              ) : (
                <>
                  <button
                    type="button"
                    className="pac-primary-btn"
                    disabled={saving === "effectiveness-approve"}
                    onClick={() =>
                      void runSave("effectiveness-approve", async () => {
                        await approveEffectivenessReview(planId);
                      })
                    }
                  >
                    {saving === "effectiveness-approve" ? "Salvando…" : "Aprovar eficácia"}
                  </button>
                  <button
                    type="button"
                    className="pac-ghost-btn"
                    disabled={
                      saving === "effectiveness-reject"
                      || effectivenessRejectionReason.trim().length < 5
                    }
                    onClick={() =>
                      void runSave("effectiveness-reject", async () => {
                        await rejectEffectivenessReview(
                          planId,
                          effectivenessRejectionReason.trim(),
                        );
                      })
                    }
                  >
                    {saving === "effectiveness-reject" ? "Salvando…" : "Rejeitar submissão"}
                  </button>
                </>
              )}
              <button
                type="button"
                className="pac-ghost-btn"
                disabled={saving === "effectiveness" || isEffectivenessPendingApproval}
                onClick={() =>
                  void runSave("effectiveness", async () => {
                    await recordEffectivenessReview(
                      planId,
                      effectivenessStatus,
                      effectivenessNotes.trim() || undefined,
                    );
                  })
                }
              >
                {saving === "effectiveness" ? "Salvando…" : "Registrar direto (coordenador)"}
              </button>
              {["effective", "partially_effective"].includes(plan.effectiveness_status ?? "") ? (
                <button
                  type="button"
                  className="pac-ghost-btn"
                  title={PAC_HELP_TOOLTIPS.detail.promotePattern}
                  disabled={saving === "promote-pattern"}
                  onClick={() =>
                    void runSave("promote-pattern", async () => {
                      await promoteSolutionPattern(planId);
                    })
                  }
                >
                  {saving === "promote-pattern" ? "Promovendo…" : "Promover a padrão de solução"}
                </button>
              ) : null}
            </FormActions>
          </SectionCard>

          {showRnc8dFlow ? (
            <>
              <Rnc8dPreventiveSection value={rnc8dForm} onChange={setRnc8dForm} />
              <EvidencePanel
                planId={planId}
                evidences={detail.evidences ?? []}
                actions={detail.actions ?? []}
                onChanged={load}
                title="7. Evidências das ações"
                subtitle="Anexe prints, PDFs e documentos do processo (planilha: Inserir evidências)."
              />
              <Rnc8dClosureSection value={rnc8dForm} onChange={setRnc8dForm} />
              <Rnc8dSaveActions
                saving={saving === "rnc-8d"}
                onSave={() =>
                  runSave("rnc-8d", async () => {
                    await upsertRnc8dReport(
                      planId,
                      sanitizeRnc8dReportPayload(
                        mergeSharedIdentificationIntoRnc8d(rnc8dForm, sharedIdentification),
                      ),
                    );
                  })
                }
              />
            </>
          ) : null}

          <PlanTimeline detail={detail} />

          {auditLog.length > 0 ? (
            <SectionCard title="Auditoria (governança)" hint={PAC_HELP_TOOLTIPS.sections.audit}>
              <ol className="pac-timeline-track">
                {auditLog.map((entry) => (
                  <li key={entry.id} className="pac-timeline-entry">
                    <div className="pac-timeline-entry__header">
                      <strong>
                        {AUDIT_EVENT_LABELS[entry.event_type] ?? entry.event_type}
                      </strong>
                      <span className="pac-muted">{formatDateTime(entry.created_at)}</span>
                    </div>
                    {(() => {
                      const actorLabel = formatActorDisplay({
                        userId: entry.actor_user_id,
                        name: entry.actor_name,
                        email: entry.actor_email,
                      });
                      return actorLabel ? (
                        <p className="pac-timeline-entry__meta pac-muted">{actorLabel}</p>
                      ) : null;
                    })()}
                  </li>
                ))}
              </ol>
            </SectionCard>
          ) : null}
        </div>
      ) : null}
    </>
  );
}
