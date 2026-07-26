import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import type { AuditListItem } from "../api/audit5sApi";
import { fetchMeProfile } from "../api/meApi";
import type { NcBoardFilterParams } from "../types/ncManagement";
import { computeAuditDateRange } from "../utils/auditDashboardDefaults";
import { formatPersonName } from "../utils/formatPersonName";

const PAGE_SIZE = 20;

export type NcBoardFilterState = {
  dateStart: string;
  dateEnd: string;
  areaId: string;
  /** Status canônico (`open`…) ou `pending` (abertas: open + in_progress). */
  status: string;
  responsible: string;
  responsibleUserId: string;
  overdueOnly: boolean;
};

export type NcBoardScope = "my-pending" | null;

function createDefaultFilters(audits: AuditListItem[]): NcBoardFilterState {
  const { dateStart, dateEnd } = computeAuditDateRange(audits);
  return {
    dateStart,
    dateEnd,
    areaId: "",
    status: "",
    responsible: "",
    responsibleUserId: "",
    overdueOnly: false,
  };
}

function createMyPendingFilters(
  responsibleName: string,
  responsibleUserId: string,
): NcBoardFilterState {
  return {
    dateStart: "",
    dateEnd: "",
    areaId: "",
    status: "pending",
    responsible: responsibleName,
    responsibleUserId,
    overdueOnly: false,
  };
}

function toApiParams(
  branch: string,
  filters: NcBoardFilterState,
  page: number,
): NcBoardFilterParams {
  const responsible = filters.responsible.trim();
  const responsibleUserId = filters.responsibleUserId.trim();
  const dateStart = filters.dateStart.trim();
  const dateEnd = filters.dateEnd.trim();
  const pendingOnly = filters.status === "pending";
  const status =
    filters.status && filters.status !== "pending" ? filters.status : undefined;

  return {
    branch,
    start_date: dateStart || undefined,
    end_date: dateEnd || undefined,
    area_id: filters.areaId || undefined,
    status,
    pending_only: pendingOnly || undefined,
    responsible: !responsibleUserId && responsible ? responsible : undefined,
    responsible_user_id: responsibleUserId || undefined,
    overdue_only: filters.overdueOnly || undefined,
    sort: "due_date_asc",
    page,
    page_size: PAGE_SIZE,
  };
}

export function useAudit5sNcBoardFilters(
  branch: string,
  audits: AuditListItem[],
  scope: NcBoardScope = null,
) {
  const [filters, setFilters] = useState<NcBoardFilterState>(() =>
    scope === "my-pending"
      ? createMyPendingFilters("", "")
      : createDefaultFilters(audits),
  );
  const [page, setPage] = useState(1);
  const datesTouchedRef = useRef(false);
  const myPendingAppliedRef = useRef(false);

  useEffect(() => {
    if (scope === "my-pending") return;
    if (datesTouchedRef.current || audits.length === 0) return;
    const range = computeAuditDateRange(audits);
    setFilters((current) => {
      if (
        current.dateStart === range.dateStart &&
        current.dateEnd === range.dateEnd
      ) {
        return current;
      }
      return { ...current, dateStart: range.dateStart, dateEnd: range.dateEnd };
    });
  }, [audits, scope]);

  useEffect(() => {
    if (scope !== "my-pending" || myPendingAppliedRef.current) return;
    let cancelled = false;
    void fetchMeProfile()
      .then((profile) => {
        if (cancelled) return;
        const name =
          formatPersonName(profile.name.trim() || profile.email) ||
          profile.name.trim() ||
          profile.email;
        myPendingAppliedRef.current = true;
        setFilters(createMyPendingFilters(name, profile.id));
        setPage(1);
      })
      .catch(() => {
        if (cancelled) return;
        myPendingAppliedRef.current = true;
        setFilters(createMyPendingFilters("", ""));
      });
    return () => {
      cancelled = true;
    };
  }, [scope]);

  const apiParams = useMemo(
    () => toApiParams(branch, filters, page),
    [branch, filters, page],
  );

  const patchFilters = useCallback((patch: Partial<NcBoardFilterState>) => {
    if ("dateStart" in patch || "dateEnd" in patch) {
      datesTouchedRef.current = true;
    }
    if ("responsible" in patch && !("responsibleUserId" in patch)) {
      patch = { ...patch, responsibleUserId: "" };
    }
    setFilters((current) => ({ ...current, ...patch }));
    setPage(1);
  }, []);

  return {
    filters,
    apiParams,
    page,
    setPage,
    setDateStart: (value: string) => patchFilters({ dateStart: value }),
    setDateEnd: (value: string) => patchFilters({ dateEnd: value }),
    setAreaId: (value: string) => patchFilters({ areaId: value }),
    setStatus: (value: string) => patchFilters({ status: value }),
    setResponsible: (value: string) =>
      patchFilters({ responsible: value, responsibleUserId: "" }),
    setOverdueOnly: (value: boolean) => patchFilters({ overdueOnly: value }),
    clearDates: () => patchFilters({ dateStart: "", dateEnd: "" }),
  };
}
