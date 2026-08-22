import { useEffect, useMemo, useState } from "react";
import { ActionButton, BackLink, DataTable, type DataTableColumn } from "@delpi/plugin-ui/index";
import { FilePlus2 } from "lucide-react";

import {
  createReport,
  deleteReport,
  listReports,
  type ReportListItem,
  type TravelAccess,
} from "../api/travelExpensesApi";
import { formatBrl, formatDate, STATUS_LABELS, UNIT_LABELS } from "../constants/labels";
import { helpTooltips } from "../content/helpTooltips";
import {
  navigateTravel,
  readListSearch,
  replaceTravel,
} from "../hooks/useTravelRouterPath";
import { writableUnits } from "../security/travelAccess";
import {
  TravelFilterInputField,
  TravelFilterSelectField,
  TravelFiltersRow,
  TravelPageHeader,
  TravelPageNotices,
  TravelSectionCard,
} from "../ui/travelUi";
import { travelDataTableClassNames, travelDataTableLabels } from "../ui/travelUiContracts";

export function ListPage({ access, search }: { access: TravelAccess; search: string }) {
  const filters = readListSearch(search);
  const [items, setItems] = useState<ReportListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState(filters.q);
  const [unit, setUnit] = useState(filters.unit);
  const [periodFrom, setPeriodFrom] = useState(filters.periodFrom);
  const [periodTo, setPeriodTo] = useState(filters.periodTo);

  useEffect(() => {
    setQ(filters.q);
    setUnit(filters.unit);
    setPeriodFrom(filters.periodFrom);
    setPeriodTo(filters.periodTo);
  }, [filters.q, filters.unit, filters.periodFrom, filters.periodTo]);

  useEffect(() => {
    const next = new URLSearchParams();
    if (filters.scope === "unit") next.set("scope", "unit");
    if (q) next.set("q", q);
    if (unit) next.set("unit", unit);
    if (periodFrom) next.set("from", periodFrom);
    if (periodTo) next.set("to", periodTo);
    const suffix = next.toString() ? `?${next}` : "";
    const target = `/apps/travel-expenses/reports${suffix}`;
    if (`${window.location.pathname}${window.location.search}` !== target) {
      replaceTravel(target);
    }
  }, [filters.scope, q, unit, periodFrom, periodTo]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    listReports({
      scope: filters.scope,
      unit: unit || undefined,
      q: q || undefined,
      periodFrom: periodFrom || undefined,
      periodTo: periodTo || undefined,
    })
      .then((rows) => {
        if (!cancelled) setItems(rows);
      })
      .catch((err: Error) => {
        if (!cancelled) setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [filters.scope, q, unit, periodFrom, periodTo]);

  const columns: DataTableColumn<ReportListItem>[] = useMemo(
    () => [
      { key: "number", header: "Número", render: (row) => row.number },
      { key: "destination", header: "Destino", render: (row) => row.destination || "—" },
      { key: "unit", header: "Filial", render: (row) => UNIT_LABELS[row.unitCode] || row.unitCode },
      {
        key: "period",
        header: "Período",
        render: (row) => `${formatDate(row.periodStart)} – ${formatDate(row.periodEnd)}`,
      },
      { key: "status", header: "Status", render: (row) => STATUS_LABELS[row.status] || row.status },
      { key: "total", header: "Total", render: (row) => formatBrl(row.totalAmountBrl), align: "right" },
      {
        key: "actions",
        header: "Ações",
        interactive: true,
        render: (row) =>
          row.status === "draft" && access.canWrite ? (
            <ActionButton
              variant="ghost"
              onClick={() => {
                if (!window.confirm(`Excluir ${row.number}?`)) return;
                deleteReport(row.id)
                  .then(() => setItems((current) => current.filter((item) => item.id !== row.id)))
                  .catch((err: Error) => setError(err.message));
              }}
            >
              Excluir
            </ActionButton>
          ) : null,
      },
    ],
    [access.canWrite],
  );

  async function onCreate() {
    const chosen = unit || writableUnits(access)[0]?.id;
    if (!chosen) {
      setError("Você não tem permissão para criar prestações.");
      return;
    }
    try {
      const created = await createReport({ unitCode: chosen });
      navigateTravel(`/apps/travel-expenses/reports/${created.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível criar a prestação.");
    }
  }

  return (
    <div className="te-page-stack">
      <TravelPageHeader
        title={filters.scope === "unit" ? "Prestações da unidade" : "Minhas prestações"}
        subtitle={helpTooltips.unitScope}
        nav={<BackLink onClick={() => navigateTravel("/apps/travel-expenses")}>Início</BackLink>}
        actions={
          access.canWrite ? (
            <ActionButton variant="primary" onClick={onCreate}>
              <FilePlus2 size={16} /> Nova prestação
            </ActionButton>
          ) : null
        }
      />
      <TravelPageNotices error={error} onDismissError={() => setError(null)} />
      <TravelSectionCard title="Filtros">
        <TravelFiltersRow>
          <TravelFilterInputField
            label="Busca"
            type="search"
            value={q}
            onChange={setQ}
            placeholder="Número ou destino"
          />
          <TravelFilterSelectField
            label="Filial"
            value={unit}
            onChange={setUnit}
            options={[
              { value: "", label: "Todas" },
              ...access.units.map((item) => ({ value: item.id, label: item.label })),
            ]}
          />
          <TravelFilterInputField label="De" type="date" value={periodFrom} onChange={setPeriodFrom} />
          <TravelFilterInputField label="Até" type="date" value={periodTo} onChange={setPeriodTo} />
        </TravelFiltersRow>
      </TravelSectionCard>
      <TravelSectionCard title="Prestações">
        <DataTable
          rows={items}
          columns={columns}
          rowKey={(row) => row.id}
          loading={loading}
          onRowClick={(row) => navigateTravel(`/apps/travel-expenses/reports/${row.id}`)}
          classNames={travelDataTableClassNames}
          labels={travelDataTableLabels}
        />
      </TravelSectionCard>
    </div>
  );
}
