import { useEffect, useState } from "react";
import { Modal } from "./Modal";
import { SectionBlock } from "./SectionBlock";
import { InfoState } from "./InfoState";
import { ActionButtons } from "./ActionButtons";
import { useStrategicIndicatorGoals } from "../../state/hooks/useStrategicIndicatorGoals";
import type {
  DuplicateStrategicIndicatorGoalsYearRequest,
  FillMissingStrategicIndicatorGoalsRequest,
} from "../../data/types/indicatorGoals";

type GoalYearManagementModalProps = {
  open: boolean;
  goalYear: number | null;
  onClose: () => void;
  getAccessToken?: () => string | undefined;
};

export function GoalYearManagementModal({
  open,
  goalYear,
  onClose,
  getAccessToken,
}: GoalYearManagementModalProps) {
  const goals = useStrategicIndicatorGoals({
    getAccessToken,
    initialGoalYear: goalYear ?? new Date().getFullYear(),
  });

  const [duplicateModalOpen, setDuplicateModalOpen] = useState(false);
  const [fillMissingModalOpen, setFillMissingModalOpen] = useState(false);
  const [sourceYear, setSourceYear] = useState<number>(new Date().getFullYear() - 1);
  const [overwriteExisting, setOverwriteExisting] = useState(false);
  const [copyFromYear, setCopyFromYear] = useState<number>(new Date().getFullYear() - 1);

  useEffect(() => {
    if (typeof goalYear === "number") {
      goals.setSelectedGoalYear(goalYear);
    }
  }, [goalYear]);

  async function handleDuplicateYear() {
    if (typeof goalYear !== "number") return;

    const payload: DuplicateStrategicIndicatorGoalsYearRequest = {
      source_year: sourceYear,
      target_year: goalYear,
      overwrite_existing: overwriteExisting,
    };

    await goals.duplicateGoalsYear(payload);
    setDuplicateModalOpen(false);
  }

  async function handleFillMissingYear() {
    if (typeof goalYear !== "number") return;

    const payload: FillMissingStrategicIndicatorGoalsRequest = {
      goal_year: goalYear,
      copy_from_year: copyFromYear,
    };

    await goals.fillMissingGoals(payload);
    setFillMissingModalOpen(false);
  }

  return (
    <>
      <Modal
        open={open}
        onClose={onClose}
        title={goalYear ? `Ciclo anual: ${goalYear}` : "Ciclo anual"}
        description="Gestão completa das metas do ano selecionado."
        size="xl"
      >
        <div className="si-goal-year-workspace">
          <SectionBlock
            title={`Ano ${goalYear ?? "—"}`}
            description="Visão consolidada das metas do ciclo anual."
            aside={
              <div className="si-admin-inline-actions">
                <button
                  type="button"
                  className="si-settings-editor__button si-settings-editor__button--secondary"
                  onClick={() => setDuplicateModalOpen(true)}
                >
                  Duplicar de outro ano
                </button>
                <button
                  type="button"
                  className="si-settings-editor__button si-settings-editor__button--secondary"
                  onClick={() => setFillMissingModalOpen(true)}
                >
                  Preencher faltantes
                </button>
              </div>
            }
          >
            <div className="si-admin-detail-grid">
              <div className="si-admin-detail-card">
                <span className="si-admin-detail-card__label">Ano</span>
                <strong>{goalYear ?? "—"}</strong>
              </div>
              <div className="si-admin-detail-card">
                <span className="si-admin-detail-card__label">Metas carregadas</span>
                <strong>{goals.items.length}</strong>
              </div>
            </div>
          </SectionBlock>

          <SectionBlock
            title="Filtros internos"
            description="Refine a visualização das metas do ano."
          >
            <div className="si-admin-form-grid">
              <label className="si-admin-form-field">
                <span>Departamento</span>
                <input
                  value={goals.selectedDepartmentId}
                  onChange={(event) => goals.setSelectedDepartmentId(event.target.value)}
                  placeholder="financial, hr..."
                />
              </label>

              <label className="si-admin-form-field">
                <span>Indicador</span>
                <input
                  value={goals.selectedIndicatorId}
                  onChange={(event) => goals.setSelectedIndicatorId(event.target.value)}
                  placeholder="financial-ebitda..."
                />
              </label>
            </div>
          </SectionBlock>

          <SectionBlock
            title="Metas do ano"
            description="Listagem filtrada das metas do ciclo."
          >
            {goals.error ? (
              <InfoState
                title="Falha ao carregar metas do ano"
                description={goals.error}
                actionLabel="Recarregar"
                onAction={() => void goals.reload()}
              />
            ) : goals.loading ? (
              <div className="si-admin-placeholder">Carregando metas...</div>
            ) : goals.items.length === 0 ? (
              <InfoState
                title="Nenhuma meta encontrada"
                description="Não há metas para o filtro atual."
              />
            ) : (
              <div className="si-admin-card-list">
                {goals.items.map((item) => (
                  <article key={item.id} className="si-admin-card-list__item">
                    <div className="si-admin-card-list__content">
                      <strong>{item.indicator_id}</strong>
                      <p>
                        {item.goal_label} · {item.goal_value} · {item.goal_periodicity}
                      </p>
                      <small>
                        Versão {item.version} · {item.is_active ? "Ativa" : "Inativa"}
                      </small>
                    </div>

                    <ActionButtons
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
                        Ano {item.goal_year} · v{item.version}
                      </strong>
                      <span>
                        {item.goal_label} · {item.goal_value} · {item.goal_periodicity}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}
          </SectionBlock>
        </div>
      </Modal>

      <Modal
        open={duplicateModalOpen}
        onClose={() => setDuplicateModalOpen(false)}
        title="Duplicar metas entre anos"
        description="Copie as metas ativas de um ano-base para este ciclo."
        size="md"
        footer={
          <>
            <button
              type="button"
              className="si-settings-editor__button si-settings-editor__button--secondary"
              onClick={() => setDuplicateModalOpen(false)}
            >
              Cancelar
            </button>
            <button
              type="button"
              className="si-settings-editor__button"
              onClick={() => void handleDuplicateYear()}
              disabled={goals.saving}
            >
              {goals.saving ? "Processando..." : "Duplicar"}
            </button>
          </>
        }
      >
        <div className="si-admin-form-grid">
          <label className="si-admin-form-field">
            <span>Ano de origem</span>
            <input
              type="number"
              value={sourceYear}
              onChange={(event) => setSourceYear(Number(event.target.value || 0))}
            />
          </label>

          <label className="si-admin-form-field si-admin-form-field--full">
            <span>
              <input
                type="checkbox"
                checked={overwriteExisting}
                onChange={(event) => setOverwriteExisting(event.target.checked)}
              />{" "}
              Sobrescrever metas existentes no ano de destino
            </span>
          </label>
        </div>
      </Modal>

      <Modal
        open={fillMissingModalOpen}
        onClose={() => setFillMissingModalOpen(false)}
        title="Preencher metas faltantes"
        description="Crie metas ausentes deste ano usando outro ciclo como referência."
        size="md"
        footer={
          <>
            <button
              type="button"
              className="si-settings-editor__button si-settings-editor__button--secondary"
              onClick={() => setFillMissingModalOpen(false)}
            >
              Cancelar
            </button>
            <button
              type="button"
              className="si-settings-editor__button"
              onClick={() => void handleFillMissingYear()}
              disabled={goals.saving}
            >
              {goals.saving ? "Processando..." : "Preencher"}
            </button>
          </>
        }
      >
        <div className="si-admin-form-grid">
          <label className="si-admin-form-field">
            <span>Copiar de</span>
            <input
              type="number"
              value={copyFromYear}
              onChange={(event) => setCopyFromYear(Number(event.target.value || 0))}
            />
          </label>
        </div>
      </Modal>
    </>
  );
}