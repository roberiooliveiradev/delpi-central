// src/ui/admin/tabs/StatsTab.tsx

import { useCallback, useContext, useEffect, useMemo, useState } from "react";
import {
  BarChart3,
  LayoutGrid,
  RefreshCw,
  Shield,
  Users,
  UsersRound,
} from "lucide-react";

import { AuthContext } from "../../../state/AuthContext";
import { ApiClient } from "../../../data/apiClient";
import { AdminApi, type AdminStatistics } from "../../../data/adminApi";

import "./StatsTab.css";

type StatMetricProps = {
  label: string;
  value: number;
  highlight?: boolean;
};

function StatMetric({ label, value, highlight }: StatMetricProps) {
  return (
    <div
      className={
        highlight
          ? "admin-stats__metric admin-stats__metric--highlight"
          : "admin-stats__metric"
      }
    >
      <strong>{value.toLocaleString("pt-BR")}</strong>
      <span>{label}</span>
    </div>
  );
}

function StatBar({
  label,
  value,
  max,
}: {
  label: string;
  value: number;
  max: number;
}) {
  const width = max > 0 ? Math.max(4, Math.round((value / max) * 100)) : 0;

  return (
    <div className="admin-stats__bar-row">
      <span className="admin-stats__bar-label" title={label}>
        {label}
      </span>
      <div className="admin-stats__bar-track" aria-hidden="true">
        <div className="admin-stats__bar-fill" style={{ width: `${width}%` }} />
      </div>
      <span className="admin-stats__bar-value">{value}</span>
    </div>
  );
}

