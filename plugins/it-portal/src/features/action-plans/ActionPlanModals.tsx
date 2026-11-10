import { useMutation } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";

import {
  ACTION_STATUS_TRANSITIONS,
  itPortalApi,
  type ActionPlan,
  type ActionPlanInput,
  type ActionStatus,
} from "../../api/itPortalApi";
import { FormErrors } from "../../app/FormErrors";
import {
  ItpActionButton,
  ItpDateField,
  ItpDialog,
  ItpSelectField,
  ItpTextAreaField,
  ItpTextField,
} from "../../app/itPortalUi";
import { toApiError, usePortal } from "../../app/PortalContext";
import {
  ACTION_FIELD_LABELS,
  ACTION_PRIORITY_OPTIONS,
  ACTION_STATUS_LABELS,
  SECRET_WARNING,
} from "../../content/labels";
import { useInvalidateInventory } from "../servers/ServerFormModal";

function toForm(plan?: ActionPlan | null): ActionPlanInput {
  return {
    title: plan?.title ?? "",
    description: plan?.description ?? "",
    responsible: plan?.responsible ?? "",
    priority: plan?.priority ?? "medium",
    due_date: plan?.due_date ?? null,
  };
}

export function ActionPlanFormModal({
  open,
  serverId,
  plan,
  onClose,
}: {
  open: boolean;
  serverId: string;
  plan?: ActionPlan | null;
  onClose: () => void;
}) {
  const { notifySuccess } = usePortal();
  const invalidate = useInvalidateInventory();
  const [form, setForm] = useState<ActionPlanInput>(() => toForm(plan));
  const editing = Boolean(plan);

  const mutation = useMutation({
    mutationFn: (input: ActionPlanInput) =>
      plan
        ? itPortalApi.updateActionPlan(plan.id, input, plan.revision)
        : itPortalApi.createActionPlan(serverId, input),
    onSuccess: (saved) => {
      invalidate();
      notifySuccess(editing ? `Plano ${saved.code} atualizado.` : `Plano ${saved.code} criado.`);
      onClose();
    },
  });

  const set = (field: keyof ActionPlanInput) => (value: string) =>
    setForm((prev) => ({ ...prev, [field]: field === "due_date" ? value || null : value }));

  const submit = (event: FormEvent) => {
    event.preventDefault();
    mutation.mutate(form);
  };

  return (
    <ItpDialog
      open={open}
      title={editing ? `Editar ${plan?.code}` : "Novo plano de ação"}
      description="Registre a ação planejada para este servidor."
      onClose={onClose}
      footer={
        <div className="itp-form-actions">
          <ItpActionButton variant="ghost" onClick={onClose} disabled={mutation.isPending}>
            Cancelar
          </ItpActionButton>
          <ItpActionButton variant="primary" type="submit" form="itp-action-form" disabled={mutation.isPending}>
            {mutation.isPending ? "Salvando…" : editing ? "Salvar alterações" : "Criar plano"}
          </ItpActionButton>
        </div>
      }
    >
      <form id="itp-action-form" className="itp-form" onSubmit={submit} noValidate>
        <FormErrors error={mutation.error ? toApiError(mutation.error) : null} fieldLabels={ACTION_FIELD_LABELS} />
        <ItpTextField label={ACTION_FIELD_LABELS.title} value={form.title} onChange={set("title")} required fullWidth />
        <div className="itp-form-grid">
          <ItpSelectField
            label={ACTION_FIELD_LABELS.priority}
            options={ACTION_PRIORITY_OPTIONS}
            value={form.priority}
            onChange={set("priority")}
            required
          />
          <ItpDateField label={ACTION_FIELD_LABELS.due_date} value={form.due_date ?? ""} onChange={set("due_date")} />
          <ItpTextField
            label={ACTION_FIELD_LABELS.responsible}
            value={form.responsible}
            onChange={set("responsible")}
          />
        </div>
        <ItpTextAreaField
          label={ACTION_FIELD_LABELS.description}
          hint={SECRET_WARNING}
          value={form.description}
          onChange={set("description")}
          rows={4}
          maxLength={4000}
          fullWidth
        />
      </form>
    </ItpDialog>
  );
}

export function ActionPlanStatusModal({
  open,
  plan,
  onClose,
}: {
  open: boolean;
  plan: ActionPlan;
  onClose: () => void;
}) {
  const { notifySuccess } = usePortal();
  const invalidate = useInvalidateInventory();
  const targets = ACTION_STATUS_TRANSITIONS[plan.status];
  const [status, setStatus] = useState<string>(targets[0] ?? "");

  const mutation = useMutation({
    mutationFn: (target: ActionStatus) => itPortalApi.changeActionPlanStatus(plan.id, target, plan.revision),
    onSuccess: (saved) => {
      invalidate();
      notifySuccess(`${saved.code}: status alterado para ${ACTION_STATUS_LABELS[saved.status]}.`);
      onClose();
    },
  });

  return (
    <ItpDialog
      open={open}
      title={`Alterar status — ${plan.code}`}
      description={`Status atual: ${ACTION_STATUS_LABELS[plan.status]}.`}
      onClose={onClose}
      footer={
        <div className="itp-form-actions">
          <ItpActionButton variant="ghost" onClick={onClose} disabled={mutation.isPending}>
            Cancelar
          </ItpActionButton>
          <ItpActionButton
            variant="primary"
            disabled={mutation.isPending || !status}
            onClick={() => mutation.mutate(status as ActionStatus)}
          >
            {mutation.isPending ? "Salvando…" : "Confirmar"}
          </ItpActionButton>
        </div>
      }
    >
      <div className="itp-form">
        <FormErrors error={mutation.error ? toApiError(mutation.error) : null} fieldLabels={ACTION_FIELD_LABELS} />
        <ItpSelectField
          label="Novo status"
          options={targets.map((value) => ({ value, label: ACTION_STATUS_LABELS[value] }))}
          value={status}
          onChange={setStatus}
          required
        />
      </div>
    </ItpDialog>
  );
}
