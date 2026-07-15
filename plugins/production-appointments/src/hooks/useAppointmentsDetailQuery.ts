import { useEffect, useMemo, useState } from "react";

import {
  fetchAllAppointments,
  fetchAppointmentsByOp,
  fetchAppointmentsSeries,
  fetchAppointmentsSummary,
  fetchWorkCenters,
} from "../api/appointmentsApi";
import { replaceDetailPeriodInUrl, readDetailPeriodFromUrl } from "../constants/routes";
import type {
  AppointmentRow,
  AppointmentsQueryFilters,
  AppointmentTotals,
  ByOpRow,
  FilterFormState,
  SeriesPoint,
  WorkCenterItem,
  WorkCenterSummaryRow,
} from "../types/appointments";
import {
  createDefaultFilterFormState,
  filtersFromFormState,
  resolveQuickRangePreset,
  type QuickRangePreset,
  validatePeriodRange,
} from "../utils/dateRange";
import { useDebouncedValue } from "./useDebouncedValue";

export type DetailLockedFilters = {
  workCenter?: string;
  op?: string;
};

type UseAppointmentsDetailQueryOptions = {
  totvsBranch: string;
  locked: DetailLockedFilters;
};

export function useAppointmentsDetailQuery({
  totvsBranch,
  locked,
}: UseAppointmentsDetailQueryOptions) {
  const defaults = useMemo(() => createDefaultFilterFormState(), []);
  const urlPeriod = useMemo(() => readDetailPeriodFromUrl(), []);

  const [draftFilters, setDraftFilters] = useState<FilterFormState>(() => ({
    ...defaults,
    ...(urlPeriod ?? {}),
    workCenter: locked.workCenter ?? "",
    op: locked.op ?? "",
    product: "",
  }));
  const [validationError, setValidationError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [appointments, setAppointments] = useState<AppointmentRow[]>([]);
  const [byOpRows, setByOpRows] = useState<ByOpRow[]>([]);
  const [totals, setTotals] = useState<AppointmentTotals | null>(null);
  const [summaryItems, setSummaryItems] = useState<WorkCenterSummaryRow[]>([]);
  const [seriesPoints, setSeriesPoints] = useState<SeriesPoint[]>([]);
  const [workCenters, setWorkCenters] = useState<WorkCenterItem[]>([]);

  const debouncedOp = useDebouncedValue(draftFilters.op, 350);
  const debouncedProduct = useDebouncedValue(draftFilters.product, 350);

  const autoFilters = useMemo(
    () => ({
      ...draftFilters,
      workCenter: locked.workCenter ?? draftFilters.workCenter,
      op: locked.op ?? debouncedOp,
      product: debouncedProduct,
    }),
    [draftFilters, locked.workCenter, locked.op, debouncedOp, debouncedProduct],
  );

  const appliedFilters = useMemo<AppointmentsQueryFilters | null>(() => {
    const periodError = validatePeriodRange(autoFilters.dateStart, autoFilters.dateEnd);
    if (periodError) return null;
    return filtersFromFormState(totvsBranch, autoFilters);
  }, [autoFilters, totvsBranch]);

  useEffect(() => {
    setValidationError(validatePeriodRange(draftFilters.dateStart, draftFilters.dateEnd));
  }, [draftFilters.dateStart, draftFilters.dateEnd]);

  useEffect(() => {
    if (validationError) return;
    replaceDetailPeriodInUrl(draftFilters.dateStart, draftFilters.dateEnd);
  }, [draftFilters.dateStart, draftFilters.dateEnd, validationError]);

  useEffect(() => {
    if (!appliedFilters) {
      setLoading(false);
      return;
    }

    const controller = new AbortController();
    async function run() {
      try {
        setLoading(true);
        setError(null);
        const [items, byOp, summary, series, centers] = await Promise.all([
          fetchAllAppointments(appliedFilters, { signal: controller.signal }),
          fetchAppointmentsByOp(appliedFilters, 1, 200, { signal: controller.signal }),
          fetchAppointmentsSummary(appliedFilters, { signal: controller.signal }),
          fetchAppointmentsSeries(appliedFilters, "day", { signal: controller.signal }),
          fetchWorkCenters(appliedFilters.branch, { signal: controller.signal }),
        ]);
        setAppointments(items);
        setByOpRows(byOp.items);
        setTotals(summary.totals);
        setSummaryItems(summary.items);
        setSeriesPoints(series.points ?? []);
        setWorkCenters(centers.items ?? []);
      } catch (err) {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : "Falha ao carregar o detalhe.");
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }
    void run();
    return () => controller.abort();
  }, [appliedFilters]);

  const handleFiltersChange = (patch: Partial<FilterFormState>) => {
    setDraftFilters((current) => {
      const next = { ...current, ...patch };
      if (locked.workCenter) next.workCenter = locked.workCenter;
      if (locked.op) next.op = locked.op;
      return next;
    });
  };

  const handleQuickRange = (preset: QuickRangePreset) => {
    handleFiltersChange(resolveQuickRangePreset(preset));
  };

  return {
    draftFilters,
    validationError,
    appliedFilters,
    loading,
    error,
    appointments,
    byOpRows,
    totals,
    summaryItems,
    seriesPoints,
    workCenters,
    handleFiltersChange,
    handleQuickRange,
    period: {
      dateStart: draftFilters.dateStart,
      dateEnd: draftFilters.dateEnd,
    },
  };
}
