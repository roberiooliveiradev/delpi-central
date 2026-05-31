import { useEffect, useState } from "react";

import {
  getAdminResponseEvaluationSummary,
  getAdminSecuritySummary,
} from "../../../../data/api/adminApi";
import type {
  AdminLlmStatus,
  AdminMetricsSummary,
  AdminRbacSummary,
} from "../../../../data/api/adminTypes";
import type { AdminNavState, AdminSection } from "../../../../navigation/adminNavigation";
import { ADMIN_SECTIONS } from "../../../../navigation/adminNavigation";
import { AdminRbacPanel } from "../rbac/AdminRbacPanel";

import "./AdminOverviewTab.css";

type AdminOverviewTabProps = {
  metricsSummary: AdminMetricsSummary | null;
  llmStatus: AdminLlmStatus | null;
  rbac: AdminRbacSummary | null;
  isLoading: boolean;
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
  onNavigate: (nav: Partial<AdminNavState>) => void;
};

function formatNumber(value?: number | null): string {
  if (typeof value !== "number") {
    return "—";
  }

  return new Intl.NumberFormat("pt-BR").format(value);
}

export function AdminOverviewTab({
  metricsSummary,
  llmStatus,
  rbac,
  isLoading,
  getAccessToken,
  onNavigate,
}: AdminOverviewTabProps) {
  const [securitySummary, setSecuritySummary] = useState<{
    totalEvents?: number;
    blockedCount?: number;
  } | null>(null);
  const [evaluationSummary, setEvaluationSummary] = useState<{
    recent24h?: number;
    averageScore?: number | null;
  } | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      if (!getAccessToken) {
        return;
      }

      try {
        const [security, evaluations] = await Promise.all([
          getAdminSecuritySummary(24, { getAccessToken }),
          getAdminResponseEvaluationSummary({ getAccessToken }),
        ]);

        if (!cancelled) {
          setSecuritySummary(security);
          setEvaluationSummary(evaluations);
        }
      } catch {
        if (!cancelled) {
          setSecuritySummary(null);
          setEvaluationSummary(null);
        }
      }
    }

    void load();

    return () => {
      cancelled = true;
    };
  }, [getAccessToken]);

  const quickSections = ADMIN_SECTIONS.filter((section) => section.key !== "overview");

  return (
    <section className="mdc-admin-overview">
      <header className="mdc-admin-overview__header">
        <h2>Painel administrativo</h2>
        <p>Resumo em 30 segundos: saúde do chat, alertas e atalhos para as demais áreas.</p>
      </header>

      <div className="mdc-admin-overview__kpis">
        <article className="mdc-admin-kpi-card">
          <span>Sessões (janela)</span>
          <strong>{formatNumber(metricsSummary?.sessions)}</strong>
        </article>
        <article className="mdc-admin-kpi-card">
          <span>Mensagens</span>
          <strong>{formatNumber(metricsSummary?.messages)}</strong>
        </article>
        <article className="mdc-admin-kpi-card">
          <span>Erros 24h</span>
          <strong>{formatNumber(metricsSummary?.recentErrors24h)}</strong>
        </article>
        <article className="mdc-admin-kpi-card">
          <span>Tools 24h</span>
          <strong>{formatNumber(metricsSummary?.recentToolCalls24h)}</strong>
        </article>
        <article className="mdc-admin-kpi-card">
          <span>LLM</span>
          <strong>{llmStatus?.provider ? llmStatus.provider : isLoading ? "…" : "—"}</strong>
        </article>
        <article className="mdc-admin-kpi-card">
          <span>Eventos segurança 24h</span>
          <strong>{formatNumber(securitySummary?.totalEvents)}</strong>
        </article>
        <article className="mdc-admin-kpi-card">
          <span>Docs ativos</span>
          <strong>{formatNumber(metricsSummary?.activeKnowledgeDocuments)}</strong>
        </article>
        <article className="mdc-admin-kpi-card">
          <span>Avaliações 24h</span>
          <strong>{formatNumber(evaluationSummary?.recent24h)}</strong>
        </article>
      </div>

      <AdminRbacPanel rbac={rbac} />

      <div className="mdc-admin-overview__quick">
        <h3>Navegação rápida</h3>
        <div className="mdc-admin-overview__cards">
          {quickSections.map((section) => {
            const Icon = section.icon;

            return (
              <button
                key={section.key}
                type="button"
                className="mdc-admin-overview__card"
                onClick={() =>
                  onNavigate({
                    section: section.key as AdminSection,
                    subTab: section.subTabs[0]?.key ?? null,
                  })
                }
              >
                <Icon size={20} aria-hidden />
                <span className="mdc-admin-overview__card-title">{section.label}</span>
                <span className="mdc-admin-overview__card-desc">{section.description}</span>
              </button>
            );
          })}
        </div>
      </div>
    </section>
  );
}
