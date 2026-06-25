import { useCallback, useEffect, useState } from "react";
import {
  ArrowLeft,
  Cog,
  Download,
  FlaskConical,
  Leaf,
  Ruler,
  Save,
  Users,
  Wrench,
} from "lucide-react";

import {
  createPlanActions,
  exportRnc8dSpreadsheet,
  fetchActionPlanDetail,
  promoteSolutionPattern,
  recordEffectivenessReview,
  updateActionPlan,
  updatePlanAction,
  updatePlanStatus,
  upsertFiveWhys,
  upsertIshikawa,
  upsertRnc8dReport,
} from "../api/actionPlansApi";
import { EvidencePanel } from "../components/EvidencePanel";
import { PlanTimeline } from "../components/PlanTimeline";
import { SimilarCasesPanel } from "../components/SimilarCasesPanel";
import { PageHeader } from "../components/PageHeader";
import { Rnc8dReportEditor } from "../components/Rnc8dReportEditor";
import { ScopeBadge, SeverityBadge, StatusBadge } from "../components/StatusBadge";
import { StateAlert } from "../components/StateAlert";
import { FormActions } from "../components/ui/FormActions";
import { SectionCard } from "../components/ui/SectionCard";
import { SelectField } from "../components/ui/SelectField";
import { StatusPipeline } from "../components/ui/StatusPipeline";
import { TextAreaField } from "../components/ui/TextAreaField";
import { TextField } from "../components/ui/TextField";
import {
  ACTION_STATUSES,
  ACTION_TYPES,
  actionTypeLabel,
  branchLabel,
  dashboardPath,
  EFFECTIVENESS_STATUSES,
  listPath,
  PAC_BRANCH_OPTIONS,
  PAC_NONCONFORMITY_SCOPES,
  PLAN_SEVERITIES,
  PLAN_STATUSES,
} from "../constants/actionPlans";
import type { ActionPlanDetail, FiveWhysAnalysis, IshikawaAnalysis } from "../types/actionPlan";
import type { Rnc8dReportPayload } from "../types/rnc8d";
import { emptyRnc8dPayload } from "../types/rnc8d";
import { formatDate } from "../utils/format";
import { formatSymptomTags, parseSymptomTags } from "../utils/symptomTags";

type Props = {
  planId: string;
  onNavigate: (path: string) => void;
};

const EMPTY_ISHIKAWA: IshikawaAnalysis = {
  machine: "",
  method_process: "",
  material: "",
  manpower: "",
  measurement: "",
  environment: "",
  notes: "",
};

const EMPTY_FIVE_WHYS: FiveWhysAnalysis = {
  why_1: "",
  why_2: "",
  why_3: "",
  why_4: "",
  why_5: "",
  detection_why_1: "",
  detection_why_2: "",
  detection_why_3: "",
  detection_why_4: "",
  detection_why_5: "",
  root_cause: "",
  confidence_level: "medium",
};

const CAUSE_TRACK_OPTIONS = [
  { value: "", label: "—" },
  { value: "occurrence", label: "Ocorrência" },
  { value: "detection", label: "Detecção" },
];

const ISHIKAWA_FIELDS = [
  { key: "machine" as const, label: "Máquina", icon: Cog },
  { key: "method_process" as const, label: "Método", icon: Wrench },
  { key: "material" as const, label: "Material", icon: FlaskConical },
  { key: "manpower" as const, label: "Mão de obra", icon: Users },
  { key: "measurement" as const, label: "Medição", icon: Ruler },
  { key: "environment" as const, label: "Meio ambiente", icon: Leaf },
];

