import { useEffect, useMemo, useState } from "react";
import type {
  BulkCreateStrategicIndicatorGoalsRequest,
  DuplicateStrategicIndicatorGoalsYearRequest,
  FillMissingStrategicIndicatorGoalsRequest,
} from "../../data/types/indicatorGoals";
import { useStrategicIndicatorGoals } from "../../state/hooks/useStrategicIndicatorGoals";
import { useStrategicIndicatorsGoalYearsOverview } from "../../state/hooks/useStrategicIndicatorsGoalYearsOverview";
import { InfoState } from "./InfoState";
import { Modal } from "./Modal";

type AnnualGoalsWorkspaceMode =
  | "create_year"
  | "duplicate_into_year"
  | "fill_missing_for_year";

type AnnualGoalsWorkspaceProps = {
  open: boolean;
  mode: AnnualGoalsWorkspaceMode;
  fixedTargetYear: number | null;
  onClose: () => void;
  getAccessToken?: () => string | undefined;
};

type BulkGoalRow = {
  indicator_id: string;
  goal_label: string;
  goal_value: number;
  goal_periodicity: "monthly" | "annual" | "quarterly" | "weekly";
  goal_mode: "standard" | "monthly_curve";
  monthly_targets: Array<{
    month_number: number;
    target_value: number;
  }>;
};

const emptyBulkRow: BulkGoalRow = {
  indicator_id: "",
  goal_label: "",
  goal_value: 0,
  goal_periodicity: "monthly",
  goal_mode: "standard",
  monthly_targets: [],
};

