// src/ui/admin/stats/StatsEnrichment.tsx

import { useState, type ReactNode } from "react";
import { ChevronDown, Ghost, UserX } from "lucide-react";

import type {
  AdminStatisticsLeastEngaged,
  AdminStatisticsRankItem,
} from "../../../data/adminApi";
import { formatGeneratedAt } from "./StatsShared";

export function statPercent(part: number, total: number): number {
  if (total <= 0) return 0;
  return Math.round((part / total) * 100);
}

export function formatPercent(value: number): string {
  return `${value}%`;
}

type MiniKpiProps = {
  label: string;
  value: string | number;
  hint?: string;
  tone?: "default" | "primary" | "success" | "warning" | "danger";
};

export function StatsMiniKpi({ label, value, hint, tone = "default" }: MiniKpiProps) {
  return (
    <article className={`admin-stats-mini-kpi admin-stats-mini-kpi--${tone}`}>
      <span className="admin-stats-mini-kpi__value">{value}</span>
      <span className="admin-stats-mini-kpi__label">{label}</span>
      {hint ? <span className="admin-stats-mini-kpi__hint">{hint}</span> : null}
    </article>
  );
}

export function StatsMiniKpiRow({ children }: { children: ReactNode }) {
  return (
    <div className="admin-stats-mini-kpi-row" role="list">
      {children}
    </div>
  );
}

type InsightProps = {
  label: string;
  value: string;
  detail?: string;
};

export function StatsInsight({ label, value, detail }: InsightProps) {
  return (
    <div className="admin-stats-insight">
      <span className="admin-stats-insight__label">{label}</span>
      <strong className="admin-stats-insight__value">{value}</strong>
      {detail ? <span className="admin-stats-insight__detail">{detail}</span> : null}
    </div>
  );
}

export function StatsInsightRow({ children }: { children: ReactNode }) {
  return <div className="admin-stats-insight-row">{children}</div>;
}

type ChartCardProps = {
  title: string;
  children: ReactNode;
  foot?: string;
  action?: ReactNode;
};

export function StatsChartCard({ title, children, foot, action }: ChartCardProps) {
  return (
    <article className="admin-stats__chart-card">
      <div className="admin-stats-chart-card__head">
        <h5>{title}</h5>
        {action}
      </div>
      {children}
      {foot ? <p className="admin-stats__chart-foot">{foot}</p> : null}
    </article>
  );
}

const GHOST_PREVIEW = 6;

export function GhostAppsCompact({ apps }: { apps: AdminStatisticsRankItem[] }) {
  const [expanded, setExpanded] = useState(false);
  const count = apps.length;
  const hasMore = count > GHOST_PREVIEW;
  const visible = expanded || !hasMore ? apps : apps.slice(0, GHOST_PREVIEW);

  if (count === 0) {
    return (
      <aside className="admin-stats-ghost-panel admin-stats-ghost-panel--ok">
        <header className="admin-stats-ghost-panel__head">
          <Ghost size={16} aria-hidden="true" />
          <div>
            <strong>Apps fantasmas</strong>
            <span>Todas as apps com UI ativas tiveram abertura no portal</span>
          </div>
        </header>
      </aside>
    );
  }

  return (
    <aside className="admin-stats-ghost-panel">
      <header className="admin-stats-ghost-panel__head">
        <Ghost size={16} aria-hidden="true" />
        <div>
          <strong>
            Fantasmas <span className="admin-stats-ghost-panel__badge">{count}</span>
          </strong>
          <span>Com interface no portal, sem abertura nos últimos 30 dias</span>
        </div>
      </header>
      <ul className="admin-stats-ghost-panel__list" aria-label="Aplicações fantasmas">
        {visible.map((item) => (
          <li key={item.id} title={item.id}>
            <span className="admin-stats-ghost-panel__name">{item.name}</span>
            <span className="admin-stats-ghost-panel__id">{item.id}</span>
          </li>
        ))}
      </ul>
      {hasMore ? (
        <button
          type="button"
          className="admin-stats-ghost-panel__toggle"
          onClick={() => setExpanded((v) => !v)}
          aria-expanded={expanded}
        >
          <ChevronDown
            size={14}
            className={expanded ? "admin-stats-ghost-panel__chevron--open" : ""}
            aria-hidden="true"
          />
          {expanded ? "Mostrar menos" : `Ver mais ${count - GHOST_PREVIEW}`}
        </button>
      ) : null}
    </aside>
  );
}

