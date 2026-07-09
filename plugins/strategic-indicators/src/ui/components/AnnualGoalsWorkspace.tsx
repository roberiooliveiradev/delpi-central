import { useEffect, useMemo, useState } from "react";
import {
  buildYearSelectOptions,
  pickSourceYearForTarget,
  suggestYearBeforeLatest,
  clampGoalYear,
} from "../utils/goalYearHelpers";
import type {
  BulkCreateStrategicIndicatorGoalsRequest,
  DuplicateStrategicIndicatorGoalsYearRequest,
  FillMissingStrategicIndicatorGoalsRequest,
} from "../../data/types/indicatorGoals";
import { useStrategicIndicatorGoals } from "../../state/hooks/useStrategicIndicatorGoals";
import { useStrategicIndicatorsGoalYearsOverview } from "../../state/hooks/useStrategicIndicatorsGoalYearsOverview";
import { InfoState } from "./InfoState";
import { Modal } from "./Modal";
import {
  getGoalModeLabel,
  getGoalPeriodicityLabel,
  getGoalScopeBranchLabel,
} from "../presentation/labels";
import { buildEmptyCurveTargets } from "../utils/curveTargets";
import { resolveGoalValueForApi } from "../utils/goalValuePolicy";
import "./AnnualGoalsWorkspace.css";
import { SiSelectControl } from "./siFiltersUi";

type AnnualGoalsWorkspaceMode =
  | "create_year"
  | "duplicate_into_year"
  | "fill_missing_for_year";

type IndicatorOption = {
  value: string;
  label: string;
};

type AnnualGoalsWorkspaceProps = {
  open: boolean;
  mode: AnnualGoalsWorkspaceMode;
  fixedTargetYear: number | null;
  onClose: () => void;
  getAccessToken?: () => string | undefined;
  /** Renderiza o formulário inline (sem modal), para painéis administrativos. */
  embedded?: boolean;
  existingYears?: number[];
  indicatorOptions?: IndicatorOption[];
  /** Origem fixa ao abrir duplicação (ex.: clicou em 2026 na lista). */
  initialSourceYear?: number | null;
};

type BulkGoalRow = {
  indicator_id: string;
  goal_label: string;
  goal_value: number;
  goal_periodicity: "monthly" | "annual" | "quarterly" | "weekly";
  goal_mode: "standard" | "monthly_curve";
  goal_scope_branch: "" | "01" | "02";
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
  goal_scope_branch: "",
  monthly_targets: [],
};

