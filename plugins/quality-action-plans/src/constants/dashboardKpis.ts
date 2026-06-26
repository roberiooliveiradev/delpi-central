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
import { PAC_HELP_TOOLTIPS } from "../content/helpTooltips";

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
  hint?: string;
  tone?: KpiTone;
  icon: LucideIcon;
};

export const DASHBOARD_KPIS: KpiDefinition[] = [
  { key: "open_plans", label: "Planos abertos", icon: ClipboardList, hint: PAC_HELP_TOOLTIPS.kpis.openPlans },
  { key: "critical_open", label: "Críticos abertos", tone: "danger", icon: ShieldAlert, hint: PAC_HELP_TOOLTIPS.kpis.criticalOpen },
  { key: "overdue_plans", label: "Planos com atraso", tone: "warning", icon: Timer, hint: PAC_HELP_TOOLTIPS.kpis.overduePlans },
  { key: "overdue_actions", label: "Ações atrasadas", tone: "warning", icon: Clock, hint: PAC_HELP_TOOLTIPS.kpis.overdueActions },
  { key: "waiting_validation", label: "Aguardando validação", icon: AlertTriangle, hint: PAC_HELP_TOOLTIPS.kpis.waitingValidation },
  { key: "completed_this_month", label: "Concluídos no mês", tone: "success", icon: CalendarCheck, hint: PAC_HELP_TOOLTIPS.kpis.completedThisMonth },
];
