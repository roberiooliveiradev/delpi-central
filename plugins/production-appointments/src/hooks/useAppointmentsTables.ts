import { useCallback, useEffect, useState } from "react";

import { fetchAppointmentsByOp, fetchAppointmentsList } from "../api/appointmentsApi";
import type {
  AppointmentsByOpData,
  AppointmentsListData,
  AppointmentsQueryFilters,
} from "../types/appointments";

const PAGE_SIZE = 50;

export function useAppointmentsTables(
  appliedFilters: AppointmentsQueryFilters | null,
  listPage: number,
  byOpPage: number,
) {
  const [list, setList] = useState<AppointmentsListData | null>(null);
  const [byOp, setByOp] = useState<AppointmentsByOpData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  const reload = useCallback(() => setReloadKey((n) => n + 1), []);

  useEffect(() => {
    if (!appliedFilters?.branch || !appliedFilters.dateStart || !appliedFilters.dateEnd) {
      setList(null);
      setByOp(null);
      return;
    }

    const controller = new AbortController();
    const filters = appliedFilters;

    async function run() {
      try {
        setLoading(true);
        setError(null);
        const [listData, byOpData] = await Promise.all([
          fetchAppointmentsList(filters, listPage, PAGE_SIZE, {
            signal: controller.signal,
          }),
          fetchAppointmentsByOp(filters, byOpPage, PAGE_SIZE, {
            signal: controller.signal,
          }),
        ]);
        setList(listData);
        setByOp(byOpData);
      } catch (err) {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : "Falha ao carregar tabelas.");
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }

    void run();
    return () => controller.abort();
  }, [appliedFilters, listPage, byOpPage, reloadKey]);

  return { list, byOp, loading, error, reload, pageSize: PAGE_SIZE };
}
