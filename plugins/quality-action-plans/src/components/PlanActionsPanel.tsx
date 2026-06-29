import { useState } from "react";
import { Pencil, Trash2, X } from "lucide-react";

import {
  createPlanActions,
  deletePlanAction,
  updatePlanAction,
  type UpdatePlanActionPayload,
} from "../api/actionPlansApi";
import {
  ActionResponsibleField,
  type ActionResponsibleValue,
} from "./ActionResponsibleField";
import { RequiredEvidenceAlert } from "./RequiredEvidenceAlert";
import { FormActions } from "./ui/FormActions";
import { FieldLabel, TableHeaderCell } from "./ui/HelpTooltip";
import { SelectField } from "./ui/SelectField";
import { TextAreaField } from "./ui/TextAreaField";
import { TextField } from "./ui/TextField";
import {
  ACTION_STATUSES,
  ACTION_TYPES,
  actionTypeLabel,
} from "../constants/actionPlans";
import { PAC_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { PlanAction } from "../types/actionPlan";
import type { PlanEvidence } from "../types/rnc8d";
import { formatDate } from "../utils/format";
import type { SelectOption } from "./ui/types";

const T = PAC_HELP_TOOLTIPS.tables;

const CAUSE_TRACK_OPTIONS = [
  { value: "", label: "—" },
  { value: "occurrence", label: "Ocorrência" },
  { value: "detection", label: "Detecção" },
];

type ActionFormState = {
  actionType: string;
  description: string;
  responsible: ActionResponsibleValue;
  dueDate: string;
  causeTrack: string;
  status: string;
  evidenceRequired: boolean;
};

const EMPTY_RESPONSIBLE: ActionResponsibleValue = {
  responsibleUserId: null,
  responsibleName: "",
};

const EMPTY_FORM: ActionFormState = {
  actionType: "corrective",
  description: "",
  responsible: EMPTY_RESPONSIBLE,
  dueDate: "",
  causeTrack: "",
  status: "pending",
  evidenceRequired: false,
};

type Props = {
  planId: string;
  actions: PlanAction[];
  evidences: PlanEvidence[];
  saving: string | null;
  onSave: (key: string, action: () => Promise<void>) => Promise<void>;
  /** Quando informado (fluxo 8D), permite escolher membro da equipe além do vínculo Delpi. */
  responsibleOptions?: SelectOption[];
};

function toFormState(action: PlanAction): ActionFormState {
  return {
    actionType: action.action_type,
    description: action.description,
    responsible: {
      responsibleUserId: action.responsible_user_id ?? null,
      responsibleName: action.responsible_name ?? "",
    },
    dueDate: action.due_date?.slice(0, 10) ?? "",
    causeTrack: action.cause_track ?? "",
    status: action.status,
    evidenceRequired: Boolean(action.evidence_required),
  };
}

function responsiblePayload(responsible: ActionResponsibleValue): Pick<
  UpdatePlanActionPayload,
  "responsible_name" | "responsible_user_id"
> {
  const name = responsible.responsibleName.trim();
  return {
    responsible_name: name || undefined,
    responsible_user_id: responsible.responsibleUserId,
  };
}

function toUpdatePayload(form: ActionFormState): UpdatePlanActionPayload {
  return {
    action_type: form.actionType,
    description: form.description.trim(),
    ...responsiblePayload(form.responsible),
    due_date: form.dueDate || undefined,
    cause_track: form.causeTrack || undefined,
    status: form.status,
    evidence_required: form.evidenceRequired,
  };
}

export function PlanActionsPanel({
  planId,
  actions,
  evidences,
  saving,
  onSave,
  responsibleOptions,
}: Props) {
  const [editingActionId, setEditingActionId] = useState<string | null>(null);
  const [form, setForm] = useState<ActionFormState>(EMPTY_FORM);

  function resetForm() {
    setEditingActionId(null);
    setForm(EMPTY_FORM);
  }

  function startEdit(action: PlanAction) {
    setEditingActionId(action.id);
    setForm(toFormState(action));
  }

  async function handleDelete(action: PlanAction) {
    const label = action.description.trim().slice(0, 80);
    if (!window.confirm(`Remover a ação "${label}"?`)) {
      return;
    }
    await onSave(`delete-action-${action.id}`, async () => {
      await deletePlanAction(planId, action.id);
      if (editingActionId === action.id) {
        resetForm();
      }
    });
  }

  async function handleSubmit() {
    if (editingActionId) {
      await onSave(`edit-action-${editingActionId}`, async () => {
        if (!form.description.trim()) {
          throw new Error("Informe a descrição da ação.");
        }
        await updatePlanAction(planId, editingActionId, toUpdatePayload(form));
        resetForm();
      });
      return;
    }

    await onSave("new-action", async () => {
      if (!form.description.trim()) {
        throw new Error("Informe a descrição da ação.");
      }
      const responsible = responsiblePayload(form.responsible);
      await createPlanActions(planId, [
        {
          action_type: form.actionType,
          description: form.description.trim(),
          responsible_name: responsible.responsible_name,
          responsible_user_id: responsible.responsible_user_id || undefined,
          due_date: form.dueDate || undefined,
          cause_track: form.causeTrack || undefined,
          status: form.status,
          evidence_required: form.evidenceRequired,
        },
      ]);
      resetForm();
    });
  }

  const typeOptions = Object.entries(ACTION_TYPES).map(([value, label]) => ({ value, label }));
  const statusOptions = Object.entries(ACTION_STATUSES).map(([value, label]) => ({ value, label }));
  const isEditing = Boolean(editingActionId);
  const formBusy =
    saving === "new-action" ||
    (editingActionId ? saving === `edit-action-${editingActionId}` : false);

  return (
    <>
      <RequiredEvidenceAlert actions={actions} evidences={evidences} />

      {actions.length ? (
        <div className="pac-table-wrap">
          <table className="pac-table">
            <thead>
              <tr>
                <TableHeaderCell label="Tipo" hint={T.actionType} />
                <TableHeaderCell label="Ocorr./Det." hint={T.causeTrack} />
                <TableHeaderCell label="Descrição" hint={PAC_HELP_TOOLTIPS.form.actionDescription} />
                <TableHeaderCell label="Responsável" hint={PAC_HELP_TOOLTIPS.form.actionResponsible} />
                <TableHeaderCell label="Prazo" hint={T.dueDate} />
                <TableHeaderCell label="Evidência" hint={T.evidenceRequired} />
                <TableHeaderCell label="Status" hint={T.actionStatus} />
                <TableHeaderCell
                  label="Ações"
                  hint={T.rowActions}
                  className="pac-table__actions-col"
                />
              </tr>
            </thead>
            <tbody>
              {actions.map((action) => (
                <tr
                  key={action.id}
                  className={editingActionId === action.id ? "pac-table-row--editing" : undefined}
                >
                  <td>{actionTypeLabel(action.action_type)}</td>
                  <td>
                    {action.cause_track === "detection"
                      ? "Detecção"
                      : action.cause_track === "occurrence"
                        ? "Ocorrência"
                        : "—"}
                  </td>
                  <td>{action.description}</td>
                  <td>
                    <span className="pac-action-responsible-cell">
                      <span>{action.responsible_name ?? "—"}</span>
                      {action.responsible_user_id ? (
                        <span
                          className="pac-badge pac-badge--linked"
                          title={PAC_HELP_TOOLTIPS.form.actionResponsibleLinked}
                        >
                          Fila
                        </span>
                      ) : null}
                    </span>
                  </td>
                  <td>{formatDate(action.due_date)}</td>
                  <td className="pac-table-cell--evidence">
                    <span
                      className={`pac-evidence-chip__label pac-evidence-chip__label--static${
                        action.evidence_required ? " pac-evidence-chip__label--required" : ""
                      }`}
                    >
                      {action.evidence_required ? "Obrigatória" : "Opcional"}
                    </span>
                  </td>
                  <td>
                    {ACTION_STATUSES[action.status as keyof typeof ACTION_STATUSES] ?? action.status}
                  </td>
                  <td className="pac-table-actions">
                    <button
                      type="button"
                      className="pac-ghost-btn pac-ghost-btn--icon"
                      title="Editar ação"
                      disabled={Boolean(saving)}
                      onClick={() => startEdit(action)}
                    >
                      <Pencil size={16} />
                    </button>
                    <button
                      type="button"
                      className="pac-ghost-btn pac-ghost-btn--icon pac-ghost-btn--danger"
                      title="Excluir ação"
                      disabled={Boolean(saving)}
                      onClick={() => void handleDelete(action)}
                    >
                      <Trash2 size={16} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="pac-muted">Nenhuma ação cadastrada.</p>
      )}

      <div className={`pac-new-action-form${isEditing ? " pac-new-action-form--editing" : ""}`}>
        {isEditing ? (
          <div className="pac-new-action-form__banner">
            <span>Editando ação selecionada</span>
            <button type="button" className="pac-ghost-btn pac-ghost-btn--icon" onClick={resetForm}>
              <X size={16} />
              <span>Cancelar</span>
            </button>
          </div>
        ) : null}

        <div className="pac-form-grid pac-new-action-form__meta">
          <SelectField
            id="pac-action-type"
            label="Tipo"
            hint={PAC_HELP_TOOLTIPS.form.actionType}
            options={typeOptions}
            value={form.actionType}
            onChange={(actionType) => setForm((current) => ({ ...current, actionType }))}
            searchable={false}
          />
          <SelectField
            id="pac-action-track"
            label="Ocorrência / Detecção"
            hint={PAC_HELP_TOOLTIPS.form.actionTrack}
            options={CAUSE_TRACK_OPTIONS}
            value={form.causeTrack}
            onChange={(causeTrack) => setForm((current) => ({ ...current, causeTrack }))}
            searchable={false}
          />
          <TextField
            id="pac-action-due"
            label="Prazo"
            hint={PAC_HELP_TOOLTIPS.form.actionDueDate}
            type="date"
            value={form.dueDate}
            onChange={(dueDate) => setForm((current) => ({ ...current, dueDate }))}
          />
          <SelectField
            id="pac-action-status"
            label="Status"
            hint={PAC_HELP_TOOLTIPS.form.actionStatus}
            options={statusOptions}
            value={form.status}
            onChange={(status) => setForm((current) => ({ ...current, status }))}
            searchable={false}
          />
        </div>

        <ActionResponsibleField
          value={form.responsible}
          teamOptions={responsibleOptions}
          onChange={(responsible) => setForm((current) => ({ ...current, responsible }))}
        />

        <TextAreaField
          id="pac-action-desc"
          label="Descrição"
          hint={PAC_HELP_TOOLTIPS.form.actionDescription}
          value={form.description}
          onChange={(description) => setForm((current) => ({ ...current, description }))}
          rows={3}
          fullWidth
        />

        <label className="pac-checkbox-field">
          <input
            type="checkbox"
            checked={form.evidenceRequired}
            onChange={(event) =>
              setForm((current) => ({ ...current, evidenceRequired: event.target.checked }))
            }
          />
          <span className="pac-field__label-row">
            <FieldLabel
              label="Exigir evidência anexada para concluir esta ação"
              hint={PAC_HELP_TOOLTIPS.form.actionEvidence}
            />
          </span>
        </label>

        <FormActions>
          <button
            type="button"
            className="pac-primary-btn"
            disabled={formBusy}
            onClick={() => void handleSubmit()}
          >
            {formBusy ? "Salvando…" : isEditing ? "Salvar alterações" : "Adicionar ação"}
          </button>
          {isEditing ? (
            <button type="button" className="pac-ghost-btn" disabled={formBusy} onClick={resetForm}>
              Cancelar
            </button>
          ) : null}
        </FormActions>
      </div>
    </>
  );
}
