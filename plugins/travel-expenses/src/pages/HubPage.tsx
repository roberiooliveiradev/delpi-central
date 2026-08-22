import { useEffect, useMemo, useState } from "react";
import { ActionButton, DataTable, KpiCard, type DataTableColumn } from "@delpi/plugin-ui/index";
import { Building2, FilePlus2, Plane, Receipt, Wallet } from "lucide-react";

import {
  listReports,
  type ReportListItem,
  type TravelAccess,
} from "../api/travelExpensesApi";
import { formatBrl, formatDate, STATUS_LABELS, UNIT_LABELS } from "../constants/labels";
import { helpTooltips } from "../content/helpTooltips";
import { useTravelUserDisplayName } from "../hooks/useTravelUserDisplayName";
import { navigateTravel } from "../hooks/useTravelRouterPath";
import { writableUnits } from "../security/travelAccess";
import { isSameMonth } from "../utils/dates";
import {
  TravelLoadingState,
  TravelNavigationCard,
  TravelPageHeader,
  TravelPageNotices,
  TravelSectionCard,
  travelKpiClassNames,
  travelKpiLabels,
} from "../ui/travelUi";
import { travelDataTableClassNames, travelDataTableLabels } from "../ui/travelUiContracts";

export function HubPage({ access }: { access: TravelAccess }) {
  const displayName = useTravelUserDisplayName();
  const [items, setItems] = useState<ReportListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const units = writableUnits(access);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    listReports({ scope: "mine" })
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
  }, []);

  const kpis = useMemo(() => {
    const drafts = items.filter((item) => item.status === "draft").length;
    const total = items.reduce((sum, item) => sum + Number(item.totalAmountBrl || 0), 0);
    const missing = items.reduce((sum, item) => sum + Number(item.missingReceiptCount || 0), 0);
    const thisMonth = items.filter((item) => isSameMonth(item.updatedAt || item.periodStart)).length;
    return { drafts, total, missing, thisMonth };
  }, [items]);

  function onCreate() {
    if (!units.length) {
      setError("Você não tem permissão para criar prestações nesta unidade.");
      return;
    }
    navigateTravel("/apps/travel-expenses/reports/new");
  }

  const columns: DataTableColumn<ReportListItem>[] = [
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
  ];

  return (
    <div className="te-page-stack">
      <TravelPageHeader
        title={`Olá, ${displayName}`}
        subtitle={`Despesas de Viagem — ${helpTooltips.hub}`}
        actions={
          access.canWrite ? (
            <ActionButton variant="primary" onClick={onCreate}>
              <FilePlus2 size={16} /> Nova prestação
            </ActionButton>
          ) : null
        }
      />
      <TravelPageNotices error={error} onDismissError={() => setError(null)} />
      <div className="te-kpi-row">
        <KpiCard
          title="Este mês"
          value={String(kpis.thisMonth)}
          icon={<Plane size={22} />}
          classNames={travelKpiClassNames}
          labels={travelKpiLabels}
        />
        <KpiCard
          title="Rascunhos"
          value={String(kpis.drafts)}
          icon={<Receipt size={22} />}
          classNames={travelKpiClassNames}
          labels={travelKpiLabels}
        />
        <KpiCard
          title="Total lançado"
          value={formatBrl(kpis.total)}
          icon={<Wallet size={22} />}
          classNames={travelKpiClassNames}
          labels={travelKpiLabels}
        />
        <KpiCard
          title="Sem cupom"
          value={String(kpis.missing)}
          icon={<Receipt size={22} />}
          classNames={travelKpiClassNames}
          labels={travelKpiLabels}
        />
      </div>
      <div className="te-hub-split">
        <TravelSectionCard title="Atalhos">
          <div className="te-shortcut-stack">
            <TravelNavigationCard
              title="Minhas prestações"
              description="Rascunhos e relatórios que você criou."
              icon={<Receipt size={20} />}
              onClick={() => navigateTravel("/apps/travel-expenses/reports")}
            />
            {access.canManage ? (
              <TravelNavigationCard
                title="Prestações da unidade"
                description={helpTooltips.unitScope}
                icon={<Building2 size={20} />}
                onClick={() => navigateTravel("/apps/travel-expenses/reports?scope=unit")}
              />
            ) : null}
          </div>
        </TravelSectionCard>
      <TravelSectionCard title="Recentes" hint={helpTooltips.hub}>
        {loading ? (
          <TravelLoadingState />
        ) : (
          <DataTable
            rows={items.slice(0, 8)}
            columns={columns}
            rowKey={(row) => row.id}
            onRowClick={(row) => navigateTravel(`/apps/travel-expenses/reports/${row.id}`)}
            classNames={travelDataTableClassNames}
            labels={travelDataTableLabels}
          />
        )}
      </TravelSectionCard>
      </div>
    </div>
  );
}
