import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ArrowLeft,
  Download,
  Paperclip,
  Trash2,
} from "lucide-react";

import {
  approveEffectivenessReview,
  deleteActionPlan,
  exportPlanPdf,
  exportRnc8dPdf,
  exportRnc8dSpreadsheet,
  fetchActionPlanDetail,
  fetchPlanAuditLog,
  listRnc8dExportTemplates,
  promoteSolutionPattern,
  recordEffectivenessReview,
  rejectEffectivenessReview,
  reopenPlan,
  submitEffectivenessReview,
  updateActionPlan,
  updatePlanStatus,
  upsertFiveWhys,
  upsertIshikawa,
  upsertRnc8dReport,
} from "../api/actionPlansApi";
import { EvidencePanel } from "../components/EvidencePanel";
import { FiveWhysFlowPanel } from "../components/FiveWhysFlowPanel";
import { PlanActionsPanel } from "../components/PlanActionsPanel";
import { PlanGlobalSaveBar } from "../components/PlanGlobalSaveBar";
import { IshikawaFishboneDiagram } from "../components/IshikawaFishboneDiagram";
import { PlanTimeline } from "../components/PlanTimeline";
import { SimilarCasesPanel } from "../components/SimilarCasesPanel";
import { PageHeader } from "../components/PageHeader";
import { PlanProblemSection, buildIdentificationUpdatePayload } from "../components/PlanProblemSection";
import { PlanStatusSection } from "../components/PlanStatusSection";
import {
  EffectivenessPacReadContent,
  FiveWhysReadContent,
  IshikawaReadContent,
  PlanActionsReadContent,
  PlanProblemReadContent,
  PlanStatusReadContent,
} from "../components/plan-detail/PlanDetailReadViews";
import { Rnc8dDisciplineProgress } from "../components/Rnc8dDisciplineProgress";
import { formatActorDisplay } from "../utils/actorDisplay";
import { IncompletePlanActionsNotice } from "../components/IncompletePlanActionsNotice";
import {
  Rnc8dClosureSection,
  Rnc8dContainmentSection,
  Rnc8dEffectivenessSection,
  Rnc8dHeaderFields,
  Rnc8dNcDescriptionSection,
  Rnc8dPreventiveSection,
  Rnc8dTeamSection,
} from "../components/rnc8d/Rnc8dSections";
import { SaveStatusBanner } from "../components/SaveStatusBanner";
import { SectionSaveButton } from "../components/ui/SectionSaveButton";
import { EditableSectionCard } from "../components/ui/EditableSectionCard";
import { FormActions } from "../components/ui/FormActions";
import { SectionCard } from "../components/ui/SectionCard";
import { SelectField } from "../components/ui/SelectField";
import { TextAreaField } from "../components/ui/TextAreaField";
import {
  dashboardPath,
  EFFECTIVENESS_STATUSES,
  listPath,
  PLAN_STATUSES,
} from "../constants/actionPlans";
import { PAC_HELP_TOOLTIPS } from "../content/helpTooltips";
import {
  usePlanSectionEdit,
  type PlanSectionEditBindings,
} from "../hooks/usePlanSectionEdit";
import { useConfirmDialog } from "../hooks/useConfirmDialog";
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
  serializeFiveWhysForm,
  type FiveWhysForm,
} from "../utils/fiveWhys";
import {
  buildPlanDetailSnapshot,
  cloneFiveWhysForm,
  computePlanDirtySections,
  hasAnyRnc8dDirtySection,
  isPlanSectionDirty,
  revertRnc8dFormSection,
  type PlanDetailSnapshot,
  type PlanSectionEditKey,
} from "../utils/planDetailDirtyState";
import { canDeleteActionPlan, planDeleteBlockedReason } from "../utils/planDeletePolicy";
import { resolveEffectivenessUiPermissions } from "../utils/pacPermissions";
import { usePacPermissions } from "../context/PacPermissionsContext";
import { parseStoredTaggedList } from "../utils/taggedList";

