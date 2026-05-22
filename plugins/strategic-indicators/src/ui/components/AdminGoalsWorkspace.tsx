import { useEffect, useMemo, useState } from "react";
import { fetchAdminDepartmentIndicators } from "../../data/api/strategicIndicatorsSettingsApi";
import { InfoState } from "./InfoState";
import { IndicatorGoalForm } from "./IndicatorGoalForm";
import { DrawerPanel } from "./DrawerPanel";
import { AdminInlineToolPanel } from "./AdminInlineToolPanel";
import { ActiveToggle } from "./ActiveToggle";
import { AnnualGoalsWorkspace } from "./AnnualGoalsWorkspace";
import { useStrategicIndicatorGoals } from "../../state/hooks/useStrategicIndicatorGoals";
import { useStrategicIndicatorsAdminDepartments } from "../../state/hooks/useStrategicIndicatorsAdminDepartments";
import { useStrategicIndicatorsGoalYearsOverview } from "../../state/hooks/useStrategicIndicatorsGoalYearsOverview";
import type {
  DuplicateStrategicIndicatorGoalsYearRequest,
  FillMissingStrategicIndicatorGoalsRequest,
  GoalYearOverviewItem,
  StrategicIndicatorGoalItem,
} from "../../data/types/indicatorGoals";
import {
  getGoalModeLabel,
  getGoalPeriodicityLabel,
  getGoalScopeBranchLabel,
} from "../presentation/labels";
import "./AdminGoalsWorkspace.css";

type AdminGoalsWorkspaceProps = {
  getAccessToken?: () => string | undefined;
};

type BulkToolMode = "create_year" | "duplicate" | "fill" | null;

type CatalogIndicatorOption = {
  indicatorId: string;
  indicatorName: string;
  departmentId: string;
  departmentName: string;
};

