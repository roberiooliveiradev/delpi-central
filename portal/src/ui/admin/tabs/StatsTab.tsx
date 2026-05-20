// src/ui/admin/tabs/StatsTab.tsx

import { useCallback, useContext, useEffect, useMemo, useState } from "react";
import {
  Activity,
  ArrowRight,
  BarChart3,
  Bell,
  Ghost,
  LayoutGrid,
  RefreshCw,
  Shield,
  Sparkles,
  Users,
  UsersRound,
} from "lucide-react";

import { AuthContext } from "../../../state/AuthContext";
import { ApiClient } from "../../../data/apiClient";
import { AdminApi, type AdminStatistics } from "../../../data/adminApi";
import type { AdminTab } from "../AdminPage";
import {
  BarChart,
  DonutChart,
  LiveAppUsageCard,
  type ChartSegment,
} from "../stats/StatsCharts";

import "./StatsTab.css";

type StatsTabProps = {
  onNavigateTab?: (tab: AdminTab) => void;
};

const CHART_COLORS = {
  primary: "var(--primary)",
  success: "#16a34a",
  warning: "#d97706",
  danger: "#dc2626",
  muted: "color-mix(in srgb, var(--text-muted) 55%, var(--border))",
  violet: "#7c3aed",
  cyan: "#0891b2",
};

function PanelNav({
  tab,
  label,
  onNavigateTab,
}: {
  tab: AdminTab;
  label: string;
  onNavigateTab?: (tab: AdminTab) => void;
}) {
  if (!onNavigateTab) return null;

  return (
    <button
      type="button"
      className="admin-stats__panel-link"
      onClick={() => onNavigateTab(tab)}
    >
      {label}
      <ArrowRight size={14} aria-hidden="true" />
    </button>
  );
}

const formatAppType = (type: string) => {
  if (type === "iframe") return "Iframe";
  if (type === "microfrontend") return "Microfrontend";
  if (type === "backend-only") return "Backend-only";
  return type;
};

