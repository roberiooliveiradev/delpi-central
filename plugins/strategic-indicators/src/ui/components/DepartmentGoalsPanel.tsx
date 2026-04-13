import { useEffect, useMemo, useState } from "react";
import { SectionBlock } from "./SectionBlock";
import { InfoState } from "./InfoState";
import { Modal } from "./Modal";
import { ActionButtons } from "./ActionButtons";
import { useStrategicIndicatorGoals } from "../../state/hooks/useStrategicIndicatorGoals";
import type {
  CreateStrategicIndicatorGoalRequest,
  StrategicIndicatorGoalItem,
  UpdateStrategicIndicatorGoalRequest,
  GoalPeriodicity,
} from "../../data/types/indicatorGoals";
import type { AdminDepartmentIndicatorItem } from "../../data/types/settings";

type DepartmentGoalsPanelProps = {
  departmentId: string;
  getAccessToken?: () => string | undefined;
  indicators: AdminDepartmentIndicatorItem[];
};

type GoalFormState = {
  id?: string;
  indicator_id: string;
  goal_year: number;
  goal_label: string;
  goal_value: number;
  goal_periodicity: GoalPeriodicity;
  valid_from: string;
  valid_to: string;
  notes: string;
};

const emptyGoalForm: GoalFormState = {
  indicator_id: "",
  goal_year: new Date().getFullYear(),
  goal_label: "",
  goal_value: 0,
  goal_periodicity: "annual",
  valid_from: "",
  valid_to: "",
  notes: "",
};

function getGoalPeriodicityLabel(value: GoalPeriodicity): string {
  switch (value) {
    case "annual":
      return "Anual";
    case "monthly":
      return "Mensal";
    case "quarterly":
      return "Trimestral";
    case "weekly":
      return "Semanal";
    default:
      return value;
  }
}

