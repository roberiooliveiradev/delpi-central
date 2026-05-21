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
import { getGoalScopeBranchLabel } from "../presentation/labels";
import "./IndicatorGoalForm.css";

type IndicatorOption = {
  value: string;
  label: string;
};

type IndicatorGoalFormProps = {
  saving: boolean;
  initialValue?: StrategicIndicatorGoalItem | null;
  indicatorOptions?: Array<string | IndicatorOption>;
  onCreate?: (payload: CreateStrategicIndicatorGoalRequest) => Promise<void>;
  onUpdate?: (
    goalId: string,
    payload: UpdateStrategicIndicatorGoalRequest,
  ) => Promise<void>;
  onCancel?: () => void;
};

const MONTH_LABELS = [
  "Jan",
  "Fev",
  "Mar",
  "Abr",
  "Mai",
  "Jun",
  "Jul",
  "Ago",
  "Set",
  "Out",
  "Nov",
  "Dez",
];

function buildEmptyMonthlyTargets(): MonthlyTargetItem[] {
  return Array.from({ length: 12 }, (_, index) => ({
    month_number: index + 1,
    target_value: 0,
  }));
}

function normalizeIndicatorOptions(
  options: Array<string | IndicatorOption>,
): IndicatorOption[] {
  return options.map((option) =>
    typeof option === "string"
      ? { value: option, label: option }
      : option,
  );
}

function normalizeMonthlyTargets(
  input?: MonthlyTargetItem[] | null,
): MonthlyTargetItem[] {
  const base = buildEmptyMonthlyTargets();

  if (!input?.length) return base;

  const byMonth = new Map<number, number>();
  input.forEach((item) => {
    byMonth.set(item.month_number, Number(item.target_value || 0));
  });

  return base.map((item) => ({
    month_number: item.month_number,
    target_value: byMonth.get(item.month_number) ?? 0,
  }));
}

function formatGoalModeLabel(value: GoalMode) {
  return value === "monthly_curve" ? "Curva mensal" : "Meta padrão";
}

