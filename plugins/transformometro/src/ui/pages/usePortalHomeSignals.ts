import { useEffect, useMemo, useState } from "react";

import {
  fetchDashboardAlertas,
  fetchDashboardResumo,
  fetchDashboardVencimentos,
  fetchOptions,
  type DashboardAlertItem,
  type DashboardResumo,
  type DashboardVencimentos,
  type FilialOption,
} from "../../data/api/transformometroApi";
import { currentMonthFilterRange } from "../../utils/dashboardFilters";
import {
  buildDashboardKpiContextLabel,
  formatDashboardPeriodLabel,
} from "../../utils/dashboardKpiContext";
import {
  buildDashboardQueryParams,
  defaultDashboardFilialFilter,
} from "../../utils/dashboardViewScope";
import { buildPortalHomeEvents, buildPortalHomeHighlights } from "./portalHomeSignals";

type HomeSignalScope = {
  filialIds: string[];
  filiais: FilialOption[];
  dataInicial: string;
  dataFinal: string;
};

export function usePortalHomeSignals(getAccessToken?: () => string | undefined) {
  const [loading, setLoading] = useState(true);
  const [resumo, setResumo] = useState<DashboardResumo | null>(null);
  const [vencimentos, setVencimentos] = useState<DashboardVencimentos | null>(null);
  const [alertas, setAlertas] = useState<DashboardAlertItem[]>([]);
  const [scope, setScope] = useState<HomeSignalScope | null>(null);

  useEffect(() => {
    let cancelled = false;
    const range = currentMonthFilterRange();
    setLoading(true);
    void fetchOptions(getAccessToken)
      .then((options) => {
        const defaultFilial = defaultDashboardFilialFilter(options.access_scope);
        const filialIds = defaultFilial ? [defaultFilial] : [];
        if (!cancelled) {
          setScope({
            filialIds,
            filiais: options.filiais ?? [],
            dataInicial: range.dataInicial,
            dataFinal: range.dataFinal,
          });
        }
        return buildDashboardQueryParams(
          {
            dataInicial: range.dataInicial,
            dataFinal: range.dataFinal,
            filialIds,
            setorIds: [],
          },
          options.access_scope,
        );
      })
      .catch(() => {
        if (!cancelled) {
          setScope({
            filialIds: [],
            filiais: [],
            dataInicial: range.dataInicial,
            dataFinal: range.dataFinal,
          });
        }
        return buildDashboardQueryParams({
          dataInicial: range.dataInicial,
          dataFinal: range.dataFinal,
          filialIds: [],
          setorIds: [],
        });
      })
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

  const contextLabel = useMemo(() => {
    if (!scope) return null;
    return buildDashboardKpiContextLabel({
      viewMode: scope.filialIds.length > 0 ? "filial" : "consolidated",
      filialIds: scope.filialIds,
      periodLabel: formatDashboardPeriodLabel(scope.dataInicial, scope.dataFinal),
      filiais: scope.filiais,
    });
  }, [scope]);

  const highlights = useMemo(
    () => buildPortalHomeHighlights({ loading, resumo, contextLabel }),
    [contextLabel, loading, resumo],
  );
  const events = useMemo(
    () => buildPortalHomeEvents({ vencimentos, alertas }),
    [alertas, vencimentos],
  );

  return { loading, highlights, events };
}
