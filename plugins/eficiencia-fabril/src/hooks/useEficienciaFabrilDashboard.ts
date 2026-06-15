import { useCallback, useEffect, useMemo, useState } from "react";

import { fetchAllEficienciaFabrilItems } from "../api/fetchAllEficienciaFabrilItems";
import { isProductionEfficiencyOutlier } from "../constants/businessRules";
import { matchesShiftFilter } from "../constants/shifts";
import type {
  EficienciaFabrilDashboardData,
  EficienciaFabrilFilterParams,
  EficienciaFabrilItem,
} from "../types/eficienciaFabril";
import {
  DEFAULT_APPOINTMENTS_SORT,
  sortAppointments,
} from "../utils/appointmentsTableSort";
import { buildEmployeeOptionValue } from "../utils/filterOptions";

const FALLBACK_PAGE_SIZE = 50;

type LoadedRange = {
  dateStart: string;
  dateEnd: string;
  branch: string;
};

function hasDateRange(item: EficienciaFabrilItem): item is EficienciaFabrilItem & {
  data_producao: string;
} {
  return Boolean(item.data_producao);
}

function isWithinRange(date: string, dateStart: string, dateEnd: string): boolean {
  return date >= dateStart && date <= dateEnd;
}

function includesSelectedValue(
  value: string | null | undefined,
  selected: string[] | undefined
): boolean {
  if (!selected || selected.length === 0) return true;
  const normalized = value?.trim();
  if (!normalized) return false;
  return selected.includes(normalized);
}

function applyScopeFilters(
  items: EficienciaFabrilItem[],
  params: EficienciaFabrilFilterParams
): EficienciaFabrilItem[] {
  return items
    .filter(hasDateRange)
    .filter((item) => isWithinRange(item.data_producao, params.date_start, params.date_end))
    .filter((item) => (params.branch ? item.filial === params.branch : true))
    .filter((item) => includesSelectedValue(item.op, params.ops))
    .filter((item) => includesSelectedValue(item.centro_trabalho, params.work_centers))
    .filter((item) => {
      if (!params.employees || params.employees.length === 0) return true;
      const employeeValue = buildEmployeeOptionValue(item);
      return employeeValue ? params.employees.includes(employeeValue) : false;
    })
    .filter((item) => matchesShiftFilter(item.hora_inicio, params.shifts));
}