function RankList({
  title,
  items,
  countLabel,
}: {
  title: string;
  items: { id: string; name: string; count: number }[];
  countLabel: string;
}) {
  if (items.length === 0) {
    return (
      <div className="admin-stats__rank">
        <h5>{title}</h5>
        <p className="admin-stats__empty">Sem dados para exibir.</p>
      </div>
    );
  }

  return (
    <div className="admin-stats__rank">
      <h5>{title}</h5>
      {items.map((item, index) => (
        <div key={item.id} className="admin-stats__rank-item">
          <span className="admin-stats__rank-pos">{index + 1}</span>
          <span className="admin-stats__rank-name" title={item.name}>
            {item.name}
          </span>
          <span className="admin-stats__rank-count">
            {item.count} {countLabel}
          </span>
        </div>
      ))}
    </div>
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

export const StatsTab = () => {
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

  const appsTypeMax = useMemo(() => {
    if (!stats?.apps.byType.length) return 0;
    return Math.max(...stats.apps.byType.map((item) => item.count));
  }, [stats]);

  if (loading && !stats) {
    return <div className="admin-stats__state">Carregando estatísticas…</div>;
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

  if (!stats) {
    return <div className="admin-stats__state">Nenhum dado disponível.</div>;
  }

  return (
    <section className="admin-stats" aria-labelledby="admin-stats-title">
      <header className="admin-stats__header">
        <div>
          <h3 id="admin-stats-title">Estatísticas da plataforma</h3>
          <p>
            Visão consolidada de usuários, aplicações, papéis e grupos para apoiar
            governança de acesso e saúde do ecossistema Minha DELPI.
          </p>
        </div>
        <div className="admin-stats__header-actions">
          {stats.generatedAt ? (
            <span className="admin-stats__generated">
              Atualizado: {formatGeneratedAt(stats.generatedAt)}
            </span>
          ) : null}
          <button
            type="button"
            className="admin-stats__refresh"
            onClick={() => void load()}
            disabled={loading}
          >
            <RefreshCw size={16} aria-hidden="true" />
            {loading ? "Atualizando…" : "Atualizar"}
          </button>
        </div>
      </header>

      <div className="admin-stats__kpis" aria-label="Indicadores principais">
        <article className="admin-stats__kpi">
          <span className="admin-stats__kpi-icon" aria-hidden="true">
            <Users size={18} />
          </span>
          <strong>{stats.users.total}</strong>
          <span>Usuários</span>
          <small>
            {stats.users.online} online · {stats.users.active} ativos
          </small>
        </article>
        <article className="admin-stats__kpi">
          <span className="admin-stats__kpi-icon" aria-hidden="true">
            <LayoutGrid size={18} />
          </span>
          <strong>{stats.apps.total}</strong>
          <span>Aplicações</span>
          <small>
            {stats.apps.active} ativas · {stats.apps.routesTotal} rotas
          </small>
        </article>
        <article className="admin-stats__kpi">
          <span className="admin-stats__kpi-icon" aria-hidden="true">
            <Shield size={18} />
          </span>
          <strong>{stats.roles.total}</strong>
          <span>Papéis</span>
          <small>
            {stats.roles.system} sistema · {stats.roles.custom} customizados
          </small>
        </article>
        <article className="admin-stats__kpi">
          <span className="admin-stats__kpi-icon" aria-hidden="true">
            <UsersRound size={18} />
          </span>
          <strong>{stats.groups.total}</strong>
          <span>Grupos</span>
          <small>
            {stats.groups.active} ativos · {stats.permissions.total} permissões
          </small>
        </article>
      </div>

      <div className="admin-stats__grid">
        <article className="admin-stats__panel">
          <div className="admin-stats__panel-head">
            <span className="admin-stats__panel-icon" aria-hidden="true">
              <Users size={16} />
            </span>
            <h4>Usuários</h4>
          </div>
          <div className="admin-stats__metrics">
            <StatMetric label="Ativos" value={stats.users.active} />
            <StatMetric label="Inativos" value={stats.users.inactive} />
            <StatMetric label="Online agora" value={stats.users.online} highlight />
            <StatMetric label="Superadmins" value={stats.users.superadmins} />
            <StatMetric label="Login últimos 7 dias" value={stats.users.loggedInLast7Days} />
            <StatMetric label="Login últimos 30 dias" value={stats.users.loggedInLast30Days} />
            <StatMetric label="Com data de nascimento" value={stats.users.withBirthDate} />
            <StatMetric label="Sem papel direto" value={stats.users.withoutDirectRoles} />
            <StatMetric label="Sem grupo" value={stats.users.withoutGroups} />
          </div>
          <div className="admin-stats__bars" aria-label="Proporção ativos e inativos">
            <StatBar label="Ativos" value={stats.users.active} max={stats.users.total} />
            <StatBar label="Inativos" value={stats.users.inactive} max={stats.users.total} />
          </div>
        </article>

        <article className="admin-stats__panel">
          <div className="admin-stats__panel-head">
            <span className="admin-stats__panel-icon" aria-hidden="true">
              <LayoutGrid size={16} />
            </span>
            <h4>Aplicações</h4>
          </div>
          <div className="admin-stats__metrics">
            <StatMetric label="Ativas" value={stats.apps.active} />
            <StatMetric label="Inativas" value={stats.apps.inactive} />
            <StatMetric label="Rotas totais" value={stats.apps.routesTotal} />
            <StatMetric label="Rotas ativas" value={stats.apps.routesActive} highlight />
          </div>
          <div className="admin-stats__bars" aria-label="Aplicações por tipo">
            {stats.apps.byType.length === 0 ? (
              <p className="admin-stats__empty">Nenhuma aplicação cadastrada.</p>
            ) : (
              stats.apps.byType.map((item) => (
                <StatBar
                  key={item.type}
                  label={formatAppType(item.type)}
                  value={item.count}
                  max={appsTypeMax}
                />
              ))
            )}
          </div>
        </article>

        <article className="admin-stats__panel">
          <div className="admin-stats__panel-head">
            <span className="admin-stats__panel-icon" aria-hidden="true">
              <Shield size={16} />
            </span>
            <h4>Papéis</h4>
          </div>
          <div className="admin-stats__metrics">
            <StatMetric label="De sistema" value={stats.roles.system} />
            <StatMetric label="Customizados" value={stats.roles.custom} />
            <StatMetric label="Sem usuários" value={stats.roles.withoutUsers} />
          </div>
          <RankList
            title="Mais atribuídos a usuários"
            items={stats.roles.topByUsers}
            countLabel="usuários"
          />
        </article>

        <article className="admin-stats__panel">
          <div className="admin-stats__panel-head">
            <span className="admin-stats__panel-icon" aria-hidden="true">
              <UsersRound size={16} />
            </span>
            <h4>Grupos</h4>
          </div>
          <div className="admin-stats__metrics">
            <StatMetric label="Ativos" value={stats.groups.active} />
            <StatMetric label="Inativos" value={stats.groups.inactive} />
            <StatMetric label="Sem usuários" value={stats.groups.withoutUsers} />
          </div>
          <RankList
            title="Mais usuários"
            items={stats.groups.topByUsers}
            countLabel="usuários"
          />
          <RankList
            title="Mais papéis vinculados"
            items={stats.groups.topByRoles}
            countLabel="papéis"
          />
        </article>
      </div>

      <article className="admin-stats__overview" aria-label="Vínculos RBAC">
        <h4>
          <BarChart3 size={16} aria-hidden="true" /> Vínculos e permissões
        </h4>
        <div className="admin-stats__metrics">
          <StatMetric
            label="Atribuições usuário → papel"
            value={stats.assignments.userRoles}
          />
          <StatMetric
            label="Atribuições usuário → grupo"
            value={stats.assignments.userGroups}
          />
          <StatMetric
            label="Atribuições grupo → papel"
            value={stats.assignments.groupRoles}
          />
          <StatMetric
            label="Permissões em papéis"
            value={stats.assignments.rolePermissions}
          />
          <StatMetric label="Permissões cadastradas" value={stats.permissions.total} />
        </div>
      </article>
    </section>
  );
};
