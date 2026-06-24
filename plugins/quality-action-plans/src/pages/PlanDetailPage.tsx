import { useCallback, useEffect, useState, type ReactNode } from "react";
import { ArrowLeft } from "lucide-react";

import { fetchActionPlanDetail } from "../api/actionPlansApi";
import { PageHeader } from "../components/PageHeader";
import { SeverityBadge, StatusBadge } from "../components/StatusBadge";
import { StateAlert } from "../components/StateAlert";
import {
  actionTypeLabel,
  branchLabel,
  dashboardPath,
  listPath,
} from "../constants/actionPlans";
import type { ActionPlanDetail } from "../types/actionPlan";
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

export function PlanDetailPage({ planId, onNavigate }: Props) {
  const [detail, setDetail] = useState<ActionPlanDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchActionPlanDetail(planId);
      setDetail(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar plano.");
    } finally {
      setLoading(false);
    }
  }, [planId]);

  useEffect(() => {
    void load();
  }, [load]);

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
          </DetailSection>

          <DetailSection title="Ishikawa">
            {detail.ishikawa ? (
              <dl className="pac-dl">
                <div><dt>Máquina</dt><dd>{detail.ishikawa.machine ?? "—"}</dd></div>
                <div><dt>Método</dt><dd>{detail.ishikawa.method_process ?? "—"}</dd></div>
                <div><dt>Material</dt><dd>{detail.ishikawa.material ?? "—"}</dd></div>
                <div><dt>Mão de obra</dt><dd>{detail.ishikawa.manpower ?? "—"}</dd></div>
                <div><dt>Medição</dt><dd>{detail.ishikawa.measurement ?? "—"}</dd></div>
                <div><dt>Meio ambiente</dt><dd>{detail.ishikawa.environment ?? "—"}</dd></div>
              </dl>
            ) : (
              <p className="pac-muted">Ishikawa ainda não registrado.</p>
            )}
          </DetailSection>

          <DetailSection title="5 Porquês">
            {detail.five_whys ? (
              <dl className="pac-dl">
                <div><dt>1º porquê</dt><dd>{detail.five_whys.why_1 ?? "—"}</dd></div>
                <div><dt>2º porquê</dt><dd>{detail.five_whys.why_2 ?? "—"}</dd></div>
                <div><dt>3º porquê</dt><dd>{detail.five_whys.why_3 ?? "—"}</dd></div>
                <div><dt>4º porquê</dt><dd>{detail.five_whys.why_4 ?? "—"}</dd></div>
                <div><dt>5º porquê</dt><dd>{detail.five_whys.why_5 ?? "—"}</dd></div>
                <div className="pac-dl__full">
                  <dt>Causa raiz</dt>
                  <dd>{detail.five_whys.root_cause ?? "—"}</dd>
                </div>
              </dl>
            ) : (
              <p className="pac-muted">5 Porquês ainda não registrado.</p>
            )}
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
                        <td>{action.status}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="pac-muted">Nenhuma ação cadastrada.</p>
            )}
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
