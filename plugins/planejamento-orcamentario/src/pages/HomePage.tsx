import { useEffect, useMemo, useState, type ReactNode } from "react";
import {
  AlertCircle,
  ArrowRight,
  BookOpen,
  Building2,
  CalendarRange,
  CheckCircle2,
  ClipboardCheck,
  Layers,
  Lock,
  PieChart,
  Unlock,
  Users,
} from "lucide-react";

import { fetchBudgetContext } from "../api/budgetPlanningApi";
import type { BudgetContext, BudgetExercise } from "../types/budgetPlanning";
import { PageShell } from "../components/PageShell";
import { LoadingActivityCard, StateBox } from "../components/uiKit";
import { usePermissions } from "../hooks/usePermissions";
import {
  hasCapexApproveAccess,
  hasCapexConsolidationViewAccess,
  hasCapexSubmitAccess,
  hasPersonnelApproveAccess,
  hasPersonnelViewAccess,
} from "../utils/permissions";
import { routeHref } from "../utils/routing";
import {
  firstNameFromDisplayName,
  timeOfDayGreeting,
} from "../utils/homeGreeting";

type HomeState =
  | "loading"
  | "error"
  | "no-exercise"
  | "guidance-unpublished"
  | "reading-pending"
  | "unlocked"
  | "closed-locked";

