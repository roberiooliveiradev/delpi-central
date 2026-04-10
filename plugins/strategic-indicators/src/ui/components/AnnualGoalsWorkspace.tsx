import { useMemo, useState } from "react";
import type {
  BulkCreateStrategicIndicatorGoalsRequest,
  DuplicateStrategicIndicatorGoalsYearRequest,
  FillMissingStrategicIndicatorGoalsRequest,
} from "../../data/types/indicatorGoals";
import { useStrategicIndicatorGoals } from "../../state/hooks/useStrategicIndicatorGoals";
import { useStrategicIndicatorsGoalYearsOverview } from "../../state/hooks/useStrategicIndicatorsGoalYearsOverview";
import { InfoState } from "./InfoState";
import { Modal } from "./Modal";
import { SectionBlock } from "./SectionBlock";

type AnnualGoalsWorkspaceProps = {
  getAccessToken?: () => string | undefined;
};

type BulkGoalRow = {
  indicator_id: string;
  goal_label: string;
  goal_value: number;
  goal_periodicity: "monthly" | "annual" | "quarterly" | "weekly";
};

const emptyBulkRow: BulkGoalRow = {
  indicator_id: "",
  goal_label: "",
  goal_value: 0,
  goal_periodicity: "monthly",
};

export function AnnualGoalsWorkspace({
  getAccessToken,
}: AnnualGoalsWorkspaceProps) {
  const goals = useStrategicIndicatorGoals({ getAccessToken });
  const yearsOverview = useStrategicIndicatorsGoalYearsOverview({ getAccessToken });

  const [bulkModalOpen, setBulkModalOpen] = useState(false);
  const [duplicateModalOpen, setDuplicateModalOpen] = useState(false);
  const [fillMissingModalOpen, setFillMissingModalOpen] = useState(false);

  const [bulkGoalYear, setBulkGoalYear] = useState<number>(
    typeof goals.selectedGoalYear === "number"
      ? goals.selectedGoalYear
      : new Date().getFullYear(),
  );
  const [bulkRows, setBulkRows] = useState<BulkGoalRow[]>([emptyBulkRow]);

  const [sourceYear, setSourceYear] = useState<number>(new Date().getFullYear());
  const [targetYear, setTargetYear] = useState<number>(new Date().getFullYear() + 1);
  const [overwriteExisting, setOverwriteExisting] = useState(false);

  const [fillGoalYear, setFillGoalYear] = useState<number>(new Date().getFullYear());
  const [copyFromYear, setCopyFromYear] = useState<number | "">(new Date().getFullYear() - 1);

  const selectedYearLabel = useMemo(() => {
    return typeof goals.selectedGoalYear === "number"
      ? String(goals.selectedGoalYear)
      : "Todos";
  }, [goals.selectedGoalYear]);

  async function handleSubmitBulkCreate() {
    const payload: BulkCreateStrategicIndicatorGoalsRequest = {
      goal_year: bulkGoalYear,
      items: bulkRows
        .filter((item) => item.indicator_id.trim() && item.goal_label.trim())
        .map((item) => ({
          indicator_id: item.indicator_id.trim(),
          goal_label: item.goal_label.trim(),
          goal_value: Number(item.goal_value || 0),
          goal_periodicity: item.goal_periodicity,
        })),
    };

    await goals.bulkCreateGoals(payload);
    await yearsOverview.reload();
    setBulkModalOpen(false);
  }

  async function handleSubmitDuplicateYear() {
    const payload: DuplicateStrategicIndicatorGoalsYearRequest = {
      source_year: sourceYear,
      target_year: targetYear,
      overwrite_existing: overwriteExisting,
    };

    await goals.duplicateGoalsYear(payload);
    await yearsOverview.reload();
    setDuplicateModalOpen(false);
  }

  async function handleSubmitFillMissing() {
    const payload: FillMissingStrategicIndicatorGoalsRequest = {
      goal_year: fillGoalYear,
      copy_from_year: typeof copyFromYear === "number" ? copyFromYear : null,
    };

    await goals.fillMissingGoals(payload);
    await yearsOverview.reload();
    setFillMissingModalOpen(false);
  }

  return (
    <div className="si-admin-workspace">
      <SectionBlock
        title="Ciclos anuais de metas"
        description="Gerencie metas analíticas por ano, com visão consolidada e ações em lote."
      >
        <div className="si-goals-overview-grid">
          {yearsOverview.loading ? (
            <div className="si-admin-placeholder">Carregando visão anual...</div>
          ) : yearsOverview.items.length === 0 ? (
            <InfoState
              title="Nenhum ciclo anual disponível"
              description="As metas analíticas ainda não possuem anos cadastrados."
            />
          ) : (
            yearsOverview.items.map((item) => (
              <article key={item.goal_year} className="si-goals-overview-card">
                <span className="si-goals-overview-card__label">Ano</span>
                <strong className="si-goals-overview-card__value">{item.goal_year}</strong>
                <p>Indicadores ativos: {item.total_active_indicators}</p>
                <p>Versões ativas: {item.total_active_versions}</p>
              </article>
            ))
          )}
        </div>
      </SectionBlock>

      <SectionBlock
        title="Operações em lote"
        description="Use ações administrativas para acelerar a preparação anual das metas."
      >
        {!!goals.successMessage ? (
          <div className="si-settings-editor__alert si-settings-editor__alert--success">
            {goals.successMessage}
          </div>
        ) : null}

        {goals.error ? (
          <InfoState
            title="Falha ao processar metas"
            description={goals.error}
            actionLabel="Recarregar"
            onAction={() => void goals.reload()}
          />
        ) : null}

        <div className="si-admin-batch-actions">
          <button
            type="button"
            className="si-settings-editor__button"
            onClick={() => setBulkModalOpen(true)}
          >
            Criar metas em lote
          </button>

          <button
            type="button"
            className="si-settings-editor__button si-settings-editor__button--secondary"
            onClick={() => setDuplicateModalOpen(true)}
          >
            Duplicar metas entre anos
          </button>

          <button
            type="button"
            className="si-settings-editor__button si-settings-editor__button--secondary"
            onClick={() => setFillMissingModalOpen(true)}
          >
            Preencher metas faltantes
          </button>
        </div>
      </SectionBlock>

      <SectionBlock
        title="Metas carregadas"
        description={`Listagem atual filtrada para o ano ${selectedYearLabel}.`}
        aside={
          <div className="si-goals-filter-row">
            <label className="si-admin-form-field si-admin-form-field--compact">
              <span>Ano</span>
              <input
                type="number"
                value={goals.selectedGoalYear}
                onChange={(event) =>
                  goals.setSelectedGoalYear(Number(event.target.value || new Date().getFullYear()))
                }
              />
            </label>

            <label className="si-admin-form-field si-admin-form-field--compact">
              <span>Departamento</span>
              <input
                value={goals.selectedDepartmentId}
                onChange={(event) => goals.setSelectedDepartmentId(event.target.value)}
                placeholder="financial, hr..."
              />
            </label>

            <label className="si-admin-form-field si-admin-form-field--compact">
              <span>Indicador</span>
              <input
                value={goals.selectedIndicatorId}
                onChange={(event) => goals.setSelectedIndicatorId(event.target.value)}
                placeholder="financial-ebitda..."
              />
            </label>
          </div>
        }
      >
        {goals.loading ? (
          <div className="si-admin-placeholder">Carregando metas analíticas...</div>
        ) : goals.items.length === 0 ? (
          <InfoState
            title="Nenhuma meta encontrada"
            description="Ajuste os filtros ou utilize uma das operações em lote para iniciar a configuração anual."
          />
        ) : (
          <div className="si-goals-list">
            {goals.items.map((item) => (
              <article key={item.id} className="si-goals-list__item">
                <div>
                  <strong>{item.indicator_id}</strong>
                  <p>
                    {item.goal_label} · {item.goal_value} · {item.goal_periodicity}
                  </p>
                </div>

                <div className="si-goals-list__meta">
                  <span>Ano {item.goal_year}</span>
                  <span>Versão {item.version}</span>
                  <span>{item.is_active ? "Ativa" : "Inativa"}</span>
                </div>

                <div className="si-goals-list__actions">
                  {!item.is_active ? (
                    <button
                      type="button"
                      className="si-settings-editor__button si-settings-editor__button--secondary"
                      onClick={() => void goals.activateGoal(item.id)}
                    >
                      Ativar
                    </button>
                  ) : null}

                  <button
                    type="button"
                    className="si-settings-editor__button si-settings-editor__button--secondary"
                    onClick={() => void goals.deactivateGoal(item.id)}
                  >
                    Desativar
                  </button>

                  <button
                    type="button"
                    className="si-settings-editor__button si-settings-editor__button--secondary"
                    onClick={() => void goals.loadHistory(item.indicator_id, item.goal_year)}
                  >
                    Histórico
                  </button>
                </div>
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

      <Modal
        open={bulkModalOpen}
        onClose={() => setBulkModalOpen(false)}
        title="Criar metas em lote"
        description="Cadastre várias metas para um mesmo ano em uma única operação."
        size="lg"
      >
        <div className="si-admin-form-grid">
          <label className="si-admin-form-field">
            <span>Ano</span>
            <input
              type="number"
              value={bulkGoalYear}
              onChange={(event) => setBulkGoalYear(Number(event.target.value || 0))}
            />
          </label>

          <div className="si-admin-form-field si-admin-form-field--full">
            <span>Itens</span>

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
                            ? { ...item, goal_value: Number(event.target.value || 0) }
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
                                goal_periodicity: event.target.value as BulkGoalRow["goal_periodicity"],
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
        </div>

        <div className="si-admin-modal-actions">
          <button
            type="button"
            className="si-settings-editor__button si-settings-editor__button--secondary"
            onClick={() => setBulkModalOpen(false)}
          >
            Cancelar
          </button>
          <button
            type="button"
            className="si-settings-editor__button"
            onClick={() => void handleSubmitBulkCreate()}
            disabled={goals.saving}
          >
            {goals.saving ? "Salvando..." : "Criar em lote"}
          </button>
        </div>
      </Modal>

      <Modal
        open={duplicateModalOpen}
        onClose={() => setDuplicateModalOpen(false)}
        title="Duplicar metas entre anos"
        description="Copie as metas ativas de um ano-base para um novo ciclo anual."
        size="md"
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

          <label className="si-admin-form-field">
            <span>Ano de destino</span>
            <input
              type="number"
              value={targetYear}
              onChange={(event) => setTargetYear(Number(event.target.value || 0))}
            />
          </label>

          <label className="si-admin-form-field si-admin-form-field--full">
            <span>
              <input
                type="checkbox"
                checked={overwriteExisting}
                onChange={(event) => setOverwriteExisting(event.target.checked)}
              />{" "}
              Sobrescrever metas ativas já existentes no ano de destino
            </span>
          </label>
        </div>

        <div className="si-admin-modal-actions">
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
            onClick={() => void handleSubmitDuplicateYear()}
            disabled={goals.saving}
          >
            {goals.saving ? "Processando..." : "Duplicar"}
          </button>
        </div>
      </Modal>

      <Modal
        open={fillMissingModalOpen}
        onClose={() => setFillMissingModalOpen(false)}
        title="Preencher metas faltantes"
        description="Crie metas ausentes de um ano usando outro ciclo como referência."
        size="md"
      >
        <div className="si-admin-form-grid">
          <label className="si-admin-form-field">
            <span>Ano alvo</span>
            <input
              type="number"
              value={fillGoalYear}
              onChange={(event) => setFillGoalYear(Number(event.target.value || 0))}
            />
          </label>

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
        </div>

        <div className="si-admin-modal-actions">
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
            onClick={() => void handleSubmitFillMissing()}
            disabled={goals.saving}
          >
            {goals.saving ? "Processando..." : "Preencher"}
          </button>
        </div>
      </Modal>
    </div>
  );
}