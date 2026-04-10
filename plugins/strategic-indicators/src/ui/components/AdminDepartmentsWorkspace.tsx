import { useMemo, useState } from "react";
import type {
  AdminDepartmentItem,
  CreateAdminDepartmentRequest,
  UpdateAdminDepartmentRequest,
} from "../../data/types/settings";
import { useStrategicIndicatorsAdminDepartments } from "../../state/hooks/useStrategicIndicatorsAdminDepartments";
import { useStrategicIndicatorsDepartmentIndicators } from "../../state/hooks/useStrategicIndicatorsDepartmentIndicators";
import { InfoState } from "./InfoState";
import { Modal } from "./Modal";
import { SectionBlock } from "./SectionBlock";

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
  strategic_description: string;
  source_key: string;
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
  strategic_description: "",
  source_key: "",
  display_order: 0,
  is_active: true,
};

export function AdminDepartmentsWorkspace({
  getAccessToken,
}: AdminDepartmentsWorkspaceProps) {
  const departments = useStrategicIndicatorsAdminDepartments({ getAccessToken });

  const [selectedDepartmentId, setSelectedDepartmentId] = useState<string | null>(null);
  const [departmentModalOpen, setDepartmentModalOpen] = useState(false);
  const [departmentMode, setDepartmentMode] = useState<"create" | "edit">("create");
  const [departmentForm, setDepartmentForm] =
    useState<DepartmentFormState>(emptyDepartmentForm);

  const [indicatorModalOpen, setIndicatorModalOpen] = useState(false);
  const [indicatorMode, setIndicatorMode] = useState<"create" | "edit">("create");
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

  function openCreateDepartmentModal() {
    setDepartmentMode("create");
    setDepartmentForm(emptyDepartmentForm);
    setDepartmentModalOpen(true);
  }

  function openEditDepartmentModal(item: AdminDepartmentItem) {
    setDepartmentMode("edit");
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
    setDepartmentModalOpen(true);
  }

  function openCreateIndicatorModal() {
    setIndicatorMode("create");
    setIndicatorForm(emptyIndicatorForm);
    setIndicatorModalOpen(true);
  }

  function openEditIndicatorModal(
    item: Awaited<
      ReturnType<typeof useStrategicIndicatorsDepartmentIndicators>
    >["items"][number],
  ) {
    setIndicatorMode("edit");
    setIndicatorForm({
      indicator_id: item.indicator_id,
      indicator_name: item.indicator_name,
      weight_pct: item.weight_pct,
      scope_type: item.scope_type,
      strategic_description: item.strategic_description,
      source_key: item.source_key ?? "",
      display_order: item.display_order,
      is_active: item.is_active,
    });
    setIndicatorModalOpen(true);
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
    } else {
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

      await departments.updateDepartment(departmentForm.department_id, payload);
    }

    setDepartmentModalOpen(false);
  }

  async function handleSubmitIndicator() {
    if (!selectedDepartmentId) return;

    if (indicatorMode === "create") {
      await departmentIndicators.createIndicator({
        indicator_id: indicatorForm.indicator_id.trim(),
        indicator_name: indicatorForm.indicator_name.trim(),
        weight_pct: Number(indicatorForm.weight_pct || 0),
        scope_type: indicatorForm.scope_type,
        strategic_description: indicatorForm.strategic_description.trim(),
        source_key: indicatorForm.source_key.trim() || null,
        display_order: Number(indicatorForm.display_order || 0),
      });
    } else {
      await departmentIndicators.updateIndicator(indicatorForm.indicator_id, {
        indicator_name: indicatorForm.indicator_name.trim(),
        weight_pct: Number(indicatorForm.weight_pct || 0),
        scope_type: indicatorForm.scope_type,
        strategic_description: indicatorForm.strategic_description.trim(),
        source_key: indicatorForm.source_key.trim() || null,
        display_order: Number(indicatorForm.display_order || 0),
        is_active: indicatorForm.is_active,
      });
    }

    setIndicatorModalOpen(false);
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
            onClick={openCreateDepartmentModal}
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
                onAction={openCreateDepartmentModal}
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
                        onClick={() => openEditDepartmentModal(selectedDepartment)}
                      >
                        Editar
                      </button>

                      <button
                        type="button"
                        className="si-settings-editor__button si-settings-editor__button--secondary"
                        onClick={() =>
                          void departments.deactivateDepartment(selectedDepartment.department_id)
                        }
                      >
                        Desativar
                      </button>

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
                      <strong>{selectedDepartment.aggregation_mode}</strong>
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
                      onClick={openCreateIndicatorModal}
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
                      onAction={openCreateIndicatorModal}
                    />
                  ) : (
                    <div className="si-admin-indicators-table">
                      {departmentIndicators.items.map((item) => (
                        <article
                          key={item.indicator_id}
                          className="si-admin-indicators-table__row"
                        >
                          <div>
                            <strong>{item.indicator_name}</strong>
                            <p>{item.strategic_description || "Sem descrição estratégica."}</p>
                          </div>

                          <div className="si-admin-indicators-table__meta">
                            <span>{item.weight_pct}%</span>
                            <span>{item.scope_type}</span>
                            <span>{item.is_active ? "Ativo" : "Inativo"}</span>
                          </div>

                          <div className="si-admin-indicators-table__actions">
                            <button
                              type="button"
                              className="si-settings-editor__button si-settings-editor__button--secondary"
                              onClick={() => openEditIndicatorModal(item)}
                            >
                              Editar
                            </button>

                            <button
                              type="button"
                              className="si-settings-editor__button si-settings-editor__button--secondary"
                              onClick={() =>
                                void departmentIndicators.deactivateIndicator(item.indicator_id)
                              }
                            >
                              Desativar
                            </button>

                            <button
                              type="button"
                              className="si-settings-editor__button si-settings-editor__button--secondary"
                              onClick={() =>
                                void departmentIndicators.removeIndicator(item.indicator_id)
                              }
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

      <Modal
        open={departmentModalOpen}
        onClose={() => setDepartmentModalOpen(false)}
        title={departmentMode === "create" ? "Novo departamento" : "Editar departamento"}
        description="Defina a base executiva e estrutural do departamento."
        size="lg"
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
              disabled={departmentMode === "edit"}
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
            <select
              value={departmentForm.aggregation_mode}
              onChange={(event) =>
                setDepartmentForm((current) => ({
                  ...current,
                  aggregation_mode: event.target.value as "consolidated" | "average_of_units",
                }))
              }
            >
              <option value="consolidated">consolidated</option>
              <option value="average_of_units">average_of_units</option>
            </select>
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
            <textarea
              rows={3}
              value={departmentForm.strategic_summary}
              onChange={(event) =>
                setDepartmentForm((current) => ({
                  ...current,
                  strategic_summary: event.target.value,
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

        <div className="si-admin-modal-actions">
          <button
            type="button"
            className="si-settings-editor__button si-settings-editor__button--secondary"
            onClick={() => setDepartmentModalOpen(false)}
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
        </div>
      </Modal>

      <Modal
        open={indicatorModalOpen}
        onClose={() => setIndicatorModalOpen(false)}
        title={indicatorMode === "create" ? "Novo indicador estrutural" : "Editar indicador estrutural"}
        description="Defina a estrutura oficial do indicador dentro do departamento."
        size="lg"
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
              disabled={indicatorMode === "edit"}
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
              <option value="consolidated">consolidated</option>
              <option value="per_unit">per_unit</option>
            </select>
          </label>

          <label className="si-admin-form-field">
            <span>Source key</span>
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

        <div className="si-admin-modal-actions">
          <button
            type="button"
            className="si-settings-editor__button si-settings-editor__button--secondary"
            onClick={() => setIndicatorModalOpen(false)}
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
        </div>
      </Modal>
    </div>
  );
}