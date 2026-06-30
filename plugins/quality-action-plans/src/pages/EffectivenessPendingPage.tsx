import { Fragment, useCallback, useEffect, useState } from "react";
import { Eye, X } from "lucide-react";

import {
  approveEffectivenessReview,
  fetchPendingEffectivenessReviews,
  rejectEffectivenessReview,
} from "../api/actionPlansApi";
import { AppNav } from "../components/AppNav";
import { PageHeader } from "../components/PageHeader";
import { OpenPlanActionsBadge } from "../components/OpenPlanActionsBadge";
import { ScopeBadge, SeverityBadge } from "../components/StatusBadge";
import { StateAlert } from "../components/StateAlert";
import { TableHeaderCell } from "../components/ui/HelpTooltip";
import { TextAreaField } from "../components/ui/TextAreaField";
import { PAC_HELP_TOOLTIPS } from "../content/helpTooltips";
import {
  branchLabel,
  dashboardPath,
  detailPath,
  EFFECTIVENESS_STATUSES,
} from "../constants/actionPlans";
import type { ActionPlanSummary } from "../types/actionPlan";
import { formatDateTime } from "../utils/format";
import { formatEffectivenessSubmittedBy } from "../utils/actorDisplay";
import { usePacPermissions } from "../context/PacPermissionsContext";

const T = PAC_HELP_TOOLTIPS.tables;

type Props = {
  onNavigate: (path: string) => void;
};

function proposedLabel(value?: string | null): string {
  if (!value) return "—";
  return EFFECTIVENESS_STATUSES.find((item) => item.value === value)?.label ?? value;
}

