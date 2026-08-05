import { useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  BookOpen,
  CalendarRange,
  CheckCircle2,
  Lock,
  PieChart,
  Unlock,
} from "lucide-react";

import { fetchBudgetContext } from "../api/budgetPlanningApi";
import type { BudgetContext } from "../types/budgetPlanning";
import { PageShell } from "../components/PageShell";
import { LoadingActivityCard, SectionCard, StateBox } from "../components/uiKit";
import { usePermissions } from "../hooks/usePermissions";
import {
  hasCapexApproveAccess,
  hasCapexConsolidationViewAccess,
  hasPersonnelApproveAccess,
  hasPersonnelViewAccess,
} from "../utils/permissions";
import { routeHref } from "../utils/routing";

type HomeState =
  | "loading"
  | "error"
  | "no-exercise"
  | "guidance-unpublished"
  | "reading-pending"
  | "unlocked"
  | "closed-locked";

function resolveHomeState(context: BudgetContext): HomeState {
  if (!context.exercise) return "no-exercise";
  if (context.reason === "guidance_not_published" || context.guidance?.current_version == null) {
    return "guidance-unpublished";
  }

  const status = context.exercise.status;
  if (status === "locked" || status === "archived") return "closed-locked";

  if (context.modules_unlocked) return "unlocked";
  if (!context.guidance.acknowledged) return "reading-pending";

  return "reading-pending";
}

function formatDate(value?: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString("pt-BR");
}

