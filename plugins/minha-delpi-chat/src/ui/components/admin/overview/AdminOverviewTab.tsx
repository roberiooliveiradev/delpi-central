import { useEffect, useMemo, useState } from "react";

import {
  getAdminLearningSummary,
  getAdminMetricsSummary,
  getAdminRbacSummary,
  getAdminSecuritySummary,
  getAdminToolHealth,
  getAdminResponseEvaluationSummary,
} from "../../../../data/api/adminApi";
import type {
  AdminLearningSummary,
  AdminMetricsSummary,
  AdminRbacSummary,
  AdminResponseEvaluationSummary,
  AdminSecuritySummary,
  AdminToolHealthResponse,
} from "../../../../data/api/adminTypes";
import {
  buildAdminHref,
  type AdminNavState,
} from "../../../../navigation/adminNavigation";
import { navigateChatHref } from "../../../../navigation/chatNavigation";
import { AdminTabHeader } from "../shared/AdminTabHeader";
import { AdminRbacPanel } from "../rbac/AdminRbacPanel";
import { ADMIN_HELP } from "../../../../content/adminHelpTooltips";

import { AdminAttentionQueue } from "./AdminAttentionQueue";
import { AdminManualPanel } from "./AdminManualPanel";
import { buildAttentionQueue } from "./attentionQueue";

import "./AdminOverviewTab.css";

type AdminOverviewTabProps = {
  metricsSummary?: AdminMetricsSummary | null;
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
  onNavigate: (nav: AdminNavState) => void;
};

type OverviewCard = {
  title: string;
  value: string;
  detail?: string;
  nav: AdminNavState;
};

function formatNumber(value?: number | null): string {
  if (typeof value !== "number") {
    return "—";
  }

  return new Intl.NumberFormat("pt-BR").format(value);
}

