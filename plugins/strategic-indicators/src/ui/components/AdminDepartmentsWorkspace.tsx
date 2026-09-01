import { SectionHintLabel } from "@delpi/plugin-ui/index";
import { useEffect, useMemo, useState } from "react";
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
import {
  AdminDepartmentFormDrawer,
  departmentFormFromItem,
  emptyDepartmentForm,
  type DepartmentFormState,
} from "./AdminDepartmentFormDrawer";
import {
  AdminIndicatorFormDrawer,
  emptyIndicatorForm,
  indicatorFormFromItem,
  type IndicatorFormState,
} from "./AdminIndicatorFormDrawer";
import { ActiveToggle } from "./ActiveToggle";
import { SiAdminFormField } from "./SiAdminFormField";
import { useSiPhoneViewport } from "../hooks/useSiPhoneViewport";
import {
  getAggregationModeLabel,
  getScopeTypeLabel,
} from "../presentation/labels";
import { SI_HELP } from "../../content/helpTooltips";
import type { CatalogAdminAction } from "../settings/settingsAdminTabs";
import { SiHelpActionButton } from "./SiHelpActionButton";
import { SiNativeTextControl } from "./siNativeFormFields";
import "./AdminDepartmentsWorkspace.css";

type AdminDepartmentsWorkspaceProps = {
  getAccessToken?: () => string | undefined;
  structureFocus?: { departmentId: string; indicatorId: string } | null;
  catalogAction?: CatalogAdminAction | null;
  onStructureFocusConsumed?: () => void;
  onCatalogActionConsumed?: () => void;
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
  structureFocus = null,
  catalogAction = null,
  onStructureFocusConsumed,
  onCatalogActionConsumed,
}: AdminDepartmentsWorkspaceProps) {
  const isPhone = useSiPhoneViewport();
  const departments = useStrategicIndicatorsAdminDepartments({ getAccessToken });

  const [selectedDepartmentId, setSelectedDepartmentId] = useState<string | null>(null);
  const [departmentFormMode, setDepartmentFormMode] = useState<"create" | "edit" | null>(null);
  const [editingDepartmentId, setEditingDepartmentId] = useState<string | null>(null);
  const [departmentForm, setDepartmentForm] =
    useState<DepartmentFormState>(emptyDepartmentForm);

  const [indicatorFormMode, setIndicatorFormMode] = useState<"create" | "edit" | null>(null);
  const [indicatorFormError, setIndicatorFormError] = useState<string | null>(null);
  const [editingIndicatorId, setEditingIndicatorId] = useState<string | null>(null);
  const [indicatorForm, setIndicatorForm] =
    useState<IndicatorFormState>(emptyIndicatorForm);
  const [departmentSearch, setDepartmentSearch] = useState("");
  const [indicatorSearch, setIndicatorSearch] = useState("");

  const departmentIndicators = useStrategicIndicatorsDepartmentIndicators({
    departmentId: selectedDepartmentId,
    getAccessToken,
  });

  const selectedDepartment = useMemo(
    () =>
      departments.items.find((item) => item.department_id === selectedDepartmentId) ?? null,
    [departments.items, selectedDepartmentId],
  );

  const filteredDepartments = useMemo(() => {
    const query = departmentSearch.trim().toLowerCase();
    if (!query) return departments.items;

    return departments.items.filter((item) => {
      const haystack = [
        item.department_id,
        item.department_name,
        item.short_name,
      ]
        .join(" ")
        .toLowerCase();
      return haystack.includes(query);
    });
  }, [departments.items, departmentSearch]);

  const filteredIndicators = useMemo(() => {
    const query = indicatorSearch.trim().toLowerCase();
    if (!query) return departmentIndicators.items;

    return departmentIndicators.items.filter((item) => {
      const haystack = [item.indicator_id, item.indicator_name].join(" ").toLowerCase();
      return haystack.includes(query);
    });
  }, [departmentIndicators.items, indicatorSearch]);

  useEffect(() => {
    if (!structureFocus) return;
    setSelectedDepartmentId(structureFocus.departmentId);
  }, [structureFocus]);

  useEffect(() => {
    if (!structureFocus || departmentIndicators.loading) return;

    const match = departmentIndicators.items.find(
      (item) => item.indicator_id === structureFocus.indicatorId,
    );
    if (!match) return;

    setIndicatorFormMode("edit");
    setEditingIndicatorId(match.indicator_id);
    setIndicatorForm(indicatorFormFromItem(match));
    setIndicatorFormError(null);
    onStructureFocusConsumed?.();
  }, [
    structureFocus,
    departmentIndicators.loading,
    departmentIndicators.items,
    onStructureFocusConsumed,
  ]);

  useEffect(() => {
    if (!catalogAction || departments.loading) return;

    if (catalogAction === "new-department") {
      openCreateDepartmentForm();
      onCatalogActionConsumed?.();
      return;
    }

    if (catalogAction === "new-indicator") {
      if (!selectedDepartmentId && departments.items.length > 0) {
        setSelectedDepartmentId(departments.items[0].department_id);
        return;
      }
      if (!selectedDepartmentId) {
        onCatalogActionConsumed?.();
        return;
      }
      if (departmentIndicators.loading) return;

      openCreateIndicatorForm();
      onCatalogActionConsumed?.();
    }
  }, [
    catalogAction,
    departments.loading,
    departments.items,
    selectedDepartmentId,
    departmentIndicators.loading,
    onCatalogActionConsumed,
  ]);

  function closeDepartmentForm() {
    setDepartmentFormMode(null);
    setEditingDepartmentId(null);
    setDepartmentForm(emptyDepartmentForm);
  }

  function closeIndicatorForm() {
    setIndicatorFormMode(null);
    setEditingIndicatorId(null);
    setIndicatorForm(emptyIndicatorForm);
    setIndicatorFormError(null);
  }

  function openCreateDepartmentForm() {
    closeIndicatorForm();
    setDepartmentFormMode("create");
    setEditingDepartmentId(null);
    setDepartmentForm(emptyDepartmentForm);
  }

  function openEditDepartmentForm(item: AdminDepartmentItem) {
    closeIndicatorForm();
    setDepartmentFormMode("edit");
    setEditingDepartmentId(item.department_id);
    setDepartmentForm(departmentFormFromItem(item));
  }

  function openCreateIndicatorForm() {
    closeDepartmentForm();
    setIndicatorFormMode("create");
    setEditingIndicatorId(null);
    setIndicatorForm(emptyIndicatorForm);
    setIndicatorFormError(null);
  }

  function openEditIndicatorForm(item: AdminDepartmentIndicatorItem) {
    closeDepartmentForm();
    setIndicatorFormMode("edit");
    setEditingIndicatorId(item.indicator_id);
    setIndicatorForm(indicatorFormFromItem(item));
    setIndicatorFormError(null);
  }

  const catalogFormOpen = Boolean(departmentFormMode || indicatorFormMode);

  async function handleSubmitDepartment() {
    if (departmentFormMode === "create") {
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

    closeDepartmentForm();
  }

  async function handleSubmitIndicator() {
    if (!selectedDepartmentId) return;

    setIndicatorFormError(null);

    if (indicatorFormMode === "create") {
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
        branch_value_aggregation: indicatorForm.branch_value_aggregation,
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
        branch_value_aggregation: indicatorForm.branch_value_aggregation,
        display_order: Number(indicatorForm.display_order || 0),
        is_active: indicatorForm.is_active,
      };

      if (nextIndicatorId !== editingIndicatorId) {
        payload.new_indicator_id = nextIndicatorId;
      }

      await departmentIndicators.updateIndicator(editingIndicatorId, payload);
    }

    closeIndicatorForm();
  }

  const departmentFormTitle =
    departmentFormMode === "edit" ? "Editar departamento" : "Novo departamento";
  const indicatorFormTitle =
    indicatorFormMode === "edit"
      ? "Editar indicador estrutural"
      : "Novo indicador estrutural";

  return (
    <div className="si-admin-workspace">
      {departments.error ? (
        <InfoState
          title="Falha ao carregar departamentos"
          description={departments.error}
          actionLabel="Tentar novamente"
          onAction={() => void departments.reload()}
        />
      ) : null}

      {departments.successMessage ? (
        <div className="si-settings-editor__alert si-settings-editor__alert--success">
          {departments.successMessage}
        </div>
      ) : null}

      <div
        className={`si-admin-master-detail ${
          isPhone && (selectedDepartmentId || catalogFormOpen)
            ? "is-mobile-detail-open"
            : ""
        } ${catalogFormOpen ? "si-admin-catalog-detail--form" : ""}`}
      >
        <div className="si-admin-master-detail__master">
          <div className="si-admin-master-detail__master-header">
            <SectionHintLabel
              label="Departamentos"
              hint={SI_HELP.catalog.departmentList}
            />
            <SiHelpActionButton
              className="si-settings-editor__button"
              helpHint={SI_HELP.catalog.newDepartment}
              onClick={openCreateDepartmentForm}
              disabled={!!catalogFormOpen}
            >
              Novo departamento
            </SiHelpActionButton>
          </div>

          {departments.items.length > 0 ? (
            <SiAdminFormField
              label="Buscar departamentos"
              hint={SI_HELP.catalog.searchDepartments}
              compact
            >
              <SiNativeTextControl
                value={departmentSearch}
                placeholder="Nome, sigla ou ID"
                onChange={setDepartmentSearch}
              />
            </SiAdminFormField>
          ) : null}

          {departments.loading ? (
            <div className="si-admin-placeholder">Carregando departamentos...</div>
          ) : departments.items.length === 0 ? (
            <InfoState
              title="Nenhum departamento cadastrado"
              description="Crie o primeiro departamento administrativo para começar a configurar o módulo."
              actionLabel="Criar departamento"
              onAction={openCreateDepartmentForm}
            />
          ) : (
            <div className="si-admin-list">
              {filteredDepartments.map((item) => {
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
          {isPhone && (selectedDepartment || catalogFormOpen) ? (
            <button
              type="button"
              className="si-admin-master-detail__back"
              onClick={() => {
                if (catalogFormOpen) {
                  if (departmentFormMode) closeDepartmentForm();
                  else closeIndicatorForm();
                  return;
                }
                setSelectedDepartmentId(null);
              }}
            >
              ← Lista de departamentos
            </button>
          ) : null}

          {departmentFormMode ? (
            <AdminDepartmentFormDrawer
              mode={departmentFormMode}
              saving={departments.saving}
              form={departmentForm}
              panelShell={{
                title: departmentFormTitle,
                onBack: closeDepartmentForm,
                backLabel: "← Voltar ao catálogo",
              }}
              onChange={setDepartmentForm}
              onSubmit={handleSubmitDepartment}
            />
          ) : indicatorFormMode && selectedDepartment ? (
            <AdminIndicatorFormDrawer
              mode={indicatorFormMode}
              saving={departmentIndicators.saving}
              form={indicatorForm}
              formError={indicatorFormError}
              panelShell={{
                title: indicatorFormTitle,
                subtitle: selectedDepartment.department_name,
                onBack: closeIndicatorForm,
                backLabel: "← Voltar ao departamento",
              }}
              onChange={setIndicatorForm}
              onSubmit={handleSubmitIndicator}
            />
          ) : !selectedDepartment ? (
            <InfoState
              title="Selecione um departamento"
              description="Escolha um departamento na lista para editar cadastro e indicadores."
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
                        onClick={() => openEditDepartmentForm(selectedDepartment)}
                      >
                        Editar
                      </button>

                      <ActiveToggle
                        active={selectedDepartment.is_active}
                        disabled={departments.saving}
                        helpHint={SI_HELP.department.isActive}
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
                      <SectionHintLabel
                        label="Peso no IGD"
                        hint={SI_HELP.catalog.departmentWeight}
                        className="si-admin-detail-card__label"
                      />
                      <strong>{selectedDepartment.weight_pct}%</strong>
                    </div>

                    <div>
                      <SectionHintLabel
                        label="Agregação"
                        hint={SI_HELP.catalog.departmentAggregation}
                        className="si-admin-detail-card__label"
                      />
                      <strong>{getAggregationModeLabel(selectedDepartment.aggregation_mode)}</strong>
                    </div>
                  </div>
                </div>

                <div className="si-admin-indicators-section">
                  <header className="si-admin-indicators-section__header">
                    <SectionHintLabel
                      label="Indicadores estruturais"
                      hint={SI_HELP.catalog.indicatorList}
                    />
                    <SiHelpActionButton
                      className="si-settings-editor__button"
                      helpHint={SI_HELP.catalog.newIndicator}
                      onClick={openCreateIndicatorForm}
                      disabled={!!indicatorFormMode}
                    >
                      Novo indicador
                    </SiHelpActionButton>
                  </header>

                  {departmentIndicators.items.length > 0 ? (
                    <SiAdminFormField
                      label="Buscar indicadores"
                      hint={SI_HELP.catalog.searchIndicators}
                      compact
                    >
                      <SiNativeTextControl
                        value={indicatorSearch}
                        placeholder="Nome ou ID do indicador"
                        onChange={setIndicatorSearch}
                      />
                    </SiAdminFormField>
                  ) : null}

                  {departmentIndicators.successMessage ? (
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
                      onAction={openCreateIndicatorForm}
                    />
                  ) : (
                    <div className="si-admin-indicators-table">
                      {filteredIndicators.map((item) => (
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
                              onClick={() => openEditIndicatorForm(item)}
                            >
                              Editar
                            </button>

                            <ActiveToggle
                              active={item.is_active}
                              disabled={departmentIndicators.saving}
                              helpHint={SI_HELP.indicator.isActive}
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
                </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}