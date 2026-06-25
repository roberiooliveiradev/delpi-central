import { useCallback, useEffect, useState } from "react";
import { Eye } from "lucide-react";

import {
  approveEffectivenessReview,
  fetchPendingEffectivenessReviews,
  rejectEffectivenessReview,
} from "../api/actionPlansApi";
import { AppNav } from "../components/AppNav";
import { PageHeader } from "../components/PageHeader";
import { ScopeBadge, SeverityBadge } from "../components/StatusBadge";
import { StateAlert } from "../components/StateAlert";
import { TextAreaField } from "../components/ui/TextAreaField";
import {
  branchLabel,
  detailPath,
  EFFECTIVENESS_STATUSES,
} from "../constants/actionPlans";
import type { ActionPlanSummary } from "../types/actionPlan";
import { formatDateTime } from "../utils/format";

type Props = {
  onNavigate: (path: string) => void;
};

function proposedLabel(value?: string | null): string {
  if (!value) return "—";
  return EFFECTIVENESS_STATUSES.find((item) => item.value === value)?.label ?? value;
}

export function EffectivenessPendingPage({ onNavigate }: Props) {
  const [items, setItems] = useState<ActionPlanSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [savingId, setSavingId] = useState<string | null>(null);
  const [rejectPlanId, setRejectPlanId] = useState<string | null>(null);
  const [rejectReason, setRejectReason] = useState("");

  const load = useCallback(async () => {
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
  }, []);

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
      setRejectPlanId(null);
      setRejectReason("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao rejeitar eficácia.");
    } finally {
      setSavingId(null);
    }
  }

  return (
    <>
      <PageHeader
        title="Aprovações de eficácia"
        subtitle="Fila de submissões aguardando validação do coordenador."
      />
      <AppNav active="effectiveness-pending" onNavigate={onNavigate} />
      {error ? <StateAlert variant="error">{error}</StateAlert> : null}
      {success ? <StateAlert variant="success">{success}</StateAlert> : null}

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
                  <th>Código</th>
                  <th>Título</th>
                  <th>Filial</th>
                  <th>Escopo</th>
                  <th>Severidade</th>
                  <th>Proposta</th>
                  <th>Submetido em</th>
                  <th>Por</th>
                  <th aria-label="Ações" />
                </tr>
              </thead>
              <tbody>
                {items.map((plan) => (
                  <tr key={plan.id}>
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
                    <td>{plan.effectiveness_submitted_by ?? "—"}</td>
                    <td>
                      <div className="pac-table-actions">
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
                          className="pac-ghost-btn pac-btn--sm"
                          disabled={savingId === plan.id}
                          onClick={() => {
                            setRejectPlanId(plan.id);
                            setRejectReason("");
                          }}
                        >
                          Rejeitar
                        </button>
                      </div>
                      {rejectPlanId === plan.id ? (
                        <div className="pac-inline-form" style={{ marginTop: "8px", minWidth: "240px" }}>
                          <TextAreaField
                            id={`pac-reject-${plan.id}`}
                            label="Motivo"
                            value={rejectReason}
                            onChange={setRejectReason}
                            placeholder="Motivo da rejeição"
                            fullWidth
                          />
                          <button
                            type="button"
                            className="pac-primary-btn pac-btn--sm"
                            disabled={savingId === plan.id || rejectReason.trim().length < 5}
                            onClick={() => void handleReject(plan.id)}
                          >
                            Confirmar rejeição
                          </button>
                        </div>
                      ) : null}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  );
}
