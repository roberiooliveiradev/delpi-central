import { useMemo, useState } from "react";
import { Modal } from "./Modal";
import { SiNativeTextAreaControl, SiNativeTextControl } from "./siNativeFormFields";
import { SectionBlock } from "./SectionBlock";
import { InfoState } from "./InfoState";
import { ActionButtons } from "./ActionButtons";
import { useStrategicIndicatorsDepartmentIndicators } from "../../state/hooks/useStrategicIndicatorsDepartmentIndicators";
import { DepartmentGoalsPanel } from "./DepartmentGoalsPanel";
import type {
  AdminDepartmentItem,
  AdminDepartmentIndicatorItem,
  CreateAdminDepartmentIndicatorRequest,
  UpdateAdminDepartmentIndicatorRequest,
} from "../../data/types/settings";
import {
  getAggregationModeLabel,
  getPerformanceDirectionLabel,
  getScopeTypeLabel,
} from "../presentation/labels";
import { validateIndicatorSourceKey } from "../utils/indicatorSourceKeyValidation";
import "./DepartmentManagementModal.css";
import { SI_VALUE_UNIT_OPTIONS, SiSelectControl } from "./siFiltersUi";

type DepartmentManagementModalProps = {
  department: AdminDepartmentItem | null;
  open: boolean;
  onClose: () => void;
  getAccessToken?: () => string | undefined;
  onEditDepartment: (department: AdminDepartmentItem) => void;
  onActivateDepartment?: (departmentId: string) => void;
  onDeactivateDepartment?: (departmentId: string) => void;
  onDeleteDepartment?: (departmentId: string) => void;
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

export function DepartmentManagementModal({
  open,
  department,
  onClose,
  getAccessToken,
  onEditDepartment,
  onActivateDepartment,
  onDeactivateDepartment,
  onDeleteDepartment,
}: DepartmentManagementModalProps) {
  const departmentIndicators = useStrategicIndicatorsDepartmentIndicators({
    departmentId: department?.department_id ?? null,
    getAccessToken,
  });

  const [indicatorFormOpen, setIndicatorFormOpen] = useState(false);
  const [indicatorFormMode, setIndicatorFormMode] = useState<"create" | "edit">("create");
  const [indicatorForm, setIndicatorForm] = useState<IndicatorFormState>(emptyIndicatorForm);
  const [indicatorFormError, setIndicatorFormError] = useState<string | null>(null);

  const selectedDepartmentId = department?.department_id ?? null;

  function openCreateIndicatorForm() {
    setIndicatorFormMode("create");
    setIndicatorForm(emptyIndicatorForm);
    setIndicatorFormOpen(true);
  }

  function openEditIndicatorForm(item: AdminDepartmentIndicatorItem) {
    setIndicatorFormMode("edit");
    setIndicatorForm({
      indicator_id: item.indicator_id,
      indicator_name: item.indicator_name,
      weight_pct: item.weight_pct,
      scope_type: item.scope_type,
      performance_direction: item.performance_direction,
      strategic_description: item.strategic_description,
      source_key: item.source_key ?? "",
      display_order: item.display_order,
      is_active: item.is_active,
      value_unit: item.value_unit ?? "",
      value_prefix: item.value_prefix ?? "",
      value_suffix: item.value_suffix ?? "",
      value_decimals: Number(item.value_decimals ?? 2),
    });
    setIndicatorFormOpen(true);
  }

  async function handleSubmitIndicatorForm() {
    if (!selectedDepartmentId) return;

    const sourceKeyError = validateIndicatorSourceKey(
      indicatorForm.source_key,
      indicatorFormMode === "create" ? true : indicatorForm.is_active,
    );
    if (sourceKeyError) {
      setIndicatorFormError(sourceKeyError);
      return;
    }
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
        display_order: Number(indicatorForm.display_order || 0),
        value_unit: indicatorForm.value_unit.trim() || null,
        value_prefix: indicatorForm.value_prefix.trim() || null,
        value_suffix: indicatorForm.value_suffix.trim() || null,
        value_decimals: Number(indicatorForm.value_decimals ?? 2),
      };

      await departmentIndicators.createIndicator(payload);
    } else {
      const payload: UpdateAdminDepartmentIndicatorRequest = {
        indicator_name: indicatorForm.indicator_name.trim(),
        weight_pct: Number(indicatorForm.weight_pct || 0),
        scope_type: indicatorForm.scope_type,
        performance_direction: indicatorForm.performance_direction,
        strategic_description: indicatorForm.strategic_description.trim(),
        source_key: indicatorForm.source_key.trim() || null,
        display_order: Number(indicatorForm.display_order || 0),
        is_active: indicatorForm.is_active,
        value_unit: indicatorForm.value_unit.trim() || null,
        value_prefix: indicatorForm.value_prefix.trim() || null,
        value_suffix: indicatorForm.value_suffix.trim() || null,
        value_decimals: Number(indicatorForm.value_decimals ?? 2),
      };

      await departmentIndicators.updateIndicator(indicatorForm.indicator_id, payload);
    }

    setIndicatorFormOpen(false);
  }

  const indicatorsRows = useMemo(() => departmentIndicators.items, [departmentIndicators.items]);

  return (
    <>
      <Modal
        open={open}
        onClose={onClose}
        title={department ? `Departamento: ${department.department_name}` : "Departamento"}
        description="Gestão completa do departamento selecionado."
        size="xl"
      >
        {!department ? null : (
          <div className="si-department-workspace">
            <SectionBlock
              title={department.department_name}
              description={department.strategic_summary || "Sem resumo estratégico."}
              aside={
                <div className="si-admin-inline-actions">
                  <button
                    type="button"
                    className="si-settings-editor__button si-settings-editor__button--secondary"
                    onClick={() => onEditDepartment(department)}
                  >
                    Editar departamento
                  </button>

                  {!department.is_active && onActivateDepartment ? (
                    <button
                      type="button"
                      className="si-settings-editor__button"
                      onClick={() => onActivateDepartment(department.department_id)}
                    >
                      Ativar
                    </button>
                  ) : null}

                  {department.is_active && onDeactivateDepartment ? (
                    <button
                      type="button"
                      className="si-settings-editor__button si-settings-editor__button--secondary"
                      onClick={() => onDeactivateDepartment(department.department_id)}
                    >
                      Desativar
                    </button>
                  ) : null}

                  {onDeleteDepartment ? (
                    <button
                      type="button"
                      className="si-settings-editor__button si-settings-editor__button--secondary"
                      onClick={() => onDeleteDepartment(department.department_id)}
                    >
                      Excluir
                    </button>
                  ) : null}
                </div>
              }
            >
              <div className="si-admin-detail-grid">
                <div className="si-admin-detail-card">
                  <span className="si-admin-detail-card__label">Meta principal</span>
                  <strong>{department.headline_goal || "—"}</strong>
                </div>
                <div className="si-admin-detail-card">
                  <span className="si-admin-detail-card__label">Foco complementar</span>
                  <strong>{department.supporting_focus || "—"}</strong>
                </div>
                <div className="si-admin-detail-card">
                  <span className="si-admin-detail-card__label">Peso no IGD</span>
                  <strong>{department.weight_pct}%</strong>
                </div>
                <div className="si-admin-detail-card">
                  <span className="si-admin-detail-card__label">Agregação</span>
                  <strong>{getAggregationModeLabel(department.aggregation_mode)}</strong>
                </div>
              </div>
            </SectionBlock>

            <SectionBlock
              title="Indicadores estruturais"
              description="Catálogo oficial de indicadores do departamento."
              aside={
                <button
                  type="button"
                  className="si-settings-editor__button"
                  onClick={openCreateIndicatorForm}
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
              ) : indicatorsRows.length === 0 ? (
                <InfoState
                  title="Nenhum indicador estrutural cadastrado"
                  description="Crie os indicadores oficiais deste departamento para habilitar metas anuais."
                  actionLabel="Criar indicador"
                  onAction={openCreateIndicatorForm}
                />
              ) : (
                <div className="si-admin-card-list">
                  {indicatorsRows.map((item) => (
                    <article key={item.indicator_id} className="si-admin-card-list__item">
                      <div className="si-admin-card-list__content">
                        <strong>{item.indicator_name}</strong>
                        <p>{item.strategic_description || "Sem descrição estratégica."}</p>
                        <small>
                          {item.weight_pct}% · {getScopeTypeLabel(item.scope_type)} ·{" "}
                          {item.value_prefix || ""}
                          {item.value_suffix ? ` ${item.value_suffix}` : item.value_unit ? ` ${item.value_unit}` : ""} ·{" "}
                          {item.is_active ? "Ativo" : "Inativo"}
                        </small>
                      </div>
                      <ActionButtons
                        onEdit={() => openEditIndicatorForm(item)}
                        onActivate={
                          !item.is_active
                            ? () => void departmentIndicators.activateIndicator(item.indicator_id)
                            : undefined
                        }
                        onDeactivate={
                          item.is_active
                            ? () => void departmentIndicators.deactivateIndicator(item.indicator_id)
                            : undefined
                        }
                        disabled={departmentIndicators.saving}
                      />
                    </article>
                  ))}
                </div>
              )}
            </SectionBlock>

            <DepartmentGoalsPanel
              departmentId={department.department_id}
              getAccessToken={getAccessToken}
              indicators={departmentIndicators.items}
            />
          </div>
        )}
      </Modal>

      <Modal
        open={indicatorFormOpen}
        onClose={() => setIndicatorFormOpen(false)}
        title={
          indicatorFormMode === "create"
            ? "Novo indicador estrutural"
            : "Editar indicador estrutural"
        }
        description="Defina a estrutura oficial do indicador dentro do departamento."
        size="lg"
        footer={
          <>
            <button
              type="button"
              className="si-settings-editor__button si-settings-editor__button--secondary"
              onClick={() => setIndicatorFormOpen(false)}
            >
              Cancelar
            </button>
            <button
              type="button"
              className="si-settings-editor__button"
              onClick={() => void handleSubmitIndicatorForm()}
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
            <SiNativeTextControl
              value={indicatorForm.indicator_id}
              disabled={indicatorFormMode === "edit"}
              onChange={(value) =>
                setIndicatorForm((current) => ({
                  ...current,
                  indicator_id: value,
                }))
              }
            />
          </label>

          <label className="si-admin-form-field">
            <span>Nome</span>
            <SiNativeTextControl
              value={indicatorForm.indicator_name}
              onChange={(value) =>
                setIndicatorForm((current) => ({
                  ...current,
                  indicator_name: value,
                }))
              }
            />
          </label>

          <label className="si-admin-form-field">
            <span>Peso</span>
            <SiNativeTextControl
              type="number"
              value={indicatorForm.weight_pct}
              onChange={(value) =>
                setIndicatorForm((current) => ({
                  ...current,
                  weight_pct: Number(value || 0),
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
            <SiNativeTextControl
              value={indicatorForm.source_key}
              placeholder="ex.: commercial_rol, production_otd"
              onChange={(value) =>
                setIndicatorForm((current) => ({
                  ...current,
                  source_key: value,
                }))
              }
            />
            <small className="si-admin-form-field__hint">
              Liga o indicador às medições do SI e às metas nos dashboards
              departamentais.
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
            <SiNativeTextControl
              placeholder="Ex.: R$"
              value={indicatorForm.value_prefix}
              onChange={(value) =>
                setIndicatorForm((current) => ({
                  ...current,
                  value_prefix: value,
                }))
              }
            />
          </label>

          <label className="si-admin-form-field">
            <span>Sufixo</span>
            <SiNativeTextControl
              placeholder="Ex.: %, PPM, /mês, dias"
              value={indicatorForm.value_suffix}
              onChange={(value) =>
                setIndicatorForm((current) => ({
                  ...current,
                  value_suffix: value,
                }))
              }
            />
          </label>

          <label className="si-admin-form-field">
            <span>Casas decimais</span>
            <SiNativeTextControl
              type="number"
              min={0}
              max={6}
              value={indicatorForm.value_decimals}
              onChange={(value) =>
                setIndicatorForm((current) => ({
                  ...current,
                  value_decimals: Number(value || 0),
                }))
              }
            />
          </label>
          <label className="si-admin-form-field">
            <span>Ordem</span>
            <SiNativeTextControl
              type="number"
              value={indicatorForm.display_order}
              onChange={(value) =>
                setIndicatorForm((current) => ({
                  ...current,
                  display_order: Number(value || 0),
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
      </Modal>
    </>
  );
}