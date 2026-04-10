import { useEffect, useState } from "react";
import type {
  CreateStrategicIndicatorGoalRequest,
  StrategicIndicatorGoalItem,
  UpdateStrategicIndicatorGoalRequest,
} from "../../data/types/indicatorGoals";

type IndicatorGoalFormProps = {
  saving: boolean;
  initialValue?: StrategicIndicatorGoalItem | null;
  onCreate?: (payload: CreateStrategicIndicatorGoalRequest) => Promise<void>;
  onUpdate?: (
    goalId: string,
    payload: UpdateStrategicIndicatorGoalRequest,
  ) => Promise<void>;
};

export function IndicatorGoalForm({
  saving,
  initialValue,
  onCreate,
  onUpdate,
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
      setLocalError("Goal label is required.");
      return;
    }

    if (!initialValue && !indicatorId.trim()) {
      setLocalError("Indicator ID is required.");
      return;
    }

    if (goalValue < 0) {
      setLocalError("Goal value cannot be negative.");
      return;
    }

    if (initialValue && onUpdate) {
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
    <section className="si-settings-editor">
      <div className="si-settings-editor__header">
        <div>
          <h3 className="si-settings-editor__title">
            {initialValue ? "Edit analytical goal" : "Create analytical goal"}
          </h3>
          <span className="si-settings-editor__subtitle">
            Manage year-based and versioned indicator goals.
          </span>
        </div>
      </div>

      {localError ? (
        <div className="si-settings-editor__alert si-settings-editor__alert--error">
          {localError}
        </div>
      ) : null}

      <div className="si-settings-form-list">
        <article className="si-settings-form-card">
          <div className="si-settings-form-card__grid">
            {!initialValue ? (
              <Field label="Indicator ID">
                <input
                  value={indicatorId}
                  onChange={(e) => setIndicatorId(e.target.value)}
                />
              </Field>
            ) : null}

            {!initialValue ? (
              <Field label="Goal year">
                <input
                  type="number"
                  value={goalYear}
                  onChange={(e) => setGoalYear(Number(e.target.value))}
                />
              </Field>
            ) : null}

            <Field label="Goal label">
              <input
                value={goalLabel}
                onChange={(e) => setGoalLabel(e.target.value)}
              />
            </Field>

            <Field label="Goal value">
              <input
                type="number"
                step="0.0001"
                value={goalValue}
                onChange={(e) => setGoalValue(Number(e.target.value))}
              />
            </Field>

            <Field label="Periodicity">
              <select
                value={goalPeriodicity}
                onChange={(e) =>
                  setGoalPeriodicity(
                    e.target.value as
                      | "monthly"
                      | "annual"
                      | "quarterly"
                      | "weekly",
                  )
                }
              >
                <option value="monthly">monthly</option>
                <option value="annual">annual</option>
                <option value="quarterly">quarterly</option>
                <option value="weekly">weekly</option>
              </select>
            </Field>

            <Field label="Valid from">
              <input
                type="date"
                value={validFrom}
                onChange={(e) => setValidFrom(e.target.value)}
              />
            </Field>

            <Field label="Valid to">
              <input
                type="date"
                value={validTo}
                onChange={(e) => setValidTo(e.target.value)}
              />
            </Field>

            <Field label="Notes">
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
              />
            </Field>
          </div>
        </article>
      </div>

      <div className="si-settings-editor__actions">
        <button
          type="button"
          className="si-settings-editor__button"
          onClick={() => void handleSubmit()}
          disabled={saving}
        >
          {saving ? "Saving..." : initialValue ? "Update goal" : "Create goal"}
        </button>
      </div>
    </section>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label className="si-settings-form-field">
      <span className="si-settings-form-field__label">{label}</span>
      {children}
    </label>
  );
}