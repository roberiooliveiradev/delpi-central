export type AlertSeverity = "high" | "medium" | "low";

export type ExecutiveAlertViewItem = {
  id: string;
  title: string;
  severity: AlertSeverity;
  impact: string;
  recommendation: string;
};

export type DepartmentAlertViewItem = {
  id: string;
  departmentName: string;
  currentScore: number;
  previousScore: number;
  severity: AlertSeverity;
  reason: string;
  recommendation: string;
};

export type IndicatorAlertViewItem = {
  id: string;
  departmentName: string;
  indicatorName: string;
  simulatedScore: number;
  goalLabel: string;
  severity: AlertSeverity;
  reason: string;
  recommendation: string;
};

export type AlertsDashboardViewData = {
  competence: string;
  igdClassification: string;
  executiveAlerts: ExecutiveAlertViewItem[];
  departmentAlerts: DepartmentAlertViewItem[];
  indicatorAlerts: IndicatorAlertViewItem[];
  partialSuccess: boolean;
  errors: Array<{
    departmentId: string;
    source: string;
    message: string;
  }>;
};

export type StrategicIndicatorsAlertsResponse = {
  competence: string;
  executive_alerts: Array<{
    title: string;
    severity: AlertSeverity;
    impact: string;
    recommendation: string;
  }>;
  department_alerts: Array<{
    department_id: string;
    department_name: string;
    severity: AlertSeverity;
    score: number;
    classification: string;
    contribution: number;
    message: string;
  }>;
  indicator_alerts: Array<{
    department_id: string;
    department_name: string;
    indicator_id: string;
    indicator_name: string;
    severity: AlertSeverity;
    score: number;
    gap: number;
    classification: string;
    source: string;
    message: string;
    goal_label?: string;
  }>;
  errors?: Array<{
    department_id: string;
    source: string;
    message: string;
  }>;
  partial_success?: boolean;
};