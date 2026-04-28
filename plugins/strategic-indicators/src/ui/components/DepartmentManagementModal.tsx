import { useMemo, useState } from "react";
import { Modal } from "./Modal";
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
            <input
              value={indicatorForm.indicator_id}
              disabled={indicatorFormMode === "edit"}
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
            <select
              value={indicatorForm.scope_type}
              onChange={(event) =>
                setIndicatorForm((current) => ({
                  ...current,
                  scope_type: event.target.value as "consolidated" | "per_unit",
                }))
              }
            >
              <option value="consolidated">{getScopeTypeLabel("consolidated")}</option>
              <option value="per_unit">{getScopeTypeLabel("per_unit")}</option>
            </select>
          </label>

          <label className="si-admin-form-field">
            <span>Direção de performance</span>
            <select
              value={indicatorForm.performance_direction}
              onChange={(event) =>
                setIndicatorForm((current) => ({
                  ...current,
                  performance_direction: event.target.value as
                    | "higher_is_better"
                    | "lower_is_better",
                }))
              }
            >
              <option value="higher_is_better">
                {getPerformanceDirectionLabel("higher_is_better")}
              </option>
              <option value="lower_is_better">
                {getPerformanceDirectionLabel("lower_is_better")}
              </option>
            </select>
          </label>

          <label className="si-admin-form-field">
            <span>Chave da fonte</span>
            <input
              value={indicatorForm.source_key}
              onChange={(event) =>
                setIndicatorForm((current) => ({
                  ...current,
                  source_key: event.target.value,
                }))
              }
            />
          </label>
          
          <label className="si-admin-form-field">
            <span>Unidade</span>
            <select
              value={indicatorForm.value_unit}
              onChange={(event) =>
                setIndicatorForm((current) => ({
                  ...current,
                  value_unit: event.target.value,
                }))
              }
            >
              <option value="">Não informada</option>
              <option value="percent">Percentual</option>
              <option value="currency">Moeda</option>
              <option value="ppm">PPM</option>
              <option value="days">Dias</option>
              <option value="hours">Horas</option>
              <option value="count">Quantidade</option>
              <option value="months">Meses</option>
              <option value="ratio">Razão</option>
            </select>
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
            <textarea
              rows={3}
              value={indicatorForm.strategic_description}
              onChange={(event) =>
                setIndicatorForm((current) => ({
                  ...current,
                  strategic_description: event.target.value,
                }))
              }
            />
          </label>
        </div>
      </Modal>
    </>
  );
}