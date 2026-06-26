import type { AdminDepartmentIndicatorItem, AdminDepartmentItem } from "../data/types/settings";
import type { StrategicIndicatorGoalItem } from "../data/types/indicatorGoals";

const OPERATIONAL_UNIT_NAMES: Record<string, string> = {
  "01": "Santa Catarina",
  "02": "Espírito Santo",
};

function formatOperationalUnitCodesList(codes: string): string {
  return codes
    .split(" e ")
    .map((code) => OPERATIONAL_UNIT_NAMES[code.trim()] ?? code.trim())
    .join(" e ");
}

export type ValidationSeverity = "ok" | "info" | "warning" | "error";

export type CatalogValidationIssue = {
  code: string;
  severity: ValidationSeverity;
  message: string;
};

export type GoalScopeCoverage = {
  consolidated: boolean;
  branch01: boolean;
  branch02: boolean;
  activeCount: number;
};

export type CatalogValidationRow = {
  departmentId: string;
  departmentName: string;
  departmentShortName: string;
  departmentAggregation: AdminDepartmentItem["aggregation_mode"];
  departmentWeightPct: number;
  departmentActive: boolean;
  indicatorId: string;
  indicatorName: string;
  scopeType: AdminDepartmentIndicatorItem["scope_type"];
  indicatorWeightPct: number;
  indicatorActive: boolean;
  goalCoverage: GoalScopeCoverage;
  issues: CatalogValidationIssue[];
  worstSeverity: ValidationSeverity;
};

const SEVERITY_RANK: Record<ValidationSeverity, number> = {
  ok: 0,
  info: 1,
  warning: 2,
  error: 3,
};

function worstOf(issues: CatalogValidationIssue[]): ValidationSeverity {
  if (issues.length === 0) return "ok";
  return issues.reduce<ValidationSeverity>(
    (worst, issue) =>
      SEVERITY_RANK[issue.severity] > SEVERITY_RANK[worst] ? issue.severity : worst,
    "ok",
  );
}

function normalizeScope(scope: string | null | undefined): string {
  return (scope ?? "").trim();
}

export function buildGoalCoverage(
  goals: StrategicIndicatorGoalItem[],
): GoalScopeCoverage {
  const active = goals.filter((goal) => goal.is_active);
  return {
    consolidated: active.some((goal) => normalizeScope(goal.goal_scope_branch) === ""),
    branch01: active.some((goal) => normalizeScope(goal.goal_scope_branch) === "01"),
    branch02: active.some((goal) => normalizeScope(goal.goal_scope_branch) === "02"),
    activeCount: active.length,
  };
}

export function validateCatalogRow(input: {
  department: AdminDepartmentItem;
  indicator: AdminDepartmentIndicatorItem;
  goalsForYear: StrategicIndicatorGoalItem[];
}): CatalogValidationIssue[] {
  const { department, indicator, goalsForYear } = input;
  const issues: CatalogValidationIssue[] = [];
  const coverage = buildGoalCoverage(goalsForYear);
  const deptAggregation = department.aggregation_mode;
  const scopeType = indicator.scope_type;

  if (!department.is_active && indicator.is_active) {
    issues.push({
      code: "inactive_department_active_indicator",
      severity: "warning",
      message: "Indicador ativo em departamento inativo.",
    });
  }

  if (!indicator.is_active && coverage.activeCount > 0) {
    issues.push({
      code: "inactive_indicator_active_goal",
      severity: "warning",
      message: "Meta ativa em indicador inativo.",
    });
  }

  if (indicator.is_active && !(indicator.source_key ?? "").trim()) {
    issues.push({
      code: "missing_source_key",
      severity: "error",
      message:
        "Chave da fonte obrigatória para indicador ativo (medições e dashboards departamentais).",
    });
  }

  if (indicator.is_active && coverage.activeCount === 0) {
    issues.push({
      code: "no_active_goal",
      severity: "error",
      message: "Sem meta ativa para o ano selecionado.",
    });
  }

  if (deptAggregation === "average_of_units") {
    if (indicator.is_active && coverage.activeCount > 0) {
      if (!coverage.branch01 || !coverage.branch02) {
        const missing = [
          !coverage.branch01 ? "01" : null,
          !coverage.branch02 ? "02" : null,
        ]
          .filter(Boolean)
          .join(" e ");
        issues.push({
          code: "missing_branch_goals",
          severity: "error",
          message: `Departamento por unidade exige metas ativas para ${formatOperationalUnitCodesList(missing)}.`,
        });
      }
      if (coverage.consolidated && !coverage.branch01 && !coverage.branch02) {
        issues.push({
          code: "only_consolidated_goal_on_average_dept",
          severity: "warning",
          message:
            "Só meta consolidada: visão por unidade (Santa Catarina / Espírito Santo) não pontua até cadastrar metas por unidade.",
        });
      }
    }

    if (scopeType === "consolidated" && indicator.is_active) {
      issues.push({
        code: "consolidated_indicator_on_average_dept",
        severity: "info",
        message:
          "Indicador consolidado em depto por unidade (ex.: RH): use metas por unidade e realizado por unidade.",
      });
    }
  }

  if (deptAggregation === "consolidated") {
    if (indicator.is_active && coverage.activeCount > 0) {
      const hasBranchOnly =
        (coverage.branch01 || coverage.branch02) && !coverage.consolidated;
      if (hasBranchOnly && scopeType === "consolidated") {
        issues.push({
          code: "branch_only_goals_on_consolidated_indicator",
          severity: "warning",
          message:
            "Indicador consolidado só com metas por unidade: visão consolidada pode ficar sem meta.",
        });
      }
      if (!coverage.consolidated && !coverage.branch01 && !coverage.branch02) {
        issues.push({
          code: "no_goal_scope",
          severity: "error",
          message: "Nenhuma meta ativa com escopo reconhecido.",
        });
      }
    }

    if (scopeType === "per_unit" && indicator.is_active) {
      issues.push({
        code: "per_unit_indicator_on_consolidated_dept",
        severity: "info",
        message:
          "Indicador por unidade em depto consolidado (ex.: ROL): IDD do depto usa nota consolidada na visão geral.",
      });
    }

    if (indicator.is_active && !coverage.consolidated && coverage.branch01 && coverage.branch02) {
      issues.push({
        code: "consolidated_dept_branch_goals_ok",
        severity: "info",
        message:
          "Metas 01/02 sem consolidado: painel repetirá metas consolidadas nas filiais (regra do depto).",
      });
    }
  }

  if (
    deptAggregation === "consolidated" &&
    scopeType === "per_unit" &&
    indicator.is_active &&
    coverage.consolidated &&
    (coverage.branch01 || coverage.branch02)
  ) {
    issues.push({
      code: "mixed_goal_scopes",
      severity: "info",
      message: "Metas consolidado e filiais coexistem; confira qual escopo o painel usa por visão.",
    });
  }

  return issues;
}