export function AdminOverviewTab({
  metricsSummary,
  getAccessToken,
  onNavigate,
}: AdminOverviewTabProps) {
  const [rbac, setRbac] = useState<AdminRbacSummary | null>(null);
  const [security, setSecurity] = useState<AdminSecuritySummary | null>(null);
  const [evaluations, setEvaluations] = useState<AdminResponseEvaluationSummary | null>(null);
  const [toolHealth, setToolHealth] = useState<AdminToolHealthResponse | null>(null);
  const [learning, setLearning] = useState<AdminLearningSummary | null>(null);
  const [metrics, setMetrics] = useState<AdminMetricsSummary | null>(metricsSummary ?? null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setMetrics(metricsSummary ?? null);
  }, [metricsSummary]);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);

      try {
        const [
          rbacResult,
          securityResult,
          evaluationsResult,
          healthResult,
          learningResult,
          metricsResult,
        ] = await Promise.all([
          getAdminRbacSummary({ getAccessToken }),
          getAdminSecuritySummary(24, { getAccessToken }),
          getAdminResponseEvaluationSummary({ getAccessToken }),
          getAdminToolHealth({ getAccessToken }),
          getAdminLearningSummary({ getAccessToken }, { hours: 24 }),
          metricsSummary
            ? Promise.resolve(metricsSummary)
            : getAdminMetricsSummary(24, { getAccessToken }),
        ]);

        if (cancelled) {
          return;
        }

        setRbac(rbacResult);
        setSecurity(securityResult);
        setEvaluations(evaluationsResult);
        setToolHealth(healthResult);
        setLearning(learningResult);
        setMetrics(metricsResult);
      } catch {
        if (!cancelled) {
          setRbac(null);
          setSecurity(null);
          setEvaluations(null);
          setToolHealth(null);
          setLearning(null);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void load();

    return () => {
      cancelled = true;
    };
  }, [getAccessToken, metricsSummary]);

  const attentionItems = useMemo(
    () =>
      buildAttentionQueue({
        toolHealth,
        security,
        learning,
        evaluations,
        metrics,
      }),
    [toolHealth, security, learning, evaluations, metrics],
  );

  const toolIssues =
    toolHealth?.items?.filter((item) => item.status !== "ok").length ?? 0;
  const toolTotal = toolHealth?.items?.length ?? 0;

  const cards: OverviewCard[] = [
    {
      title: "Sessões (24h)",
      value: formatNumber(metrics?.sessions),
      detail: `${formatNumber(metrics?.messages)} mensagens`,
      nav: { section: "quality", subTab: "metrics", page: "overview" },
    },
    {
      title: "Erros (24h)",
      value: formatNumber(metrics?.recentErrors24h),
      detail: `Tools: ${formatNumber(metrics?.recentToolCalls24h)} chamadas`,
      nav: { section: "quality", subTab: "metrics", page: "errors" },
    },
    {
      title: "Segurança (24h)",
      value: formatNumber(security?.blockedCount),
      detail: `${formatNumber(security?.flaggedCount)} sinalizados`,
      nav: { section: "governance", subTab: "security" },
    },
    {
      title: "Avaliações",
      value: formatNumber(evaluations?.recent24h),
      detail:
        typeof evaluations?.averageScore === "number"
          ? `Média ${evaluations.averageScore.toFixed(1)}`
          : "Sem média recente",
      nav: { section: "quality", subTab: "evaluations" },
    },
    {
      title: "Conhecimento",
      value: formatNumber(metrics?.activeKnowledgeDocuments),
      detail: `${formatNumber(metrics?.knowledgeDocuments)} documentos`,
      nav: { section: "knowledge", subTab: "documents" },
    },
    {
      title: "Ferramentas",
      value: toolTotal ? `${toolTotal - toolIssues}/${toolTotal}` : "—",
      detail: toolIssues ? `${toolIssues} com alerta` : "Saúde geral",
      nav: { section: "platform", subTab: "tools" },
    },
  ];

  const quickLinks: Array<{ label: string; nav: AdminNavState }> = [
    { label: "Documentos", nav: { section: "knowledge", subTab: "documents" } },
    { label: "Diretrizes", nav: { section: "knowledge", subTab: "guidelines" } },
    { label: "Simulação", nav: { section: "agents", subTab: "simulation" } },
    { label: "Inteligência", nav: { section: "platform", subTab: "intelligence" } },
    { label: "Melhoria contínua", nav: { section: "quality", subTab: "improve" } },
    { label: "Auditoria", nav: { section: "governance", subTab: "audit" } },
  ];

  function openNav(nav: AdminNavState) {
    onNavigate(nav);
    navigateChatHref(buildAdminHref(nav));
  }

  return (
    <section className="mdc-admin-overview-tab">
      <AdminTabHeader
        eyebrow="Painel"
        title="Como está o chat?"
        description="Resumo operacional das últimas 24 horas. Clique nos cards ou na fila de atenção para ir à seção."
        helpHint={ADMIN_HELP.pages.overview}
      />

      {loading ? <p className="mdc-chat-muted">Atualizando indicadores...</p> : null}

      <AdminAttentionQueue items={attentionItems} onOpen={openNav} />

      <div className="mdc-admin-overview-tab__cards">
        {cards.map((card) => (
          <button
            key={card.title}
            type="button"
            className="mdc-admin-overview-card"
            onClick={() => openNav(card.nav)}
          >
            <span className="mdc-admin-overview-card__label">{card.title}</span>
            <strong className="mdc-admin-overview-card__value">{card.value}</strong>
            {card.detail ? <small>{card.detail}</small> : null}
          </button>
        ))}
      </div>

      <article className="mdc-admin-overview-tab__quick">
        <h3>Navegação rápida</h3>
        <div className="mdc-admin-overview-tab__quick-links">
          {quickLinks.map((link) => (
            <button key={link.label} type="button" onClick={() => openNav(link.nav)}>
              {link.label}
            </button>
          ))}
        </div>
      </article>

      <AdminManualPanel onOpen={openNav} />

      <AdminRbacPanel rbac={rbac} />
    </section>
  );
}