type Props = {
  planId: string;
  onNavigate: (path: string) => void;
};

const AUDIT_EVENT_LABELS: Record<string, string> = {
  plan_created: "Plano criado",
  plan_updated: "Identificação atualizada",
  plan_deleted: "Plano excluído",
  plan_closed: "Plano encerrado",
  plan_reopened: "Plano reaberto",
  effectiveness_submitted: "Eficácia submetida",
  effectiveness_approved: "Eficácia aprovada",
  effectiveness_reviewed: "Eficácia registrada",
  effectiveness_approval_rejected: "Submissão rejeitada",
};

const SAVE_KEY_TO_EDIT_SECTION: Partial<Record<string, PlanSectionEditKey>> = {
  identification: "problem",
  "rnc8d-material": "problem",
  reopen: "status",
  "effectiveness-submit": "effectiveness-pac",
  "effectiveness-approve": "effectiveness-pac",
  "effectiveness-reject": "effectiveness-pac",
  effectiveness: "effectiveness-pac",
  "promote-pattern": "effectiveness-pac",
};

function resolveEditSectionForSaveKey(saveKey: string): PlanSectionEditKey | null {
  const mapped = SAVE_KEY_TO_EDIT_SECTION[saveKey];
  if (mapped) {
    return mapped;
  }
  if (
    saveKey === "status"
    || saveKey === "problem"
    || saveKey === "evidences"
    || saveKey === "actions"
    || saveKey.startsWith("rnc8d-")
    || saveKey === "five-whys"
    || saveKey === "ishikawa"
    || saveKey === "effectiveness-pac"
  ) {
    return saveKey as PlanSectionEditKey;
  }
  return null;
}

