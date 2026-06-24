import { useCallback, useEffect, useState, type ReactNode } from "react";
import { ArrowLeft, Save } from "lucide-react";

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
import { SeverityBadge, StatusBadge } from "../components/StatusBadge";
import { StateAlert } from "../components/StateAlert";
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

function DetailSection({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="pac-card pac-detail-section">
      <h2 className="pac-section-title">{title}</h2>
      {children}
    </section>
  );
}

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
          <DetailSection title="Problema">
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
              <div className="pac-filter-box">
                <label htmlFor="pac-plan-status">Atualizar status</label>
                <select
                  id="pac-plan-status"
                  value={statusValue}
                  onChange={(event) => setStatusValue(event.target.value)}
                >
                  {PLAN_STATUSES.map((item) => (
                    <option key={item.value} value={item.value}>
                      {item.label}
                    </option>
                  ))}
                </select>
              </div>
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
          </DetailSection>

          <DetailSection title="Ishikawa">
            <div className="pac-form-grid">
              {(
                [
                  ["machine", "Máquina"],
                  ["method_process", "Método"],
                  ["material", "Material"],
                  ["manpower", "Mão de obra"],
                  ["measurement", "Medição"],
                  ["environment", "Meio ambiente"],
                ] as const
              ).map(([key, label]) => (
                <div key={key} className="pac-filter-box">
                  <label htmlFor={`pac-ishikawa-${key}`}>{label}</label>
                  <input
                    id={`pac-ishikawa-${key}`}
                    value={ishikawaForm[key] ?? ""}
                    onChange={(event) =>
                      setIshikawaForm((current) => ({ ...current, [key]: event.target.value }))
                    }
                  />
                </div>
              ))}
            </div>
            <div className="pac-form-actions">
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
            </div>
          </DetailSection>

          <DetailSection title="5 Porquês">
            <div className="pac-form-grid">
              {(["why_1", "why_2", "why_3", "why_4", "why_5"] as const).map((key, index) => (
                <div key={key} className="pac-filter-box pac-filter-box--full">
                  <label htmlFor={`pac-${key}`}>{index + 1}º porquê</label>
                  <input
                    id={`pac-${key}`}
                    value={fiveWhysForm[key] ?? ""}
                    onChange={(event) =>
                      setFiveWhysForm((current) => ({ ...current, [key]: event.target.value }))
                    }
                  />
                </div>
              ))}
              <div className="pac-filter-box pac-filter-box--full">
                <label htmlFor="pac-root-cause">Causa raiz</label>
                <input
                  id="pac-root-cause"
                  value={fiveWhysForm.root_cause ?? ""}
                  onChange={(event) =>
                    setFiveWhysForm((current) => ({ ...current, root_cause: event.target.value }))
                  }
                />
              </div>
            </div>
            <div className="pac-form-actions">
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
            </div>
          </DetailSection>

          <DetailSection title="Ações">
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

            <div className="pac-inline-form pac-inline-form--stack">
              <div className="pac-form-grid">
                <div className="pac-filter-box">
                  <label htmlFor="pac-new-action-type">Tipo</label>
                  <select
                    id="pac-new-action-type"
                    value={newActionType}
                    onChange={(event) => setNewActionType(event.target.value)}
                  >
                    {Object.entries(ACTION_TYPES).map(([value, label]) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="pac-filter-box">
                  <label htmlFor="pac-new-action-responsible">Responsável</label>
                  <input
                    id="pac-new-action-responsible"
                    value={newActionResponsible}
                    onChange={(event) => setNewActionResponsible(event.target.value)}
                  />
                </div>
                <div className="pac-filter-box">
                  <label htmlFor="pac-new-action-due">Prazo</label>
                  <input
                    id="pac-new-action-due"
                    type="date"
                    value={newActionDueDate}
                    onChange={(event) => setNewActionDueDate(event.target.value)}
                  />
                </div>
                <div className="pac-filter-box pac-filter-box--full">
                  <label htmlFor="pac-new-action-desc">Descrição</label>
                  <input
                    id="pac-new-action-desc"
                    value={newActionDescription}
                    onChange={(event) => setNewActionDescription(event.target.value)}
                  />
                </div>
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
          </DetailSection>

          <DetailSection title="Eficácia">
            <div className="pac-inline-form pac-inline-form--stack">
              <div className="pac-form-grid">
                <div className="pac-filter-box">
                  <label htmlFor="pac-effectiveness-status">Resultado</label>
                  <select
                    id="pac-effectiveness-status"
                    value={effectivenessStatus}
                    onChange={(event) => setEffectivenessStatus(event.target.value)}
                  >
                    {EFFECTIVENESS_STATUSES.map((item) => (
                      <option key={item.value} value={item.value}>
                        {item.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="pac-filter-box pac-filter-box--full">
                  <label htmlFor="pac-effectiveness-notes">Observações</label>
                  <textarea
                    id="pac-effectiveness-notes"
                    rows={3}
                    value={effectivenessNotes}
                    onChange={(event) => setEffectivenessNotes(event.target.value)}
                    placeholder="Evidências e conclusão da verificação de eficácia"
                  />
                </div>
              </div>
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
            </div>
          </DetailSection>

          <DetailSection title="Histórico">
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
          </DetailSection>
        </div>
      ) : null}
    </>
  );
}
