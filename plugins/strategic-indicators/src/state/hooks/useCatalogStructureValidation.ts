import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { fetchStrategicIndicatorGoals } from "../../data/api/strategicIndicatorGoalsApi";
import {
  fetchAdminDepartmentIndicators,
  fetchAdminDepartments,
} from "../../data/api/strategicIndicatorsSettingsApi";
import {
  buildCatalogValidationRows,
  summarizeDepartmentWeight,
  summarizeValidation,
  type CatalogValidationRow,
} from "../../domain/catalogStructureValidation";
import type { StrategicIndicatorGoalItem } from "../../data/types/indicatorGoals";
import type { AdminDepartmentIndicatorItem, AdminDepartmentItem } from "../../data/types/settings";

type UseCatalogStructureValidationParams = {
  getAccessToken?: () => string | undefined;
  goalYear?: number;
};

export function useCatalogStructureValidation({
  getAccessToken,
  goalYear: initialGoalYear = new Date().getFullYear(),
}: UseCatalogStructureValidationParams) {
  const [goalYear, setGoalYear] = useState(initialGoalYear);
  const [departments, setDepartments] = useState<AdminDepartmentItem[]>([]);
  const [indicatorsByDepartment, setIndicatorsByDepartment] = useState<
    Record<string, AdminDepartmentIndicatorItem[]>
  >({});
  const [goalsByIndicator, setGoalsByIndicator] = useState<
    Record<string, StrategicIndicatorGoalItem[]>
  >({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const getAccessTokenRef = useRef(getAccessToken);
  useEffect(() => {
    getAccessTokenRef.current = getAccessToken;
  }, [getAccessToken]);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const departmentsResponse = await fetchAdminDepartments(getAccessTokenRef.current);
      const sortedDepartments = [...departmentsResponse.items].sort(
        (left, right) => left.display_order - right.display_order,
      );

      const indicatorResponses = await Promise.all(
        sortedDepartments.map((department) =>
          fetchAdminDepartmentIndicators(
            department.department_id,
            getAccessTokenRef.current,
          ),
        ),
      );

      const nextIndicatorsByDepartment: Record<string, AdminDepartmentIndicatorItem[]> = {};
      sortedDepartments.forEach((department, index) => {
        nextIndicatorsByDepartment[department.department_id] = [
          ...(indicatorResponses[index]?.items ?? []),
        ].sort((left, right) => left.display_order - right.display_order);
      });

      const goalsResponse = await fetchStrategicIndicatorGoals(
        getAccessTokenRef.current,
        { goalYear, activeOnly: false },
      );

      const nextGoalsByIndicator: Record<string, StrategicIndicatorGoalItem[]> = {};
      for (const goal of goalsResponse.items) {
        if (goal.goal_year !== goalYear) continue;
        nextGoalsByIndicator[goal.indicator_id] ??= [];
        nextGoalsByIndicator[goal.indicator_id].push(goal);
      }

      setDepartments(sortedDepartments);
      setIndicatorsByDepartment(nextIndicatorsByDepartment);
      setGoalsByIndicator(nextGoalsByIndicator);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Falha ao carregar catálogo para validação.",
      );
    } finally {
      setLoading(false);
    }
  }, [goalYear]);

  useEffect(() => {
    void load();
  }, [load]);

  const rows = useMemo(
    () =>
      buildCatalogValidationRows({
        departments,
        indicatorsByDepartment,
        goalsByIndicator,
      }),
    [departments, indicatorsByDepartment, goalsByIndicator],
  );

  const summary = useMemo(() => summarizeValidation(rows), [rows]);

  const departmentWeightIssues = useMemo(() => {
    return departments
      .filter((department) => department.is_active)
      .map((department) => {
        const indicators = indicatorsByDepartment[department.department_id] ?? [];
        const weight = summarizeDepartmentWeight(indicators);
        return {
          departmentId: department.department_id,
          departmentName: department.department_name,
          shortName: department.short_name,
          totalWeight: weight.total,
          ok: weight.ok,
        };
      })
      .filter((item) => !item.ok);
  }, [departments, indicatorsByDepartment]);

  return {
    goalYear,
    setGoalYear,
    rows,
    summary,
    departmentWeightIssues,
    loading,
    error,
    reload: load,
  };
}

export type { CatalogValidationRow };
