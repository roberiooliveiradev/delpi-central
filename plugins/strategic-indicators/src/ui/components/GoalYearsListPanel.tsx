import { useState } from "react";
import { InfoState } from "./InfoState";
import { DataTable, type DataTableColumn } from "./DataTable";
import { useStrategicIndicatorsGoalYearsOverview } from "../../state/hooks/useStrategicIndicatorsGoalYearsOverview";
import { GoalYearManagementModal } from "./GoalYearManagementModal";
import type { GoalYearOverviewItem } from "../../data/types/indicatorGoals";

type GoalYearsListPanelProps = {
  getAccessToken?: () => string | undefined;
};

export function GoalYearsListPanel({
  getAccessToken,
}: GoalYearsListPanelProps) {
  const yearsOverview = useStrategicIndicatorsGoalYearsOverview({ getAccessToken });
  const [openedYear, setOpenedYear] = useState<GoalYearOverviewItem | null>(null);

  const columns: DataTableColumn<GoalYearOverviewItem>[] = [
    {
      key: "year",
      header: "Ano",
      render: (row) => <strong>{row.goal_year}</strong>,
    },
    {
      key: "activeIndicators",
      header: "Indicadores ativos",
      render: (row) => row.total_active_indicators,
    },
    {
      key: "activeVersions",
      header: "Versões ativas",
      render: (row) => row.total_active_versions,
    },
    {
      key: "versions",
      header: "Versões totais",
      render: (row) => row.total_versions,
    },
    {
      key: "open",
      header: "Workspace",
      render: (row) => (
        <button
          type="button"
          className="si-settings-editor__button"
          onClick={() => setOpenedYear(row)}
        >
          Abrir
        </button>
      ),
    },
  ];

  return (
    <>
      {yearsOverview.error ? (
        <InfoState
          title="Falha ao carregar ciclos anuais"
          description={yearsOverview.error}
          actionLabel="Recarregar"
          onAction={() => void yearsOverview.reload()}
        />
      ) : null}

      <DataTable
        columns={columns}
        rows={yearsOverview.items}
        loading={yearsOverview.loading}
        emptyText="Nenhum ciclo anual encontrado."
        getRowKey={(row) => String(row.goal_year)}
      />

      <GoalYearManagementModal
        open={!!openedYear}
        goalYear={openedYear?.goal_year ?? null}
        onClose={() => setOpenedYear(null)}
        getAccessToken={getAccessToken}
      />
    </>
  );
}