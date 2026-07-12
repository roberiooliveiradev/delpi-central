import { useEffect, useMemo, useState } from "react";
import { SectionBlock } from "./SectionBlock";
import { InfoState } from "./InfoState";
import { Modal } from "./Modal";
import { ActionButtons } from "./ActionButtons";
import { IndicatorGoalForm } from "./IndicatorGoalForm";
import { useStrategicIndicatorGoals } from "../../state/hooks/useStrategicIndicatorGoals";
import type { StrategicIndicatorGoalItem } from "../../data/types/indicatorGoals";
import type { AdminDepartmentIndicatorItem } from "../../data/types/settings";
import { SiNativeTextControl } from "./siNativeFormFields";
import "./DepartmentGoalsPanel.css";

type DepartmentGoalsPanelProps = {
  departmentId: string;
  getAccessToken?: () => string | undefined;
  indicators: AdminDepartmentIndicatorItem[];
};

function getGoalPeriodicityLabel(value: string): string {
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

function getGoalModeLabel(value: string): string {
  return value === "monthly_curve" ? "Curva" : "Padrão";
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
  const [editingGoal, setEditingGoal] =
    useState<StrategicIndicatorGoalItem | null>(null);

  useEffect(() => {
    goals.setSelectedDepartmentId(departmentId);
    goals.setSelectedIndicatorId("");
  }, [departmentId]);

  const activeIndicators = useMemo(
    () => indicators.filter((item) => item.is_active),
    [indicators],
  );

  const indicatorOptions = useMemo(
    () =>
      activeIndicators.map((item) => ({
        value: item.indicator_id,
        label: item.indicator_name,
      })),
    [activeIndicators],
  );

  function openCreateGoalForm() {
    setEditingGoal(null);
    setGoalFormOpen(true);
  }

  function openEditGoalForm(item: StrategicIndicatorGoalItem) {
    setEditingGoal(item);
    setGoalFormOpen(true);
  }

  async function handleCreate(payload: any) {
    await goals.createGoal(payload);
    setGoalFormOpen(false);
  }

  async function handleUpdate(goalId: string, payload: any) {
    await goals.updateGoal(goalId, payload);
    setGoalFormOpen(false);
    setEditingGoal(null);
  }

  return (
    <>
      <SectionBlock
        title="Metas do departamento por ano"
        description="Gerencie as metas dos indicadores estruturais deste departamento. Indicadores sazonais podem usar curva mensal."
        aside={
          <div className="si-admin-inline-actions">
            <label className="si-admin-form-field si-admin-form-field--compact">
              <span>Ano</span>
              <SiNativeTextControl
                type="number"
                value={goals.selectedGoalYear}
                onChange={(value) =>
                  goals.setSelectedGoalYear(
                    Number(value || new Date().getFullYear()),
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
          <div className="si-admin-placeholder">
            Carregando metas do departamento...
          </div>
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
                    {item.goal_label} ·{" "}
                    {getGoalPeriodicityLabel(item.goal_periodicity)} ·{" "}
                    {getGoalModeLabel(item.goal_mode)}
                  </p>
                  <small>
                    Ano {item.goal_year} · Versão {item.version} ·{" "}
                    {item.is_active ? "Ativa" : "Inativa"}
                  </small>
                </div>

                <ActionButtons
                  onEdit={() => openEditGoalForm(item)}
                  onHistory={() =>
                    void goals.loadHistory(item.indicator_id, item.goal_year)
                  }
                  onActivate={
                    !item.is_active
                      ? () => void goals.activateGoal(item.id)
                      : undefined
                  }
                  onDeactivate={
                    item.is_active
                      ? () => void goals.deactivateGoal(item.id)
                      : undefined
                  }
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
                    {item.indicator_name || item.indicator_id} · Ano{" "}
                    {item.goal_year} · v{item.version}
                  </strong>
                  <span>
                    {item.goal_label} ·{" "}
                    {getGoalPeriodicityLabel(item.goal_periodicity)} ·{" "}
                    {getGoalModeLabel(item.goal_mode)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        ) : null}
      </SectionBlock>

      <Modal
        open={goalFormOpen}
        onClose={() => {
          setGoalFormOpen(false);
          setEditingGoal(null);
        }}
        title={editingGoal ? "Editar meta analítica" : "Nova meta analítica"}
        description="Cadastre ou ajuste a meta do indicador para o ano selecionado."
        size="lg"
        initialFocusSelector="select, input, textarea"
      >
        <IndicatorGoalForm
          saving={goals.saving}
          initialValue={editingGoal}
          indicatorOptions={indicatorOptions}
          onCreate={handleCreate}
          onUpdate={handleUpdate}
          onCancel={() => {
            setGoalFormOpen(false);
            setEditingGoal(null);
          }}
        />
      </Modal>
    </>
  );
}