export function buildCatalogValidationRows(input: {
  departments: AdminDepartmentItem[];
  indicatorsByDepartment: Record<string, AdminDepartmentIndicatorItem[]>;
  goalsByIndicator: Record<string, StrategicIndicatorGoalItem[]>;
}): CatalogValidationRow[] {
  const rows: CatalogValidationRow[] = [];

  for (const department of input.departments) {
    const indicators = input.indicatorsByDepartment[department.department_id] ?? [];

    if (department.is_active && indicators.filter((item) => item.is_active).length === 0) {
      rows.push({
        departmentId: department.department_id,
        departmentName: department.department_name,
        departmentShortName: department.short_name,
        departmentAggregation: department.aggregation_mode,
        departmentWeightPct: department.weight_pct,
        departmentActive: department.is_active,
        indicatorId: "—",
        indicatorName: "—",
        scopeType: "consolidated",
        indicatorWeightPct: 0,
        indicatorActive: false,
        goalCoverage: buildGoalCoverage([]),
        issues: [
          {
            code: "department_without_indicators",
            severity: "error",
            message: "Departamento ativo sem indicadores ativos.",
          },
        ],
        worstSeverity: "error",
      });
      continue;
    }

    for (const indicator of indicators) {
      const goalsForYear = input.goalsByIndicator[indicator.indicator_id] ?? [];
      const issues = validateCatalogRow({ department, indicator, goalsForYear });

      rows.push({
        departmentId: department.department_id,
        departmentName: department.department_name,
        departmentShortName: department.short_name,
        departmentAggregation: department.aggregation_mode,
        departmentWeightPct: department.weight_pct,
        departmentActive: department.is_active,
        indicatorId: indicator.indicator_id,
        indicatorName: indicator.indicator_name,
        scopeType: indicator.scope_type,
        indicatorWeightPct: indicator.weight_pct,
        indicatorActive: indicator.is_active,
        goalCoverage: buildGoalCoverage(goalsForYear),
        issues,
        worstSeverity: worstOf(issues),
      });
    }
  }

  return rows;
}

export function summarizeDepartmentWeight(
  indicators: AdminDepartmentIndicatorItem[],
): { total: number; ok: boolean } {
  const total = indicators
    .filter((item) => item.is_active)
    .reduce((sum, item) => sum + Number(item.weight_pct || 0), 0);
  return {
    total: Math.round(total * 100) / 100,
    ok: Math.abs(total - 100) < 0.05,
  };
}

export function summarizeValidation(rows: CatalogValidationRow[]) {
  const indicatorRows = rows.filter((row) => row.indicatorId !== "—");
  return {
    totalRows: indicatorRows.length,
    errors: indicatorRows.filter((row) => row.worstSeverity === "error").length,
    warnings: indicatorRows.filter((row) => row.worstSeverity === "warning").length,
    infos: indicatorRows.filter((row) => row.worstSeverity === "info").length,
    ok: indicatorRows.filter((row) => row.worstSeverity === "ok").length,
  };
}
