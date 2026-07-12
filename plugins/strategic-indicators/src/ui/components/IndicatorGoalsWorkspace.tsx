import { useMemo, useState } from "react";
import { InfoState } from "./InfoState";
import { IndicatorGoalForm } from "./IndicatorGoalForm";
import { Modal } from "./Modal";
import { DataTable } from "./DataTable";
import { ActionButtons } from "./ActionButtons";
import { useStrategicIndicatorGoals } from "../../state/hooks/useStrategicIndicatorGoals";
import type { StrategicIndicatorGoalItem } from "../../data/types/indicatorGoals";
import {
  formatAdminGoalMeta,
  formatAdminGoalValueOnly,
} from "../utils/goalValuePolicy";
import "./IndicatorGoalsWorkspace.css";
import { SiSelectControl } from "./siFiltersUi";
import { SiNativeTextControl } from "./siNativeFormFields";

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

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<StrategicIndicatorGoalItem | null>(null);
  const [historyContext, setHistoryContext] = useState<{
    indicatorId: string;
    goalYear?: number;
  } | null>(null);

  const indicatorOptions = useMemo(() => {
    return Array.from(new Set(items.map((item) => item.indicator_id))).sort();
  }, [items]);

  const columns = useMemo(
    () => [
      {
        key: "indicator",
        header: "Indicador",
        render: (row: StrategicIndicatorGoalItem) => row.indicator_id,
      },
      {
        key: "year",
        header: "Ano",
        render: (row: StrategicIndicatorGoalItem) => row.goal_year,
      },
      {
        key: "version",
        header: "Versão",
        render: (row: StrategicIndicatorGoalItem) => row.version,
      },
      {
        key: "label",
        header: "Meta",
        render: (row: StrategicIndicatorGoalItem) => row.goal_label,
      },
      {
        key: "value",
        header: "Valor",
        render: (row: StrategicIndicatorGoalItem) =>
          formatAdminGoalValueOnly(row),
      },
      {
        key: "periodicity",
        header: "Periodicidade",
        render: (row: StrategicIndicatorGoalItem) =>
          translatePeriodicity(row.goal_periodicity),
      },
      {
        key: "status",
        header: "Situação",
        render: (row: StrategicIndicatorGoalItem) => (
          <span
            className={`si-goal-status-badge ${
              row.is_active
                ? "si-goal-status-badge--active"
                : "si-goal-status-badge--inactive"
            }`}
          >
            {row.is_active ? "Ativa" : "Inativa"}
          </span>
        ),
      },
      {
        key: "actions",
        header: "Ações",
        render: (row: StrategicIndicatorGoalItem) => (
          <ActionButtons
            disabled={saving}
            onEdit={() => setEditingItem(row)}
            onHistory={() => void handleOpenHistory(row.indicator_id, row.goal_year)}
            onActivate={!row.is_active ? () => void activateGoal(row.id) : undefined}
            onDeactivate={row.is_active ? () => void deactivateGoal(row.id) : undefined}
          />
        ),
      },
    ],
    [saving, activateGoal, deactivateGoal],
  );

  async function handleOpenHistory(indicatorId: string, goalYear?: number) {
    setHistoryContext({ indicatorId, goalYear });
    await loadHistory(indicatorId, goalYear);
  }

  async function handleCreate(payload: any) {
    await createGoal(payload);
    setIsCreateModalOpen(false);
  }

  async function handleUpdate(goalId: string, payload: any) {
    await updateGoal(goalId, payload);
    setEditingItem(null);
  }

  return (
    <section className="si-settings-goals-shell" aria-label="Metas analíticas">
      {successMessage ? (
        <InfoState
          title="Metas analíticas atualizadas"
          description={successMessage}
          actionLabel="Fechar aviso"
          onAction={clearSuccessMessage}
        />
      ) : null}

      {error ? (
        <InfoState
          title="Falha ao carregar metas analíticas"
          description={error}
          actionLabel="Tentar novamente"
          onAction={() => void reload()}
        />
      ) : null}

      <div className="si-goals-toolbar">
        <div className="si-goals-toolbar__filters">
          <label className="si-settings-form-field">
            <span className="si-settings-form-field__label">
              Filtrar por indicador
            </span>
            <SiSelectControl
              value={selectedIndicatorId}
              onChange={setSelectedIndicatorId}
              allowEmpty
              emptyLabel="Todos"
              options={indicatorOptions.map((indicatorId) => ({
                value: indicatorId,
                label: indicatorId,
              }))}
            />
          </label>

          <label className="si-settings-form-field">
            <span className="si-settings-form-field__label">Ano da meta</span>
            <SiNativeTextControl
              type="number"
              value={selectedGoalYear}
              onChange={(value) =>
                setSelectedGoalYear(value ? Number(value) : "")
              }
            />
          </label>
        </div>

        <div className="si-goals-toolbar__actions">
          <div className="si-settings-editor__summary">
            <span>Registros</span>
            <strong>{items.length}</strong>
          </div>

          <button
            type="button"
            className="si-settings-editor__button"
            onClick={() => setIsCreateModalOpen(true)}
          >
            Nova meta
          </button>
        </div>
      </div>

      {refreshing ? (
        <InfoState
          title="Atualizando metas analíticas"
          description="Os registros estão sendo recarregados sem sair da página."
        />
      ) : null}

      <DataTable
        columns={columns}
        rows={items}
        loading={loading}
        emptyText="Nenhuma meta analítica encontrada para os filtros selecionados."
        getRowKey={(row) => row.id}
      />

      <Modal
        open={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Criar meta analítica"
        description="Cadastre uma nova meta versionada por indicador e ano."
        size="lg"
        initialFocusSelector="select, input"
      >
        <IndicatorGoalForm
          saving={saving}
          indicatorOptions={indicatorOptions}
          onCreate={handleCreate}
          onCancel={() => setIsCreateModalOpen(false)}
        />
      </Modal>

      <Modal
        open={!!editingItem}
        onClose={() => setEditingItem(null)}
        title="Editar meta analítica"
        description="Atualize os dados da versão selecionada."
        size="lg"
        initialFocusSelector="input, select, textarea"
      >
        <IndicatorGoalForm
          saving={saving}
          initialValue={editingItem}
          indicatorOptions={indicatorOptions}
          onUpdate={handleUpdate}
          onCancel={() => setEditingItem(null)}
        />
      </Modal>

      <Modal
        open={!!historyContext}
        onClose={() => setHistoryContext(null)}
        title="Histórico da meta"
        description="Versões registradas para o indicador e ano selecionados."
        size="lg"
      >
        {historyError ? (
          <InfoState
            title="Falha ao carregar histórico"
            description={historyError}
          />
        ) : historyLoading ? (
          <InfoState
            title="Carregando histórico"
            description="As versões anteriores estão sendo carregadas."
          />
        ) : historyItems.length === 0 ? (
          <InfoState
            title="Sem histórico disponível"
            description="Nenhuma versão foi encontrada para este contexto."
          />
        ) : (
          <div className="si-history-list">
            {historyItems.map((item) => (
              <article key={item.id} className="si-history-card">
                <div className="si-history-card__top">
                  <strong className="si-history-card__title">
                    {item.indicator_id} • {item.goal_year}
                  </strong>
                  <span className="si-history-card__badge">
                    Versão {item.version}
                  </span>
                </div>

                <div className="si-history-card__meta">
                  <span>Meta: {formatAdminGoalMeta(item)}</span>
                  <span>Valor: {formatAdminGoalValueOnly(item)}</span>
                  <span>
                    Periodicidade: {translatePeriodicity(item.goal_periodicity)}
                  </span>
                  <span>Situação: {item.is_active ? "Ativa" : "Inativa"}</span>
                  <span>Atualizado em: {formatDateTime(item.updated_at)}</span>
                  <span>Atualizado por: {item.updated_by_email ?? item.updated_by_user_id ?? "-"}</span>
                </div>
              </article>
            ))}
          </div>
        )}
      </Modal>
    </section>
  );
}

function translatePeriodicity(value: string) {
  switch (value) {
    case "monthly":
      return "Mensal";
    case "annual":
      return "Anual";
    case "quarterly":
      return "Trimestral";
    case "weekly":
      return "Semanal";
    default:
      return value;
  }
}

function formatDateTime(value: string) {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;

  return parsed.toLocaleString("pt-BR");
}