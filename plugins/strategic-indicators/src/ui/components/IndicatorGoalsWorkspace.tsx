import { useMemo, useState } from "react";
import { InfoState } from "./InfoState";
import { IndicatorGoalForm } from "./IndicatorGoalForm";
import { useStrategicIndicatorGoals } from "../../state/hooks/useStrategicIndicatorGoals";
import type { StrategicIndicatorGoalItem } from "../../data/types/indicatorGoals";

type IndicatorGoalsWorkspaceProps = {
  getAccessToken?: () => string | undefined;
};

export function IndicatorGoalsWorkspace({
  getAccessToken,
}: IndicatorGoalsWorkspaceProps) {
  const {
    items,
    historyItems,
    selectedIndicatorId,
    selectedGoalYear,
    setSelectedIndicatorId,
    setSelectedGoalYear,
    loading,
    refreshing,
    saving,
    historyLoading,
    error,
    historyError,
    successMessage,
    reload,
    loadHistory,
    createGoal,
    updateGoal,
    activateGoal,
    deactivateGoal,
    clearSuccessMessage,
  } = useStrategicIndicatorGoals({
    getAccessToken,
    initialGoalYear: new Date().getFullYear(),
  });

  const [editingItem, setEditingItem] = useState<StrategicIndicatorGoalItem | null>(null);

  const groupedIndicators = useMemo(() => {
    return Array.from(new Set(items.map((item) => item.indicator_id))).sort();
  }, [items]);

  return (
    <div className="si-page">
      {successMessage ? (
        <InfoState
          title="Analytical goals updated"
          description={successMessage}
          actionLabel="Dismiss"
          onAction={clearSuccessMessage}
        />
      ) : null}

      {error ? (
        <InfoState
          title="Failed to load analytical goals"
          description={error}
          actionLabel="Retry"
          onAction={() => void reload()}
        />
      ) : null}

      <section className="si-settings-editor">
        <div className="si-settings-editor__header">
          <div>
            <h3 className="si-settings-editor__title">Analytical goals</h3>
            <span className="si-settings-editor__subtitle">
              Manage versioned goals by indicator and year.
            </span>
          </div>

          <div className="si-settings-editor__meta-group">
            <div className="si-settings-editor__summary">
              <span>Records</span>
              <strong>{items.length}</strong>
            </div>
          </div>
        </div>

        <div className="si-settings-form-list">
          <article className="si-settings-form-card">
            <div className="si-settings-form-card__grid">
              <Field label="Indicator filter">
                <select
                  value={selectedIndicatorId}
                  onChange={(e) => setSelectedIndicatorId(e.target.value)}
                >
                  <option value="">All indicators</option>
                  {groupedIndicators.map((indicatorId) => (
                    <option key={indicatorId} value={indicatorId}>
                      {indicatorId}
                    </option>
                  ))}
                </select>
              </Field>

              <Field label="Goal year">
                <input
                  type="number"
                  value={selectedGoalYear}
                  onChange={(e) =>
                    setSelectedGoalYear(
                      e.target.value ? Number(e.target.value) : "",
                    )
                  }
                />
              </Field>
            </div>
          </article>
        </div>

        {loading ? (
          <InfoState
            title="Loading analytical goals"
            description="Please wait while the administrative catalog is loaded."
          />
        ) : null}

        {refreshing ? (
          <InfoState
            title="Refreshing analytical goals"
            description="The goal list is being refreshed without leaving the page."
          />
        ) : null}

        {!loading ? (
          <div className="si-settings-form-list">
            {items.map((item) => (
              <article key={item.id} className="si-settings-form-card">
                <div className="si-settings-form-card__grid">
                  <Field label="Indicator">
                    <input value={item.indicator_id} readOnly />
                  </Field>

                  <Field label="Year">
                    <input value={item.goal_year} readOnly />
                  </Field>

                  <Field label="Version">
                    <input value={item.version} readOnly />
                  </Field>

                  <Field label="Label">
                    <input value={item.goal_label} readOnly />
                  </Field>

                  <Field label="Value">
                    <input value={item.goal_value} readOnly />
                  </Field>

                  <Field label="Periodicity">
                    <input value={item.goal_periodicity} readOnly />
                  </Field>

                  <Field label="Status">
                    <input value={item.is_active ? "Active" : "Inactive"} readOnly />
                  </Field>
                </div>

                <div className="si-settings-editor__actions">
                  <button
                    type="button"
                    className="si-settings-editor__button si-settings-editor__button--secondary"
                    onClick={() => setEditingItem(item)}
                    disabled={saving}
                  >
                    Edit
                  </button>

                  <button
                    type="button"
                    className="si-settings-editor__button si-settings-editor__button--secondary"
                    onClick={() =>
                      void loadHistory(item.indicator_id, item.goal_year)
                    }
                    disabled={historyLoading}
                  >
                    History
                  </button>

                  {!item.is_active ? (
                    <button
                      type="button"
                      className="si-settings-editor__button"
                      onClick={() => void activateGoal(item.id)}
                      disabled={saving}
                    >
                      Activate
                    </button>
                  ) : (
                    <button
                      type="button"
                      className="si-settings-editor__button si-settings-editor__button--secondary"
                      onClick={() => void deactivateGoal(item.id)}
                      disabled={saving}
                    >
                      Deactivate
                    </button>
                  )}
                </div>
              </article>
            ))}
          </div>
        ) : null}
      </section>

      <IndicatorGoalForm saving={saving} onCreate={createGoal} />

      {editingItem ? (
        <IndicatorGoalForm
          saving={saving}
          initialValue={editingItem}
          onUpdate={updateGoal}
        />
      ) : null}

      <section className="si-settings-editor">
        <div className="si-settings-editor__header">
          <div>
            <h3 className="si-settings-editor__title">Goal history</h3>
            <span className="si-settings-editor__subtitle">
              Historical versions for the selected indicator/year.
            </span>
          </div>
        </div>

        {historyError ? (
          <InfoState
            title="Failed to load history"
            description={historyError}
          />
        ) : null}

        {historyLoading ? (
          <InfoState
            title="Loading history"
            description="Historical versions are being loaded."
          />
        ) : null}

        {!historyLoading && historyItems.length === 0 ? (
          <InfoState
            title="No history loaded"
            description="Use the History button on a row to inspect past versions."
          />
        ) : null}

        {!historyLoading && historyItems.length > 0 ? (
          <div className="si-settings-form-list">
            {historyItems.map((item) => (
              <article key={item.id} className="si-settings-form-card">
                <div className="si-settings-form-card__grid">
                  <Field label="Indicator">
                    <input value={item.indicator_id} readOnly />
                  </Field>

                  <Field label="Year">
                    <input value={item.goal_year} readOnly />
                  </Field>

                  <Field label="Version">
                    <input value={item.version} readOnly />
                  </Field>

                  <Field label="Label">
                    <input value={item.goal_label} readOnly />
                  </Field>

                  <Field label="Updated at">
                    <input value={item.updated_at} readOnly />
                  </Field>

                  <Field label="Updated by">
                    <input value={item.updated_by_email ?? "-"} readOnly />
                  </Field>
                </div>
              </article>
            ))}
          </div>
        ) : null}
      </section>
    </div>
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