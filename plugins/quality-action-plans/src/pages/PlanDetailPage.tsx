import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ArrowLeft,
  Download,
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
import { PlanProblemSection, buildIdentificationUpdatePayload } from "../components/PlanProblemSection";
import { PlanStatusSection } from "../components/PlanStatusSection";
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
import { SaveStatusBanner } from "../components/SaveStatusBanner";
import { FormActions } from "../components/ui/FormActions";
import { SectionCard } from "../components/ui/SectionCard";
import { SelectField } from "../components/ui/SelectField";
import { StatusPipeline } from "../components/ui/StatusPipeline";
import { TextAreaField } from "../components/ui/TextAreaField";
import {
  dashboardPath,
  EFFECTIVENESS_STATUSES,
  listPath,
  PLAN_STATUSES,
} from "../constants/actionPlans";
import { PAC_HELP_TOOLTIPS } from "../content/helpTooltips";
import type {
  ActionPlanDetail,
  PlanAuditLogEntry,
} from "../types/actionPlan";
import type { Rnc8dReportPayload } from "../types/rnc8d";
import { emptyRnc8dPayload } from "../types/rnc8d";
import { mergeSharedIdentificationIntoRnc8d, sanitizeRnc8dReportPayload } from "../utils/rnc8dPayload";
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
import { parseStoredTaggedList } from "../utils/taggedList";

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
    customer_code: "",
    customer_store: "",
    customer_name: "",
    product_code: "",
    product_description: "",
    batch_number: "",
    department: "",
    failure_modes: [] as string[],
    problem_categories: [] as string[],
    symptom_tags: [] as string[],
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
        customer_code: data.plan.customer_code ?? "",
        customer_store: data.plan.customer_store ?? "",
        customer_name: data.plan.customer_name ?? "",
        product_code: data.plan.product_code ?? "",
        product_description: data.plan.product_description ?? "",
        batch_number: data.plan.batch_number ?? "",
        department: data.plan.department ?? "",
        failure_modes: parseStoredTaggedList(data.plan.failure_mode),
        problem_categories: parseStoredTaggedList(data.plan.problem_category),
        symptom_tags: data.plan.symptom_tags ?? [],
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
            title="Status do plano"
            hint={PAC_HELP_TOOLTIPS.sections.planStatus}
          >
            <StatusPipeline
              currentStatus={plan.status}
              hint={PAC_HELP_TOOLTIPS.detail.statusPipeline}
            />
            <PlanStatusSection
              planStatus={plan.status}
              planBranchCode={plan.branch_code}
              planScope={plan.nonconformity_scope}
              planSeverity={plan.severity}
              isTerminalPlan={isTerminalPlan}
              statusValue={statusValue}
              onStatusChange={setStatusValue}
              reopenReason={reopenReason}
              onReopenReasonChange={setReopenReason}
              reopenTargetStatus={reopenTargetStatus}
              onReopenTargetStatusChange={setReopenTargetStatus}
              reopenStatusOptions={reopenStatusOptions}
              saving={saving}
              onSaveStatus={() =>
                void runSave("status", async () => {
                  await updatePlanStatus(planId, statusValue);
                })
              }
              onReopen={() =>
                void runSave("reopen", async () => {
                  await reopenPlan(planId, reopenReason, reopenTargetStatus);
                  setReopenReason("");
                })
              }
            />
          </SectionCard>

          <SectionCard
            title={showRnc8dFlow ? "Problema e cabeçalho 8D" : "Problema"}
            hint={PAC_HELP_TOOLTIPS.sections.problem}
            subtitle={
              showRnc8dFlow
                ? "Identificação do plano e complementos da planilha (material, NF e contato)."
                : undefined
            }
          >
            {showRnc8dFlow && detail ? <Rnc8dDisciplineProgress detail={detail} /> : null}
            <PlanProblemSection
              showRnc8dFlow={showRnc8dFlow}
              identificationForm={identificationForm}
              onIdentificationChange={setIdentificationForm}
              saving={saving}
              onSaveIdentification={() =>
                void runSave("identification", async () => {
                  const payload = buildIdentificationUpdatePayload(identificationForm);
                  const shared = {
                    client_nc_registry: identificationForm.client_nc_registry,
                    customer_name: identificationForm.customer_name,
                    product_code: identificationForm.product_code,
                    product_description: identificationForm.product_description,
                    batch_number: identificationForm.batch_number,
                    reported_problem: identificationForm.reported_problem,
                  };
                  await updateActionPlan(planId, payload);
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
              materialSection={
                showRnc8dFlow ? (
                  <>
                    <h3 className="pac-subsection-title">Material e nota fiscal</h3>
                    <Rnc8dHeaderFields value={rnc8dForm} onChange={setRnc8dForm} />
                  </>
                ) : null
              }
            />
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
                  teamMembers={rnc8dForm.team_members}
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
