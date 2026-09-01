import { SectionHintLabel } from "@delpi/plugin-ui/index";
import { useEffect, useState, type ReactNode } from "react";
import type { AdminDepartmentItem } from "../../data/types/settings";
import { SI_HELP } from "../../content/helpTooltips";
import { getAggregationModeLabel } from "../presentation/labels";
import { ActiveToggle } from "./ActiveToggle";
import { DrawerPanel } from "./DrawerPanel";
import { SiAdminFormField } from "./SiAdminFormField";
import { SiSelectControl } from "./siFiltersUi";
import { SiNativeTextAreaControl, SiNativeTextControl } from "./siNativeFormFields";
import "./AdminDepartmentFormDrawer.css";

export type DepartmentFormState = {
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

export const emptyDepartmentForm: DepartmentFormState = {
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

export function departmentFormFromItem(item: AdminDepartmentItem): DepartmentFormState {
  return {
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
  };
}

type DepartmentAccordionPanel = "identity" | "idd" | "narrative";

type AdminDepartmentFormDrawerProps = {
  open: boolean;
  mode: "create" | "edit";
  saving: boolean;
  form: DepartmentFormState;
  onClose: () => void;
  onChange: (next: DepartmentFormState) => void;
  onSubmit: () => Promise<void>;
};

function validateDepartmentForm(
  form: DepartmentFormState,
  mode: "create" | "edit",
): { message: string; panel: DepartmentAccordionPanel } | null {
  if (mode === "create" && !form.department_id.trim()) {
    return { message: "Informe o ID técnico do departamento.", panel: "identity" };
  }
  if (!form.department_name.trim()) {
    return { message: "Informe o nome do departamento.", panel: "identity" };
  }
  if (!form.short_name.trim()) {
    return { message: "Informe a sigla do departamento.", panel: "identity" };
  }
  return null;
}

type AccordionPanelProps = {
  panelId: DepartmentAccordionPanel;
  title: string;
  hint: string;
  open: boolean;
  onToggle: () => void;
  children: ReactNode;
};

function AccordionPanel({
  panelId,
  title,
  hint,
  open,
  onToggle,
  children,
}: AccordionPanelProps) {
  return (
    <section
      className={`si-dept-form-drawer__panel ${open ? "is-open" : ""}`}
      data-panel={panelId}
    >
      <button
        type="button"
        className="si-dept-form-drawer__panel-trigger"
        aria-expanded={open}
        onClick={onToggle}
      >
        <SectionHintLabel label={title} hint={hint} />
        <span className="si-dept-form-drawer__panel-icon" aria-hidden>
          {open ? "−" : "+"}
        </span>
      </button>
      {open ? <div className="si-dept-form-drawer__panel-body">{children}</div> : null}
    </section>
  );
}

export function AdminDepartmentFormDrawer({
  open,
  mode,
  saving,
  form,
  onClose,
  onChange,
  onSubmit,
}: AdminDepartmentFormDrawerProps) {
  const [openPanel, setOpenPanel] = useState<DepartmentAccordionPanel>("identity");
  const [localError, setLocalError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setOpenPanel("identity");
      setLocalError(null);
    }
  }, [open, mode]);

  function patchForm(patch: Partial<DepartmentFormState>) {
    onChange({ ...form, ...patch });
  }

  async function handleSave() {
    const validationError = validateDepartmentForm(form, mode);
    if (validationError) {
      setLocalError(validationError.message);
      setOpenPanel(validationError.panel);
      return;
    }
    setLocalError(null);
    await onSubmit();
  }

  const title = mode === "create" ? "Novo departamento" : "Editar departamento";

  return (
    <DrawerPanel
      open={open}
      onClose={onClose}
      title={title}
      description="Identidade, IDD e narrativa estratégica do departamento."
      size="lg"
      footer={
        <>
          <button
            type="button"
            className="si-settings-editor__button si-settings-editor__button--secondary"
            onClick={onClose}
          >
            Cancelar
          </button>
          <button
            type="button"
            className="si-settings-editor__button"
            onClick={() => void handleSave()}
            disabled={saving}
          >
            {saving ? "Salvando..." : "Salvar"}
          </button>
        </>
      }
    >
      {localError ? (
        <p className="si-dept-form-drawer__error" role="alert">
          {localError}
        </p>
      ) : null}

      <div className="si-dept-form-drawer__accordion">
        <AccordionPanel
          panelId="identity"
          title="Identidade"
          hint={SI_HELP.department.sectionIdentity}
          open={openPanel === "identity"}
          onToggle={() => setOpenPanel("identity")}
        >
          <div className="si-admin-form-grid">
            <SiAdminFormField label="ID" hint={SI_HELP.department.departmentId}>
              <SiNativeTextControl
                value={form.department_id}
                onChange={(value) => patchForm({ department_id: value })}
              />
            </SiAdminFormField>

            <SiAdminFormField label="Nome" hint={SI_HELP.department.departmentName}>
              <SiNativeTextControl
                value={form.department_name}
                onChange={(value) => patchForm({ department_name: value })}
              />
            </SiAdminFormField>

            <SiAdminFormField label="Sigla" hint={SI_HELP.department.shortName}>
              <SiNativeTextControl
                value={form.short_name}
                onChange={(value) => patchForm({ short_name: value })}
              />
            </SiAdminFormField>
          </div>
        </AccordionPanel>

        <AccordionPanel
          panelId="idd"
          title="IDD & peso"
          hint={SI_HELP.department.sectionIdd}
          open={openPanel === "idd"}
          onToggle={() => setOpenPanel("idd")}
        >
          <div className="si-admin-form-grid">
            <SiAdminFormField label="Peso" hint={SI_HELP.department.weightPct}>
              <SiNativeTextControl
                type="number"
                value={form.weight_pct}
                onChange={(value) => patchForm({ weight_pct: Number(value || 0) })}
              />
            </SiAdminFormField>

            <SiAdminFormField label="Agregação" hint={SI_HELP.department.aggregationMode}>
              <SiSelectControl
                value={form.aggregation_mode}
                onChange={(value) =>
                  patchForm({
                    aggregation_mode: value as DepartmentFormState["aggregation_mode"],
                  })
                }
                options={[
                  { value: "consolidated", label: getAggregationModeLabel("consolidated") },
                  {
                    value: "average_of_units",
                    label: getAggregationModeLabel("average_of_units"),
                  },
                ]}
              />
            </SiAdminFormField>

            <SiAdminFormField label="Ordem" hint={SI_HELP.department.displayOrder}>
              <SiNativeTextControl
                type="number"
                value={form.display_order}
                onChange={(value) => patchForm({ display_order: Number(value || 0) })}
              />
            </SiAdminFormField>

            {mode === "edit" ? (
              <SiAdminFormField label="Ativo" hint={SI_HELP.department.isActive}>
                <ActiveToggle
                  active={form.is_active}
                  disabled={saving}
                  helpHint={SI_HELP.department.isActive}
                  ariaLabel="Departamento ativo"
                  onToggle={(is_active) => patchForm({ is_active })}
                />
              </SiAdminFormField>
            ) : null}
          </div>
        </AccordionPanel>

        <AccordionPanel
          panelId="narrative"
          title="Resumo estratégico"
          hint={SI_HELP.department.sectionNarrative}
          open={openPanel === "narrative"}
          onToggle={() => setOpenPanel("narrative")}
        >
          <div className="si-admin-form-grid">
            <SiAdminFormField
              label="Resumo estratégico"
              hint={SI_HELP.department.strategicSummary}
              fullWidth
            >
              <SiNativeTextAreaControl
                rows={3}
                value={form.strategic_summary}
                aria-label="Resumo estratégico"
                onChange={(strategic_summary) => patchForm({ strategic_summary })}
              />
            </SiAdminFormField>

            <SiAdminFormField label="Meta principal" hint={SI_HELP.department.headlineGoal}>
              <SiNativeTextControl
                value={form.headline_goal}
                onChange={(value) => patchForm({ headline_goal: value })}
              />
            </SiAdminFormField>

            <SiAdminFormField label="Foco complementar" hint={SI_HELP.department.supportingFocus}>
              <SiNativeTextControl
                value={form.supporting_focus}
                onChange={(value) => patchForm({ supporting_focus: value })}
              />
            </SiAdminFormField>
          </div>
        </AccordionPanel>
      </div>
    </DrawerPanel>
  );
}
