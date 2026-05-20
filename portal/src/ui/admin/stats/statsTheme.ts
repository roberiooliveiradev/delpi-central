// src/ui/admin/stats/statsTheme.ts
// Paleta alinhada aos tokens do portal (index.css — Minha DELPI)

export const STATS_CHART_COLORS = {
  primary: "var(--primary)",
  secondary: "var(--secundary)",
  success: "var(--success)",
  danger: "var(--danger)",
  muted: "color-mix(in srgb, var(--text-muted) 60%, var(--border))",
  primaryLight: "color-mix(in srgb, var(--primary) 72%, #ffffff)",
  secondaryMuted: "color-mix(in srgb, var(--secundary) 45%, var(--primary))",
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