export function AnnualGoalsWorkspace({
  open,
  mode,
  fixedTargetYear,
  onClose,
  getAccessToken,
  embedded = false,
  existingYears = [],
  indicatorOptions = [],
  initialSourceYear = null,
}: AnnualGoalsWorkspaceProps) {
  const goals = useStrategicIndicatorGoals({ getAccessToken });
  const yearsOverview = useStrategicIndicatorsGoalYearsOverview({ getAccessToken });

  const catalogYears = useMemo(() => {
    const fromOverview = yearsOverview.items.map((item) => item.goal_year);
    return [...new Set([...existingYears, ...fromOverview])];
  }, [existingYears, yearsOverview.items]);

  const suggestedNewYear = useMemo(
    () => suggestYearBeforeLatest(catalogYears) ?? clampGoalYear(new Date().getFullYear()),
    [catalogYears],
  );

  const yearSelectOptions = useMemo(
    () =>
      buildYearSelectOptions(catalogYears, [
        suggestedNewYear,
        typeof fixedTargetYear === "number" ? fixedTargetYear : suggestedNewYear,
      ]),
    [catalogYears, fixedTargetYear, suggestedNewYear],
  );

  const [targetYear, setTargetYear] = useState<number>(
    fixedTargetYear ?? suggestedNewYear,
  );
  const [bulkRows, setBulkRows] = useState<BulkGoalRow[]>([emptyBulkRow]);
  const [sourceYear, setSourceYear] = useState<number>(
    pickSourceYearForTarget(catalogYears, suggestedNewYear),
  );
  const [overwriteExisting, setOverwriteExisting] = useState(false);
  const [copyFromYear, setCopyFromYear] = useState<number | "">(
    pickSourceYearForTarget(catalogYears, fixedTargetYear ?? suggestedNewYear),
  );

  useEffect(() => {
    if (!open && !embedded) return;

    if (mode === "duplicate_into_year" && typeof fixedTargetYear === "number") {
      setTargetYear(fixedTargetYear);
      setSourceYear(
        typeof initialSourceYear === "number"
          ? initialSourceYear
          : pickSourceYearForTarget(catalogYears, fixedTargetYear),
      );
    } else if (typeof fixedTargetYear === "number") {
      setTargetYear(fixedTargetYear);
    } else if (mode === "create_year") {
      setTargetYear(suggestedNewYear);
    } else {
      setTargetYear(clampGoalYear(new Date().getFullYear()));
    }

    if (mode === "fill_missing_for_year") {
      const target =
        typeof fixedTargetYear === "number" ? fixedTargetYear : suggestedNewYear;
      setCopyFromYear(pickSourceYearForTarget(catalogYears, target));
    }

    if (mode === "create_year") {
      setBulkRows([emptyBulkRow]);
    }

    setOverwriteExisting(false);
  }, [
    open,
    embedded,
    mode,
    fixedTargetYear,
    initialSourceYear,
    catalogYears,
    suggestedNewYear,
  ]);

  function indicatorLabelForValue(value: string) {
    const match = indicatorOptions.find((option) => option.value === value);
    if (!match) return "";
    const [name] = match.label.split(" · ");
    return name?.trim() ?? match.label;
  }

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
          goal_value: resolveGoalValueForApi(
            item.goal_mode,
            Number(item.goal_value || 0),
          ),
          goal_periodicity: item.goal_periodicity,
          goal_mode: item.goal_mode,
          goal_scope_branch: item.goal_scope_branch,
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

  const footer = (
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
  );

  const body = (
    <>
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
              <span>Ano de origem (copiar de)</span>
              <SiSelectControl
                value={String(sourceYear)}
                onChange={(value) => setSourceYear(Number(value))}
                options={yearSelectOptions.map((year) => ({
                  value: String(year),
                  label: String(year),
                }))}
              />
            </label>

            <label className="si-admin-form-field">
              <span>Ano de destino (criar/atualizar)</span>
              {typeof fixedTargetYear === "number" ? (
                <input type="number" value={resolvedTargetYear} readOnly />
              ) : (
                <SiSelectControl
                  value={String(targetYear)}
                  onChange={(value) => setTargetYear(Number(value))}
                  options={yearSelectOptions.map((year) => ({
                    value: String(year),
                    label: String(year),
                  }))}
                />
              )}
            </label>
          </>
        ) : (
          <label className="si-admin-form-field">
            <span>Ano de destino</span>
            {typeof fixedTargetYear === "number" ? (
              <input type="number" value={resolvedTargetYear} readOnly />
            ) : (
              <SiSelectControl
                value={String(resolvedTargetYear)}
                onChange={(value) => setTargetYear(Number(value))}
                options={yearSelectOptions.map((year) => ({
                  value: String(year),
                  label: `${year}${catalogYears.includes(year) ? "" : " (novo)"}`,
                }))}
              />
            )}
          </label>
        )}

        {mode === "fill_missing_for_year" ? (
          <label className="si-admin-form-field">
            <span>Copiar estrutura de</span>
            <SiSelectControl
              value={String(copyFromYear)}
              onChange={(value) => setCopyFromYear(Number(value))}
              options={yearSelectOptions.map((year) => ({
                value: String(year),
                label: String(year),
              }))}
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
                  {indicatorOptions.length > 0 ? (
                    <SiSelectControl
                      value={row.indicator_id}
                      ariaLabel="Indicador estrutural"
                      onChange={(nextId) => {
                        const labelHint = indicatorLabelForValue(nextId);
                        setBulkRows((current) =>
                          current.map((item, itemIndex) =>
                            itemIndex === index
                              ? {
                                  ...item,
                                  indicator_id: nextId,
                                  goal_label: item.goal_label || labelHint,
                                }
                              : item,
                          ),
                        );
                      }}
                      allowEmpty
                      emptyLabel="Selecione o indicador"
                      options={indicatorOptions}
                    />
                  ) : (
                    <input
                      placeholder="ID do indicador"
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
                  )}

                  <input
                    placeholder="Nome da meta"
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

                  {row.goal_mode === "standard" ? (
                    <input
                      type="number"
                      placeholder="Valor da meta"
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
                  ) : null}

                  <SiSelectControl
                    value={row.goal_periodicity}
                    ariaLabel="Periodicidade da meta"
                    onChange={(value) =>
                      setBulkRows((current) =>
                        current.map((item, itemIndex) =>
                          itemIndex === index
                            ? {
                                ...item,
                                goal_periodicity:
                                  value as BulkGoalRow["goal_periodicity"],
                              }
                            : item,
                        ),
                      )
                    }
                    options={[
                      { value: "monthly", label: getGoalPeriodicityLabel("monthly") },
                      { value: "annual", label: getGoalPeriodicityLabel("annual") },
                      { value: "quarterly", label: getGoalPeriodicityLabel("quarterly") },
                      { value: "weekly", label: getGoalPeriodicityLabel("weekly") },
                    ]}
                  />

                  <SiSelectControl
                    value={row.goal_mode}
                    ariaLabel="Modo da meta"
                    onChange={(value) =>
                      setBulkRows((current) =>
                        current.map((item, itemIndex) =>
                          itemIndex === index
                            ? {
                                ...item,
                                goal_mode: value as "standard" | "monthly_curve",
                                monthly_targets:
                                  value === "monthly_curve"
                                    ? buildEmptyCurveTargets(item.goal_periodicity)
                                    : [],
                              }
                            : item,
                        ),
                      )
                    }
                    options={[
                      { value: "standard", label: getGoalModeLabel("standard") },
                      { value: "monthly_curve", label: getGoalModeLabel("monthly_curve") },
                    ]}
                  />

                  <SiSelectControl
                    value={row.goal_scope_branch}
                    ariaLabel="Escopo da meta"
                    onChange={(value) =>
                      setBulkRows((current) =>
                        current.map((item, itemIndex) =>
                          itemIndex === index
                            ? {
                                ...item,
                                goal_scope_branch: value as BulkGoalRow["goal_scope_branch"],
                              }
                            : item,
                        ),
                      )
                    }
                    allowEmpty
                    emptyLabel={getGoalScopeBranchLabel("")}
                    options={[
                      { value: "01", label: getGoalScopeBranchLabel("01") },
                      { value: "02", label: getGoalScopeBranchLabel("02") },
                    ]}
                  />
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
    </>
  );

  if (embedded) {
    return (
      <div className="si-annual-goals-embedded">
        {body}
        <div className="si-annual-goals-embedded__footer">{footer}</div>
      </div>
    );
  }

  if (!open) return null;

  const modalTitle =
    mode === "create_year"
      ? "Novo ano"
      : mode === "duplicate_into_year"
        ? `Duplicar metas de ${sourceYear} para ${resolvedTargetYear}`
        : `Preencher metas faltantes de ${resolvedTargetYear}`;

  const modalDescription =
    mode === "create_year"
      ? "Crie um novo ciclo anual e, se quiser, já adicione metas iniciais."
      : mode === "duplicate_into_year"
        ? "Copie metas ativas do ano de origem para o ciclo de destino (ex.: 2026 → 2025)."
        : "Complete metas ausentes do ano selecionado usando outro ciclo como referência.";

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={modalTitle}
      description={modalDescription}
      size="lg"
      footer={footer}
    >
      {body}
    </Modal>
  );
}