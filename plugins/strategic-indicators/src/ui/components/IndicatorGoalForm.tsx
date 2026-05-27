import { useEffect, useMemo, useState } from "react";
import type {
  CreateStrategicIndicatorGoalRequest,
  GoalMode,
  GoalPeriodicity,
  GoalScopeBranch,
  MonthlyTargetItem,
  StrategicIndicatorGoalItem,
  UpdateStrategicIndicatorGoalRequest,
} from "../../data/types/indicatorGoals";
import {
  getGoalModeLabel,
  getGoalPeriodicityLabel,
  getGoalScopeBranchLabel,
} from "../presentation/labels";
import { clampGoalYear, MIN_GOAL_YEAR, MAX_GOAL_YEAR } from "../utils/goalYearHelpers";
import {
  buildEmptyCurveTargets,
  getCurveHintText,
  getCurvePointLabels,
  getCurveSectionTitle,
  normalizeCurveTargets,
} from "../utils/curveTargets";
import {
  validateIndicatorGoalForm,
  type IndicatorGoalCatalogEntry,
} from "../utils/goalFormValidation";
import {
  expectedMonthlyCurvePointCount,
  resolveGoalValueForApi,
} from "../utils/goalValuePolicy";
import "./IndicatorGoalForm.css";

type IndicatorOption = {
  value: string;
  label: string;
};

type IndicatorGoalFormProps = {
  saving: boolean;
  initialValue?: StrategicIndicatorGoalItem | null;
  /** Pré-preenche o formulário para criar uma cópia (não edita o registro de origem). */
  duplicateFrom?: StrategicIndicatorGoalItem | null;
  indicatorOptions?: Array<string | IndicatorOption>;
  indicatorCatalog?: IndicatorGoalCatalogEntry[];
  defaultGoalYear?: number;
  lockGoalYear?: boolean;
  onCreate?: (payload: CreateStrategicIndicatorGoalRequest) => Promise<void>;
  onUpdate?: (
    goalId: string,
    payload: UpdateStrategicIndicatorGoalRequest,
  ) => Promise<void>;
  onCancel?: () => void;
};

function normalizeIndicatorOptions(
  options: Array<string | IndicatorOption>,
): IndicatorOption[] {
  return options.map((option) =>
    typeof option === "string"
      ? { value: option, label: option }
      : option,
  );
}