export function PlanDetailPage({ planId, onNavigate }: Props) {
  const { profile } = usePacPermissions();
  const { confirm, confirmDialog } = useConfirmDialog();
  const [detail, setDetail] = useState<ActionPlanDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [exportTemplates, setExportTemplates] = useState<
    Awaited<ReturnType<typeof listRnc8dExportTemplates>>
  >([]);
  const [exportTemplateKey, setExportTemplateKey] = useState("");
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
  const [savedSnapshot, setSavedSnapshot] = useState<PlanDetailSnapshot | null>(null);
  const [auditLog, setAuditLog] = useState<PlanAuditLogEntry[]>([]);
  const sectionEdit = usePlanSectionEdit();
  const [identificationForm, setIdentificationForm] = useState({
    title: "",
    customer_code: "",
    customer_store: "",
    customer_name: "",
    product_code: "",
    customer_product_reference: "",
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
      const nextFiveWhysForm = parseFiveWhysForm(data.five_whys);
      setFiveWhysForm(nextFiveWhysForm);
      const nextRnc8dForm: Rnc8dReportPayload = {
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
      };
      setRnc8dForm(nextRnc8dForm);
      const nextEffectivenessStatus =
        data.plan.effectiveness_proposed_status
        ?? data.plan.effectiveness_status
        ?? "pending";
      setEffectivenessStatus(nextEffectivenessStatus);
      const nextEffectivenessNotes = data.plan.effectiveness_notes ?? "";
      setEffectivenessNotes(nextEffectivenessNotes);
      setEffectivenessRejectionReason("");
      const nextIdentification = {
        title: data.plan.title ?? "",
        customer_code: data.plan.customer_code ?? "",
        customer_store: data.plan.customer_store ?? "",
        customer_name: data.plan.customer_name ?? "",
        product_code: data.plan.product_code ?? "",
        customer_product_reference: data.plan.customer_product_reference ?? "",
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
      };
      setIdentificationForm(nextIdentification);
      setSavedSnapshot(
        buildPlanDetailSnapshot({
          status: data.plan.status,
          identification: nextIdentification,
          rnc8dForm: nextRnc8dForm,
          fiveWhysForm: nextFiveWhysForm,
          ishikawaCausesForm: parseIshikawaCausesForm(data.ishikawa),
          ishikawaNotes: data.ishikawa?.notes ?? "",
          effectivenessStatus: nextEffectivenessStatus,
          effectivenessNotes: nextEffectivenessNotes,
        }),
      );
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
      const editKey = resolveEditSectionForSaveKey(key);
      if (editKey) {
        sectionEdit.stopEdit(editKey);
      }
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
  const planDeleteAllowed = canDeleteActionPlan(plan);
  const planDeleteBlockReason = planDeleteBlockedReason(plan);
  const submittableEffectivenessOptions = EFFECTIVENESS_STATUSES.filter((item) =>
    ["effective", "partially_effective", "ineffective"].includes(item.value),
  );
  const effectivenessUi = useMemo(
    () =>
      resolveEffectivenessUiPermissions({
        profile,
        isPendingApproval: isEffectivenessPendingApproval,
      }),
    [profile, isEffectivenessPendingApproval],
  );

  const currentSnapshot = useMemo<PlanDetailSnapshot>(
    () => ({
      status: statusValue,
      identification: identificationForm,
      rnc8dForm,
      fiveWhysForm,
      ishikawaCausesForm,
      ishikawaNotes,
      effectivenessStatus,
      effectivenessNotes,
    }),
    [
      statusValue,
      identificationForm,
      rnc8dForm,
      fiveWhysForm,
      ishikawaCausesForm,
      ishikawaNotes,
      effectivenessStatus,
      effectivenessNotes,
    ],
  );

  const dirtySections = useMemo(
    () => computePlanDirtySections(savedSnapshot, currentSnapshot, { showRnc8dFlow }),
    [savedSnapshot, currentSnapshot, showRnc8dFlow],
  );

  const isDirty = useCallback(
    (section: Parameters<typeof isPlanSectionDirty>[1]) =>
      isPlanSectionDirty(dirtySections, section),
    [dirtySections],
  );

  const handleCancelEdit = useCallback(
    (key: PlanSectionEditKey) => {
      if (savedSnapshot) {
        switch (key) {
          case "status":
            setStatusValue(savedSnapshot.status);
            setReopenReason("");
            break;
          case "problem":
            setIdentificationForm({ ...savedSnapshot.identification });
            setRnc8dForm((current) =>
              revertRnc8dFormSection(current, savedSnapshot.rnc8dForm, "rnc8d-material"),
            );
            break;
          case "rnc8d-nc":
          case "rnc8d-team":
          case "rnc8d-containment":
          case "rnc8d-effectiveness-8d":
          case "rnc8d-preventive":
          case "rnc8d-closure":
            setRnc8dForm((current) =>
              revertRnc8dFormSection(current, savedSnapshot.rnc8dForm, key),
            );
            break;
          case "five-whys":
            setFiveWhysForm(cloneFiveWhysForm(savedSnapshot.fiveWhysForm));
            break;
          case "ishikawa":
            setIshikawaCausesForm({ ...savedSnapshot.ishikawaCausesForm });
            setIshikawaNotes(savedSnapshot.ishikawaNotes);
            break;
          case "effectiveness-pac":
            setEffectivenessStatus(savedSnapshot.effectivenessStatus);
            setEffectivenessNotes(savedSnapshot.effectivenessNotes);
            setEffectivenessRejectionReason("");
            break;
          case "evidences":
          case "actions":
          default:
            break;
        }
      }
      sectionEdit.stopEdit(key);
    },
    [savedSnapshot, sectionEdit],
  );

  const bindSection = useCallback(
    (key: PlanSectionEditKey): PlanSectionEditBindings => ({
      isEditing: sectionEdit.isEditing(key),
      onEdit: () => sectionEdit.startEdit(key),
      onCancelEdit: () => handleCancelEdit(key),
    }),
    [sectionEdit, handleCancelEdit],
  );

  const saveRnc8dReport = useCallback(async () => {
    await upsertRnc8dReport(
      planId,
      sanitizeRnc8dReportPayload(
        mergeSharedIdentificationIntoRnc8d(rnc8dForm, sharedIdentification),
      ),
    );
  }, [planId, rnc8dForm, sharedIdentification]);

  const saveIdentification = useCallback(async () => {
    const payload = buildIdentificationUpdatePayload(identificationForm);
    await updateActionPlan(planId, payload);
    if (showRnc8dFlow) {
      await saveRnc8dReport();
    }
  }, [identificationForm, planId, saveRnc8dReport, showRnc8dFlow]);

  const saveProblemHeader = useCallback(async () => {
    if (isDirty("identification")) {
      await saveIdentification();
      return;
    }
    if (isDirty("rnc8d-material")) {
      await saveRnc8dReport();
    }
  }, [saveIdentification, saveRnc8dReport, isDirty]);

  async function runGlobalSave() {
    if (!dirtySections.length) {
      return;
    }

    setSaving("global");
    setError(null);
    setSuccess(null);

    try {
      if (isDirty("status")) {
        await updatePlanStatus(planId, statusValue);
      }

      const identificationDirty = isDirty("identification");
      const rnc8dDirty = hasAnyRnc8dDirtySection(dirtySections);

      if (identificationDirty) {
        await saveIdentification();
      } else if (rnc8dDirty) {
        await saveRnc8dReport();
      }

      if (isDirty("five-whys")) {
        await upsertFiveWhys(planId, serializeFiveWhysForm(fiveWhysForm));
      }

      if (isDirty("ishikawa")) {
        await upsertIshikawa(
          planId,
          serializeIshikawaCausesForm(ishikawaCausesForm, ishikawaNotes),
        );
      }

      if (isDirty("effectiveness-pac")) {
        await recordEffectivenessReview(
          planId,
          effectivenessStatus,
          effectivenessNotes.trim() || undefined,
        );
      }

      const count = dirtySections.length;
      setSuccess(
        count === 1
          ? "Alterações salvas."
          : `Alterações salvas (${count} blocos).`,
      );
      await load();
      sectionEdit.stopAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar.");
    } finally {
      setSaving(null);
    }
  }

  useEffect(() => {
    if (!showRnc8dFlow) {
      return undefined;
    }

    let cancelled = false;
    void listRnc8dExportTemplates()
      .then((items) => {
        if (cancelled) {
          return;
        }
        setExportTemplates(items);
        const planKey = plan?.export_template_key?.trim();
        if (planKey && items.some((item) => item.key === planKey)) {
          setExportTemplateKey(planKey);
          return;
        }
        const customerName = (plan?.customer_name ?? "").toLowerCase();
        const hinted = items.find((item) =>
          (item.customer_name_hints ?? []).some((hint) =>
            customerName.includes(String(hint).toLowerCase()),
          ),
        );
        const fallback =
          hinted?.key
          ?? items.find((item) => item.key === "weg_wfr20997")?.key
          ?? items[0]?.key
          ?? "";
        setExportTemplateKey(fallback);
      })
      .catch(() => {
        if (!cancelled) {
          setExportTemplates([]);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [showRnc8dFlow, plan?.export_template_key, plan?.customer_name]);

  useEffect(() => {
    if (!dirtySections.length) {
      return undefined;
    }

    const handleBeforeUnload = (event: BeforeUnloadEvent) => {
      event.preventDefault();
    };

    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => window.removeEventListener("beforeunload", handleBeforeUnload);
  }, [dirtySections.length]);

  async function handleExportRnc8d() {
    setError(null);
    try {
      const registry = plan?.client_nc_registry || plan?.code || planId.slice(0, 8);
      await exportRnc8dSpreadsheet(
        planId,
        `RNC_${registry}_8D.xlsx`,
        exportTemplateKey || undefined,
      );
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

  async function handleDeletePlan() {
    if (!plan || !planDeleteAllowed) return;
    const label = plan.code ? `${plan.code} — ${plan.title}` : plan.title;
    const confirmed = await confirm({
      title: "Excluir plano",
      message: `Excluir o plano "${label}"?\n\nEsta ação remove o plano das listagens. Evidências e histórico permanecem no banco, mas o plano deixa de ser acessível.`,
      confirmLabel: "Excluir",
      variant: "danger",
    });
    if (!confirmed) {
      return;
    }
    setDeleting(true);
    setError(null);
    try {
      await deleteActionPlan(planId);
      onNavigate(listPath());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao excluir plano.");
    } finally {
      setDeleting(false);
    }
  }

  return (
    <>
      {confirmDialog}
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
                {exportTemplates.length > 0 ? (
                  <label className="pac-export-template-picker">
                    <span className="pac-sr-only">Template Excel 8D</span>
                    <select
                      className="pac-select pac-export-template-select"
                      value={exportTemplateKey}
                      onChange={(event) => setExportTemplateKey(event.target.value)}
                      title="Modelo de planilha 8D"
                    >
                      {exportTemplates.map((item) => (
                        <option key={item.key} value={item.key}>
                          {item.label}
                        </option>
                      ))}
                    </select>
                  </label>
                ) : null}
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
            {planDeleteAllowed ? (
              <button
                type="button"
                className="pac-ghost-btn pac-ghost-btn--danger"
                disabled={deleting}
                title="Excluir plano de ação"
                onClick={() => void handleDeletePlan()}
              >
                <Trash2 size={16} />
                {deleting ? "Excluindo…" : "Excluir plano"}
              </button>
            ) : planDeleteBlockReason ? (
              <span className="pac-muted pac-header-delete-hint" title={planDeleteBlockReason}>
                {planDeleteBlockReason}
              </span>
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
      <PlanGlobalSaveBar
        dirtySections={dirtySections}
        saving={saving}
        onSaveAll={() => void runGlobalSave()}
      />
      {loading && !detail ? <p className="pac-muted">Carregando detalhe…</p> : null}

      {plan ? (
        <div className="pac-detail-grid">
          <EditableSectionCard
            title="Status do plano"
            hint={PAC_HELP_TOOLTIPS.sections.planStatus}
            isEditing={bindSection("status").isEditing}
            onEdit={bindSection("status").onEdit}
            onCancelEdit={bindSection("status").onCancelEdit}
            readContent={
              <PlanStatusReadContent
                planStatus={plan.status}
                planBranchCode={plan.branch_code}
                planScope={plan.nonconformity_scope}
                planSeverity={plan.severity}
              />
            }
            editContent={
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
                dirtyStatus={isDirty("status")}
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
            }
          />

          <EditableSectionCard
            title={showRnc8dFlow ? "Problema e cabeçalho 8D" : "Problema"}
            hint={PAC_HELP_TOOLTIPS.sections.problem}
            subtitle={
              showRnc8dFlow
                ? "Identificação do plano e complementos da planilha (material, NF e contato)."
                : undefined
            }
            isEditing={bindSection("problem").isEditing}
            onEdit={bindSection("problem").onEdit}
            onCancelEdit={bindSection("problem").onCancelEdit}
            readContent={
              <>
                {showRnc8dFlow && detail ? <Rnc8dDisciplineProgress detail={detail} /> : null}
                <PlanProblemReadContent
                  showRnc8dFlow={showRnc8dFlow}
                  identification={identificationForm}
                  rnc8dForm={rnc8dForm}
                />
              </>
            }
            editContent={
              <>
                {showRnc8dFlow && detail ? <Rnc8dDisciplineProgress detail={detail} /> : null}
                <PlanProblemSection
                  showRnc8dFlow={showRnc8dFlow}
                  identificationForm={identificationForm}
                  onIdentificationChange={setIdentificationForm}
                  saving={saving}
                  dirtyIdentification={
                    isDirty("identification") || isDirty("rnc8d-material")
                  }
                  identificationSaveKey={
                    isDirty("identification") ? "identification" : "rnc8d-material"
                  }
                  onSaveIdentification={() =>
                    void runSave(
                      isDirty("identification") ? "identification" : "rnc8d-material",
                      saveProblemHeader,
                    )
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
              </>
            }
          />

          <SimilarCasesPanel planId={planId} onNavigate={onNavigate} />

          {showRnc8dFlow ? (
            <>
              <Rnc8dNcDescriptionSection
                value={rnc8dForm}
                onChange={setRnc8dForm}
                sectionEdit={bindSection("rnc8d-nc")}
                saveKey="rnc8d-nc"
                saving={saving}
                dirty={isDirty("rnc8d-nc")}
                onSave={() => void runSave("rnc8d-nc", saveRnc8dReport)}
              />
              <Rnc8dTeamSection
                value={rnc8dForm}
                onChange={setRnc8dForm}
                sectionEdit={bindSection("rnc8d-team")}
                saveKey="rnc8d-team"
                saving={saving}
                dirty={isDirty("rnc8d-team")}
                onSave={() => void runSave("rnc8d-team", saveRnc8dReport)}
                planActions={detail.actions}
                onBindingConflict={setError}
              />
              <Rnc8dContainmentSection
                value={rnc8dForm}
                onChange={setRnc8dForm}
                sectionEdit={bindSection("rnc8d-containment")}
                saveKey="rnc8d-containment"
                saving={saving}
                dirty={isDirty("rnc8d-containment")}
                onSave={() => void runSave("rnc8d-containment", saveRnc8dReport)}
              />

              <EditableSectionCard
                title="4. Estudo da causa do defeito (5 Porquês)"
                hint={PAC_HELP_TOOLTIPS.sections.fiveWhys}
                isEditing={bindSection("five-whys").isEditing}
                onEdit={bindSection("five-whys").onEdit}
                onCancelEdit={bindSection("five-whys").onCancelEdit}
                readContent={<FiveWhysReadContent form={fiveWhysForm} />}
                editContent={
                  <FiveWhysFlowPanel
                    planId={planId}
                    form={fiveWhysForm}
                    saving={saving}
                    dirty={isDirty("five-whys")}
                    onChange={setFiveWhysForm}
                    onSave={runSave}
                  />
                }
              />

              <EditableSectionCard
                title="4. Ishikawa (6M)"
                hint={PAC_HELP_TOOLTIPS.sections.ishikawa}
                isEditing={bindSection("ishikawa").isEditing}
                onEdit={bindSection("ishikawa").onEdit}
                onCancelEdit={bindSection("ishikawa").onCancelEdit}
                readContent={
                  <IshikawaReadContent causes={ishikawaCausesForm} notes={ishikawaNotes} />
                }
                editContent={
                  <IshikawaFishboneDiagram
                    problem={plan.reported_problem || plan.title}
                    causes={ishikawaCausesForm}
                    notes={ishikawaNotes}
                    onChange={setIshikawaCausesForm}
                    onNotesChange={setIshikawaNotes}
                    saving={saving}
                    dirty={isDirty("ishikawa")}
                    onSave={() =>
                      void runSave("ishikawa", async () => {
                        await upsertIshikawa(
                          planId,
                          serializeIshikawaCausesForm(ishikawaCausesForm, ishikawaNotes),
                        );
                      })
                    }
                  />
                }
              />

              <EditableSectionCard
                title="5. Ação corretiva proposta"
                hint={PAC_HELP_TOOLTIPS.sections.actions}
                isEditing={bindSection("actions").isEditing}
                onEdit={bindSection("actions").onEdit}
                onCancelEdit={bindSection("actions").onCancelEdit}
                readContent={<PlanActionsReadContent actions={detail.actions} />}
                editContent={
                  <PlanActionsPanel
                    planId={planId}
                    actions={detail.actions}
                    evidences={detail.evidences ?? []}
                    saving={saving}
                    onSave={runSave}
                    teamMembers={rnc8dForm.team_members}
                  />
                }
              />

              <Rnc8dEffectivenessSection
                value={rnc8dForm}
                onChange={setRnc8dForm}
                sectionEdit={bindSection("rnc8d-effectiveness-8d")}
                saveKey="rnc8d-effectiveness-8d"
                saving={saving}
                dirty={isDirty("rnc8d-effectiveness-8d")}
                onSave={() => void runSave("rnc8d-effectiveness-8d", saveRnc8dReport)}
              />
            </>
          ) : (
            <>
              <EditableSectionCard
                title="Banco de conhecimento e evidências"
                hint={PAC_HELP_TOOLTIPS.sections.evidences}
                subtitle="Anexe prints, PDFs, planilhas e documentos do processo. Visível para o analista e para o agente GPT."
                isEditing={bindSection("evidences").isEditing}
                onEdit={bindSection("evidences").onEdit}
                onCancelEdit={bindSection("evidences").onCancelEdit}
                editLabel="Anexar"
                cancelLabel="Fechar"
                EditIcon={Paperclip}
                readContent={
                  <EvidencePanel
                    planId={planId}
                    evidences={detail.evidences ?? []}
                    actions={detail.actions ?? []}
                    onChanged={load}
                    bare
                    readOnly
                  />
                }
                editContent={
                  <EvidencePanel
                    planId={planId}
                    evidences={detail.evidences ?? []}
                    actions={detail.actions ?? []}
                    onChanged={load}
                    bare
                  />
                }
              />

              <EditableSectionCard
                title="Ishikawa (6M)"
                hint={PAC_HELP_TOOLTIPS.sections.ishikawa}
                isEditing={bindSection("ishikawa").isEditing}
                onEdit={bindSection("ishikawa").onEdit}
                onCancelEdit={bindSection("ishikawa").onCancelEdit}
                readContent={
                  <IshikawaReadContent causes={ishikawaCausesForm} notes={ishikawaNotes} />
                }
                editContent={
                  <IshikawaFishboneDiagram
                    problem={plan.reported_problem || plan.title}
                    causes={ishikawaCausesForm}
                    notes={ishikawaNotes}
                    onChange={setIshikawaCausesForm}
                    onNotesChange={setIshikawaNotes}
                    saving={saving}
                    dirty={isDirty("ishikawa")}
                    onSave={() =>
                      void runSave("ishikawa", async () => {
                        await upsertIshikawa(
                          planId,
                          serializeIshikawaCausesForm(ishikawaCausesForm, ishikawaNotes),
                        );
                      })
                    }
                  />
                }
              />

              <EditableSectionCard
                title="Estudo de causa — Porquês"
                hint={PAC_HELP_TOOLTIPS.sections.fiveWhys}
                isEditing={bindSection("five-whys").isEditing}
                onEdit={bindSection("five-whys").onEdit}
                onCancelEdit={bindSection("five-whys").onCancelEdit}
                readContent={<FiveWhysReadContent form={fiveWhysForm} />}
                editContent={
                  <FiveWhysFlowPanel
                    planId={planId}
                    form={fiveWhysForm}
                    saving={saving}
                    dirty={isDirty("five-whys")}
                    onChange={setFiveWhysForm}
                    onSave={runSave}
                  />
                }
              />

              <EditableSectionCard
                title="Ações corretivas e plano"
                hint={PAC_HELP_TOOLTIPS.sections.actions}
                isEditing={bindSection("actions").isEditing}
                onEdit={bindSection("actions").onEdit}
                onCancelEdit={bindSection("actions").onCancelEdit}
                readContent={<PlanActionsReadContent actions={detail.actions} />}
                editContent={
                  <PlanActionsPanel
                    planId={planId}
                    actions={detail.actions}
                    evidences={detail.evidences ?? []}
                    saving={saving}
                    onSave={runSave}
                  />
                }
              />
            </>
          )}

          <EditableSectionCard
            title={showRnc8dFlow ? "6. Registro de eficácia (PAC)" : "Eficácia"}
            hint={PAC_HELP_TOOLTIPS.sections.effectiveness}
            subtitle={
              showRnc8dFlow
                ? "Fluxo de aprovação do coordenador — complementa a seção 6 da planilha 8D."
                : undefined
            }
            isEditing={bindSection("effectiveness-pac").isEditing}
            onEdit={bindSection("effectiveness-pac").onEdit}
            onCancelEdit={bindSection("effectiveness-pac").onCancelEdit}
            editable={effectivenessUi.canEditSection}
            readContent={
              <>
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
                <EffectivenessPacReadContent
                  status={effectivenessStatus}
                  notes={effectivenessNotes}
                  proposedStatus={plan.effectiveness_proposed_status}
                  rejectionReason={plan.effectiveness_rejection_reason}
                />
              </>
            }
            editContent={
              <>
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
            <IncompletePlanActionsNotice actions={detail?.actions ?? []} />
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
            {effectivenessUi.showRejectionReasonField ? (
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
              {effectivenessUi.canSaveDraft && isDirty("effectiveness-pac") ? (
                <SectionSaveButton
                  saveKey="effectiveness-pac"
                  saving={saving}
                  dirty={isDirty("effectiveness-pac")}
                  label="Salvar eficácia (rascunho)"
                  onSave={() =>
                    void runSave("effectiveness-pac", async () => {
                      await recordEffectivenessReview(
                        planId,
                        effectivenessStatus,
                        effectivenessNotes.trim() || undefined,
                      );
                    })
                  }
                />
              ) : null}
              {effectivenessUi.canSubmit ? (
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
              ) : null}
              {effectivenessUi.canApprove ? (
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
              ) : null}
              {effectivenessUi.canReject ? (
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
              ) : null}
              {effectivenessUi.canRecordDirect ? (
                <button
                  type="button"
                  className="pac-ghost-btn"
                  disabled={saving === "effectiveness"}
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
              ) : null}
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
              </>
            }
          />

          {showRnc8dFlow ? (
            <>
              <Rnc8dPreventiveSection
                value={rnc8dForm}
                onChange={setRnc8dForm}
                sectionEdit={bindSection("rnc8d-preventive")}
                saveKey="rnc8d-preventive"
                saving={saving}
                dirty={isDirty("rnc8d-preventive")}
                onSave={() => void runSave("rnc8d-preventive", saveRnc8dReport)}
              />
              <EditableSectionCard
                title="7. Evidências das ações"
                hint={PAC_HELP_TOOLTIPS.sections.evidences}
                subtitle="Anexe prints, PDFs e documentos do processo (planilha: Inserir evidências)."
                isEditing={bindSection("evidences").isEditing}
                onEdit={bindSection("evidences").onEdit}
                onCancelEdit={bindSection("evidences").onCancelEdit}
                editLabel="Anexar"
                cancelLabel="Fechar"
                EditIcon={Paperclip}
                readContent={
                  <EvidencePanel
                    planId={planId}
                    evidences={detail.evidences ?? []}
                    actions={detail.actions ?? []}
                    onChanged={load}
                    bare
                    readOnly
                  />
                }
                editContent={
                  <EvidencePanel
                    planId={planId}
                    evidences={detail.evidences ?? []}
                    actions={detail.actions ?? []}
                    onChanged={load}
                    bare
                  />
                }
              />
              <Rnc8dClosureSection
                value={rnc8dForm}
                onChange={setRnc8dForm}
                sectionEdit={bindSection("rnc8d-closure")}
                saveKey="rnc8d-closure"
                saving={saving}
                dirty={isDirty("rnc8d-closure")}
                onSave={() => void runSave("rnc8d-closure", saveRnc8dReport)}
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
