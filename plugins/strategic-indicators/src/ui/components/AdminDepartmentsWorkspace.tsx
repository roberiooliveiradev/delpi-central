import { useMemo, useState } from "react";
import type {
  AdminDepartmentIndicatorItem,
  AdminDepartmentItem,
  CreateAdminDepartmentIndicatorRequest,
  CreateAdminDepartmentRequest,
  UpdateAdminDepartmentIndicatorRequest,
  UpdateAdminDepartmentRequest,
} from "../../data/types/settings";
import { useStrategicIndicatorsAdminDepartments } from "../../state/hooks/useStrategicIndicatorsAdminDepartments";
import { useStrategicIndicatorsDepartmentIndicators } from "../../state/hooks/useStrategicIndicatorsDepartmentIndicators";
import { InfoState } from "./InfoState";
import { DrawerPanel } from "./DrawerPanel";
import { SectionBlock } from "./SectionBlock";
import { ActiveToggle } from "./ActiveToggle";
import {
  getAggregationModeLabel,
  getPerformanceDirectionLabel,
  getScopeTypeLabel,
} from "../presentation/labels";
import { validateIndicatorSourceKey } from "../utils/indicatorSourceKeyValidation";
import "./AdminDepartmentsWorkspace.css";
import { SI_VALUE_UNIT_OPTIONS, SiSelectControl } from "./siFiltersUi";
import { SiNativeTextAreaControl } from "./siNativeFormFields";

type AdminDepartmentsWorkspaceProps = {
  getAccessToken?: () => string | undefined;
};

type DepartmentFormState = {
  department_id: string;
  department_name: string;
  short_name: string;
  strategic_summary: string;
  headline_goal: string;
  supporting_focus: string;
  weight_pct: number;
  aggregation_mode: "consolidated" | "average_of_units";
  display_order: number;
  is_active: boolean;
};

type IndicatorFormState = {
  indicator_id: string;
  indicator_name: string;
  weight_pct: number;
  scope_type: "consolidated" | "per_unit";
  performance_direction: "higher_is_better" | "lower_is_better";
  strategic_description: string;
  source_key: string;
  value_unit: string;
  value_prefix: string;
  value_suffix: string;
  value_decimals: number;
  display_order: number;
  is_active: boolean;
};

const emptyDepartmentForm: DepartmentFormState = {
  department_id: "",
  department_name: "",
  short_name: "",
  strategic_summary: "",
  headline_goal: "",
  supporting_focus: "",
  weight_pct: 0,
  aggregation_mode: "consolidated",
  display_order: 0,
  is_active: true,
};

const emptyIndicatorForm: IndicatorFormState = {
  indicator_id: "",
  indicator_name: "",
  weight_pct: 0,
  scope_type: "consolidated",
  performance_direction: "higher_is_better",
  strategic_description: "",
  source_key: "",
  value_unit: "",
  value_prefix: "",
  value_suffix: "",
  value_decimals: 2,
  display_order: 0,
  is_active: true,
};

function getIndicatorFormatLabel(item: AdminDepartmentIndicatorItem) {
  const prefix = item.value_prefix?.trim() ?? "";
  const suffix = item.value_suffix?.trim() ?? "";
  const unit = item.value_unit?.trim() ?? "";

  if (prefix || suffix) {
    return `${prefix}${suffix ? ` ${suffix}` : ""}`.trim();
  }

  return unit || "Sem unidade";
}