export function HomePage() {
  const { profile } = usePermissions();
  const canApproveCapex = hasCapexApproveAccess(profile);
  const canConsolidateCapex = hasCapexConsolidationViewAccess(profile);
  const canViewPersonnel = hasPersonnelViewAccess(profile);
  const canApprovePersonnel = hasPersonnelApproveAccess(profile);
  const [context, setContext] = useState<BudgetContext | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    fetchBudgetContext(controller.signal)
      .then((data) => {
        setContext(data);
        setError(null);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : "Erro ao carregar o exercício.");
        setContext(null);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });

    return () => controller.abort();
  }, []);

  const homeState = useMemo(() => {
    if (loading) return "loading" as const;
    if (error) return "error" as const;
    if (!context) return "error" as const;
    return resolveHomeState(context);
  }, [context, error, loading]);

  const exercise = context?.exercise;

  return (
    <PageShell
      title="Planejamento Orçamentário"
      subtitle="Acompanhe o ciclo vigente, prazos institucionais e liberação dos módulos de elaboração."
      icon={<PieChart size={28} strokeWidth={1.75} aria-hidden="true" />}
      actions={
        <a className="po-btn po-btn--secondary" href={routeHref("orientacoes")}>
          <BookOpen size={16} aria-hidden="true" />
          Orientações
        </a>
      }
    >
      {homeState === "loading" ? (
        <LoadingActivityCard title="Carregando contexto do exercício…" variant="panel" />
      ) : null}

      {homeState === "error" ? (
        <StateBox variant="error" dismissible={false}>
          {error ?? "Não foi possível carregar o planejamento orçamentário."}
        </StateBox>
      ) : null}

      {homeState === "no-exercise" ? (
        <SectionCard title="Nenhum exercício disponível" hint="Aguarde a abertura de um novo ciclo pela administração.">
          <p className="po-muted">
            Não há exercício orçamentário configurado no momento. Quando a diretoria publicar o
            ciclo, o status e os prazos aparecerão aqui.
          </p>
        </SectionCard>
      ) : null}

      {homeState === "guidance-unpublished" && exercise ? (
        <SectionCard
          title={`${exercise.name} · ${exercise.year}`}
          hint="Orientações institucionais ainda não publicadas."
        >
          <StateBox variant="warning" dismissible={false}>
            As orientações para elaboração do orçamento ainda não foram publicadas. Aguarde a
            comunicação da controladoria.
          </StateBox>
          <dl className="po-detail-grid">
            <div>
              <dt>Abertura prevista</dt>
              <dd>{formatDate(exercise.filling_starts_at)}</dd>
            </div>
            <div>
              <dt>Encerramento previsto</dt>
              <dd>{formatDate(exercise.deadline_at)}</dd>
            </div>
          </dl>
        </SectionCard>
      ) : null}

      {homeState === "reading-pending" && exercise ? (
        <SectionCard
          title={`${exercise.name} · ${exercise.year}`}
          hint="Confirmação de leitura obrigatória antes de liberar os módulos."
        >
          <div className="po-status-banner po-status-banner--warning">
            <AlertCircle size={18} aria-hidden="true" />
            <div>
              <strong>Leitura pendente</strong>
              <p className="po-muted">
                Leia e confirme as orientações institucionais para desbloquear receita, pessoal e
                CAPEX.
              </p>
            </div>
          </div>
          <a className="po-btn po-btn--primary" href={routeHref("orientacoes")}>
            Ir para orientações
          </a>
        </SectionCard>
      ) : null}

      {homeState === "unlocked" && exercise ? (
        <SectionCard
          title={`${exercise.name} · ${exercise.year}`}
          hint="Ciclo aberto — módulos liberados para elaboração conforme seu escopo."
        >
          <div className="po-status-banner po-status-banner--success">
            <Unlock size={18} aria-hidden="true" />
            <div>
              <strong>Elaboração liberada</strong>
              <p className="po-muted">
                Você concluiu a leitura das orientações. Utilize os módulos conforme seu escopo
                autorizado.
              </p>
            </div>
          </div>
          <dl className="po-detail-grid">
            <div>
              <dt>Status</dt>
              <dd className="po-badge po-badge--success">Aberto</dd>
            </div>
            <div>
              <dt>Prazo final</dt>
              <dd>{formatDate(exercise.deadline_at)}</dd>
            </div>
            <div>
              <dt>Orientações</dt>
              <dd>
                <span className="po-inline-success">
                  <CheckCircle2 size={14} aria-hidden="true" /> Confirmadas
                </span>
              </dd>
            </div>
          </dl>
        </SectionCard>
      ) : null}

      {homeState === "closed-locked" && exercise ? (
        <SectionCard
          title={`${exercise.name} · ${exercise.year}`}
          hint="Ciclo encerrado — consulta somente leitura."
        >
          <div className="po-status-banner po-status-banner--muted">
            <Lock size={18} aria-hidden="true" />
            <div>
              <strong>Ciclo encerrado</strong>
              <p className="po-muted">
                O exercício está {exercise.status === "archived" ? "arquivado" : "bloqueado"}. As
                telas de elaboração permanecem disponíveis apenas para consulta.
              </p>
            </div>
          </div>
          <dl className="po-detail-grid">
            <div>
              <dt>Status</dt>
              <dd className="po-badge po-badge--muted">{exercise.status}</dd>
            </div>
            <div>
              <dt>Encerramento</dt>
              <dd>{formatDate(exercise.deadline_at)}</dd>
            </div>
          </dl>
        </SectionCard>
      ) : null}

      {exercise && homeState !== "loading" && homeState !== "error" ? (
        <SectionCard title="Próximos passos" hint="Atalhos do ciclo orçamentário.">
          <ul className="po-link-list">
            <li>
              <a href={routeHref("orientacoes")}>
                <BookOpen size={16} aria-hidden="true" />
                Revisar orientações e documentos
              </a>
            </li>
            <li>
              <a href={routeHref("capex")}>
                <CalendarRange size={16} aria-hidden="true" />
                Meus centros de custo (CAPEX)
              </a>
            </li>
            {canApproveCapex ? (
              <li>
                <a href={routeHref("capex-approvals")}>
                  <CheckCircle2 size={16} aria-hidden="true" />
                  Fila de aprovações CAPEX
                </a>
              </li>
            ) : null}
            {canConsolidateCapex ? (
              <li>
                <a href={routeHref("capex-consolidation")}>
                  <PieChart size={16} aria-hidden="true" />
                  Consolidação de Investimentos
                </a>
              </li>
            ) : null}
            {canViewPersonnel ? (
              <li>
                <a href={routeHref("pessoal")}>
                  <CalendarRange size={16} aria-hidden="true" />
                  Orçamento de Pessoal
                </a>
              </li>
            ) : null}
            {canApprovePersonnel ? (
              <li>
                <a href={routeHref("pessoal-approvals")}>
                  <CheckCircle2 size={16} aria-hidden="true" />
                  Fila de aprovações de Pessoal
                </a>
              </li>
            ) : null}
            <li>
              <span className="po-muted">Módulo de receita (em evolução)</span>
            </li>
          </ul>
        </SectionCard>
      ) : null}
    </PageShell>
  );
}
