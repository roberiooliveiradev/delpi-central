import { useEffect, useMemo, useState } from "react";
import type {
  CreateStrategicIndicatorGoalRequest,
  StrategicIndicatorGoalItem,
  UpdateStrategicIndicatorGoalRequest,
} from "../../data/types/indicatorGoals";

type IndicatorGoalFormProps = {
  saving: boolean;
  initialValue?: StrategicIndicatorGoalItem | null;
  indicatorOptions?: string[];
  onCreate?: (payload: CreateStrategicIndicatorGoalRequest) => Promise<void>;
  onUpdate?: (
    goalId: string,
    payload: UpdateStrategicIndicatorGoalRequest,
  ) => Promise<void>;
  onCancel?: () => void;
};

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
  const [goalPeriodicity, setGoalPeriodicity] = useState<
    "monthly" | "annual" | "quarterly" | "weekly"
  >("monthly");
  const [validFrom, setValidFrom] = useState("");
  const [validTo, setValidTo] = useState("");
  const [notes, setNotes] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);

  const isEditing = useMemo(() => !!initialValue, [initialValue]);

  useEffect(() => {
    if (!initialValue) {
      setIndicatorId("");
      setGoalYear(new Date().getFullYear());
      setGoalLabel("");
      setGoalValue(0);
      setGoalPeriodicity("monthly");
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
    setValidFrom(initialValue.valid_from ?? "");
    setValidTo(initialValue.valid_to ?? "");
    setNotes(initialValue.notes ?? "");
    setLocalError(null);
  }, [initialValue]);

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

    if (goalValue < 0) {
      setLocalError("O valor da meta não pode ser negativo.");
      return;
    }

    if (validFrom && validTo && validFrom > validTo) {
      setLocalError("A data final não pode ser anterior à data inicial.");
      return;
    }

    if (isEditing && initialValue && onUpdate) {
      await onUpdate(initialValue.id, {
        goal_label: goalLabel.trim(),
        goal_value: Number(goalValue),
        goal_periodicity: goalPeriodicity,
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
        goal_label: goalLabel.trim(),
        goal_value: Number(goalValue),
        goal_periodicity: goalPeriodicity,
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
            {indicatorOptions.length > 0 ? (
              <select
                value={indicatorId}
                onChange={(e) => setIndicatorId(e.target.value)}
                autoFocus
              >
                <option value="">Selecione</option>
                {indicatorOptions.map((option) => (
                  <option key={option} value={option}>
                    {option}
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

        <Field label="Nome da meta">
          <input
            value={goalLabel}
            onChange={(e) => setGoalLabel(e.target.value)}
          />
        </Field>

        <Field label="Valor da meta">
          <input
            type="number"
            step="0.0001"
            value={goalValue}
            onChange={(e) => setGoalValue(Number(e.target.value))}
          />
        </Field>

        <Field label="Periodicidade">
          <select
            value={goalPeriodicity}
            onChange={(e) =>
              setGoalPeriodicity(
                e.target.value as "monthly" | "annual" | "quarterly" | "weekly",
              )
            }
          >
            <option value="monthly">Mensal</option>
            <option value="annual">Anual</option>
            <option value="quarterly">Trimestral</option>
            <option value="weekly">Semanal</option>
          </select>
        </Field>

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