function computeDashboardFromItems(
  scopedItems: EficienciaFabrilItem[],
  visibleItems: EficienciaFabrilItem[],
  page: number,
  pageSize: number
): EficienciaFabrilDashboardData {
  const okItems = scopedItems.filter((item) => item.status_registro === "OK");
  const indicatorItems = okItems.filter(
    (item) => !isProductionEfficiencyOutlier(item.eficiencia_percentual)
  );

  const efficiencyValues = indicatorItems
    .map((item) => item.eficiencia_percentual)
    .filter((value): value is number => value !== null && value !== undefined);

  const weighted_efficiency_pct =
    efficiencyValues.length === 0
      ? null
      : efficiencyValues.reduce((acc, value) => acc + value, 0) / efficiencyValues.length;

  const total_mod_result = indicatorItems.reduce(
    (acc, item) => acc + (item.resultado_mod ?? 0),
    0
  );

  const total_hours_gained_lost = indicatorItems.reduce(
    (acc, item) => acc + (item.tempo_ganho_perdido_horas ?? 0),
    0
  );

  const table_appointment_count = visibleItems.length;
  const verify_appointment_count = visibleItems.filter((item) =>
    isProductionEfficiencyOutlier(item.eficiencia_percentual)
  ).length;

  const efficiencyByDayMap = new Map<string, { sum: number; count: number }>();
  const appointmentsByDayMap = new Map<string, number>();
  const modByDayMap = new Map<string, { profit: number; loss: number; net: number }>();

  const operatorMap = new Map<
    string,
    {
      operator_name: string | null;
      operator_code: string | null;
      operator_login: string | null;
      sumEfficiency: number;
      countEfficiency: number;
      appointment_count: number;
      mod_result: number;
    }
  >();

  const workCenterMap = new Map<
    string,
    {
      work_center: string | null;
      real: number;
      planned: number;
      appointment_count: number;
      sumEfficiency: number;
      countEfficiency: number;
      mod_result: number;
    }
  >();

  for (const item of indicatorItems) {
    const date = item.data_producao ?? "";

    const eff = item.eficiencia_percentual;
    if (eff !== null && eff !== undefined) {
      const current = efficiencyByDayMap.get(date) ?? { sum: 0, count: 0 };
      current.sum += eff;
      current.count += 1;
      efficiencyByDayMap.set(date, current);
    }
    appointmentsByDayMap.set(date, (appointmentsByDayMap.get(date) ?? 0) + 1);

    const net = item.resultado_mod ?? 0;
    const profit = net > 0 ? net : 0;
    const loss = net < 0 ? net : 0;
    const modCurrent = modByDayMap.get(date) ?? { profit: 0, loss: 0, net: 0 };
    modCurrent.profit += profit;
    modCurrent.loss += loss;
    modCurrent.net += net;
    modByDayMap.set(date, modCurrent);

    const operatorKey =
      item.nome_operador ?? item.login_operador ?? item.cod_operador ?? "—";
    const opCurrent = operatorMap.get(operatorKey) ?? {
      operator_name: item.nome_operador,
      operator_code: item.cod_operador,
      operator_login: item.login_operador,
      sumEfficiency: 0,
      countEfficiency: 0,
      appointment_count: 0,
      mod_result: 0,
    };
    if (eff !== null && eff !== undefined) {
      opCurrent.sumEfficiency += eff;
      opCurrent.countEfficiency += 1;
    }
    opCurrent.appointment_count += 1;
    opCurrent.mod_result += net;
    operatorMap.set(operatorKey, opCurrent);

    const wcKey = item.centro_trabalho ?? "—";
    const wcCurrent = workCenterMap.get(wcKey) ?? {
      work_center: item.centro_trabalho,
      real: 0,
      planned: 0,
      appointment_count: 0,
      sumEfficiency: 0,
      countEfficiency: 0,
      mod_result: 0,
    };
    if (eff !== null && eff !== undefined) {
      wcCurrent.sumEfficiency += eff;
      wcCurrent.countEfficiency += 1;
    }
    wcCurrent.real += item.tempo_real_horas ?? 0;
    wcCurrent.planned += item.tempo_previsto_horas ?? 0;
    wcCurrent.appointment_count += 1;
    wcCurrent.mod_result += net;
    workCenterMap.set(wcKey, wcCurrent);
  }

  const efficiency_by_day = [...appointmentsByDayMap.entries()]
    .map(([date, appointment_count]) => {
      const eff = efficiencyByDayMap.get(date);
      return {
        date,
        efficiency_pct: eff && eff.count > 0 ? eff.sum / eff.count : null,
        appointment_count,
      };
    })
    .sort((a, b) => String(a.date).localeCompare(String(b.date)));

  const mod_result_by_day = [...modByDayMap.entries()]
    .map(([date, row]) => ({
      date,
      profit: row.profit,
      loss: row.loss,
      net_result: row.net,
    }))
    .sort((a, b) => String(a.date).localeCompare(String(b.date)));

  const efficiency_by_operator = [...operatorMap.values()].map((row) => ({
    operator_name: row.operator_name,
    operator_code: row.operator_code,
    operator_login: row.operator_login,
    efficiency_pct: row.countEfficiency > 0 ? row.sumEfficiency / row.countEfficiency : null,
    appointment_count: row.appointment_count,
    mod_result: row.mod_result,
  }));

  const efficiency_by_work_center = [...workCenterMap.values()]
    .map((row) => ({
      work_center: row.work_center,
      efficiency_pct:
        row.countEfficiency > 0 ? row.sumEfficiency / row.countEfficiency : null,
      appointment_count: row.appointment_count,
    }))
    .sort((a, b) =>
      String(a.work_center ?? "").localeCompare(String(b.work_center ?? ""), "pt-BR")
    );

  const mod_result_by_work_center = [...workCenterMap.values()]
    .map((row) => ({
      work_center: row.work_center,
      mod_result: row.mod_result,
      appointment_count: row.appointment_count,
    }))
    .sort((a, b) =>
      String(a.work_center ?? "").localeCompare(String(b.work_center ?? ""), "pt-BR")
    );

  const hours_by_work_center = [...workCenterMap.values()].map((row) => ({
    work_center: row.work_center,
    real_hours: row.real,
    planned_hours: row.planned,
    appointment_count: row.appointment_count,
  }));

  const total = visibleItems.length;
  const totalPages = Math.max(Math.ceil(total / pageSize), 1);
  const safePage = Math.min(Math.max(page, 1), totalPages);
  const offset = (safePage - 1) * pageSize;
  const pageItems = visibleItems.slice(offset, offset + pageSize);

  return {
    summary: {
      weighted_efficiency_pct,
      total_mod_result,
      total_mod_profit: null,
      total_mod_loss: null,
      total_hours_gained_lost,
      table_appointment_count,
      verify_appointment_count,
    },
    charts: {
      efficiency_by_day,
      mod_result_by_day,
      efficiency_by_operator,
      efficiency_by_work_center,
      mod_result_by_work_center,
      hours_by_work_center,
    },
    items: pageItems,
    pagination: {
      page: safePage,
      page_size: pageSize,
      total,
      total_pages: totalPages,
    },
  };
}