type ModuleTile = {
  key: string;
  href?: string;
  title: string;
  description: string;
  icon: ReactNode;
  accent?: "sky" | "indigo" | "emerald" | "amber" | "rose" | "slate" | "violet";
  tone?: "default" | "emphasis" | "muted";
  badge?: string;
  disabled?: boolean;
};

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
  return date.toLocaleDateString("pt-BR", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function statusLabel(state: HomeState, exercise?: BudgetExercise | null): string {
  switch (state) {
    case "unlocked":
      return "Elaboração liberada";
    case "reading-pending":
      return "Leitura pendente";
    case "guidance-unpublished":
      return "Aguardando orientações";
    case "closed-locked":
      return exercise?.status === "archived" ? "Arquivado" : "Encerrado";
    case "no-exercise":
      return "Sem ciclo ativo";
    default:
      return "Indisponível";
  }
}

export function HomePage() {
  const { profile } = usePermissions();
  const canSubmitCapex = hasCapexSubmitAccess(profile);
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
  const modulesReady = homeState === "unlocked";
  const greetingWord = timeOfDayGreeting();
  const firstName = firstNameFromDisplayName(profile?.name);
  const homeLead =
    homeState === "unlocked"
      ? firstName
        ? `${firstName}, tudo pronto para elaborar. Escolha um app abaixo conforme o seu escopo.`
        : "Tudo pronto para elaborar. Escolha um app abaixo conforme o seu escopo."
      : homeState === "reading-pending"
        ? "Antes de editar, confirme a leitura das orientações institucionais."
        : homeState === "guidance-unpublished"
          ? "A controladoria ainda não publicou as orientações deste ciclo."
          : homeState === "closed-locked"
            ? "O ciclo está encerrado. Consulte o histórico nos módulos autorizados."
            : "Quando um exercício for aberto, o status e os prazos aparecerão aqui.";

  const primaryAction = useMemo(() => {
    if (homeState === "reading-pending") {
      return {
        href: routeHref("orientacoes"),
        label: "Ler orientações",
        hint: "Confirme a leitura para liberar os módulos de elaboração.",
      };
    }
    if (homeState === "unlocked" && (canApproveCapex || canApprovePersonnel)) {
      return {
        href: routeHref("gestao-aprovacoes"),
        label: "Abrir gestão de aprovações",
        hint: "Painel da diretoria: insights e decisão por centro de custo.",
      };
    }
    if (homeState === "unlocked" && (canSubmitCapex || canViewPersonnel)) {
      return {
        href: routeHref("centros"),
        label: "Abrir orçamento do centro",
        hint: "Elabore CAPEX e Pessoal no mesmo centro de custo.",
      };
    }
    if (homeState === "unlocked") {
      return {
        href: routeHref("orientacoes"),
        label: "Revisar orientações",
        hint: "Consulte as premissas e o calendário do ciclo.",
      };
    }
    return null;
  }, [canApproveCapex, canApprovePersonnel, canSubmitCapex, canViewPersonnel, homeState]);

  const modules = useMemo(() => {
    const tiles: ModuleTile[] = [
      {
        key: "orientacoes",
        href: routeHref("orientacoes"),
        title: "Orientações",
        description: "Carta, premissas, cronograma e documentos do exercício.",
        icon: <BookOpen size={28} strokeWidth={1.7} aria-hidden="true" />,
        accent: "sky",
        tone: homeState === "reading-pending" ? "emphasis" : "default",
        badge: homeState === "reading-pending" ? "Obrigatório" : undefined,
      },
    ];

    if (canSubmitCapex || canViewPersonnel) {
      tiles.push({
        key: "centros",
        href: modulesReady ? routeHref("centros") : undefined,
        title: "Orçamento",
        description: "CAPEX e Pessoal juntos, por filial e centro de custo.",
        icon: <Building2 size={28} strokeWidth={1.7} aria-hidden="true" />,
        accent: "indigo",
        disabled: !modulesReady,
        badge: modulesReady ? undefined : "Bloqueado",
        tone: modulesReady ? "emphasis" : "default",
      });
    }

    if (canApproveCapex || canApprovePersonnel) {
      tiles.push({
        key: "gestao-aprovacoes",
        href: routeHref("gestao-aprovacoes"),
        title: "Aprovações",
        description: "Cockpit da diretoria: KPIs, centros pendentes e decisão no CC.",
        icon: <ClipboardCheck size={28} strokeWidth={1.7} aria-hidden="true" />,
        accent: "emerald",
        tone: "emphasis",
      });
    }

    if (canApproveCapex) {
      tiles.push({
        key: "capex-approvals",
        href: routeHref("capex-approvals"),
        title: "Fila CAPEX",
        description: "Lista avançada de planejamentos enviados.",
        icon: <Layers size={28} strokeWidth={1.7} aria-hidden="true" />,
        accent: "violet",
      });
    }

    if (canConsolidateCapex) {
      tiles.push({
        key: "capex-consolidation",
        href: routeHref("capex-consolidation"),
        title: "Consolidação",
        description: "Visão gerencial e exportação Excel dos investimentos.",
        icon: <PieChart size={28} strokeWidth={1.7} aria-hidden="true" />,
        accent: "amber",
      });
    }

    if (canApprovePersonnel) {
      tiles.push({
        key: "pessoal-approvals",
        href: routeHref("pessoal-approvals"),
        title: "Fila Pessoal",
        description: "Lista avançada de planos de headcount enviados.",
        icon: <Users size={28} strokeWidth={1.7} aria-hidden="true" />,
        accent: "rose",
      });
    }

    tiles.push({
      key: "receita",
      title: "Receita",
      description: "Módulo em evolução — disponível em versões futuras.",
      icon: <CalendarRange size={28} strokeWidth={1.7} aria-hidden="true" />,
      accent: "slate",
      tone: "muted",
      disabled: true,
      badge: "Em breve",
    });

    return tiles;
  }, [
    canApproveCapex,
    canApprovePersonnel,
    canConsolidateCapex,
    canSubmitCapex,
    canViewPersonnel,
    homeState,
    modulesReady,
  ]);

  return (
    <PageShell
      title="Planejamento Orçamentário"
      subtitle="Sua home do ciclo — status, prazos e atalhos do que você pode fazer."
      icon={<PieChart size={28} strokeWidth={1.6} aria-hidden="true" />}
    >
      {homeState === "loading" ? (
        <LoadingActivityCard title="Preparando o ciclo orçamentário…" variant="panel" />
      ) : null}

      {homeState === "error" ? (
        <StateBox variant="error" dismissible={false}>
          {error ?? "Não foi possível carregar o planejamento orçamentário."}
        </StateBox>
      ) : null}

      {homeState !== "loading" && homeState !== "error" ? (
        <section className="po-home" aria-label="Início do planejamento orçamentário">
          <div className="po-home__hero">
            <div className="po-home__hero-copy">
              <p className="po-home__eyebrow">Sua home · Planejamento orçamentário</p>
              <p className="po-home__greeting" aria-live="polite">
                {greetingWord}
                {firstName ? (
                  <>
                    , <span className="po-home__greeting-name">{firstName}</span>
                  </>
                ) : (
                  "!"
                )}
              </p>
              {exercise ? (
                <>
                  <h2 className="po-home__year">{exercise.year}</h2>
                  <p className="po-home__exercise-name">{exercise.name}</p>
                </>
              ) : (
                <>
                  <h2 className="po-home__year">—</h2>
                  <p className="po-home__exercise-name">Nenhum exercício configurado</p>
                </>
              )}
              <p className="po-home__lead">{homeLead}</p>
            </div>

            <aside className="po-home__hero-panel" aria-label="Resumo do ciclo">
              <div className={`po-home__status po-home__status--${homeState}`}>
                {homeState === "unlocked" ? (
                  <Unlock size={18} aria-hidden="true" />
                ) : homeState === "closed-locked" ? (
                  <Lock size={18} aria-hidden="true" />
                ) : (
                  <AlertCircle size={18} aria-hidden="true" />
                )}
                <span>{statusLabel(homeState, exercise)}</span>
              </div>

              <dl className="po-home__meta">
                <div>
                  <dt>Abertura</dt>
                  <dd>{formatDate(exercise?.filling_starts_at)}</dd>
                </div>
                <div>
                  <dt>Prazo final</dt>
                  <dd>{formatDate(exercise?.deadline_at)}</dd>
                </div>
                <div>
                  <dt>Orientações</dt>
                  <dd>
                    {context?.guidance?.acknowledged ? (
                      <span className="po-inline-success">
                        <CheckCircle2 size={14} aria-hidden="true" /> Confirmadas
                      </span>
                    ) : homeState === "guidance-unpublished" ? (
                      "Não publicadas"
                    ) : (
                      "Pendentes"
                    )}
                  </dd>
                </div>
              </dl>

              {primaryAction ? (
                <a className="po-btn po-btn--primary po-home__cta" href={primaryAction.href}>
                  {primaryAction.label}
                  <ArrowRight size={16} aria-hidden="true" />
                </a>
              ) : null}
              {primaryAction ? <p className="po-home__cta-hint">{primaryAction.hint}</p> : null}
            </aside>
          </div>

          {homeState === "no-exercise" ? (
            <StateBox variant="default" dismissible={false}>
              Não há exercício orçamentário configurado no momento. Aguarde a abertura do ciclo pela
              administração.
            </StateBox>
          ) : null}

          {homeState === "guidance-unpublished" ? (
            <StateBox variant="warning" dismissible={false}>
              As orientações para elaboração do orçamento ainda não foram publicadas. Aguarde a
              comunicação da controladoria.
            </StateBox>
          ) : null}

          <div className="po-home__modules-head">
            <h3 className="po-home__modules-title">Apps</h3>
            <p className="po-home__modules-subtitle">
              Atalhos do ciclo — toque no ícone para abrir.
            </p>
          </div>

          <ul className="po-home__module-grid" aria-label="Aplicativos do planejamento">
            {modules.map((tile, index) => {
              const className = [
                "po-home__module",
                tile.accent ? `po-home__module--accent-${tile.accent}` : "",
                tile.tone === "emphasis" ? "po-home__module--emphasis" : "",
                tile.tone === "muted" || tile.disabled ? "po-home__module--muted" : "",
                tile.disabled ? "is-disabled" : "",
              ]
                .filter(Boolean)
                .join(" ");

              const body = (
                <>
                  <span className="po-home__module-icon-wrap">
                    <span className="po-home__module-icon">{tile.icon}</span>
                    {tile.badge ? (
                      <span className="po-home__module-badge">{tile.badge}</span>
                    ) : null}
                  </span>
                  <strong className="po-home__module-label">{tile.title}</strong>
                  <span className="po-sr-only">{tile.description}</span>
                </>
              );

              return (
                <li
                  key={tile.key}
                  className="po-home__module-item"
                  style={{ animationDelay: `${index * 40}ms` }}
                >
                  {tile.href && !tile.disabled ? (
                    <a className={className} href={tile.href} title={tile.description}>
                      {body}
                    </a>
                  ) : (
                    <div
                      className={className}
                      title={tile.description}
                      aria-disabled={tile.disabled ? "true" : undefined}
                    >
                      {body}
                    </div>
                  )}
                </li>
              );
            })}
          </ul>
        </section>
      ) : null}
    </PageShell>
  );
}