export function PlanDetailPage({ planId, onNavigate }: Props) {
  const [detail, setDetail] = useState<ActionPlanDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [statusValue, setStatusValue] = useState("");
  const [ishikawaForm, setIshikawaForm] = useState<IshikawaAnalysis>(EMPTY_ISHIKAWA);
  const [fiveWhysForm, setFiveWhysForm] = useState<FiveWhysAnalysis>(EMPTY_FIVE_WHYS);
  const [newActionType, setNewActionType] = useState("corrective");
  const [newActionDescription, setNewActionDescription] = useState("");
  const [newActionResponsible, setNewActionResponsible] = useState("");
  const [newActionDueDate, setNewActionDueDate] = useState("");
  const [newActionCauseTrack, setNewActionCauseTrack] = useState("");
  const [rnc8dForm, setRnc8dForm] = useState<Rnc8dReportPayload>({});
  const [effectivenessStatus, setEffectivenessStatus] = useState("pending");
  const [effectivenessNotes, setEffectivenessNotes] = useState("");
  const [saving, setSaving] = useState<string | null>(null);
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
  });

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchActionPlanDetail(planId);
      setDetail(data);
      setStatusValue(data.plan.status);
      setIshikawaForm({ ...EMPTY_ISHIKAWA, ...(data.ishikawa ?? {}) });
      setFiveWhysForm({ ...EMPTY_FIVE_WHYS, ...(data.five_whys ?? {}) });
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
      setEffectivenessStatus(data.plan.effectiveness_status ?? "pending");
      setEffectivenessNotes("");
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
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar plano.");
    } finally {
      setLoading(false);
    }
  }, [planId]);

  useEffect(() => {
    void load();
  }, [load]);

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
  const statusOptions = PLAN_STATUSES.map((item) => ({ value: item.value, label: item.label }));
  const isRnc8dTemplate = plan?.customer_template === "rnc_8d";

  async function handleExportRnc8d() {
    setError(null);
    try {
      const registry = plan?.client_nc_registry || plan?.code || planId.slice(0, 8);
      await exportRnc8dSpreadsheet(planId, `RNC_${registry}_8D.xlsx`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao gerar planilha.");
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
            {isRnc8dTemplate ? (
              <button type="button" className="pac-primary-btn" onClick={() => void handleExportRnc8d()}>
                <Download size={16} />
                Gerar planilha 8D
              </button>
            ) : null}
          </>
        }
      />
      {error ? <StateAlert variant="error">{error}</StateAlert> : null}
      {success ? <StateAlert variant="success">{success}</StateAlert> : null}
      {loading && !detail ? <p className="pac-muted">Carregando detalhe…</p> : null}

      {plan ? (
        <div className="pac-detail-grid">
          <SectionCard title="Problema">
            <StatusPipeline currentStatus={plan.status} />
            <div className="pac-form-grid">
              <TextField
                id="pac-detail-title"
                label="Título"
                value={identificationForm.title}
                onChange={(title) => setIdentificationForm((c) => ({ ...c, title }))}
                fullWidth
              />
              <TextField
                id="pac-detail-customer"
                label="Cliente"
                value={identificationForm.customer_name}
                onChange={(customer_name) =>
                  setIdentificationForm((c) => ({ ...c, customer_name }))
                }
              />
              <SelectField
                id="pac-detail-branch"
                label="Filial"
                options={PAC_BRANCH_OPTIONS.map((item) => ({ value: item.value, label: item.label }))}
                value={identificationForm.branch_code}
                onChange={(branch_code) => setIdentificationForm((c) => ({ ...c, branch_code }))}
                searchable={false}
              />
              <SelectField
                id="pac-detail-scope"
                label="Escopo NC"
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
                label="Código produto"
                value={identificationForm.product_code}
                onChange={(product_code) => setIdentificationForm((c) => ({ ...c, product_code }))}
              />
              <TextField
                id="pac-detail-product-desc"
                label="Descrição produto"
                value={identificationForm.product_description}
                onChange={(product_description) =>
                  setIdentificationForm((c) => ({ ...c, product_description }))
                }
              />
              <TextField
                id="pac-detail-batch"
                label="Lote"
                value={identificationForm.batch_number}
                onChange={(batch_number) => setIdentificationForm((c) => ({ ...c, batch_number }))}
              />
              <TextField
                id="pac-detail-department"
                label="Área"
                value={identificationForm.department}
                onChange={(department) => setIdentificationForm((c) => ({ ...c, department }))}
              />
              <TextField
                id="pac-detail-failure"
                label="Modo de falha"
                value={identificationForm.failure_mode}
                onChange={(failure_mode) => setIdentificationForm((c) => ({ ...c, failure_mode }))}
              />
              <TextField
                id="pac-detail-problem-category"
                label="Categoria do problema"
                value={identificationForm.problem_category}
                onChange={(problem_category) =>
                  setIdentificationForm((c) => ({ ...c, problem_category }))
                }
              />
              <TextField
                id="pac-detail-symptom-tags"
                label="Tags de sintoma"
                value={identificationForm.symptom_tags_text}
                onChange={(symptom_tags_text) =>
                  setIdentificationForm((c) => ({ ...c, symptom_tags_text }))
                }
                placeholder="oxidacao, trinca"
              />
              <SelectField
                id="pac-detail-severity"
                label="Severidade"
                options={PLAN_SEVERITIES.map((item) => ({ value: item.value, label: item.label }))}
                value={identificationForm.severity}
                onChange={(severity) => setIdentificationForm((c) => ({ ...c, severity }))}
                searchable
              />
              {isRnc8dTemplate ? (
                <TextField
                  id="pac-detail-nc-registry"
                  label="Registro NC do cliente"
                  value={identificationForm.client_nc_registry}
                  onChange={(client_nc_registry) =>
                    setIdentificationForm((c) => ({ ...c, client_nc_registry }))
                  }
                />
              ) : null}
              <TextAreaField
                id="pac-detail-problem"
                label="Relato do problema"
                value={identificationForm.reported_problem}
                onChange={(reported_problem) =>
                  setIdentificationForm((c) => ({ ...c, reported_problem }))
                }
                fullWidth
              />
            </div>
            <FormActions align="end">
              <button
                type="button"
                className="pac-primary-btn"
                disabled={saving === "identification"}
                onClick={() =>
                  void runSave("identification", async () => {
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
                    });
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
              <SelectField
                id="pac-plan-status"
                label="Atualizar status"
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
            </div>
          </SectionCard>

          <SimilarCasesPanel planId={planId} onNavigate={onNavigate} />

          <PlanTimeline detail={detail} />

          {!isRnc8dTemplate ? (
            <SectionCard title="Template do relatório">
              <p className="pac-muted">
                Ative o formulário 8D (materiais adquiridos) para preenchimento manual e exportação da planilha padrão do cliente.
              </p>
              <button
                type="button"
                className="pac-primary-btn"
                disabled={saving === "activate-rnc-8d"}
                onClick={() =>
                  void runSave("activate-rnc-8d", async () => {
                    await upsertRnc8dReport(planId, {
                      ...rnc8dForm,
                      template_payload: rnc8dForm.template_payload ?? emptyRnc8dPayload(),
                    });
                  })
                }
              >
                {saving === "activate-rnc-8d" ? "Ativando…" : "Ativar relatório 8D"}
              </button>
            </SectionCard>
          ) : null}

          {isRnc8dTemplate ? (
            <Rnc8dReportEditor
              value={rnc8dForm}
              onChange={setRnc8dForm}
              saving={saving === "rnc-8d"}
              onSave={() =>
                runSave("rnc-8d", async () => {
                  await upsertRnc8dReport(planId, rnc8dForm);
                })
              }
            />
          ) : null}

          <EvidencePanel
            planId={planId}
            evidences={detail.evidences ?? []}
            actions={detail.actions ?? []}
            onChanged={load}
          />

          <SectionCard title="Ishikawa (6M)">
            <div className="pac-ishikawa-grid">
              {ISHIKAWA_FIELDS.map(({ key, label, icon: Icon }) => (
                <div key={key} className="pac-ishikawa-item">
                  <div className="pac-ishikawa-item__head">
                    <span className="pac-ishikawa-item__icon" aria-hidden="true">
                      <Icon size={16} />
                    </span>
                    <label htmlFor={`pac-ishikawa-${key}`}>{label}</label>
                  </div>
                  <input
                    id={`pac-ishikawa-${key}`}
                    className="pac-field__control"
                    value={ishikawaForm[key] ?? ""}
                    onChange={(event) =>
                      setIshikawaForm((current) => ({ ...current, [key]: event.target.value }))
                    }
                    placeholder={`Causas relacionadas a ${label.toLowerCase()}`}
                  />
                </div>
              ))}
            </div>
            <FormActions>
              <button
                type="button"
                className="pac-primary-btn"
                disabled={saving === "ishikawa"}
                onClick={() =>
                  void runSave("ishikawa", async () => {
                    await upsertIshikawa(planId, ishikawaForm);
                  })
                }
              >
                {saving === "ishikawa" ? "Salvando…" : "Salvar Ishikawa"}
              </button>
            </FormActions>
          </SectionCard>

          <SectionCard title="4. Estudo de causa — 5 Porquês (Ocorrência)">
            <ol className="pac-five-whys">
              {(["why_1", "why_2", "why_3", "why_4", "why_5"] as const).map((key, index) => (
                <li key={key} className="pac-five-whys__step">
                  <span className="pac-five-whys__index">{index + 1}</span>
                  <TextField
                    id={`pac-${key}`}
                    label={`${index + 1}º porquê (ocorrência)`}
                    value={fiveWhysForm[key] ?? ""}
                    onChange={(value) => setFiveWhysForm((current) => ({ ...current, [key]: value }))}
                    fullWidth
                  />
                </li>
              ))}
            </ol>
            <h3 className="pac-subsection-title">Trilha de detecção</h3>
            <ol className="pac-five-whys">
                {(
                  [
                    "detection_why_1",
                    "detection_why_2",
                    "detection_why_3",
                    "detection_why_4",
                    "detection_why_5",
                  ] as const
                ).map((key, index) => (
                  <li key={key} className="pac-five-whys__step">
                    <span className="pac-five-whys__index">{index + 1}</span>
                    <TextField
                      id={`pac-${key}`}
                      label={`${index + 1}º porquê (detecção)`}
                      value={fiveWhysForm[key] ?? ""}
                      onChange={(value) => setFiveWhysForm((current) => ({ ...current, [key]: value }))}
                      fullWidth
                    />
                  </li>
                ))}
              </ol>
            <TextField
              id="pac-root-cause"
              label="Causa raiz"
              value={fiveWhysForm.root_cause ?? ""}
              onChange={(root_cause) => setFiveWhysForm((current) => ({ ...current, root_cause }))}
              fullWidth
            />
            <FormActions>
              <button
                type="button"
                className="pac-primary-btn"
                disabled={saving === "five-whys"}
                onClick={() =>
                  void runSave("five-whys", async () => {
                    await upsertFiveWhys(planId, fiveWhysForm);
                  })
                }
              >
                {saving === "five-whys" ? "Salvando…" : "Salvar 5 Porquês"}
              </button>
            </FormActions>
          </SectionCard>

          <SectionCard title="5. Ações corretivas e plano">
            {detail.actions.length ? (
              <div className="pac-table-wrap">
                <table className="pac-table">
                  <thead>
                    <tr>
                      <th>Tipo</th>
                      <th>Ocorr./Det.</th>
                      <th>Descrição</th>
                      <th>Responsável</th>
                      <th>Prazo</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {detail.actions.map((action) => (
                      <tr key={action.id}>
                        <td>{actionTypeLabel(action.action_type)}</td>
                        <td>{action.cause_track === "detection" ? "Detecção" : action.cause_track === "occurrence" ? "Ocorrência" : "—"}</td>
                        <td>{action.description}</td>
                        <td>{action.responsible_name ?? "—"}</td>
                        <td>{formatDate(action.due_date)}</td>
                        <td>
                          <select
                            className="pac-table-select"
                            value={action.status}
                            onChange={(event) =>
                              void runSave(`action-${action.id}`, async () => {
                                await updatePlanAction(planId, action.id, {
                                  status: event.target.value,
                                });
                              })
                            }
                          >
                            {Object.entries(ACTION_STATUSES).map(([value, label]) => (
                              <option key={value} value={value}>
                                {label}
                              </option>
                            ))}
                          </select>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="pac-muted">Nenhuma ação cadastrada.</p>
            )}

            <div className="pac-inline-form pac-inline-form--stack pac-new-action-form">
              <div className="pac-form-grid">
                <SelectField
                  id="pac-new-action-type"
                  label="Tipo"
                  options={Object.entries(ACTION_TYPES).map(([value, label]) => ({ value, label }))}
                  value={newActionType}
                  onChange={setNewActionType}
                  searchable={false}
                />
                <SelectField
                  id="pac-new-action-track"
                  label="Ocorrência / Detecção"
                  options={CAUSE_TRACK_OPTIONS}
                  value={newActionCauseTrack}
                  onChange={setNewActionCauseTrack}
                  searchable={false}
                />
                <TextField
                  id="pac-new-action-responsible"
                  label="Responsável"
                  value={newActionResponsible}
                  onChange={setNewActionResponsible}
                />
                <TextField
                  id="pac-new-action-due"
                  label="Prazo"
                  type="date"
                  value={newActionDueDate}
                  onChange={setNewActionDueDate}
                />
                <TextField
                  id="pac-new-action-desc"
                  label="Descrição"
                  value={newActionDescription}
                  onChange={setNewActionDescription}
                  fullWidth
                />
              </div>
              <button
                type="button"
                className="pac-primary-btn"
                disabled={saving === "new-action"}
                onClick={() =>
                  void runSave("new-action", async () => {
                    if (!newActionDescription.trim()) {
                      throw new Error("Informe a descrição da ação.");
                    }
                    await createPlanActions(planId, [
                      {
                        action_type: newActionType,
                        description: newActionDescription.trim(),
                        responsible_name: newActionResponsible.trim() || undefined,
                        due_date: newActionDueDate || undefined,
                        cause_track: newActionCauseTrack || undefined,
                      },
                    ]);
                    setNewActionDescription("");
                    setNewActionResponsible("");
                    setNewActionDueDate("");
                    setNewActionCauseTrack("");
                  })
                }
              >
                {saving === "new-action" ? "Salvando…" : "Adicionar ação"}
              </button>
            </div>
          </SectionCard>

          <SectionCard title="Eficácia">
            <div className="pac-form-grid">
              <SelectField
                id="pac-effectiveness-status"
                label="Resultado"
                options={EFFECTIVENESS_STATUSES.map((item) => ({
                  value: item.value,
                  label: item.label,
                }))}
                value={effectivenessStatus}
                onChange={setEffectivenessStatus}
                searchable={false}
              />
              <TextAreaField
                id="pac-effectiveness-notes"
                label="Observações"
                value={effectivenessNotes}
                onChange={setEffectivenessNotes}
                placeholder="Evidências e conclusão da verificação de eficácia"
                fullWidth
              />
            </div>
            <FormActions>
              <button
                type="button"
                className="pac-primary-btn"
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
                {saving === "effectiveness" ? "Salvando…" : "Registrar eficácia"}
              </button>
              {["effective", "partially_effective"].includes(plan.effectiveness_status ?? "") ? (
                <button
                  type="button"
                  className="pac-ghost-btn"
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
        </div>
      ) : null}
    </>
  );
}
