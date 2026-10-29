import { EngineeringKpiCard } from "../../../ui/engineeringUi";
import type { DashboardKpiCardProps } from "@delpi/plugin-ui/index";

export type { GoalPerformanceBadge, GoalScopeBadge } from "../utils/goalDisplay";

/** KPI canônico do Portal Engenharia (mesmo componente da Visão Geral). */
export const KpiCard = EngineeringKpiCard;

export type KpiCardProps = DashboardKpiCardProps;
