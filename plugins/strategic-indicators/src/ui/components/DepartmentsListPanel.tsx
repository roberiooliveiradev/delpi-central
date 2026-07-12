import { useMemo, useState } from "react";
import { InfoState } from "./InfoState";
import { Modal } from "./Modal";
import { SiNativeTextAreaControl, SiNativeTextControl } from "./siNativeFormFields";
import { DataTable, type DataTableColumn } from "./DataTable";
import { ActionButtons } from "./ActionButtons";
import { useStrategicIndicatorsAdminDepartments } from "../../state/hooks/useStrategicIndicatorsAdminDepartments";
import type {
  AdminDepartmentItem,
  CreateAdminDepartmentRequest,
  UpdateAdminDepartmentRequest,
} from "../../data/types/settings";
import { DepartmentManagementModal } from "./DepartmentManagementModal";
import { getAggregationModeLabel } from "../presentation/labels";
import "./DepartmentsListPanel.css";
import { SiSelectControl } from "./siFiltersUi";

type DepartmentsListPanelProps = {
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

export function DepartmentsListPanel({
  getAccessToken,
}: DepartmentsListPanelProps) {
  const departments = useStrategicIndicatorsAdminDepartments({ getAccessToken });

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<"all" | "active" | "inactive">("all");

  const [departmentFormOpen, setDepartmentFormOpen] = useState(false);
  const [departmentFormMode, setDepartmentFormMode] = useState<"create" | "edit">("create");
  const [departmentForm, setDepartmentForm] = useState<DepartmentFormState>(emptyDepartmentForm);

  const [openedDepartment, setOpenedDepartment] = useState<AdminDepartmentItem | null>(null);

  const filteredItems = useMemo(() => {
    return departments.items.filter((item) => {
      const matchesSearch =
        !search.trim() ||
        item.department_name.toLowerCase().includes(search.toLowerCase()) ||
        item.short_name.toLowerCase().includes(search.toLowerCase()) ||
        item.department_id.toLowerCase().includes(search.toLowerCase());

      const matchesStatus =
        statusFilter === "all" ||
        (statusFilter === "active" && item.is_active) ||
        (statusFilter === "inactive" && !item.is_active);

      return matchesSearch && matchesStatus;
    });
  }, [departments.items, search, statusFilter]);

  function openCreateDepartmentForm() {
    setDepartmentFormMode("create");
    setDepartmentForm(emptyDepartmentForm);
    setDepartmentFormOpen(true);
  }

  function openEditDepartmentForm(item: AdminDepartmentItem) {
    setDepartmentFormMode("edit");
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
    setDepartmentFormOpen(true);
  }

  async function handleSubmitDepartmentForm() {
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

    setDepartmentFormOpen(false);
  }

  const columns: DataTableColumn<AdminDepartmentItem>[] = [
    {
      key: "department",
      header: "Departamento",
      render: (row) => (
        <div className="si-admin-table-cell">
          <strong>{row.department_name}</strong>
          <span>{row.short_name}</span>
          <small>{row.department_id}</small>
        </div>
      ),
    },
    {
      key: "summary",
      header: "Resumo",
      render: (row) => row.strategic_summary || "Sem resumo estratégico.",
    },
    {
      key: "meta",
      header: "Estrutura",
      render: (row) => (
        <div className="si-admin-table-cell">
          <span>Peso: {row.weight_pct}%</span>
          <span>{getAggregationModeLabel(row.aggregation_mode)}</span>
          <span>{row.is_active ? "Ativo" : "Inativo"}</span>
        </div>
      ),
    },
    {
      key: "actions",
      header: "Ações",
      render: (row) => (
        <ActionButtons
          onOpen={() => setOpenedDepartment(row)}
          onEdit={() => openEditDepartmentForm(row)}
          onActivate={
            !row.is_active
              ? () => void departments.activateDepartment(row.department_id)
              : undefined
          }
          onDeactivate={
            row.is_active
              ? () => void departments.deactivateDepartment(row.department_id)
              : undefined
          }
          disabled={departments.saving}
        />
      ),
    },
  ];

  return (
    <>
      <div className="si-admin-list-shell">
        <div className="si-admin-list-toolbar">
          <label className="si-admin-form-field si-admin-form-field--compact">
            <span>Busca</span>
            <SiNativeTextControl
              value={search}
              onChange={setSearch}
              placeholder="Nome, sigla ou ID"
            />
          </label>

          <label className="si-admin-form-field si-admin-form-field--compact">
            <span>Status</span>
            <SiSelectControl
              value={statusFilter}
              onChange={(value) =>
                setStatusFilter(value as "all" | "active" | "inactive")
              }
              options={[
                { value: "all", label: "Todos" },
                { value: "active", label: "Ativos" },
                { value: "inactive", label: "Inativos" },
              ]}
            />
          </label>

          <div className="si-admin-list-toolbar__actions">
            <button
              type="button"
              className="si-settings-editor__button"
              onClick={openCreateDepartmentForm}
            >
              Novo departamento
            </button>
          </div>
        </div>

        {departments.error ? (
          <InfoState
            title="Falha ao carregar departamentos"
            description={departments.error}
            actionLabel="Recarregar"
            onAction={() => void departments.reload()}
          />
        ) : null}

        {!!departments.successMessage ? (
          <div className="si-settings-editor__alert si-settings-editor__alert--success">
            {departments.successMessage}
          </div>
        ) : null}

        <DataTable
          columns={columns}
          rows={filteredItems}
          loading={departments.loading || departments.refreshing}
          emptyText="Nenhum departamento encontrado."
          getRowKey={(row) => row.department_id}
        />
      </div>

      <Modal
        open={departmentFormOpen}
        onClose={() => setDepartmentFormOpen(false)}
        title={departmentFormMode === "create" ? "Novo departamento" : "Editar departamento"}
        description="Defina a base executiva e estrutural do departamento."
        size="lg"
        footer={
          <>
            <button
              type="button"
              className="si-settings-editor__button si-settings-editor__button--secondary"
              onClick={() => setDepartmentFormOpen(false)}
            >
              Cancelar
            </button>
            <button
              type="button"
              className="si-settings-editor__button"
              onClick={() => void handleSubmitDepartmentForm()}
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
            <SiNativeTextControl
              value={departmentForm.department_id}
              disabled={departmentFormMode === "edit"}
              onChange={(value) =>
                setDepartmentForm((current) => ({
                  ...current,
                  department_id: value,
                }))
              }
            />
          </label>

          <label className="si-admin-form-field">
            <span>Nome</span>
            <SiNativeTextControl
              value={departmentForm.department_name}
              onChange={(value) =>
                setDepartmentForm((current) => ({
                  ...current,
                  department_name: value,
                }))
              }
            />
          </label>

          <label className="si-admin-form-field">
            <span>Sigla</span>
            <SiNativeTextControl
              value={departmentForm.short_name}
              onChange={(value) =>
                setDepartmentForm((current) => ({
                  ...current,
                  short_name: value,
                }))
              }
            />
          </label>

          <label className="si-admin-form-field">
            <span>Peso</span>
            <SiNativeTextControl
              type="number"
              value={departmentForm.weight_pct}
              onChange={(value) =>
                setDepartmentForm((current) => ({
                  ...current,
                  weight_pct: Number(value || 0),
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
            <SiNativeTextControl
              type="number"
              value={departmentForm.display_order}
              onChange={(value) =>
                setDepartmentForm((current) => ({
                  ...current,
                  display_order: Number(value || 0),
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
            <SiNativeTextControl
              value={departmentForm.headline_goal}
              onChange={(value) =>
                setDepartmentForm((current) => ({
                  ...current,
                  headline_goal: value,
                }))
              }
            />
          </label>

          <label className="si-admin-form-field">
            <span>Foco complementar</span>
            <SiNativeTextControl
              value={departmentForm.supporting_focus}
              onChange={(value) =>
                setDepartmentForm((current) => ({
                  ...current,
                  supporting_focus: value,
                }))
              }
            />
          </label>
        </div>
      </Modal>

      <DepartmentManagementModal
        department={openedDepartment}
        open={!!openedDepartment}
        onClose={() => setOpenedDepartment(null)}
        getAccessToken={getAccessToken}
        onEditDepartment={openEditDepartmentForm}
        onActivateDepartment={(departmentId) =>
          void departments.activateDepartment(departmentId)
        }
        onDeactivateDepartment={(departmentId) =>
          void departments.deactivateDepartment(departmentId)
        }
        onDeleteDepartment={(departmentId) =>
          void departments.removeDepartment(departmentId)
        }
      />
    </>
  );
}