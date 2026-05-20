// src/ui/admin/stats/StatsShared.tsx

import { ArrowRight, RefreshCw } from "lucide-react";
import type { AdminTab } from "../AdminPage";
import type { AdminStatistics } from "../../../data/adminApi";

export function formatGeneratedAt(value: string) {
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
}

export function formatAppType(type: string) {
  if (type === "iframe") return "Iframe";
  if (type === "microfrontend") return "Microfrontend";
  if (type === "backend-only") return "Backend-only";
  return type;
}

export function PanelNav({
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

export function StatsPageIntro({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <header className="admin-stats-page__intro">
      <h4>{title}</h4>
      <p>{description}</p>
    </header>
  );
}

export function StatsRefreshBar({
  generatedAt,
  loading,
  onRefresh,
}: {
  generatedAt?: string;
  loading: boolean;
  onRefresh: () => void;
}) {
  return (
    <div className="admin-stats-page__toolbar">
      {generatedAt ? (
        <span className="admin-stats__generated">
          Atualizado: {formatGeneratedAt(generatedAt)}
        </span>
      ) : null}
      <button
        type="button"
        className="admin-stats__refresh"
        onClick={onRefresh}
        disabled={loading}
      >
        <RefreshCw size={16} className={loading ? "admin-stats__spin" : ""} />
        {loading ? "Atualizando…" : "Atualizar dados"}
      </button>
    </div>
  );
}

export type StatsPageProps = {
  stats: AdminStatistics;
  onNavigateTab?: (tab: AdminTab) => void;
};
