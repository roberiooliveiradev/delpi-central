import { useMemo, useState } from "react";
import { suggestYearBeforeLatest } from "../utils/goalYearHelpers";
import { InfoState } from "./InfoState";
import { DataTable, type DataTableColumn } from "./DataTable";
import { ActionButtons } from "./ActionButtons";
import { GoalYearManagementModal } from "./GoalYearManagementModal";
import { AnnualGoalsWorkspace } from "./AnnualGoalsWorkspace";
import { useStrategicIndicatorsGoalYearsOverview } from "../../state/hooks/useStrategicIndicatorsGoalYearsOverview";
import type { GoalYearOverviewItem } from "../../data/types/indicatorGoals";
import "./GoalYearsListPanel.css";

type GoalYearsListPanelProps = {
  getAccessToken?: () => string | undefined;
};

export function GoalYearsListPanel({
  getAccessToken,
}: GoalYearsListPanelProps) {
  const yearsOverview = useStrategicIndicatorsGoalYearsOverview({ getAccessToken });

  const [openedYear, setOpenedYear] = useState<GoalYearOverviewItem | null>(null);
  const [createYearOpen, setCreateYearOpen] = useState(false);
  const [duplicateYears, setDuplicateYears] = useState<{
    source: number;
    target: number;
  } | null>(null);

  const catalogYears = useMemo(
    () => yearsOverview.items.map((item) => item.goal_year),
    [yearsOverview.items],
  );
  const [fillMissingToYearOpen, setFillMissingToYearOpen] = useState<number | null>(null);

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
      key: "actions",
      header: "Ações",
      render: (row) => (
        <ActionButtons
          onOpen={() => setOpenedYear(row)}
          onDuplicate={() => {
            const target =
              suggestYearBeforeLatest(catalogYears) ?? row.goal_year - 1;
            setDuplicateYears({ source: row.goal_year, target });
          }}
          onFillMissing={() => setFillMissingToYearOpen(row.goal_year)}
        />
      ),
    },
  ];

  return (
    <>
      <div className="si-admin-list-shell">
        <div className="si-admin-list-toolbar">
          <div />
          <div className="si-admin-list-toolbar__actions">
            <button
              type="button"
              className="si-settings-editor__button"
              onClick={() => setCreateYearOpen(true)}
            >
              Novo ano
            </button>
          </div>
        </div>

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
      </div>

      <GoalYearManagementModal
        open={!!openedYear}
        goalYear={openedYear?.goal_year ?? null}
        onClose={() => setOpenedYear(null)}
        getAccessToken={getAccessToken}
      />

      <AnnualGoalsWorkspace
        open={createYearOpen}
        mode="create_year"
        fixedTargetYear={null}
        existingYears={catalogYears}
        onClose={() => {
          setCreateYearOpen(false);
          void yearsOverview.reload();
        }}
        getAccessToken={getAccessToken}
      />

      <AnnualGoalsWorkspace
        open={!!duplicateYears}
        mode="duplicate_into_year"
        fixedTargetYear={duplicateYears?.target ?? null}
        initialSourceYear={duplicateYears?.source ?? null}
        existingYears={catalogYears}
        onClose={() => {
          setDuplicateYears(null);
          void yearsOverview.reload();
        }}
        getAccessToken={getAccessToken}
      />

      <AnnualGoalsWorkspace
        open={typeof fillMissingToYearOpen === "number"}
        mode="fill_missing_for_year"
        fixedTargetYear={fillMissingToYearOpen}
        onClose={() => {
          setFillMissingToYearOpen(null);
          void yearsOverview.reload();
        }}
        getAccessToken={getAccessToken}
      />
    </>
  );
}