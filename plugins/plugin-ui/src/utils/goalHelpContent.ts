/**
 * Help texts for KPI goal lines (canonical PT in plugin-ui — not copied per MFE).
 */

export type GoalLineHelpKind = "exact" | "partial" | "accumulated";

export type GoalLineHelpMode = "standard" | "monthly_curve" | string | null | undefined;

export function resolvePeriodGoalHelp(kind: GoalLineHelpKind): string {
  if (kind === "partial") {
    return "Meta calculada para o intervalo incompleto do mês (proporcional aos dias / regra do indicador). Usada no IDD e em «dentro/fora da meta».";
  }
  if (kind === "accumulated") {
    return "Meta calculada para o intervalo multi-mês (soma ou média conforme a unidade do indicador). Usada no IDD e em «dentro/fora da meta».";
  }
  return "Meta do período filtrado; neste caso coincide com a meta do mês civil fechado cadastrada no SI.";
}

export function resolveMonthlyGoalHelp(goalMode?: GoalLineHelpMode): string {
  const mode = (goalMode ?? "standard").toString().trim().toLowerCase();
  if (mode === "monthly_curve") {
    return "Média dos pontos da curva (monthly_targets) nos meses civis que intersectam o filtro. Não aplica a prorata do período.";
  }
  return "Valor cadastrado no SI (goal_value) — referência do mês, sem prorata do filtro.";
}

export function resolveGoalLineHelp(options: {
  kind: GoalLineHelpKind;
  goalMode?: GoalLineHelpMode;
  line: "period" | "monthly";
}): string {
  if (options.line === "monthly") {
    return resolveMonthlyGoalHelp(options.goalMode);
  }
  return resolvePeriodGoalHelp(options.kind);
}