export function DepartmentGoalsPanel({
  departmentId,
  getAccessToken,
  indicators,
}: DepartmentGoalsPanelProps) {
  const goals = useStrategicIndicatorGoals({
    getAccessToken,
    initialGoalYear: new Date().getFullYear(),
  });

  const [goalFormOpen, setGoalFormOpen] = useState(false);
  const [goalFormMode, setGoalFormMode] = useState<"create" | "edit">("create");
  const [goalForm, setGoalForm] = useState<GoalFormState>(emptyGoalForm);

  useEffect(() => {
    goals.setSelectedDepartmentId(departmentId);
    goals.setSelectedIndicatorId("");
  }, [departmentId]);

  const activeIndicators = useMemo(
    () => indicators.filter((item) => item.is_active),
    [indicators],
  );

  function openCreateGoalForm() {
    setGoalFormMode("create");
    setGoalForm({
      ...emptyGoalForm,
      indicator_id: activeIndicators[0]?.indicator_id ?? "",
      goal_year:
        typeof goals.selectedGoalYear === "number"
          ? goals.selectedGoalYear
          : new Date().getFullYear(),
    });
    setGoalFormOpen(true);
  }

  function openEditGoalForm(item: StrategicIndicatorGoalItem) {
    setGoalFormMode("edit");
    setGoalForm({
      id: item.id,
      indicator_id: item.indicator_id,
      goal_year: item.goal_year,
      goal_label: item.goal_label,
      goal_value: item.goal_value,
      goal_periodicity: item.goal_periodicity,
      valid_from: item.valid_from ?? "",
      valid_to: item.valid_to ?? "",
      notes: item.notes ?? "",
    });
    setGoalFormOpen(true);
  }

  async function handleSubmitGoalForm() {
    if (goalFormMode === "create") {
      const payload: CreateStrategicIndicatorGoalRequest = {
        indicator_id: goalForm.indicator_id.trim(),
        goal_year: Number(goalForm.goal_year),
        goal_label: goalForm.goal_label.trim(),
        goal_value: Number(goalForm.goal_value || 0),
        goal_periodicity: goalForm.goal_periodicity,
        valid_from: goalForm.valid_from || null,
        valid_to: goalForm.valid_to || null,
        notes: goalForm.notes || null,
      };

      await goals.createGoal(payload);
    } else if (goalForm.id) {
      const payload: UpdateStrategicIndicatorGoalRequest = {
        goal_label: goalForm.goal_label.trim(),
        goal_value: Number(goalForm.goal_value || 0),
        goal_periodicity: goalForm.goal_periodicity,
        valid_from: goalForm.valid_from || null,
        valid_to: goalForm.valid_to || null,
        notes: goalForm.notes || null,
      };

      await goals.updateGoal(goalForm.id, payload);
    }

    setGoalFormOpen(false);
  }

  return (
    <>
      <SectionBlock
        title="Metas do departamento por ano"
        description="Gerencie as metas dos indicadores deste departamento dentro do ano selecionado."
        aside={
          <div className="si-admin-inline-actions">
            <label className="si-admin-form-field si-admin-form-field--compact">
              <span>Ano</span>
              <input
                type="number"
                value={goals.selectedGoalYear}
                onChange={(event) =>
                  goals.setSelectedGoalYear(
                    Number(event.target.value || new Date().getFullYear()),
                  )
                }
              />
            </label>

            <button
              type="button"
              className="si-settings-editor__button"
              onClick={openCreateGoalForm}
              disabled={activeIndicators.length === 0}
            >
              Nova meta
            </button>
          </div>
        }
      >
        {!!goals.successMessage ? (
          <div className="si-settings-editor__alert si-settings-editor__alert--success">
            {goals.successMessage}
          </div>
        ) : null}

        {goals.error ? (
          <InfoState
            title="Falha ao carregar metas"
            description={goals.error}
            actionLabel="Recarregar"
            onAction={() => void goals.reload()}
          />
        ) : null}

        {activeIndicators.length === 0 ? (
          <InfoState
            title="Cadastre indicadores antes de criar metas"
            description="As metas dependem do catálogo estrutural do departamento."
          />
        ) : goals.loading ? (
          <div className="si-admin-placeholder">Carregando metas do departamento...</div>
        ) : goals.items.length === 0 ? (
          <InfoState
            title="Nenhuma meta encontrada"
            description="Crie a primeira meta do departamento para o ano selecionado."
            actionLabel="Nova meta"
            onAction={openCreateGoalForm}
          />
        ) : (
          <div className="si-admin-card-list">
            {goals.items.map((item) => (
              <article key={item.id} className="si-admin-card-list__item">
                <div className="si-admin-card-list__content">
                  <strong>{item.indicator_name || item.indicator_id}</strong>
                  <p>
                    {item.goal_label} · {item.goal_value} ·{" "}
                    {getGoalPeriodicityLabel(item.goal_periodicity)}
                  </p>
                  <small>
                    Ano {item.goal_year} · Versão {item.version} ·{" "}
                    {item.is_active ? "Ativa" : "Inativa"}
                  </small>
                </div>

                <ActionButtons
                  onEdit={() => openEditGoalForm(item)}
                  onHistory={() => void goals.loadHistory(item.indicator_id, item.goal_year)}
                  onActivate={!item.is_active ? () => void goals.activateGoal(item.id) : undefined}
                  onDeactivate={item.is_active ? () => void goals.deactivateGoal(item.id) : undefined}
                  disabled={goals.saving}
                />
              </article>
            ))}
          </div>
        )}

        {goals.historyItems.length > 0 ? (
          <div className="si-goals-history-panel">
            <h4>Histórico da meta</h4>
            <div className="si-goals-history-panel__list">
              {goals.historyItems.map((item) => (
                <div key={item.id} className="si-goals-history-panel__item">
                  <strong>
                    {item.indicator_name || item.indicator_id} · Ano {item.goal_year} · v
                    {item.version}
                  </strong>
                  <span>
                    {item.goal_label} · {item.goal_value} ·{" "}
                    {getGoalPeriodicityLabel(item.goal_periodicity)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        ) : null}
      </SectionBlock>

      <Modal
        open={goalFormOpen}
        onClose={() => setGoalFormOpen(false)}
        title={goalFormMode === "create" ? "Nova meta analítica" : "Editar meta analítica"}
        description="Cadastre ou ajuste a meta do indicador para o ano selecionado."
        size="lg"
        footer={
          <>
            <button
              type="button"
              className="si-settings-editor__button si-settings-editor__button--secondary"
              onClick={() => setGoalFormOpen(false)}
            >
              Cancelar
            </button>
            <button
              type="button"
              className="si-settings-editor__button"
              onClick={() => void handleSubmitGoalForm()}
              disabled={goals.saving || (goalFormMode === "create" && !goalForm.indicator_id)}
            >
              {goals.saving ? "Salvando..." : "Salvar"}
            </button>
          </>
        }
      >
        <div className="si-admin-form-grid">
          <label className="si-admin-form-field">
            <span>Indicador</span>
            <select
              value={goalForm.indicator_id}
              disabled={goalFormMode === "edit"}
              onChange={(event) =>
                setGoalForm((current) => ({
                  ...current,
                  indicator_id: event.target.value,
                }))
              }
            >
              <option value="">Selecione um indicador</option>
              {activeIndicators.map((item) => (
                <option key={item.indicator_id} value={item.indicator_id}>
                  {item.indicator_name}
                </option>
              ))}
            </select>
          </label>

          <label className="si-admin-form-field">
            <span>Ano</span>
            <input
              type="number"
              value={goalForm.goal_year}
              disabled={goalFormMode === "edit"}
              onChange={(event) =>
                setGoalForm((current) => ({
                  ...current,
                  goal_year: Number(event.target.value || new Date().getFullYear()),
                }))
              }
            />
          </label>

          <label className="si-admin-form-field si-admin-form-field--full">
            <span>Label da meta</span>
            <input
              value={goalForm.goal_label}
              onChange={(event) =>
                setGoalForm((current) => ({
                  ...current,
                  goal_label: event.target.value,
                }))
              }
            />
          </label>

          <label className="si-admin-form-field">
            <span>Valor</span>
            <input
              type="number"
              value={goalForm.goal_value}
              onChange={(event) =>
                setGoalForm((current) => ({
                  ...current,
                  goal_value: Number(event.target.value || 0),
                }))
              }
            />
          </label>

          <label className="si-admin-form-field">
            <span>Periodicidade</span>
            <select
              value={goalForm.goal_periodicity}
              onChange={(event) =>
                setGoalForm((current) => ({
                  ...current,
                  goal_periodicity: event.target.value as GoalPeriodicity,
                }))
              }
            >
              <option value="annual">Anual</option>
              <option value="monthly">Mensal</option>
              <option value="quarterly">Trimestral</option>
              <option value="weekly">Semanal</option>
            </select>
          </label>

          <label className="si-admin-form-field">
            <span>Válido de</span>
            <input
              type="date"
              value={goalForm.valid_from}
              onChange={(event) =>
                setGoalForm((current) => ({
                  ...current,
                  valid_from: event.target.value,
                }))
              }
            />
          </label>

          <label className="si-admin-form-field">
            <span>Válido até</span>
            <input
              type="date"
              value={goalForm.valid_to}
              onChange={(event) =>
                setGoalForm((current) => ({
                  ...current,
                  valid_to: event.target.value,
                }))
              }
            />
          </label>

          <label className="si-admin-form-field si-admin-form-field--full">
            <span>Notas</span>
            <textarea
              rows={4}
              value={goalForm.notes}
              onChange={(event) =>
                setGoalForm((current) => ({
                  ...current,
                  notes: event.target.value,
                }))
              }
            />
          </label>
        </div>
      </Modal>
    </>
  );
}