export function EffectivenessPendingPage({ onNavigate }: Props) {
  const { canValidateEffectiveness, loading: permissionsLoading } = usePacPermissions();
  const [items, setItems] = useState<ActionPlanSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [savingId, setSavingId] = useState<string | null>(null);
  const [rejectPlanId, setRejectPlanId] = useState<string | null>(null);
  const [rejectReason, setRejectReason] = useState("");

  const load = useCallback(async () => {
    if (!canValidateEffectiveness) {
      setItems([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const data = await fetchPendingEffectivenessReviews(1, 100);
      setItems(data.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar aprovações pendentes.");
    } finally {
      setLoading(false);
    }
  }, [canValidateEffectiveness]);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleApprove(planId: string) {
    setSavingId(planId);
    setError(null);
    setSuccess(null);
    try {
      await approveEffectivenessReview(planId);
      setSuccess("Eficácia aprovada.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao aprovar eficácia.");
    } finally {
      setSavingId(null);
    }
  }

  async function handleReject(planId: string) {
    const reason = rejectReason.trim();
    if (reason.length < 5) {
      setError("Informe o motivo da rejeição com ao menos 5 caracteres.");
      return;
    }
    setSavingId(planId);
    setError(null);
    setSuccess(null);
    try {
      await rejectEffectivenessReview(planId, reason);
      setSuccess("Submissão rejeitada.");
      closeRejectForm();
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao rejeitar eficácia.");
    } finally {
      setSavingId(null);
    }
  }

  function closeRejectForm() {
    setRejectPlanId(null);
    setRejectReason("");
  }

  function openRejectForm(planId: string) {
    if (rejectPlanId === planId) {
      closeRejectForm();
      return;
    }
    setRejectPlanId(planId);
    setRejectReason("");
    setError(null);
  }

  return (
    <>
      <PageHeader
        title="Aprovações de eficácia"
        subtitle="Fila de submissões aguardando validação do coordenador."
      />
      <AppNav active="effectiveness-pending" onNavigate={onNavigate} />
      {!permissionsLoading && !canValidateEffectiveness ? (
        <StateAlert>
          Você não tem permissão para validar eficácia. Solicite a permissão{" "}
          <strong>quality-action-plans.validate-effectiveness</strong> ao administrador.
          <div style={{ marginTop: "0.75rem" }}>
            <button
              type="button"
              className="pac-ghost-btn"
              onClick={() => onNavigate(dashboardPath())}
            >
              Voltar ao resumo
            </button>
          </div>
        </StateAlert>
      ) : null}
      {canValidateEffectiveness && error ? <StateAlert variant="error">{error}</StateAlert> : null}
      {canValidateEffectiveness && success ? (
        <StateAlert variant="success">{success}</StateAlert>
      ) : null}

      {canValidateEffectiveness ? (
      <section className="pac-card">
        <div className="pac-section-card__header pac-table-header">
          <h2 className="pac-section-title">Pendentes</h2>
          <span className="pac-muted pac-table-header__count">
            {loading ? "…" : `${items.length} plano(s)`}
          </span>
        </div>

        {loading ? (
          <p className="pac-muted">Carregando fila…</p>
        ) : !items.length ? (
          <p className="pac-muted">Nenhuma submissão de eficácia aguardando aprovação.</p>
        ) : (
          <div className="pac-table-wrap">
            <table className="pac-table">
              <thead>
                <tr>
                  <TableHeaderCell label="Código" hint={T.code} />
                  <TableHeaderCell label="Título" hint={T.title} />
                  <TableHeaderCell label="Filial" hint={T.branch} />
                  <TableHeaderCell label="Escopo" hint={T.scope} />
                  <TableHeaderCell label="Severidade" hint={T.severity} />
                  <TableHeaderCell label="Proposta" hint={T.proposedEffectiveness} />
                  <TableHeaderCell label="Submetido em" hint={T.submittedAt} />
                  <TableHeaderCell label="Por" hint={T.submittedBy} />
                  <TableHeaderCell
                    label="Ações"
                    hint={T.rowActions}
                    className="pac-table__actions-col"
                  />
                </tr>
              </thead>
              <tbody>
                {items.map((plan) => (
                  <Fragment key={plan.id}>
                    <tr>
                      <td>{plan.code ?? "—"}</td>
                      <td>{plan.title}</td>
                      <td>{branchLabel(plan.branch_code)}</td>
                      <td>
                        <ScopeBadge scope={plan.nonconformity_scope} />
                      </td>
                      <td>
                        <SeverityBadge severity={plan.severity} />
                      </td>
                      <td>{proposedLabel(plan.effectiveness_proposed_status)}</td>
                      <td>{formatDateTime(plan.effectiveness_submitted_at)}</td>
                      <td>{formatEffectivenessSubmittedBy(plan)}</td>
                      <td>
                        <div className="pac-table-actions">
                          <OpenPlanActionsBadge
                            count={plan.incomplete_actions_count ?? 0}
                            onClick={() => onNavigate(detailPath(plan.id))}
                          />
                          <button
                            type="button"
                            className="pac-icon-btn"
                            title="Ver plano"
                            onClick={() => onNavigate(detailPath(plan.id))}
                          >
                            <Eye size={16} />
                          </button>
                          <button
                            type="button"
                            className="pac-primary-btn pac-btn--sm"
                            disabled={savingId === plan.id}
                            onClick={() => void handleApprove(plan.id)}
                          >
                            Aprovar
                          </button>
                          <button
                            type="button"
                            className={`pac-ghost-btn pac-btn--sm${
                              rejectPlanId === plan.id ? " pac-btn--active" : ""
                            }`}
                            disabled={savingId === plan.id}
                            onClick={() => openRejectForm(plan.id)}
                          >
                            {rejectPlanId === plan.id ? "Cancelar" : "Rejeitar"}
                          </button>
                        </div>
                      </td>
                    </tr>
                    {rejectPlanId === plan.id ? (
                      <tr className="pac-table__reject-row">
                        <td colSpan={9}>
                          <div className="pac-effectiveness-reject-panel">
                            <div className="pac-effectiveness-reject-panel__header">
                              <div>
                                <strong>Motivo da rejeição</strong>
                                <p className="pac-muted pac-effectiveness-reject-panel__hint">
                                  {plan.code ?? plan.id} — descreva o que deve ser corrigido antes de
                                  uma nova submissão.
                                </p>
                              </div>
                              <button
                                type="button"
                                className="pac-ghost-btn pac-ghost-btn--icon"
                                aria-label="Fechar formulário de rejeição"
                                title="Fechar"
                                disabled={savingId === plan.id}
                                onClick={closeRejectForm}
                              >
                                <X size={18} />
                              </button>
                            </div>
                            <TextAreaField
                              id={`pac-reject-${plan.id}`}
                              label="Motivo"
                              hint={PAC_HELP_TOOLTIPS.detail.effectivenessRejection}
                              value={rejectReason}
                              onChange={setRejectReason}
                              placeholder="Descreva o motivo da rejeição (mínimo 5 caracteres)"
                              rows={6}
                              fullWidth
                            />
                            <div className="pac-effectiveness-reject-panel__actions">
                              <button
                                type="button"
                                className="pac-ghost-btn"
                                disabled={savingId === plan.id}
                                onClick={closeRejectForm}
                              >
                                Cancelar
                              </button>
                              <button
                                type="button"
                                className="pac-primary-btn"
                                disabled={savingId === plan.id || rejectReason.trim().length < 5}
                                onClick={() => void handleReject(plan.id)}
                              >
                                {savingId === plan.id ? "Salvando…" : "Confirmar rejeição"}
                              </button>
                            </div>
                          </div>
                        </td>
                      </tr>
                    ) : null}
                  </Fragment>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
      ) : null}
    </>
  );
}