const formatGeneratedAt = (value: string) => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";

  return new Intl.DateTimeFormat("pt-BR", {
    timeZone: "America/Sao_Paulo",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
};

export const StatsTab = ({ onNavigateTab }: StatsTabProps) => {
  const { getAccessToken } = useContext(AuthContext);
  const [stats, setStats] = useState<AdminStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const api = useMemo(() => {
    return new AdminApi(new ApiClient("", getAccessToken));
  }, [getAccessToken]);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await api.getAdminStatistics();
      setStats(data);
    } catch (err) {
      setStats(null);
      setError(
        err instanceof Error ? err.message : "Falha ao carregar estatísticas",
      );
    } finally {
      setLoading(false);
    }
  }, [api]);

  useEffect(() => {
    void load();
  }, [load]);

  const charts = useMemo(() => {
    if (!stats) return null;

    const usage = stats.apps.usage;
    const ghostCount = usage?.ghostApps?.length ?? 0;
    const usedInPeriod = usage?.usedInPeriod ?? 0;
    const appsActive = stats.apps.active;
    const appsIdle = Math.max(0, appsActive - usedInPeriod);

    const userSegments: ChartSegment[] = [
      { label: "Ativos", value: stats.users.active, color: CHART_COLORS.success },
      { label: "Inativos", value: stats.users.inactive, color: CHART_COLORS.muted },
    ];

    const appSegments: ChartSegment[] = [
      {
        label: "Em uso agora",
        value: usage?.inUseNow ?? 0,
        color: CHART_COLORS.success,
      },
      {
        label: "Usadas (30d)",
        value: Math.max(0, usedInPeriod - (usage?.inUseNow ?? 0)),
        color: CHART_COLORS.primary,
      },
      { label: "Fantasmas", value: ghostCount, color: CHART_COLORS.warning },
      { label: "Sem uso recente", value: appsIdle, color: CHART_COLORS.muted },
    ];

    const notifyTotal = stats.notifications?.dispatchesTotal ?? 0;
    const notifyPending = stats.notifications?.dispatchesPending ?? 0;
    const notifyCompleted = stats.notifications?.dispatchesCompleted ?? 0;
    const notifyFailed = stats.notifications?.dispatchesFailed ?? 0;
    const notifyOther = Math.max(
      0,
      notifyTotal - notifyPending - notifyCompleted - notifyFailed,
    );

    const notificationSegments: ChartSegment[] = [
      { label: "Concluídos", value: notifyCompleted, color: CHART_COLORS.success },
      { label: "Pendentes", value: notifyPending, color: CHART_COLORS.warning },
      { label: "Falhas", value: notifyFailed, color: CHART_COLORS.danger },
      { label: "Outros", value: notifyOther, color: CHART_COLORS.muted },
    ];

    return { userSegments, appSegments, notificationSegments };
  }, [stats]);

  if (loading && !stats) {
    return (
      <div className="admin-stats admin-stats--loading">
        <div className="admin-stats__skeleton admin-stats__skeleton--hero" />
        <div className="admin-stats__skeleton-row">
          <div className="admin-stats__skeleton admin-stats__skeleton--kpi" />
          <div className="admin-stats__skeleton admin-stats__skeleton--kpi" />
          <div className="admin-stats__skeleton admin-stats__skeleton--kpi" />
          <div className="admin-stats__skeleton admin-stats__skeleton--kpi" />
        </div>
        <div className="admin-stats__skeleton admin-stats__skeleton--panel" />
      </div>
    );
  }

  if (error && !stats) {
    return (
      <div className="admin-stats">
        <div className="admin-stats__state admin-stats__state--error">{error}</div>
        <button type="button" className="admin-stats__refresh" onClick={() => void load()}>
          Tentar novamente
        </button>
      </div>
    );
  }

  if (!stats || !charts) {
    return <div className="admin-stats__state">Nenhum dado disponível.</div>;
  }

  const usage = stats.apps.usage;

  return (
    <section className="admin-stats" aria-labelledby="admin-stats-title">
      <header className="admin-stats__hero">
        <div className="admin-stats__hero-copy">
          <span className="admin-stats__eyebrow">
            <Sparkles size={14} aria-hidden="true" />
            Painel executivo
          </span>
          <h3 id="admin-stats-title">Estatísticas da plataforma</h3>
          <p>
            Usuários online, uso real de aplicações (com quem está em cada app) e
            indicadores de governança RBAC em um só lugar.
          </p>
        </div>
        <div className="admin-stats__hero-actions">
          {stats.generatedAt ? (
            <span className="admin-stats__generated">
              <Activity size={14} aria-hidden="true" />
              Atualizado: {formatGeneratedAt(stats.generatedAt)}
            </span>
          ) : null}
          <button
            type="button"
            className="admin-stats__refresh"
            onClick={() => void load()}
            disabled={loading}
          >
            <RefreshCw size={16} className={loading ? "admin-stats__spin" : ""} />
            {loading ? "Atualizando…" : "Atualizar"}
          </button>
        </div>
      </header>

      <div className="admin-stats__kpis" aria-label="Indicadores principais">
        <article className="admin-stats__kpi admin-stats__kpi--users">
          <span className="admin-stats__kpi-icon">
            <Users size={18} />
          </span>
          <div>
            <strong>{stats.users.total}</strong>
            <span>Usuários</span>
            <small>
              {stats.users.online} online · {stats.users.loggedInLast7Days} logins (7d)
            </small>
          </div>
        </article>
        <article className="admin-stats__kpi admin-stats__kpi--apps">
          <span className="admin-stats__kpi-icon">
            <LayoutGrid size={18} />
          </span>
          <div>
            <strong>{stats.apps.total}</strong>
            <span>Aplicações</span>
            <small>
              {usage?.inUseNow ?? 0} em uso · {usage?.ghostApps?.length ?? 0} fantasmas
            </small>
          </div>
        </article>
        <article className="admin-stats__kpi admin-stats__kpi--roles">
          <span className="admin-stats__kpi-icon">
            <Shield size={18} />
          </span>
          <div>
            <strong>{stats.roles.total}</strong>
            <span>Papéis</span>
            <small>
              {stats.roles.system} sistema · {stats.roles.custom} customizados
            </small>
          </div>
        </article>
        <article className="admin-stats__kpi admin-stats__kpi--groups">
          <span className="admin-stats__kpi-icon">
            <UsersRound size={18} />
          </span>
          <div>
            <strong>{stats.groups.total}</strong>
            <span>Grupos</span>
            <small>
              {stats.groups.active} ativos · {stats.permissions.total} permissões
            </small>
          </div>
        </article>
      </div>

      <div className="admin-stats__charts-row">
        <article className="admin-stats__chart-card">
          <h4>Usuários</h4>
          <DonutChart
            segments={charts.userSegments}
            centerValue={String(stats.users.total)}
            centerLabel="Cadastrados"
          />
        </article>
        <article className="admin-stats__chart-card">
          <h4>Apps — adoção</h4>
          <DonutChart
            segments={charts.appSegments}
            centerValue={String(stats.apps.active)}
            centerLabel="Ativas"
          />
        </article>
        <article className="admin-stats__chart-card">
          <h4>Notificações</h4>
          <DonutChart
            segments={charts.notificationSegments}
            centerValue={String(stats.notifications?.dispatchesTotal ?? 0)}
            centerLabel="Envios"
          />
        </article>
      </div>

      <article className="admin-stats__panel admin-stats__panel--wide">
        <div className="admin-stats__panel-head">
          <div className="admin-stats__panel-head-main">
            <span className="admin-stats__panel-icon">
              <LayoutGrid size={16} />
            </span>
            <div>
              <h4>Uso de aplicações</h4>
              <p className="admin-stats__panel-sub">
                Registra o app aberto e o usuário (nome/e-mail). Apps fantasmas = ativas
                sem abertura em 30 dias.
              </p>
            </div>
          </div>
          <PanelNav tab="apps" label="Gerenciar apps" onNavigateTab={onNavigateTab} />
        </div>

        {usage?.enabled ? (
          <div className="admin-stats__apps-layout">
            <div className="admin-stats__apps-col">
              <h5>Em uso agora</h5>
              {(usage.live ?? []).length === 0 ? (
                <p className="admin-stats__empty">Nenhum app em uso no momento.</p>
              ) : (
                <div className="admin-stats__live-grid">
                  {(usage.live ?? []).map((item) => (
                    <LiveAppUsageCard
                      key={item.appId}
                      appId={item.appId}
                      appName={item.appName || item.appId}
                      userCount={item.userCount}
                      sessionCount={item.sessionCount}
                      users={item.users ?? []}
                    />
                  ))}
                </div>
              )}
            </div>
            <div className="admin-stats__apps-col">
              <h5>Top 30 dias</h5>
              <BarChart
                items={(usage.topUsed ?? []).map((item) => ({
                  id: item.id,
                  label: item.name,
                  value: item.count,
                  sublabel: "usuários únicos",
                }))}
                valueLabel="usuários"
                accent={CHART_COLORS.primary}
              />
              <h5 className="admin-stats__subsection">
                <Ghost size={14} aria-hidden="true" />
                Apps fantasmas ({usage.ghostApps?.length ?? 0})
              </h5>
              {(usage.ghostApps ?? []).length === 0 ? (
                <p className="admin-stats__empty admin-stats__empty--success">
                  Nenhuma aplicação ativa sem uso no período.
                </p>
              ) : (
                <ul className="admin-stats__ghost-tags">
                  {(usage.ghostApps ?? []).map((item) => (
                    <li key={item.id} title={item.id}>
                      {item.name}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        ) : (
          <p className="admin-stats__empty">
            Rastreamento de uso desabilitado (`APP_USAGE_ENABLED=false`).
          </p>
        )}
      </article>

      <div className="admin-stats__grid">
        <article className="admin-stats__panel">
          <div className="admin-stats__panel-head">
            <div className="admin-stats__panel-head-main">
              <span className="admin-stats__panel-icon">
                <Users size={16} />
              </span>
              <h4>Usuários</h4>
            </div>
            <PanelNav tab="users" label="Gerenciar" onNavigateTab={onNavigateTab} />
          </div>
          <div className="admin-stats__split">
            <DonutChart
              segments={charts.userSegments}
              centerValue={String(stats.users.online)}
              centerLabel="Online"
              size={112}
            />
            <BarChart
              items={[
                { id: "active", label: "Ativos", value: stats.users.active },
                { id: "inactive", label: "Inativos", value: stats.users.inactive },
                {
                  id: "login7",
                  label: "Login 7 dias",
                  value: stats.users.loggedInLast7Days,
                },
                {
                  id: "login30",
                  label: "Login 30 dias",
                  value: stats.users.loggedInLast30Days,
                },
                {
                  id: "super",
                  label: "Superadmins",
                  value: stats.users.superadmins,
                },
              ]}
              accent={CHART_COLORS.cyan}
            />
          </div>
        </article>

        <article className="admin-stats__panel">
          <div className="admin-stats__panel-head">
            <div className="admin-stats__panel-head-main">
              <span className="admin-stats__panel-icon">
                <Shield size={16} />
              </span>
              <h4>Papéis</h4>
            </div>
            <PanelNav tab="roles" label="Gerenciar" onNavigateTab={onNavigateTab} />
          </div>
          <BarChart
            items={stats.roles.topByUsers.map((item) => ({
              id: item.id,
              label: item.name,
              value: item.count,
            }))}
            valueLabel="usuários"
            accent={CHART_COLORS.violet}
          />
        </article>

        <article className="admin-stats__panel">
          <div className="admin-stats__panel-head">
            <div className="admin-stats__panel-head-main">
              <span className="admin-stats__panel-icon">
                <UsersRound size={16} />
              </span>
              <h4>Grupos</h4>
            </div>
            <PanelNav tab="groups" label="Gerenciar" onNavigateTab={onNavigateTab} />
          </div>
          <BarChart
            items={stats.groups.topByUsers.map((item) => ({
              id: item.id,
              label: item.name,
              value: item.count,
            }))}
            valueLabel="usuários"
            accent={CHART_COLORS.primary}
          />
        </article>

        <article className="admin-stats__panel">
          <div className="admin-stats__panel-head">
            <div className="admin-stats__panel-head-main">
              <span className="admin-stats__panel-icon">
                <BarChart3 size={16} />
              </span>
              <h4>Apps por tipo</h4>
            </div>
          </div>
          <BarChart
            items={stats.apps.byType.map((item) => ({
              id: item.type,
              label: formatAppType(item.type),
              value: item.count,
            }))}
            accent={CHART_COLORS.success}
          />
        </article>
      </div>

      <div className="admin-stats__overview-grid">
        <article className="admin-stats__overview">
          <div className="admin-stats__overview-head">
            <h4>
              <BarChart3 size={16} /> Vínculos RBAC
            </h4>
            <PanelNav tab="permissions" label="Permissões" onNavigateTab={onNavigateTab} />
          </div>
          <BarChart
            items={[
              {
                id: "ur",
                label: "Usuário → papel",
                value: stats.assignments.userRoles,
              },
              {
                id: "ug",
                label: "Usuário → grupo",
                value: stats.assignments.userGroups,
              },
              {
                id: "gr",
                label: "Grupo → papel",
                value: stats.assignments.groupRoles,
              },
              {
                id: "rp",
                label: "Papel → permissão",
                value: stats.assignments.rolePermissions,
              },
            ]}
            accent={CHART_COLORS.violet}
          />
        </article>

        <article className="admin-stats__overview">
          <div className="admin-stats__overview-head">
            <h4>
              <Bell size={16} /> Campanhas de notificação
            </h4>
            <PanelNav tab="notifications" label="Gerenciar" onNavigateTab={onNavigateTab} />
          </div>
          <div className="admin-stats__split admin-stats__split--compact">
            <DonutChart
              segments={charts.notificationSegments}
              size={112}
              centerLabel="Envios"
            />
            <BarChart
              items={[
                {
                  id: "pending",
                  label: "Pendentes",
                  value: stats.notifications?.dispatchesPending ?? 0,
                },
                {
                  id: "done",
                  label: "Concluídos",
                  value: stats.notifications?.dispatchesCompleted ?? 0,
                },
                {
                  id: "fail",
                  label: "Falhas",
                  value: stats.notifications?.dispatchesFailed ?? 0,
                },
              ]}
              accent={CHART_COLORS.warning}
            />
          </div>
        </article>
      </div>
    </section>
  );
};