export function AdminGoalsWorkspace({ getAccessToken }: AdminGoalsWorkspaceProps) {
  const yearsOverview = useStrategicIndicatorsGoalYearsOverview({ getAccessToken });
  const departments = useStrategicIndicatorsAdminDepartments({ getAccessToken });
  const [selectedYear, setSelectedYear] = useState<number | null>(null);
  const [catalogIndicators, setCatalogIndicators] = useState<CatalogIndicatorOption[]>(
    [],
  );
  const [catalogIndicatorsLoading, setCatalogIndicatorsLoading] = useState(false);

  const goals = useStrategicIndicatorGoals({
    getAccessToken,
    initialGoalYear: selectedYear ?? new Date().getFullYear(),
  });

  const [bulkTool, setBulkTool] = useState<BulkToolMode>(null);
  const [goalDrawerOpen, setGoalDrawerOpen] = useState(false);
  const [editingGoal, setEditingGoal] = useState<StrategicIndicatorGoalItem | null>(null);
  const [showHistory, setShowHistory] = useState(false);

  const [sourceYear, setSourceYear] = useState(new Date().getFullYear() - 1);
  const [overwriteExisting, setOverwriteExisting] = useState(false);
  const [copyFromYear, setCopyFromYear] = useState(new Date().getFullYear() - 1);

  useEffect(() => {
    if (typeof selectedYear === "number") {
      goals.setSelectedGoalYear(selectedYear);
    }
  }, [selectedYear]);

  useEffect(() => {
    if (departments.items.length === 0) {
      setCatalogIndicators([]);
      return;
    }

    let cancelled = false;
    setCatalogIndicatorsLoading(true);

    void (async () => {
      try {
        const departmentById = new Map(
          departments.items.map((department) => [
            department.department_id,
            department.department_name,
          ]),
        );

        const responses = await Promise.all(
          departments.items.map((department) =>
            fetchAdminDepartmentIndicators(
              department.department_id,
              getAccessToken,
            ),
          ),
        );

        if (cancelled) return;

        const merged: CatalogIndicatorOption[] = [];
        responses.forEach((response, index) => {
          const department = departments.items[index];
          if (!department) return;

          response.items.forEach((indicator) => {
            merged.push({
              indicatorId: indicator.indicator_id,
              indicatorName: indicator.indicator_name,
              departmentId: department.department_id,
              departmentName:
                departmentById.get(department.department_id) ??
                department.department_name,
            });
          });
        });

        merged.sort((left, right) => {
          const departmentCompare = left.departmentName.localeCompare(
            right.departmentName,
            "pt-BR",
          );
          if (departmentCompare !== 0) return departmentCompare;
          return left.indicatorName.localeCompare(right.indicatorName, "pt-BR");
        });

        setCatalogIndicators(merged);
      } catch {
        if (!cancelled) {
          setCatalogIndicators([]);
        }
      } finally {
        if (!cancelled) {
          setCatalogIndicatorsLoading(false);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [departments.items, getAccessToken]);

  const departmentFilterOptions = useMemo(
    () =>
      [...departments.items].sort((left, right) =>
        left.department_name.localeCompare(right.department_name, "pt-BR"),
      ),
    [departments.items],
  );

  const indicatorFilterOptions = useMemo(() => {
    const departmentId = goals.selectedDepartmentId.trim();
    const pool = departmentId
      ? catalogIndicators.filter((item) => item.departmentId === departmentId)
      : catalogIndicators;

    return pool.map((item) => ({
      value: item.indicatorId,
      label: departmentId
        ? item.indicatorName
        : `${item.indicatorName} · ${item.departmentName}`,
    }));
  }, [catalogIndicators, goals.selectedDepartmentId]);

  const indicatorOptions = useMemo(() => {
    if (indicatorFilterOptions.length > 0) {
      return indicatorFilterOptions;
    }

    const map = new Map<string, string>();
    goals.items.forEach((item) => {
      map.set(item.indicator_id, item.indicator_name || item.indicator_id);
    });
    return Array.from(map.entries()).map(([value, label]) => ({ value, label }));
  }, [indicatorFilterOptions, goals.items]);

  useEffect(() => {
    const selectedId = goals.selectedIndicatorId.trim();
    if (!selectedId) return;

    const stillValid = indicatorFilterOptions.some(
      (option) => option.value === selectedId,
    );
    if (!stillValid) {
      goals.setSelectedIndicatorId("");
    }
  }, [
    goals.selectedIndicatorId,
    goals.setSelectedIndicatorId,
    indicatorFilterOptions,
  ]);

  const selectedYearOverview = useMemo(
    () =>
      yearsOverview.items.find((item) => item.goal_year === selectedYear) ?? null,
    [yearsOverview.items, selectedYear],
  );

  function selectYear(year: number) {
    setSelectedYear(year);
    setBulkTool(null);
    setShowHistory(false);
    setEditingGoal(null);
    setGoalDrawerOpen(false);
  }

  async function handleDuplicateYear() {
    if (typeof selectedYear !== "number") return;

    const payload: DuplicateStrategicIndicatorGoalsYearRequest = {
      source_year: sourceYear,
      target_year: selectedYear,
      overwrite_existing: overwriteExisting,
    };

    await goals.duplicateGoalsYear(payload);
    setBulkTool(null);
    void yearsOverview.reload();
  }

  async function handleFillMissingYear() {
    if (typeof selectedYear !== "number") return;

    const payload: FillMissingStrategicIndicatorGoalsRequest = {
      goal_year: selectedYear,
      copy_from_year: copyFromYear,
    };

    await goals.fillMissingGoals(payload);
    setBulkTool(null);
    void yearsOverview.reload();
  }

  async function handleCreate(payload: Parameters<typeof goals.createGoal>[0]) {
    await goals.createGoal(payload);
    setGoalDrawerOpen(false);
    setEditingGoal(null);
  }

  async function handleUpdate(
    goalId: string,
    payload: Parameters<typeof goals.updateGoal>[1],
  ) {
    await goals.updateGoal(goalId, payload);
    setGoalDrawerOpen(false);
    setEditingGoal(null);
  }

  return (
    <div className="si-admin-workspace si-admin-goals-workspace">
      {goals.successMessage ? (
        <div className="si-settings-editor__alert si-settings-editor__alert--success">
          {goals.successMessage}
        </div>
      ) : null}

      <div className="si-admin-goals-toolbar">
        <p className="si-admin-goals-toolbar__hint">
          Selecione um ano para editar metas no painel ao lado. Formulários abrem em
          gaveta lateral — sem modais empilhados.
        </p>

        <div className="si-admin-goals-toolbar__actions">
          <button
            type="button"
            className="si-settings-editor__button"
            onClick={() => {
              setBulkTool("create_year");
              setSelectedYear(null);
            }}
          >
            Novo ano
          </button>
        </div>
      </div>

      {yearsOverview.error ? (
        <InfoState
          title="Falha ao carregar ciclos anuais"
          description={yearsOverview.error}
          actionLabel="Recarregar"
          onAction={() => void yearsOverview.reload()}
        />
      ) : null}

      {bulkTool === "create_year" ? (
        <AdminInlineToolPanel
          title="Criar novo ciclo anual"
          description="Defina o ano e, se quiser, cadastre metas iniciais em lote."
          open
          onClose={() => setBulkTool(null)}
        >
          <AnnualGoalsWorkspace
            open
            embedded
            mode="create_year"
            fixedTargetYear={null}
            onClose={() => {
              setBulkTool(null);
              void yearsOverview.reload();
            }}
            getAccessToken={getAccessToken}
          />
        </AdminInlineToolPanel>
      ) : null}

      <div className="si-admin-master-detail si-admin-goals-master-detail">
        <div className="si-admin-master-detail__master">
          {yearsOverview.loading ? (
            <div className="si-admin-placeholder">Carregando anos...</div>
          ) : yearsOverview.items.length === 0 ? (
            <InfoState
              title="Nenhum ciclo anual"
              description="Crie o primeiro ano para começar a configurar metas por indicador."
              actionLabel="Novo ano"
              onAction={() => setBulkTool("create_year")}
            />
          ) : (
            <div className="si-admin-list">
              {yearsOverview.items.map((item) => (
                <YearListButton
                  key={item.goal_year}
                  item={item}
                  selected={selectedYear === item.goal_year}
                  onSelect={() => selectYear(item.goal_year)}
                />
              ))}
            </div>
          )}
        </div>

        <div className="si-admin-master-detail__detail">
          {typeof selectedYear !== "number" ? (
            <InfoState
              title="Selecione um ano"
              description="Escolha um ciclo na lista para ver e editar as metas analíticas."
            />
          ) : (
            <>
              <div className="si-admin-detail-card">
                <div className="si-admin-detail-card__header">
                  <div>
                    <h3>Ciclo {selectedYear}</h3>
                    <p>
                      Metas por indicador com escopo consolidado ou por filial (01/02).
                    </p>
                  </div>

                  <div className="si-admin-detail-card__actions">
                    <button
                      type="button"
                      className="si-settings-editor__button"
                      onClick={() => {
                        setEditingGoal(null);
                        setGoalDrawerOpen(true);
                      }}
                    >
                      Nova meta
                    </button>
                    <button
                      type="button"
                      className="si-settings-editor__button si-settings-editor__button--secondary"
                      onClick={() => setBulkTool("duplicate")}
                    >
                      Duplicar ano
                    </button>
                    <button
                      type="button"
                      className="si-settings-editor__button si-settings-editor__button--secondary"
                      onClick={() => setBulkTool("fill")}
                    >
                      Preencher faltantes
                    </button>
                  </div>
                </div>

                <div className="si-admin-detail-card__grid">
                  <div>
                    <span className="si-admin-detail-card__label">Indicadores ativos</span>
                    <strong>{selectedYearOverview?.total_active_indicators ?? "—"}</strong>
                  </div>
                  <div>
                    <span className="si-admin-detail-card__label">Versões ativas</span>
                    <strong>{selectedYearOverview?.total_active_versions ?? "—"}</strong>
                  </div>
                  <div>
                    <span className="si-admin-detail-card__label">Metas carregadas</span>
                    <strong>{goals.items.length}</strong>
                  </div>
                </div>
              </div>

              {bulkTool === "duplicate" ? (
                <AdminInlineToolPanel
                  title="Duplicar metas de outro ano"
                  description={`Copia metas ativas para o ciclo ${selectedYear}.`}
                  open
                  onClose={() => setBulkTool(null)}
                  footer={
                    <>
                      <button
                        type="button"
                        className="si-settings-editor__button si-settings-editor__button--secondary"
                        onClick={() => setBulkTool(null)}
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
                        onChange={(e) => setSourceYear(Number(e.target.value || 0))}
                      />
                    </label>
                    <label className="si-admin-form-field si-admin-form-field--full">
                      <span>
                        <input
                          type="checkbox"
                          checked={overwriteExisting}
                          onChange={(e) => setOverwriteExisting(e.target.checked)}
                        />{" "}
                        Sobrescrever metas existentes em {selectedYear}
                      </span>
                    </label>
                  </div>
                </AdminInlineToolPanel>
              ) : null}

              {bulkTool === "fill" ? (
                <AdminInlineToolPanel
                  title="Preencher metas faltantes"
                  description={`Completa indicadores sem meta ativa em ${selectedYear}.`}
                  open
                  onClose={() => setBulkTool(null)}
                  footer={
                    <>
                      <button
                        type="button"
                        className="si-settings-editor__button si-settings-editor__button--secondary"
                        onClick={() => setBulkTool(null)}
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
                      <span>Copiar estrutura de</span>
                      <input
                        type="number"
                        value={copyFromYear}
                        onChange={(e) => setCopyFromYear(Number(e.target.value || 0))}
                      />
                    </label>
                  </div>
                </AdminInlineToolPanel>
              ) : null}

              <div className="si-admin-goals-filters">
                <label className="si-admin-form-field">
                  <span>Departamento</span>
                  <select
                    value={goals.selectedDepartmentId}
                    disabled={departments.loading}
                    onChange={(event) => {
                      goals.setSelectedDepartmentId(event.target.value);
                      goals.setSelectedIndicatorId("");
                    }}
                  >
                    <option value="">Todos os departamentos</option>
                    {departmentFilterOptions.map((department) => (
                      <option
                        key={department.department_id}
                        value={department.department_id}
                      >
                        {department.department_name}
                        {department.short_name
                          ? ` (${department.short_name})`
                          : ""}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="si-admin-form-field">
                  <span>Indicador</span>
                  <select
                    value={goals.selectedIndicatorId}
                    disabled={catalogIndicatorsLoading || departments.loading}
                    onChange={(event) =>
                      goals.setSelectedIndicatorId(event.target.value)
                    }
                  >
                    <option value="">
                      {catalogIndicatorsLoading
                        ? "Carregando indicadores..."
                        : "Todos os indicadores"}
                    </option>
                    {indicatorFilterOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>
              </div>

              {goals.error ? (
                <InfoState
                  title={
                    goals.loading || goals.items.length === 0
                      ? "Falha ao carregar metas"
                      : "Erro ao salvar ou atualizar meta"
                  }
                  description={goals.error}
                  actionLabel="Recarregar"
                  onAction={() => void goals.reload()}
                />
              ) : goals.loading ? (
                <div className="si-admin-placeholder">Carregando metas...</div>
              ) : goals.items.length === 0 ? (
                <InfoState
                  title="Nenhuma meta neste ano"
                  description="Cadastre a primeira meta para o ciclo selecionado."
                  actionLabel="Nova meta"
                  onAction={() => {
                    setEditingGoal(null);
                    setGoalDrawerOpen(true);
                  }}
                />
              ) : (
                <div className="si-admin-goals-table-scroll">
                <div className="si-admin-goals-table">
                  <div className="si-admin-goals-table__head">
                    <span>Indicador</span>
                    <span>Escopo</span>
                    <span>Meta</span>
                    <span>Modo</span>
                    <span>Situação</span>
                    <span>Ações</span>
                  </div>

                  {goals.items.map((item) => (
                    <article key={item.id} className="si-admin-goals-table__row">
                      <div>
                        <strong>{item.indicator_name || item.indicator_id}</strong>
                        <small>{item.indicator_id}</small>
                      </div>
                      <span>{getGoalScopeBranchLabel(item.goal_scope_branch)}</span>
                      <span>
                        {item.goal_label} · {item.goal_value}
                      </span>
                      <span>
                        {getGoalPeriodicityLabel(item.goal_periodicity)} ·{" "}
                        {getGoalModeLabel(item.goal_mode)}
                      </span>
                      <span
                        className={
                          item.is_active
                            ? "si-goal-status-badge si-goal-status-badge--active"
                            : "si-goal-status-badge si-goal-status-badge--inactive"
                        }
                      >
                        {item.is_active ? "Ativa" : "Inativa"}
                      </span>
                      <div className="si-admin-goals-table__actions">
                        <button
                          type="button"
                          className="si-settings-editor__button si-settings-editor__button--secondary"
                          onClick={() => {
                            setEditingGoal(item);
                            setGoalDrawerOpen(true);
                          }}
                        >
                          Editar
                        </button>
                        <button
                          type="button"
                          className="si-settings-editor__button si-settings-editor__button--secondary"
                          onClick={() => {
                            void goals.loadHistory(item.indicator_id, item.goal_year);
                            setShowHistory(true);
                          }}
                        >
                          Histórico
                        </button>
                        <ActiveToggle
                          active={item.is_active}
                          disabled={goals.saving}
                          ariaLabel={`Situação da meta ${item.goal_label}`}
                          onToggle={(nextActive) => {
                            if (nextActive) {
                              void goals.activateGoal(item.id);
                            } else {
                              void goals.deactivateGoal(item.id);
                            }
                          }}
                        />
                        <button
                          type="button"
                          className="si-settings-editor__button si-settings-editor__button--secondary"
                          onClick={() => {
                            if (
                              !window.confirm(
                                "Excluir permanentemente esta meta? Metas e curvas mensais vinculadas serão removidas.",
                              )
                            ) {
                              return;
                            }
                            void goals.deleteGoal(item.id);
                          }}
                          disabled={goals.saving}
                        >
                          Excluir
                        </button>
                      </div>
                    </article>
                  ))}
                </div>
                </div>
              )}

              {showHistory && goals.historyItems.length > 0 ? (
                <section className="si-goals-history-panel">
                  <div className="si-goals-history-panel__header">
                    <h4>Histórico de versões</h4>
                    <button
                      type="button"
                      className="si-settings-editor__button si-settings-editor__button--secondary"
                      onClick={() => setShowHistory(false)}
                    >
                      Ocultar
                    </button>
                  </div>
                  <div className="si-goals-history-panel__list">
                    {goals.historyItems.map((item) => (
                      <div key={item.id} className="si-goals-history-panel__item">
                        <strong>
                          {item.indicator_id} · v{item.version} ·{" "}
                          {getGoalScopeBranchLabel(item.goal_scope_branch)}
                        </strong>
                        <span>
                          {item.goal_label} · {getGoalPeriodicityLabel(item.goal_periodicity)}
                        </span>
                      </div>
                    ))}
                  </div>
                </section>
              ) : null}
            </>
          )}
        </div>
      </div>

      <DrawerPanel
        open={goalDrawerOpen}
        onClose={() => {
          setGoalDrawerOpen(false);
          setEditingGoal(null);
        }}
        title={editingGoal ? "Editar meta analítica" : "Nova meta analítica"}
        description="Meta por indicador, ano e escopo (consolidado ou filial 01/02)."
        size="xl"
      >
        <IndicatorGoalForm
          saving={goals.saving}
          initialValue={editingGoal}
          indicatorOptions={indicatorOptions}
          onCreate={handleCreate}
          onUpdate={handleUpdate}
          onCancel={() => {
            setGoalDrawerOpen(false);
            setEditingGoal(null);
          }}
        />
      </DrawerPanel>
    </div>
  );
}

function YearListButton({
  item,
  selected,
  onSelect,
}: {
  item: GoalYearOverviewItem;
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      className={`si-admin-list__item ${selected ? "is-selected" : ""}`}
      onClick={onSelect}
    >
      <div className="si-admin-list__item-top">
        <strong>{item.goal_year}</strong>
        <span>{item.total_active_versions} ativas</span>
      </div>
      <div className="si-admin-list__item-meta">
        <span>{item.total_active_indicators} indicadores</span>
        <span>{item.total_versions} versões</span>
      </div>
    </button>
  );
}