export function LeastEngagedUsersPanel({
  data,
}: {
  data?: AdminStatisticsLeastEngaged;
}) {
  const items = data?.items ?? [];
  const periodDays = data?.periodDays ?? 30;

  return (
    <section className="admin-stats__panel admin-stats__panel--wide">
      <div className="admin-stats-panel__title-row">
        <h5>
          <UserX size={14} aria-hidden="true" />
          Menor uso da plataforma
        </h5>
        <span className="admin-stats-panel__badge">{items.length}</span>
      </div>
      <p className="admin-stats-panel__lede">
        Usuários ativos com menos apps utilizados nos últimos {periodDays} dias,
        com apps, papéis e grupos liberados para cada um.
      </p>

      {items.length === 0 ? (
        <p className="admin-stats__empty">
          Nenhum usuário ativo encontrado para o ranking.
        </p>
      ) : (
        <ul className="admin-stats-least-engaged-list" aria-label="Usuários com menor engajamento">
          {items.map((user) => (
            <li key={user.id} className="admin-stats-least-engaged-item">
              <div className="admin-stats-least-engaged-item__head">
                <div>
                  <strong>{user.name}</strong>
                  <span className="admin-stats-least-engaged-item__email">
                    {user.email}
                  </span>
                </div>
                <div className="admin-stats-least-engaged-item__metrics">
                  <span>{user.appsUsedInPeriod} apps usados</span>
                  <span>{user.totalOpensInPeriod} aberturas</span>
                  <span>{user.availableAppsCount} apps</span>
                  <span>{user.availableRolesCount ?? 0} papéis</span>
                  <span>{user.availableGroupsCount ?? 0} grupos</span>
                </div>
              </div>
              <div className="admin-stats-least-engaged-item__meta">
                {user.isSuperadmin ? (
                  <span className="admin-stats-least-engaged-item__superadmin">
                    Superadmin
                  </span>
                ) : null}
                <span>
                  Último login:{" "}
                  {user.lastLoginAt
                    ? formatGeneratedAt(user.lastLoginAt)
                    : "nunca"}
                </span>
                {user.lastAppUsageAt ? (
                  <span>
                    Último app: {formatGeneratedAt(user.lastAppUsageAt)}
                  </span>
                ) : null}
              </div>
              <AccessTagSection
                label="Apps"
                items={user.availableApps}
                emptyText="Nenhum app liberado via RBAC."
                tone="apps"
              />
              <AccessTagSection
                label="Papéis"
                items={user.availableRoles ?? []}
                emptyText="Nenhum papel atribuído."
                tone="roles"
              />
              <AccessTagSection
                label="Grupos"
                items={user.availableGroups ?? []}
                emptyText="Nenhum grupo atribuído."
                tone="groups"
              />
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function AccessTagSection({
  label,
  items,
  emptyText,
  tone,
}: {
  label: string;
  items: { id: string; name: string }[];
  emptyText: string;
  tone: "apps" | "roles" | "groups";
}) {
  return (
    <div className={`admin-stats-least-engaged-item__access admin-stats-least-engaged-item__access--${tone}`}>
      <span className="admin-stats-least-engaged-item__access-label">{label}</span>
      {items.length > 0 ? (
        <ul className="admin-stats__ghost-tags admin-stats-least-engaged-item__tags">
          {items.map((item) => (
            <li key={item.id} title={item.id}>
              {item.name}
            </li>
          ))}
        </ul>
      ) : (
        <p className="admin-stats__empty admin-stats-least-engaged-item__no-apps">
          {emptyText}
        </p>
      )}
    </div>
  );
}
