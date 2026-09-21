import { useEffect, useMemo, useState } from "react";

import {
  fetchDashboardAlertas,
  fetchDashboardResumo,
  fetchDashboardVencimentos,
  fetchOptions,
  type DashboardAlertItem,
  type DashboardResumo,
  type DashboardVencimentos,
} from "../../data/api/transformometroApi";
import { currentMonthFilterRange } from "../../utils/dashboardFilters";
import {
  buildDashboardQueryParams,
  defaultDashboardFilialFilter,
} from "../../utils/dashboardViewScope";
import { buildPortalHomeEvents, buildPortalHomeHighlights } from "./portalHomeSignals";

export function usePortalHomeSignals(getAccessToken?: () => string | undefined) {
  const [loading, setLoading] = useState(true);
  const [resumo, setResumo] = useState<DashboardResumo | null>(null);
  const [vencimentos, setVencimentos] = useState<DashboardVencimentos | null>(null);
  const [alertas, setAlertas] = useState<DashboardAlertItem[]>([]);

  useEffect(() => {
    let cancelled = false;
    const range = currentMonthFilterRange();
    setLoading(true);
    void fetchOptions(getAccessToken)
      .then((options) => {
        const defaultFilial = defaultDashboardFilialFilter(options.access_scope);
        return buildDashboardQueryParams(
          {
            dataInicial: range.dataInicial,
            dataFinal: range.dataFinal,
            filialIds: defaultFilial ? [defaultFilial] : [],
            setorIds: [],
          },
          options.access_scope,
        );
      })
      .catch(() =>
        buildDashboardQueryParams({
          dataInicial: range.dataInicial,
          dataFinal: range.dataFinal,
          filialIds: [],
          setorIds: [],
        }),
      )
      .then((params) =>
        Promise.all([
          fetchDashboardResumo(getAccessToken, params),
          fetchDashboardVencimentos(getAccessToken, params),
          fetchDashboardAlertas(getAccessToken, params),
        ]),
      )
      .then(([nextResumo, nextVencimentos, nextAlertas]) => {
        if (cancelled) return;
        setResumo(nextResumo);
        setVencimentos(nextVencimentos);
        setAlertas(nextAlertas.items ?? []);
      })
      .catch(() => {
        if (cancelled) return;
        setResumo(null);
        setVencimentos(null);
        setAlertas([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [getAccessToken]);

  const highlights = useMemo(
    () => buildPortalHomeHighlights({ loading, resumo }),
    [loading, resumo],
  );
  const events = useMemo(
    () => buildPortalHomeEvents({ vencimentos, alertas }),
    [alertas, vencimentos],
  );

  return { loading, highlights, events };
}