export function IndicatorGoalForm({
  saving,
  initialValue,
  duplicateFrom = null,
  indicatorOptions = [],
  indicatorCatalog = [],
  defaultGoalYear,
  lockGoalYear = false,
  onCreate,
  onUpdate,
  onCancel,
}: IndicatorGoalFormProps) {
  const [indicatorId, setIndicatorId] = useState("");
  const [goalYear, setGoalYear] = useState<number>(new Date().getFullYear());
  const [goalLabel, setGoalLabel] = useState("");
  const [goalValue, setGoalValue] = useState<number>(0);
  const [goalPeriodicity, setGoalPeriodicity] =
    useState<GoalPeriodicity>("monthly");
  const [goalMode, setGoalMode] = useState<GoalMode>("standard");
  const [goalScopeBranch, setGoalScopeBranch] = useState<GoalScopeBranch | string>("");
  const [monthlyTargets, setMonthlyTargets] = useState<MonthlyTargetItem[]>(
    buildEmptyCurveTargets("monthly"),
  );
  const [validFrom, setValidFrom] = useState("");
  const [validTo, setValidTo] = useState("");
  const [notes, setNotes] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);

  const formSeed = duplicateFrom ?? initialValue;
  const isEditing = useMemo(
    () => !!initialValue && !duplicateFrom,
    [initialValue, duplicateFrom],
  );
  const normalizedIndicatorOptions = useMemo(
    () => normalizeIndicatorOptions(indicatorOptions),
    [indicatorOptions],
  );
  const curvePointLabels = useMemo(
    () => getCurvePointLabels(goalPeriodicity),
    [goalPeriodicity],
  );

  useEffect(() => {
    if (!formSeed) {
      setIndicatorId("");
      setGoalYear(
        clampGoalYear(defaultGoalYear ?? new Date().getFullYear()),
      );
      setGoalLabel("");
      setGoalValue(0);
      setGoalPeriodicity("monthly");
      setGoalMode("standard");
      setGoalScopeBranch("");
      setMonthlyTargets(buildEmptyCurveTargets("monthly"));
      setValidFrom("");
      setValidTo("");
      setNotes("");
      setLocalError(null);
      return;
    }

    setIndicatorId(formSeed.indicator_id);
    setGoalYear(formSeed.goal_year);
    setGoalLabel(formSeed.goal_label);
    setGoalValue(formSeed.goal_value);
    setGoalPeriodicity(formSeed.goal_periodicity);
    setGoalMode(formSeed.goal_mode);
    setGoalScopeBranch(formSeed.goal_scope_branch ?? "");
    setMonthlyTargets(
      normalizeCurveTargets(
        formSeed.monthly_targets,
        formSeed.goal_periodicity,
      ),
    );
    setValidFrom(formSeed.valid_from ?? "");
    setValidTo(formSeed.valid_to ?? "");
    setNotes(formSeed.notes ?? "");
    setLocalError(null);
  }, [formSeed, defaultGoalYear]);

  function updateMonthlyTarget(monthNumber: number, targetValue: number) {
    setMonthlyTargets((current) =>
      current.map((item) =>
        item.month_number === monthNumber
          ? { ...item, target_value: targetValue }
          : item,
      ),
    );
  }

  async function handleSubmit() {
    setLocalError(null);

    const validationError = validateIndicatorGoalForm({
      indicatorId,
      goalYear,
      goalLabel,
      goalScopeBranch,
      goalMode,
      goalPeriodicity,
      goalValue,
      monthlyTargets,
      indicatorOptions: normalizedIndicatorOptions,
      indicatorCatalog,
      isEditing,
    });
    if (validationError) {
      setLocalError(validationError);
      return;
    }

    if (validFrom && validTo && validFrom > validTo) {
      setLocalError("A data final não pode ser anterior à data inicial.");
      return;
    }

    const resolvedGoalValue = resolveGoalValueForApi(goalMode, goalValue);
    const resolvedMonthlyTargets =
      goalMode === "monthly_curve" ? monthlyTargets : [];

    if (isEditing && initialValue && onUpdate) {
      const payload: UpdateStrategicIndicatorGoalRequest = {
        goal_label: goalLabel.trim(),
        goal_value: resolvedGoalValue,
        goal_periodicity: goalPeriodicity,
        goal_mode: goalMode,
        monthly_targets: resolvedMonthlyTargets,
        valid_from: validFrom || null,
        valid_to: validTo || null,
        notes: notes || null,
      };

      if (indicatorId.trim() !== initialValue.indicator_id) {
        payload.indicator_id = indicatorId.trim();
      }
      if (Number(goalYear) !== Number(initialValue.goal_year)) {
        payload.goal_year = Number(goalYear);
      }
      const initialScope = initialValue.goal_scope_branch ?? "";
      if (goalScopeBranch !== initialScope) {
        payload.goal_scope_branch = goalScopeBranch;
      }

      await onUpdate(initialValue.id, payload);
      return;
    }

    if (onCreate) {
      await onCreate({
        indicator_id: indicatorId.trim(),
        goal_year: Number(goalYear),
        goal_scope_branch: goalScopeBranch,
        goal_label: goalLabel.trim(),
        goal_value: resolvedGoalValue,
        goal_periodicity: goalPeriodicity,
        goal_mode: goalMode,
        monthly_targets: resolvedMonthlyTargets,
        valid_from: validFrom || null,
        valid_to: validTo || null,
        notes: notes || null,
      });
    }
  }

  return (
    <div className="si-modal-form">
      {localError ? (
        <div className="si-settings-editor__alert si-settings-editor__alert--error">
          {localError}
        </div>
      ) : null}

      <div className="si-modal-form__grid">
        <Field label="Indicador">
          {normalizedIndicatorOptions.length > 0 ? (
            <select
              value={indicatorId}
              onChange={(e) => {
                const nextId = e.target.value;
                setIndicatorId(nextId);
                if (!isEditing && !goalLabel.trim()) {
                  const match = normalizedIndicatorOptions.find(
                    (option) => option.value === nextId,
                  );
                  if (match) {
                    const [name] = match.label.split(" · ");
                    setGoalLabel(name?.trim() ?? match.label);
                  }
                }
              }}
              autoFocus={!isEditing}
            >
              <option value="">Selecione</option>
              {normalizedIndicatorOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          ) : (
            <input
              value={indicatorId}
              onChange={(e) => setIndicatorId(e.target.value)}
              autoFocus={!isEditing}
            />
          )}
        </Field>

        <Field label="Ano da meta">
          <input
            type="number"
            min={MIN_GOAL_YEAR}
            max={MAX_GOAL_YEAR}
            value={goalYear}
            readOnly={lockGoalYear}
            onChange={(e) => setGoalYear(clampGoalYear(Number(e.target.value)))}
          />
        </Field>

        <Field label="Nome da meta" fullWidth>
          <input
            value={goalLabel}
            onChange={(e) => setGoalLabel(e.target.value)}
          />
        </Field>

        <Field label="Modo da meta">
          <select
            value={goalMode}
            onChange={(e) => {
              const nextMode = e.target.value as GoalMode;
              setGoalMode(nextMode);
              if (nextMode === "monthly_curve") {
                setMonthlyTargets(buildEmptyCurveTargets(goalPeriodicity));
              }
            }}
          >
            <option value="standard">{getGoalModeLabel("standard")}</option>
            <option value="monthly_curve">{getGoalModeLabel("monthly_curve")}</option>
          </select>
        </Field>

        <Field label="Escopo da meta">
          <select
            value={goalScopeBranch}
            onChange={(e) => setGoalScopeBranch(e.target.value)}
          >
            <option value="">{getGoalScopeBranchLabel("")}</option>
            <option value="01">{getGoalScopeBranchLabel("01")}</option>
            <option value="02">{getGoalScopeBranchLabel("02")}</option>
          </select>
        </Field>

        <Field label="Periodicidade">
          <select
            value={goalPeriodicity}
            onChange={(e) => {
              const nextPeriodicity = e.target.value as GoalPeriodicity;
              setGoalPeriodicity(nextPeriodicity);
              if (goalMode === "monthly_curve") {
                setMonthlyTargets((current) =>
                  normalizeCurveTargets(current, nextPeriodicity),
                );
              }
            }}
          >
            <option value="monthly">Mensal</option>
            <option value="annual">Anual</option>
            <option value="quarterly">Trimestral</option>
            <option value="weekly">Semanal</option>
          </select>
        </Field>

        {goalMode === "standard" ? (
          <Field label="Valor da meta">
            <input
              type="number"
              step="0.0001"
              value={goalValue}
              onChange={(e) => setGoalValue(Number(e.target.value))}
            />
          </Field>
        ) : null}

        <Field label="Vigência inicial">
          <input
            type="date"
            value={validFrom}
            onChange={(e) => setValidFrom(e.target.value)}
          />
        </Field>

        <Field label="Vigência final">
          <input
            type="date"
            value={validTo}
            onChange={(e) => setValidTo(e.target.value)}
          />
        </Field>

        {goalMode === "monthly_curve" ? (
          <div className="si-settings-form-field si-settings-form-field--full">
            <span className="si-settings-form-field__label">
              {getCurveSectionTitle(goalPeriodicity)}
            </span>

            <div className="si-monthly-targets-toolbar">
              <span className="si-monthly-targets-toolbar__badge">
                {getGoalModeLabel(goalMode)}
              </span>
              <span className="si-monthly-targets-toolbar__summary">
                {expectedMonthlyCurvePointCount(goalPeriodicity)} pontos ·{" "}
                {getGoalPeriodicityLabel(goalPeriodicity)}
              </span>
            </div>
            <p className="si-monthly-targets-hint">{getCurveHintText(goalPeriodicity)}</p>

            <div
              className={`si-monthly-targets-grid ${
                goalPeriodicity === "weekly"
                  ? "si-monthly-targets-grid--weekly"
                  : ""
              }`}
            >
              {monthlyTargets.map((item, index) => (
                <label
                  key={item.month_number}
                  className="si-monthly-targets-grid__item"
                >
                  <span>{curvePointLabels[index] ?? `#${item.month_number}`}</span>
                  <input
                    type="number"
                    step="0.0001"
                    value={item.target_value}
                    onChange={(event) =>
                      updateMonthlyTarget(
                        item.month_number,
                        Number(event.target.value || 0),
                      )
                    }
                  />
                </label>
              ))}
            </div>
          </div>
        ) : null}

        <Field label="Observações" fullWidth>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />
        </Field>
      </div>

      <div className="si-modal-form__actions">
        {onCancel ? (
          <button
            type="button"
            className="si-settings-editor__button si-settings-editor__button--secondary"
            onClick={onCancel}
            disabled={saving}
          >
            Cancelar
          </button>
        ) : null}

        <button
          type="button"
          className="si-settings-editor__button"
          onClick={() => void handleSubmit()}
          disabled={saving}
        >
          {saving
            ? "Salvando..."
            : isEditing
              ? "Salvar alterações"
              : duplicateFrom
                ? "Salvar cópia"
                : "Criar meta"}
        </button>
      </div>
    </div>
  );
}

function Field({
  label,
  children,
  fullWidth = false,
}: {
  label: string;
  children: React.ReactNode;
  fullWidth?: boolean;
}) {
  return (
    <label
      className={`si-settings-form-field ${fullWidth ? "si-settings-form-field--full" : ""}`}
    >
      <span className="si-settings-form-field__label">{label}</span>
      {children}
    </label>
  );
}