export function AnnualGoalsWorkspace({
  open,
  mode,
  fixedTargetYear,
  onClose,
  getAccessToken,
}: AnnualGoalsWorkspaceProps) {
  const goals = useStrategicIndicatorGoals({ getAccessToken });
  const yearsOverview = useStrategicIndicatorsGoalYearsOverview({ getAccessToken });

  const [targetYear, setTargetYear] = useState<number>(
    fixedTargetYear ?? new Date().getFullYear(),
  );
  const [bulkRows, setBulkRows] = useState<BulkGoalRow[]>([emptyBulkRow]);
  const [sourceYear, setSourceYear] = useState<number>(new Date().getFullYear() - 1);
  const [overwriteExisting, setOverwriteExisting] = useState(false);
  const [copyFromYear, setCopyFromYear] = useState<number | "">(
    new Date().getFullYear() - 1,
  );

  useEffect(() => {
    if (!open) return;

    if (typeof fixedTargetYear === "number") {
      if (mode === "duplicate_into_year") {
        // Regra correta:
        // ano selecionado = origem
        // ano digitado no modal = destino
        setSourceYear(fixedTargetYear);
        setTargetYear(fixedTargetYear + 1);
      } else {
        setTargetYear(fixedTargetYear);
      }
    } else {
      setTargetYear(new Date().getFullYear());
    }

    if (mode === "fill_missing_for_year") {
      setCopyFromYear(new Date().getFullYear() - 1);
    }

    if (mode === "create_year") {
      setBulkRows([emptyBulkRow]);
    }

    setOverwriteExisting(false);
  }, [open, mode, fixedTargetYear]);

  const resolvedTargetYear = useMemo(
    () =>
      mode === "duplicate_into_year"
        ? targetYear
        : typeof fixedTargetYear === "number"
          ? fixedTargetYear
          : targetYear,
    [mode, fixedTargetYear, targetYear],
  );

  async function handleSubmitCreateYear() {
    const payload: BulkCreateStrategicIndicatorGoalsRequest = {
      goal_year: resolvedTargetYear,
      items: bulkRows
        .filter((item) => item.indicator_id.trim() && item.goal_label.trim())
        .map((item) => ({
          indicator_id: item.indicator_id.trim(),
          goal_label: item.goal_label.trim(),
          goal_value: Number(item.goal_value || 0),
          goal_periodicity: item.goal_periodicity,
          goal_mode: item.goal_mode,
          monthly_targets:
            item.goal_mode === "monthly_curve" ? item.monthly_targets : [],
        })),
    };

    await goals.bulkCreateGoals(payload);
    await yearsOverview.reload();
    onClose();
  }

  async function handleSubmitDuplicateYear() {
    const payload: DuplicateStrategicIndicatorGoalsYearRequest = {
      source_year: sourceYear,
      target_year: resolvedTargetYear,
      overwrite_existing: overwriteExisting,
    };

    await goals.duplicateGoalsYear(payload);
    await yearsOverview.reload();
    onClose();
  }

  async function handleSubmitFillMissing() {
    const payload: FillMissingStrategicIndicatorGoalsRequest = {
      goal_year: resolvedTargetYear,
      copy_from_year: typeof copyFromYear === "number" ? copyFromYear : null,
    };

    await goals.fillMissingGoals(payload);
    await yearsOverview.reload();
    onClose();
  }

  const title =
    mode === "create_year"
      ? "Novo ano"
      : mode === "duplicate_into_year"
        ? `Duplicar metas de ${sourceYear} para outro ano`
        : `Preencher metas faltantes de ${resolvedTargetYear}`;

  const description =
    mode === "create_year"
      ? "Crie um novo ciclo anual e, se quiser, já adicione metas iniciais."
      : mode === "duplicate_into_year"
        ? "Use o ano selecionado como origem e informe o ano de destino."
        : "Complete metas ausentes do ano selecionado usando outro ciclo como referência.";

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={title}
      description={description}
      size="lg"
      footer={
        <>
          <button
            type="button"
            className="si-settings-editor__button si-settings-editor__button--secondary"
            onClick={onClose}
          >
            Cancelar
          </button>

          <button
            type="button"
            className="si-settings-editor__button"
            onClick={() => {
              if (mode === "create_year") {
                void handleSubmitCreateYear();
                return;
              }
              if (mode === "duplicate_into_year") {
                void handleSubmitDuplicateYear();
                return;
              }
              void handleSubmitFillMissing();
            }}
            disabled={goals.saving}
          >
            {goals.saving
              ? "Processando..."
              : mode === "create_year"
                ? "Criar ano"
                : mode === "duplicate_into_year"
                  ? "Duplicar"
                  : "Preencher"}
          </button>
        </>
      }
    >
      {goals.error ? (
        <InfoState
          title="Falha ao processar operação"
          description={goals.error}
          actionLabel="Recarregar"
          onAction={() => void goals.reload()}
        />
      ) : null}

      <div className="si-admin-form-grid">
        {mode === "duplicate_into_year" ? (
          <>
            <label className="si-admin-form-field">
              <span>Ano de origem</span>
              <input type="number" value={sourceYear} readOnly />
            </label>

            <label className="si-admin-form-field">
              <span>Ano de destino</span>
              <input
                type="number"
                value={targetYear}
                onChange={(event) => setTargetYear(Number(event.target.value || 0))}
              />
            </label>
          </>
        ) : (
          <label className="si-admin-form-field">
            <span>Ano de destino</span>
            <input
              type="number"
              value={resolvedTargetYear}
              readOnly={typeof fixedTargetYear === "number"}
              onChange={(event) => setTargetYear(Number(event.target.value || 0))}
            />
          </label>
        )}

        {mode === "fill_missing_for_year" ? (
          <label className="si-admin-form-field">
            <span>Copiar de</span>
            <input
              type="number"
              value={copyFromYear}
              onChange={(event) =>
                setCopyFromYear(Number(event.target.value || 0))
              }
            />
          </label>
        ) : null}

        {mode === "duplicate_into_year" ? (
          <label className="si-admin-form-field si-admin-form-field--full">
            <span>
              <input
                type="checkbox"
                checked={overwriteExisting}
                onChange={(event) => setOverwriteExisting(event.target.checked)}
              />{" "}
              Sobrescrever metas já existentes no ano de destino
            </span>
          </label>
        ) : null}

        {mode === "create_year" ? (
          <div className="si-admin-form-field si-admin-form-field--full">
            <span>Metas iniciais do novo ano</span>

            <div className="si-bulk-goals-form">
              {bulkRows.map((row, index) => (
                <div key={index} className="si-bulk-goals-form__row">
                  <input
                    placeholder="indicator_id"
                    value={row.indicator_id}
                    onChange={(event) =>
                      setBulkRows((current) =>
                        current.map((item, itemIndex) =>
                          itemIndex === index
                            ? { ...item, indicator_id: event.target.value }
                            : item,
                        ),
                      )
                    }
                  />

                  <input
                    placeholder="goal_label"
                    value={row.goal_label}
                    onChange={(event) =>
                      setBulkRows((current) =>
                        current.map((item, itemIndex) =>
                          itemIndex === index
                            ? { ...item, goal_label: event.target.value }
                            : item,
                        ),
                      )
                    }
                  />

                  <input
                    type="number"
                    placeholder="goal_value"
                    value={row.goal_value}
                    onChange={(event) =>
                      setBulkRows((current) =>
                        current.map((item, itemIndex) =>
                          itemIndex === index
                            ? {
                                ...item,
                                goal_value: Number(event.target.value || 0),
                              }
                            : item,
                        ),
                      )
                    }
                  />

                  <select
                    value={row.goal_periodicity}
                    onChange={(event) =>
                      setBulkRows((current) =>
                        current.map((item, itemIndex) =>
                          itemIndex === index
                            ? {
                                ...item,
                                goal_periodicity:
                                  event.target.value as BulkGoalRow["goal_periodicity"],
                              }
                            : item,
                        ),
                      )
                    }
                  >
                    <option value="monthly">monthly</option>
                    <option value="annual">annual</option>
                    <option value="quarterly">quarterly</option>
                    <option value="weekly">weekly</option>
                  </select>
                </div>
              ))}

              <button
                type="button"
                className="si-settings-editor__button si-settings-editor__button--secondary"
                onClick={() => setBulkRows((current) => [...current, emptyBulkRow])}
              >
                Adicionar linha
              </button>
            </div>
          </div>
        ) : null}
      </div>
    </Modal>
  );
}