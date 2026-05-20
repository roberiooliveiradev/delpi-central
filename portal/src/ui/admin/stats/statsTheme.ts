// src/ui/admin/stats/statsTheme.ts
// Paleta via tokens globais do portal (--chart-*, --stats-*) — vivida em claro e escuro

export const STATS_CHART_COLORS = {
  c1: "var(--chart-1)",
  c2: "var(--chart-2)",
  c3: "var(--chart-3)",
  c4: "var(--chart-4)",
  c5: "var(--chart-5)",
  c6: "var(--chart-6)",
  muted: "var(--chart-muted)",
  primary: "var(--chart-1)",
  accent: "var(--chart-3)",
  success: "var(--chart-4)",
  warning: "var(--chart-5)",
  danger: "var(--chart-6)",
} as const;

export type StatsSubPage = "overview" | "users" | "apps" | "access" | "notifications";

export const STATS_SUB_PAGES: {
  id: StatsSubPage;
  label: string;
  description: string;
}[] = [
  {
    id: "overview",
    label: "Visão geral",
    description: "KPIs e resumo executivo da plataforma",
  },
  {
    id: "users",
    label: "Usuários",
    description: "Atividade, presença online e logins",
  },
  {
    id: "apps",
    label: "Aplicações",
    description: "Uso em tempo real, ranking e apps fantasmas",
  },
  {
    id: "access",
    label: "Acesso RBAC",
    description: "Papéis, grupos e vínculos de permissão",
  },
  {
    id: "notifications",
    label: "Notificações",
    description: "Campanhas e envios agendados",
  },
];
