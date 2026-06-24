import {
  AlertTriangle,
  CalendarCheck,
  ClipboardList,
  Clock,
  ShieldAlert,
  Timer,
  type LucideIcon,
} from "lucide-react";

import type { DashboardSummary } from "../types/actionPlan";

export type KpiTone = "default" | "danger" | "warning" | "success";

export type KpiDefinition = {
  key: keyof Pick<
    DashboardSummary,
    | "open_plans"
    | "critical_open"
    | "waiting_validation"
    | "completed_this_month"
    | "overdue_actions"
    | "overdue_plans"
  >;
  label: string;
  tone?: KpiTone;
  icon: LucideIcon;
};

export const DASHBOARD_KPIS: KpiDefinition[] = [
  { key: "open_plans", label: "Planos abertos", icon: ClipboardList },
  { key: "critical_open", label: "Críticos abertos", tone: "danger", icon: ShieldAlert },
  { key: "overdue_plans", label: "Planos com atraso", tone: "warning", icon: Timer },
  { key: "overdue_actions", label: "Ações atrasadas", tone: "warning", icon: Clock },
  { key: "waiting_validation", label: "Aguardando validação", icon: AlertTriangle },
  { key: "completed_this_month", label: "Concluídos no mês", tone: "success", icon: CalendarCheck },
];
