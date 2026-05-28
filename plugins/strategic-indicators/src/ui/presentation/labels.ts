export function getGoalPeriodicityLabel(value: string | null | undefined): string {
  switch (value) {
    case "monthly":
      return "Mensal";
    case "annual":
      return "Anual";
    case "quarterly":
      return "Trimestral";
    case "weekly":
      return "Semanal";
    default:
      return value ?? "—";
  }
}

export function getGoalModeLabel(value: string | null | undefined): string {
  switch (value) {
    case "standard":
      return "Padrão";
    case "monthly_curve":
      return "Curva";
    default:
      return value ?? "—";
  }
}

export function getAggregationModeLabel(value: string | null | undefined): string {
  switch (value) {
    case "consolidated":
      return "Consolidado";
    case "average_of_units":
      return "Média das unidades";
    case "mixed_scope":
      return "Escopo misto";
    default:
      return value ?? "—";
  }
}

export function getScopeTypeLabel(value: string | null | undefined): string {
  switch (value) {
    case "consolidated":
      return "Consolidado";
    case "per_unit":
      return "Por unidade";
    default:
      return value ?? "—";
  }
}

export function getGoalScopeBranchLabel(value: string | null | undefined): string {
  switch ((value ?? "").trim()) {
    case "":
      return "Consolidado";
    case "01":
      return "01";
    case "02":
      return "02";
    default:
      return value ?? "—";
  }
}

export function getPerformanceDirectionLabel(
  value: string | null | undefined,
): string {
  switch (value) {
    case "higher_is_better":
      return "Quanto maior, melhor";
    case "lower_is_better":
      return "Quanto menor, melhor";
    default:
      return value ?? "—";
  }
}

export function getTrendLabel(value: string | null | undefined): string {
  switch (value) {
    case "up":
      return "Alta";
    case "down":
      return "Queda";
    case "stable":
      return "Estável";
    default:
      return value ?? "—";
  }
}

export function getSeverityLabel(value: string | null | undefined): string {
  switch (value) {
    case "high":
      return "Alta";
    case "medium":
      return "Média";
    case "low":
      return "Baixa";
    default:
      return value ?? "—";
  }
}

export function getReadinessStatusLabel(value: string | null | undefined): string {
  switch (value) {
    case "ready":
      return "Pronto";
    case "planned":
      return "Planejado";
    case "mock":
      return "Simulado";
    default:
      return value ?? "—";
  }
}

export function getMetaSourceLabel(value: string | null | undefined): string {
  switch (value) {
    case "postgres-plugins":
      return "Base interna de plugins";
    default:
      return value ?? "—";
  }
}

export function getAuditEntityKeyLabel(value: string | null | undefined): string {
  switch (value) {
    case "departments":
      return "Departamentos";
    case "department_indicators":
      return "Indicadores dos departamentos";
    case "indicator_goals":
      return "Metas dos indicadores";
    case "parameters.global":
      return "Parâmetros globais";
    case "governance.notes":
      return "Governança";
    case "weights.departments":
      return "Pesos dos departamentos";
    case "goals.summary":
      return "Resumo de metas";
    default:
      return value ?? "—";
  }
}

export function getChangeRequestStatusLabel(
  value: string | null | undefined,
): string {
  switch (value) {
    case "draft":
      return "Rascunho";
    case "submitted":
      return "Enviada";
    case "approved":
      return "Aprovada";
    case "rejected":
      return "Rejeitada";
    case "cancelled":
      return "Cancelada";
    default:
      return value ?? "—";
  }
}