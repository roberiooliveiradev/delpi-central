import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";

import { itPortalApi, type Workstation, type WorkstationInput } from "../../api/itPortalApi";
import { FormErrors } from "../../app/FormErrors";
import { ItpActionButton, ItpSelectField, ItpTextAreaField, ItpTextField, ItpWideDialog } from "../../app/itPortalUi";
import { WorkstationOwnerPicker } from "./WorkstationOwnerPicker";
import { toApiError, usePortal } from "../../app/PortalContext";
import { queryKeys } from "../../app/queryKeys";
import {
  ADMINISTRATIVE_STATUS_OPTIONS,
  SECRET_WARNING,
  UNIT_OPTIONS,
  WORKSTATION_FIELD_LABELS,
  WORKSTATION_KIND_OPTIONS,
} from "../../content/labels";

const EMPTY_FORM: WorkstationInput = {
  name: "",
  hostname: "",
  ip_address: "",
  unit_code: "",
  device_kind: "desktop",
  department: "",
  location: "",
  responsible: "",
  responsible_user_id: null,
  operating_system: "",
  administrative_status: "in_operation",
  description: "",
};

function toForm(workstation: Workstation): WorkstationInput {
  return {
    name: workstation.name,
    hostname: workstation.hostname,
    ip_address: workstation.ip_address ?? "",
    unit_code: workstation.unit_code,
    device_kind: workstation.device_kind,
    department: workstation.department ?? "",
    location: workstation.location ?? "",
    responsible: workstation.responsible ?? "",
    responsible_user_id: workstation.responsible_user_id ?? null,
    operating_system: workstation.operating_system ?? "",
    administrative_status: workstation.administrative_status,
    description: workstation.description ?? "",
  };
}

export function WorkstationFormModal({
  workstation,
  onClose,
  onSaved,
}: {
  workstation?: Workstation | null;
  onClose: () => void;
  onSaved?: (workstation: Workstation) => void;
}) {
  const { notifySuccess } = usePortal();
  const queryClient = useQueryClient();
  const [form, setForm] = useState<WorkstationInput>(() => workstation ? toForm(workstation) : EMPTY_FORM);
  const editing = Boolean(workstation);

  const mutation = useMutation({
    mutationFn: (input: WorkstationInput) =>
      workstation
        ? itPortalApi.updateWorkstation(workstation.id, input, workstation.revision)
        : itPortalApi.createWorkstation(input),
    onSuccess: (saved) => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.workstations });
      notifySuccess(editing ? "Cadastro do computador atualizado." : `Computador ${saved.code} cadastrado.`);
      onSaved?.(saved);
      onClose();
    },
  });

  const set = (field: keyof WorkstationInput) => (value: string) =>
    setForm((previous) => ({ ...previous, [field]: value }));

  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (!mutation.isPending) mutation.mutate(form);
  };

  return (
    <ItpWideDialog
      open
      title={editing ? `Editar ${workstation?.code}` : "Cadastrar computador"}
      description="Cadastro manual de equipamento corporativo. Hostname único entre cadastros ativos da mesma unidade. Nenhum agente ou acesso remoto será ativado."
      onClose={() => { if (!mutation.isPending) onClose(); }}
      footer={
        <div className="itp-form-actions">
          <ItpActionButton variant="ghost" onClick={onClose} disabled={mutation.isPending}>
            Cancelar
          </ItpActionButton>
          <ItpActionButton variant="primary" type="submit" form="itp-workstation-form" disabled={mutation.isPending}>
            {mutation.isPending ? "Salvando…" : editing ? "Salvar alterações" : "Cadastrar"}
          </ItpActionButton>
        </div>
      }
    >
      <form id="itp-workstation-form" className="itp-form" onSubmit={submit} noValidate>
        <FormErrors error={mutation.error ? toApiError(mutation.error) : null} fieldLabels={WORKSTATION_FIELD_LABELS} />
        <fieldset className="itp-form-grid">
          <legend className="itp-form-legend">Identificação</legend>
          <ItpTextField label={WORKSTATION_FIELD_LABELS.name} value={form.name} onChange={set("name")} required />
          <ItpTextField
            label={WORKSTATION_FIELD_LABELS.hostname}
            hint="Use o nome real do Windows. Ex.: pc-eng-001.delpi.local"
            value={form.hostname}
            onChange={set("hostname")}
            required
          />
          <ItpTextField
            label={WORKSTATION_FIELD_LABELS.ip_address}
            hint="Opcional. IPv4 ou IPv6. O IP não é identificador permanente."
            value={form.ip_address}
            onChange={set("ip_address")}
          />
          <ItpSelectField label={WORKSTATION_FIELD_LABELS.unit_code} options={UNIT_OPTIONS} value={form.unit_code} onChange={set("unit_code")} required />
          <ItpSelectField
            label={WORKSTATION_FIELD_LABELS.device_kind}
            options={WORKSTATION_KIND_OPTIONS}
            value={form.device_kind}
            onChange={set("device_kind")}
            required
          />
          <ItpTextField label={WORKSTATION_FIELD_LABELS.department} value={form.department} onChange={set("department")} />
        </fieldset>
        <fieldset className="itp-form-grid">
          <legend className="itp-form-legend">Localização e operação</legend>
          <ItpTextField label={WORKSTATION_FIELD_LABELS.location} value={form.location} onChange={set("location")} />
          <WorkstationOwnerPicker
            selectedId={form.responsible_user_id}
            selectedName={form.responsible}
            legacyName={workstation && !workstation.responsible_user_id ? workstation.responsible : null}
            disabled={mutation.isPending}
            onSelect={(userId, name) => setForm((previous) => ({
              ...previous,
              responsible_user_id: userId,
              responsible: name,
            }))}
          />
          <ItpTextField label={WORKSTATION_FIELD_LABELS.operating_system} value={form.operating_system} onChange={set("operating_system")} />
          <ItpSelectField
            label={WORKSTATION_FIELD_LABELS.administrative_status}
            options={ADMINISTRATIVE_STATUS_OPTIONS}
            value={form.administrative_status}
            onChange={set("administrative_status")}
            hint="Situação informada manualmente. Não representa monitoramento online."
            required
          />
        </fieldset>
        <ItpTextAreaField
          label={WORKSTATION_FIELD_LABELS.description}
          hint={SECRET_WARNING}
          value={form.description}
          onChange={set("description")}
          rows={4}
          maxLength={4000}
          fullWidth
        />
      </form>
    </ItpWideDialog>
  );
}