export function AdminDepartmentsWorkspace({
  getAccessToken,
}: AdminDepartmentsWorkspaceProps) {
  const departments = useStrategicIndicatorsAdminDepartments({ getAccessToken });

  const [selectedDepartmentId, setSelectedDepartmentId] = useState<string | null>(null);
  const [departmentDrawerOpen, setDepartmentDrawerOpen] = useState(false);
  const [departmentMode, setDepartmentMode] = useState<"create" | "edit">("create");
  const [editingDepartmentId, setEditingDepartmentId] = useState<string | null>(null);
  const [departmentForm, setDepartmentForm] =
    useState<DepartmentFormState>(emptyDepartmentForm);

  const [indicatorDrawerOpen, setIndicatorDrawerOpen] = useState(false);
  const [indicatorFormError, setIndicatorFormError] = useState<string | null>(null);
  const [indicatorMode, setIndicatorMode] = useState<"create" | "edit">("create");
  const [editingIndicatorId, setEditingIndicatorId] = useState<string | null>(null);
  const [indicatorForm, setIndicatorForm] =
    useState<IndicatorFormState>(emptyIndicatorForm);

  const departmentIndicators = useStrategicIndicatorsDepartmentIndicators({
    departmentId: selectedDepartmentId,
    getAccessToken,
  });

  const selectedDepartment = useMemo(
    () =>
      departments.items.find((item) => item.department_id === selectedDepartmentId) ?? null,
    [departments.items, selectedDepartmentId],
  );

  function openCreateDepartmentDrawer() {
    setDepartmentMode("create");
    setEditingDepartmentId(null);
    setDepartmentForm(emptyDepartmentForm);
    setDepartmentDrawerOpen(true);
  }

  function openEditDepartmentDrawer(item: AdminDepartmentItem) {
    setDepartmentMode("edit");
    setEditingDepartmentId(item.department_id);
    setDepartmentForm({
      department_id: item.department_id,
      department_name: item.department_name,
      short_name: item.short_name,
      strategic_summary: item.strategic_summary,
      headline_goal: item.headline_goal,
      supporting_focus: item.supporting_focus,
      weight_pct: item.weight_pct,
      aggregation_mode: item.aggregation_mode,
      display_order: item.display_order,
      is_active: item.is_active,
    });
    setDepartmentDrawerOpen(true);
  }

  function openCreateIndicatorDrawer() {
    setIndicatorMode("create");
    setEditingIndicatorId(null);
    setIndicatorForm(emptyIndicatorForm);
    setIndicatorDrawerOpen(true);
  }

  function openEditIndicatorDrawer(item: AdminDepartmentIndicatorItem) {
    setIndicatorMode("edit");
    setEditingIndicatorId(item.indicator_id);
    setIndicatorForm({
      indicator_id: item.indicator_id,
      indicator_name: item.indicator_name,
      weight_pct: item.weight_pct,
      scope_type: item.scope_type,
      performance_direction: item.performance_direction,
      strategic_description: item.strategic_description,
      source_key: item.source_key ?? "",
      value_unit: item.value_unit ?? "",
      value_prefix: item.value_prefix ?? "",
      value_suffix: item.value_suffix ?? "",
      value_decimals: Number(item.value_decimals ?? 2),
      display_order: item.display_order,
      is_active: item.is_active,
    });
    setIndicatorDrawerOpen(true);
  }

  async function handleSubmitDepartment() {
    if (departmentMode === "create") {
      const payload: CreateAdminDepartmentRequest = {
        department_id: departmentForm.department_id.trim(),
        department_name: departmentForm.department_name.trim(),
        short_name: departmentForm.short_name.trim(),
        strategic_summary: departmentForm.strategic_summary.trim(),
        headline_goal: departmentForm.headline_goal.trim(),
        supporting_focus: departmentForm.supporting_focus.trim(),
        weight_pct: Number(departmentForm.weight_pct || 0),
        aggregation_mode: departmentForm.aggregation_mode,
        display_order: Number(departmentForm.display_order || 0),
      };

      await departments.createDepartment(payload);
    } else if (editingDepartmentId) {
      const nextDepartmentId = departmentForm.department_id.trim();
      const payload: UpdateAdminDepartmentRequest = {
        department_name: departmentForm.department_name.trim(),
        short_name: departmentForm.short_name.trim(),
        strategic_summary: departmentForm.strategic_summary.trim(),
        headline_goal: departmentForm.headline_goal.trim(),
        supporting_focus: departmentForm.supporting_focus.trim(),
        weight_pct: Number(departmentForm.weight_pct || 0),
        aggregation_mode: departmentForm.aggregation_mode,
        display_order: Number(departmentForm.display_order || 0),
        is_active: departmentForm.is_active,
      };

      if (nextDepartmentId !== editingDepartmentId) {
        payload.new_department_id = nextDepartmentId;
      }

      await departments.updateDepartment(editingDepartmentId, payload);

      if (selectedDepartmentId === editingDepartmentId && nextDepartmentId) {
        setSelectedDepartmentId(nextDepartmentId);
      }
    }

    setDepartmentDrawerOpen(false);
  }

  async function handleSubmitIndicator() {
    if (!selectedDepartmentId) return;

    const sourceKeyError = validateIndicatorSourceKey(
      indicatorForm.source_key,
      indicatorMode === "create" ? true : indicatorForm.is_active,
    );
    if (sourceKeyError) {
      setIndicatorFormError(sourceKeyError);
      return;
    }
    setIndicatorFormError(null);

    if (indicatorMode === "create") {
      const payload: CreateAdminDepartmentIndicatorRequest = {
        indicator_id: indicatorForm.indicator_id.trim(),
        indicator_name: indicatorForm.indicator_name.trim(),
        weight_pct: Number(indicatorForm.weight_pct || 0),
        scope_type: indicatorForm.scope_type,
        performance_direction: indicatorForm.performance_direction,
        strategic_description: indicatorForm.strategic_description.trim(),
        source_key: indicatorForm.source_key.trim() || null,
        value_unit: indicatorForm.value_unit.trim() || null,
        value_prefix: indicatorForm.value_prefix.trim() || null,
        value_suffix: indicatorForm.value_suffix.trim() || null,
        value_decimals: Number(indicatorForm.value_decimals ?? 2),
        display_order: Number(indicatorForm.display_order || 0),
      };

      await departmentIndicators.createIndicator(payload);
    } else if (editingIndicatorId) {
      const nextIndicatorId = indicatorForm.indicator_id.trim();
      const payload: UpdateAdminDepartmentIndicatorRequest = {
        indicator_name: indicatorForm.indicator_name.trim(),
        weight_pct: Number(indicatorForm.weight_pct || 0),
        scope_type: indicatorForm.scope_type,
        performance_direction: indicatorForm.performance_direction,
        strategic_description: indicatorForm.strategic_description.trim(),
        source_key: indicatorForm.source_key.trim() || null,
        value_unit: indicatorForm.value_unit.trim() || null,
        value_prefix: indicatorForm.value_prefix.trim() || null,
        value_suffix: indicatorForm.value_suffix.trim() || null,
        value_decimals: Number(indicatorForm.value_decimals ?? 2),
        display_order: Number(indicatorForm.display_order || 0),
        is_active: indicatorForm.is_active,
      };

      if (nextIndicatorId !== editingIndicatorId) {
        payload.new_indicator_id = nextIndicatorId;
      }

      await departmentIndicators.updateIndicator(editingIndicatorId, payload);
    }

    setIndicatorDrawerOpen(false);
  }

  return (
    <div className="si-admin-workspace">
      <SectionBlock
        title="Departamentos administrativos"
        description="Cadastre, edite, desative ou exclua departamentos e defina a base executiva de cada área."
        aside={
          <button
            type="button"
            className="si-settings-editor__button"
            onClick={openCreateDepartmentDrawer}
          >
            Novo departamento
          </button>
        }
      >
        {departments.error ? (
          <InfoState
            title="Falha ao carregar departamentos"
            description={departments.error}
            actionLabel="Tentar novamente"
            onAction={() => void departments.reload()}
          />
        ) : null}

        {!!departments.successMessage ? (
          <div className="si-settings-editor__alert si-settings-editor__alert--success">
            {departments.successMessage}
          </div>
        ) : null}

        <div className="si-admin-master-detail">
          <div className="si-admin-master-detail__master">
            {departments.loading ? (
              <div className="si-admin-placeholder">Carregando departamentos...</div>
            ) : departments.items.length === 0 ? (
              <InfoState
                title="Nenhum departamento cadastrado"
                description="Crie o primeiro departamento administrativo para começar a configurar o módulo."
                actionLabel="Criar departamento"
                onAction={openCreateDepartmentDrawer}
              />
            ) : (
              <div className="si-admin-list">
                {departments.items.map((item) => {
                  const isSelected = item.department_id === selectedDepartmentId;

                  return (
                    <button
                      key={item.department_id}
                      type="button"
                      className={`si-admin-list__item ${isSelected ? "is-selected" : ""}`}
                      onClick={() => setSelectedDepartmentId(item.department_id)}
                    >
                      <div className="si-admin-list__item-top">
                        <strong>{item.department_name}</strong>
                        <span>{item.short_name}</span>
                      </div>

                      <div className="si-admin-list__item-meta">
                        <span>Peso: {item.weight_pct}%</span>
                        <span>{item.is_active ? "Ativo" : "Inativo"}</span>
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          <div className="si-admin-master-detail__detail">
            {!selectedDepartment ? (
              <InfoState
                title="Selecione um departamento"
                description="Escolha um departamento à esquerda para editar seu cadastro e seus indicadores estruturais."
              />
            ) : (
              <>
                <div className="si-admin-detail-card">
                  <div className="si-admin-detail-card__header">
                    <div>
                      <h3>{selectedDepartment.department_name}</h3>
                      <p>{selectedDepartment.strategic_summary}</p>
                    </div>

                    <div className="si-admin-detail-card__actions">
                      <button
                        type="button"
                        className="si-settings-editor__button si-settings-editor__button--secondary"
                        onClick={() => openEditDepartmentDrawer(selectedDepartment)}
                      >
                        Editar
                      </button>

                      <ActiveToggle
                        active={selectedDepartment.is_active}
                        disabled={departments.saving}
                        ariaLabel={`Situação do departamento ${selectedDepartment.department_name}`}
                        onToggle={(nextActive) => {
                          if (nextActive) {
                            void departments.activateDepartment(
                              selectedDepartment.department_id,
                            );
                          } else {
                            void departments.deactivateDepartment(
                              selectedDepartment.department_id,
                            );
                          }
                        }}
                      />

                      <button
                        type="button"
                        className="si-settings-editor__button si-settings-editor__button--secondary"
                        onClick={() =>
                          void departments.removeDepartment(selectedDepartment.department_id)
                        }
                      >
                        Excluir
                      </button>
                    </div>
                  </div>

                  <div className="si-admin-detail-card__grid">
                    <div>
                      <span className="si-admin-detail-card__label">Meta principal</span>
                      <strong>{selectedDepartment.headline_goal || "—"}</strong>
                    </div>

                    <div>
                      <span className="si-admin-detail-card__label">Foco complementar</span>
                      <strong>{selectedDepartment.supporting_focus || "—"}</strong>
                    </div>

                    <div>
                      <span className="si-admin-detail-card__label">Peso no IGD</span>
                      <strong>{selectedDepartment.weight_pct}%</strong>
                    </div>

                    <div>
                      <span className="si-admin-detail-card__label">Agregação</span>
                      <strong>{getAggregationModeLabel(selectedDepartment.aggregation_mode)}</strong>
                    </div>
                  </div>
                </div>

                <SectionBlock
                  title="Indicadores estruturais"
                  description="Cadastre os indicadores oficiais do departamento e mantenha o catálogo estruturado."
                  aside={
                    <button
                      type="button"
                      className="si-settings-editor__button"
                      onClick={openCreateIndicatorDrawer}
                    >
                      Novo indicador
                    </button>
                  }
                >
                  {!!departmentIndicators.successMessage ? (
                    <div className="si-settings-editor__alert si-settings-editor__alert--success">
                      {departmentIndicators.successMessage}
                    </div>
                  ) : null}

                  {departmentIndicators.error ? (
                    <InfoState
                      title="Falha ao carregar indicadores"
                      description={departmentIndicators.error}
                      actionLabel="Tentar novamente"
                      onAction={() => void departmentIndicators.reload()}
                    />
                  ) : null}

                  {departmentIndicators.loading ? (
                    <div className="si-admin-placeholder">Carregando indicadores...</div>
                  ) : departmentIndicators.items.length === 0 ? (
                    <InfoState
                      title="Nenhum indicador estrutural cadastrado"
                      description="Crie os indicadores oficiais deste departamento para habilitar metas anuais e leitura estratégica."
                      actionLabel="Criar indicador"
                      onAction={openCreateIndicatorDrawer}
                    />
                  ) : (
                    <div className="si-admin-indicators-table">
                      {departmentIndicators.items.map((item) => (
                        <article
                          key={item.indicator_id}
                          className={`si-admin-indicators-table__row ${
                            item.is_active ? "" : "is-inactive"
                          }`}
                        >
                          <div className="si-admin-indicators-table__main">
                            <div className="si-admin-indicators-table__title-row">
                              <strong>{item.indicator_name}</strong>
                              <code className="si-admin-id-chip">{item.indicator_id}</code>
                            </div>
                            <p>{item.strategic_description || "Sem descrição estratégica."}</p>
                          </div>

                          <div className="si-admin-indicators-table__meta">
                            <span className="si-admin-meta-chip si-admin-meta-chip--weight">
                              {item.weight_pct}%
                            </span>
                            <span className="si-admin-meta-chip si-admin-meta-chip--scope">
                              {getScopeTypeLabel(item.scope_type)}
                            </span>
                            <span className="si-admin-meta-chip">
                              {getIndicatorFormatLabel(item)}
                            </span>
                            <span
                              className={
                                item.is_active
                                  ? "si-admin-meta-chip si-admin-meta-chip--active"
                                  : "si-admin-meta-chip si-admin-meta-chip--inactive"
                              }
                            >
                              {item.is_active ? "Ativo" : "Inativo"}
                            </span>
                          </div>

                          <div className="si-admin-indicators-table__actions">
                            <button
                              type="button"
                              className="si-settings-editor__button si-settings-editor__button--secondary"
                              onClick={() => openEditIndicatorDrawer(item)}
                            >
                              Editar
                            </button>

                            <ActiveToggle
                              active={item.is_active}
                              disabled={departmentIndicators.saving}
                              ariaLabel={`Situação do indicador ${item.indicator_name}`}
                              onToggle={(nextActive) => {
                                if (nextActive) {
                                  void departmentIndicators.activateIndicator(
                                    item.indicator_id,
                                  );
                                } else {
                                  void departmentIndicators.deactivateIndicator(
                                    item.indicator_id,
                                  );
                                }
                              }}
                            />

                            <button
                              type="button"
                              className="si-settings-editor__button si-settings-editor__button--secondary"
                              onClick={() => {
                                if (
                                  !window.confirm(
                                    `Excluir permanentemente o indicador "${item.indicator_name}"? Metas vinculadas também serão removidas.`,
                                  )
                                ) {
                                  return;
                                }
                                void departmentIndicators.removeIndicator(item.indicator_id);
                              }}
                            >
                              Excluir
                            </button>
                          </div>
                        </article>
                      ))}
                    </div>
                  )}
                </SectionBlock>
              </>
            )}
          </div>
        </div>
      </SectionBlock>

      <DrawerPanel
        open={departmentDrawerOpen}
        onClose={() => setDepartmentDrawerOpen(false)}
        title={departmentMode === "create" ? "Novo departamento" : "Editar departamento"}
        description="Defina a base executiva e estrutural do departamento."
        size="lg"
        footer={
          <>
            <button
              type="button"
              className="si-settings-editor__button si-settings-editor__button--secondary"
              onClick={() => setDepartmentDrawerOpen(false)}
            >
              Cancelar
            </button>
            <button
              type="button"
              className="si-settings-editor__button"
              onClick={() => void handleSubmitDepartment()}
              disabled={departments.saving}
            >
              {departments.saving ? "Salvando..." : "Salvar"}
            </button>
          </>
        }
      >
        <div className="si-admin-form-grid">
          <label className="si-admin-form-field">
            <span>ID</span>
            <input
              value={departmentForm.department_id}
              onChange={(event) =>
                setDepartmentForm((current) => ({
                  ...current,
                  department_id: event.target.value,
                }))
              }
            />
          </label>

          <label className="si-admin-form-field">
            <span>Nome</span>
            <input
              value={departmentForm.department_name}
              onChange={(event) =>
                setDepartmentForm((current) => ({
                  ...current,
                  department_name: event.target.value,
                }))
              }
            />
          </label>

          <label className="si-admin-form-field">
            <span>Sigla</span>
            <input
              value={departmentForm.short_name}
              onChange={(event) =>
                setDepartmentForm((current) => ({
                  ...current,
                  short_name: event.target.value,
                }))
              }
            />
          </label>

          <label className="si-admin-form-field">
            <span>Peso</span>
            <input
              type="number"
              value={departmentForm.weight_pct}
              onChange={(event) =>
                setDepartmentForm((current) => ({
                  ...current,
                  weight_pct: Number(event.target.value || 0),
                }))
              }
            />
          </label>

          <label className="si-admin-form-field">
            <span>Agregação</span>
            <SiSelectControl
              value={departmentForm.aggregation_mode}
              onChange={(value) =>
                setDepartmentForm((current) => ({
                  ...current,
                  aggregation_mode: value as "consolidated" | "average_of_units",
                }))
              }
              options={[
                { value: "consolidated", label: getAggregationModeLabel("consolidated") },
                {
                  value: "average_of_units",
                  label: getAggregationModeLabel("average_of_units"),
                },
              ]}
            />
          </label>

          <label className="si-admin-form-field">
            <span>Ordem</span>
            <input
              type="number"
              value={departmentForm.display_order}
              onChange={(event) =>
                setDepartmentForm((current) => ({
                  ...current,
                  display_order: Number(event.target.value || 0),
                }))
              }
            />
          </label>

          <label className="si-admin-form-field si-admin-form-field--full">
            <span>Resumo estratégico</span>
            <SiNativeTextAreaControl
              rows={3}
              value={departmentForm.strategic_summary}
              aria-label="Resumo estratégico"
              onChange={(strategic_summary) =>
                setDepartmentForm((current) => ({
                  ...current,
                  strategic_summary,
                }))
              }
            />
          </label>

          <label className="si-admin-form-field">
            <span>Meta principal</span>
            <input
              value={departmentForm.headline_goal}
              onChange={(event) =>
                setDepartmentForm((current) => ({
                  ...current,
                  headline_goal: event.target.value,
                }))
              }
            />
          </label>

          <label className="si-admin-form-field">
            <span>Foco complementar</span>
            <input
              value={departmentForm.supporting_focus}
              onChange={(event) =>
                setDepartmentForm((current) => ({
                  ...current,
                  supporting_focus: event.target.value,
                }))
              }
            />
          </label>
        </div>

      </DrawerPanel>

      <DrawerPanel
        open={indicatorDrawerOpen}
        onClose={() => {
          setIndicatorDrawerOpen(false);
          setIndicatorFormError(null);
        }}
        title={indicatorMode === "create" ? "Novo indicador estrutural" : "Editar indicador estrutural"}
        description="Defina a estrutura oficial do indicador dentro do departamento."
        size="xl"
        footer={
          <>
            <button
              type="button"
              className="si-settings-editor__button si-settings-editor__button--secondary"
              onClick={() => {
                setIndicatorDrawerOpen(false);
                setIndicatorFormError(null);
              }}
            >
              Cancelar
            </button>
            <button
              type="button"
              className="si-settings-editor__button"
              onClick={() => void handleSubmitIndicator()}
              disabled={departmentIndicators.saving}
            >
              {departmentIndicators.saving ? "Salvando..." : "Salvar"}
            </button>
          </>
        }
      >
        <div className="si-admin-form-grid">
          <label className="si-admin-form-field">
            <span>ID</span>
            <input
              value={indicatorForm.indicator_id}
              onChange={(event) =>
                setIndicatorForm((current) => ({
                  ...current,
                  indicator_id: event.target.value,
                }))
              }
            />
          </label>

          <label className="si-admin-form-field">
            <span>Nome</span>
            <input
              value={indicatorForm.indicator_name}
              onChange={(event) =>
                setIndicatorForm((current) => ({
                  ...current,
                  indicator_name: event.target.value,
                }))
              }
            />
          </label>

          <label className="si-admin-form-field">
            <span>Peso</span>
            <input
              type="number"
              value={indicatorForm.weight_pct}
              onChange={(event) =>
                setIndicatorForm((current) => ({
                  ...current,
                  weight_pct: Number(event.target.value || 0),
                }))
              }
            />
          </label>

          <label className="si-admin-form-field">
            <span>Escopo</span>
            <SiSelectControl
              value={indicatorForm.scope_type}
              onChange={(value) =>
                setIndicatorForm((current) => ({
                  ...current,
                  scope_type: value as "consolidated" | "per_unit",
                }))
              }
              options={[
                { value: "consolidated", label: getScopeTypeLabel("consolidated") },
                { value: "per_unit", label: getScopeTypeLabel("per_unit") },
              ]}
            />
          </label>

          <label className="si-admin-form-field">
            <span>Direção de performance</span>
            <SiSelectControl
              value={indicatorForm.performance_direction}
              onChange={(value) =>
                setIndicatorForm((current) => ({
                  ...current,
                  performance_direction: value as "higher_is_better" | "lower_is_better",
                }))
              }
              options={[
                {
                  value: "higher_is_better",
                  label: getPerformanceDirectionLabel("higher_is_better"),
                },
                {
                  value: "lower_is_better",
                  label: getPerformanceDirectionLabel("lower_is_better"),
                },
              ]}
            />
          </label>

          <label className="si-admin-form-field">
            <span>Chave da fonte (obrigatória se ativo)</span>
            <input
              value={indicatorForm.source_key}
              placeholder="ex.: commercial_rol, production_otd"
              onChange={(event) =>
                setIndicatorForm((current) => ({
                  ...current,
                  source_key: event.target.value,
                }))
              }
            />
            <small className="si-admin-form-field__hint">
              Liga o indicador às medições do SI e às metas nos dashboards
              departamentais. Use letras minúsculas e underscore.
            </small>
          </label>

          {indicatorFormError ? (
            <p className="si-settings-editor__alert si-settings-editor__alert--error">
              {indicatorFormError}
            </p>
          ) : null}

          <label className="si-admin-form-field">
            <span>Unidade</span>
            <SiSelectControl
              value={indicatorForm.value_unit}
              onChange={(value) =>
                setIndicatorForm((current) => ({
                  ...current,
                  value_unit: value,
                }))
              }
              allowEmpty
              emptyLabel="Não informada"
              options={[...SI_VALUE_UNIT_OPTIONS]}
            />
          </label>

          <label className="si-admin-form-field">
            <span>Prefixo</span>
            <input
              placeholder="Ex.: R$"
              value={indicatorForm.value_prefix}
              onChange={(event) =>
                setIndicatorForm((current) => ({
                  ...current,
                  value_prefix: event.target.value,
                }))
              }
            />
          </label>

          <label className="si-admin-form-field">
            <span>Sufixo</span>
            <input
              placeholder="Ex.: %, PPM, /mês, dias"
              value={indicatorForm.value_suffix}
              onChange={(event) =>
                setIndicatorForm((current) => ({
                  ...current,
                  value_suffix: event.target.value,
                }))
              }
            />
          </label>

          <label className="si-admin-form-field">
            <span>Casas decimais</span>
            <input
              type="number"
              min={0}
              max={6}
              value={indicatorForm.value_decimals}
              onChange={(event) =>
                setIndicatorForm((current) => ({
                  ...current,
                  value_decimals: Number(event.target.value || 0),
                }))
              }
            />
          </label>

          <label className="si-admin-form-field">
            <span>Ordem</span>
            <input
              type="number"
              value={indicatorForm.display_order}
              onChange={(event) =>
                setIndicatorForm((current) => ({
                  ...current,
                  display_order: Number(event.target.value || 0),
                }))
              }
            />
          </label>

          <label className="si-admin-form-field si-admin-form-field--full">
            <span>Descrição estratégica</span>
            <SiNativeTextAreaControl
              rows={3}
              value={indicatorForm.strategic_description}
              aria-label="Descrição estratégica"
              onChange={(strategic_description) =>
                setIndicatorForm((current) => ({
                  ...current,
                  strategic_description,
                }))
              }
            />
          </label>
        </div>

      </DrawerPanel>
    </div>
  );
}