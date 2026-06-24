import { useCallback, useEffect, useState } from "react";
import {
  ArrowLeft,
  Cog,
  FlaskConical,
  Leaf,
  Ruler,
  Save,
  Users,
  Wrench,
} from "lucide-react";

import {
  createPlanActions,
  fetchActionPlanDetail,
  recordEffectivenessReview,
  updatePlanAction,
  updatePlanStatus,
  upsertFiveWhys,
  upsertIshikawa,
} from "../api/actionPlansApi";
import { PageHeader } from "../components/PageHeader";
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
  PLAN_STATUSES,
} from "../constants/actionPlans";
import type { ActionPlanDetail, FiveWhysAnalysis, IshikawaAnalysis } from "../types/actionPlan";
import { formatDate, formatDateTime } from "../utils/format";

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
  root_cause: "",
  confidence_level: "medium",
};

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
  const [effectivenessStatus, setEffectivenessStatus] = useState("pending");
  const [effectivenessNotes, setEffectivenessNotes] = useState("");
  const [saving, setSaving] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchActionPlanDetail(planId);
      setDetail(data);
      setStatusValue(data.plan.status);
      setIshikawaForm({ ...EMPTY_ISHIKAWA, ...(data.ishikawa ?? {}) });
      setFiveWhysForm({ ...EMPTY_FIVE_WHYS, ...(data.five_whys ?? {}) });
      setEffectivenessStatus(data.plan.effectiveness_status ?? "pending");
      setEffectivenessNotes("");
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
            <dl className="pac-dl">
              <div>
                <dt>Cliente</dt>
                <dd>{plan.customer_name ?? "—"}</dd>
              </div>
              <div>
                <dt>Filial</dt>
                <dd>{branchLabel(plan.branch_code)}</dd>
              </div>
              <div>
                <dt>Produto</dt>
                <dd>
                  {plan.product_code ?? "—"}
                  {plan.product_description ? ` — ${plan.product_description}` : ""}
                </dd>
              </div>
              <div>
                <dt>Lote</dt>
                <dd>{plan.batch_number ?? "—"}</dd>
              </div>
              <div>
                <dt>Escopo NC</dt>
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
              <div>
                <dt>Status</dt>
                <dd>
                  <StatusBadge status={plan.status} />
                </dd>
              </div>
              <div className="pac-dl__full">
                <dt>Relato</dt>
                <dd>{plan.reported_problem ?? "—"}</dd>
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

          <SectionCard title="5 Porquês">
            <ol className="pac-five-whys">
              {(["why_1", "why_2", "why_3", "why_4", "why_5"] as const).map((key, index) => (
                <li key={key} className="pac-five-whys__step">
                  <span className="pac-five-whys__index">{index + 1}</span>
                  <TextField
                    id={`pac-${key}`}
                    label={`${index + 1}º porquê`}
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

          <SectionCard title="Ações">
            {detail.actions.length ? (
              <div className="pac-table-wrap">
                <table className="pac-table">
                  <thead>
                    <tr>
                      <th>Tipo</th>
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
                      },
                    ]);
                    setNewActionDescription("");
                    setNewActionResponsible("");
                    setNewActionDueDate("");
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
            </FormActions>
          </SectionCard>

          <SectionCard title="Histórico">
            {detail.history.length ? (
              <ul className="pac-timeline">
                {detail.history.map((event) => (
                  <li key={event.id}>
                    <strong>{event.event_type}</strong>
                    <span>{formatDateTime(event.created_at)}</span>
                    {event.comment ? <p>{event.comment}</p> : null}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="pac-muted">Sem eventos registrados.</p>
            )}
          </SectionCard>
        </div>
      ) : null}
    </>
  );
}