export function IndicatorGoalForm({
  saving,
  initialValue,
  indicatorOptions = [],
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
    buildEmptyMonthlyTargets(),
  );
  const [validFrom, setValidFrom] = useState("");
  const [validTo, setValidTo] = useState("");
  const [notes, setNotes] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);

  const isEditing = useMemo(() => !!initialValue, [initialValue]);
  const normalizedIndicatorOptions = useMemo(
    () => normalizeIndicatorOptions(indicatorOptions),
    [indicatorOptions],
  );

  useEffect(() => {
    if (!initialValue) {
      setIndicatorId("");
      setGoalYear(new Date().getFullYear());
      setGoalLabel("");
      setGoalValue(0);
      setGoalPeriodicity("monthly");
      setGoalMode("standard");
      setGoalScopeBranch("");
      setMonthlyTargets(buildEmptyMonthlyTargets());
      setValidFrom("");
      setValidTo("");
      setNotes("");
      setLocalError(null);
      return;
    }

    setIndicatorId(initialValue.indicator_id);
    setGoalYear(initialValue.goal_year);
    setGoalLabel(initialValue.goal_label);
    setGoalValue(initialValue.goal_value);
    setGoalPeriodicity(initialValue.goal_periodicity);
    setGoalMode(initialValue.goal_mode);
    setGoalScopeBranch(initialValue.goal_scope_branch ?? "");
    setMonthlyTargets(normalizeMonthlyTargets(initialValue.monthly_targets));
    setValidFrom(initialValue.valid_from ?? "");
    setValidTo(initialValue.valid_to ?? "");
    setNotes(initialValue.notes ?? "");
    setLocalError(null);
  }, [initialValue]);

  function updateMonthlyTarget(monthNumber: number, targetValue: number) {
    setMonthlyTargets((current) =>
      current.map((item) =>
        item.month_number === monthNumber
          ? { ...item, target_value: targetValue }
          : item,
      ),
    );
  }

  function buildResolvedGoalValue() {
    if (goalMode === "monthly_curve") {
      return monthlyTargets.reduce(
        (sum, item) => sum + Number(item.target_value || 0),
        0,
      );
    }

    return Number(goalValue || 0);
  }

  async function handleSubmit() {
    setLocalError(null);

    if (!goalLabel.trim()) {
      setLocalError("O nome da meta é obrigatório.");
      return;
    }

    if (!isEditing && !indicatorId.trim()) {
      setLocalError("Selecione um indicador.");
      return;
    }

    if (goalMode === "standard" && goalValue < 0) {
      setLocalError("O valor da meta não pode ser negativo.");
      return;
    }

    if (goalMode === "monthly_curve") {
      const hasInvalidMonthlyValue = monthlyTargets.some(
        (item) => Number(item.target_value) < 0,
      );
      if (hasInvalidMonthlyValue) {
        setLocalError("Os valores mensais não podem ser negativos.");
        return;
      }
    }

    if (validFrom && validTo && validFrom > validTo) {
      setLocalError("A data final não pode ser anterior à data inicial.");
      return;
    }

    const resolvedGoalValue = buildResolvedGoalValue();
    const resolvedMonthlyTargets =
      goalMode === "monthly_curve" ? monthlyTargets : [];

    if (isEditing && initialValue && onUpdate) {
      await onUpdate(initialValue.id, {
        goal_label: goalLabel.trim(),
        goal_value: resolvedGoalValue,
        goal_periodicity: goalPeriodicity,
        goal_mode: goalMode,
        monthly_targets: resolvedMonthlyTargets,
        valid_from: validFrom || null,
        valid_to: validTo || null,
        notes: notes || null,
      });
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
        {!isEditing ? (
          <Field label="Indicador">
            {normalizedIndicatorOptions.length > 0 ? (
              <select
                value={indicatorId}
                onChange={(e) => setIndicatorId(e.target.value)}
                autoFocus
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
                autoFocus
              />
            )}
          </Field>
        ) : (
          <Field label="Indicador">
            <input value={indicatorId} readOnly />
          </Field>
        )}

        {!isEditing ? (
          <Field label="Ano da meta">
            <input
              type="number"
              value={goalYear}
              onChange={(e) => setGoalYear(Number(e.target.value))}
            />
          </Field>
        ) : (
          <Field label="Ano da meta">
            <input value={goalYear} readOnly />
          </Field>
        )}

        <Field label="Nome da meta" fullWidth>
          <input
            value={goalLabel}
            onChange={(e) => setGoalLabel(e.target.value)}
          />
        </Field>

        <Field label="Modo da meta">
          <select
            value={goalMode}
            onChange={(e) => setGoalMode(e.target.value as GoalMode)}
          >
            <option value="standard">Meta padrão</option>
            <option value="monthly_curve">Curva mensal</option>
          </select>
        </Field>

        {!isEditing ? (
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
        ) : (
          <Field label="Escopo da meta">
            <input value={getGoalScopeBranchLabel(goalScopeBranch)} readOnly />
          </Field>
        )}

        <Field label="Periodicidade">
          <select
            value={goalPeriodicity}
            onChange={(e) =>
              setGoalPeriodicity(e.target.value as GoalPeriodicity)
            }
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
        ) : (
          <Field label="Valor consolidado da curva">
            <input value={buildResolvedGoalValue()} readOnly />
          </Field>
        )}

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
              Curva mensal da meta
            </span>

            <div className="si-monthly-targets-toolbar">
              <span className="si-monthly-targets-toolbar__badge">
                {formatGoalModeLabel(goalMode)}
              </span>
              <span className="si-monthly-targets-toolbar__summary">
                Soma anual: {buildResolvedGoalValue().toLocaleString("pt-BR")}
              </span>
            </div>

            <div className="si-monthly-targets-grid">
              {monthlyTargets.map((item, index) => (
                <label
                  key={item.month_number}
                  className="si-monthly-targets-grid__item"
                >
                  <span>{MONTH_LABELS[index]}</span>
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