export function useEficienciaFabrilDashboard(params: EficienciaFabrilFilterParams) {
  const [allItems, setAllItems] = useState<EficienciaFabrilItem[]>([]);
  const [loadedRange, setLoadedRange] = useState<LoadedRange | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  const isRangeLoaded = useMemo(() => {
    if (!loadedRange) return false;
    return (
      loadedRange.dateStart <= params.date_start &&
      loadedRange.dateEnd >= params.date_end &&
      loadedRange.branch === (params.branch ?? "")
    );
  }, [loadedRange, params.branch, params.date_end, params.date_start]);

  useEffect(() => {
    if (isRangeLoaded && reloadKey === 0) return;

    const controller = new AbortController();

    async function run() {
      setLoading(true);
      setError(null);

      try {
        const items = await fetchAllEficienciaFabrilItems(
          {
            date_start: params.date_start,
            date_end: params.date_end,
            branch: params.branch,
            status_ok_only: false,
          },
          controller.signal
        );
        if (controller.signal.aborted) return;
        setAllItems(items);
        setLoadedRange({
          dateStart: params.date_start,
          dateEnd: params.date_end,
          branch: params.branch ?? "",
        });
      } catch (err) {
        if (controller.signal.aborted) return;
        const message =
          err instanceof Error ? err.message : "Erro ao carregar dashboard";
        setError(message);
        setAllItems([]);
        setLoadedRange(null);
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    void run();

    return () => controller.abort();
  }, [isRangeLoaded, reloadKey, params.branch, params.date_end, params.date_start]);

  const reload = useCallback(() => {
    setReloadKey((prev) => prev + 1);
  }, []);

  const derived = useMemo(() => {
    if (!loadedRange || allItems.length === 0) return null;

    const page = params.page ?? 1;
    const pageSize = params.page_size ?? FALLBACK_PAGE_SIZE;

    const scopedItems = applyScopeFilters(allItems, params);
    const visibleItems =
      params.status_ok_only === true
        ? scopedItems.filter((item) => item.status_registro === "OK")
        : scopedItems;

    const sortedVisibleItems = sortAppointments(
      visibleItems,
      params.sort_by ?? DEFAULT_APPOINTMENTS_SORT.sortBy,
      params.sort_dir ?? DEFAULT_APPOINTMENTS_SORT.sortDir
    );

    return {
      data: computeDashboardFromItems(scopedItems, sortedVisibleItems, page, pageSize),
      exportItems: sortedVisibleItems,
    };
  }, [allItems, loadedRange, params]);

  const data = derived?.data ?? null;

  return {
    data,
    allItems: derived?.exportItems ?? [],
    loadedItems: allItems,
    loading,
    error,
    reload,
  };
}
