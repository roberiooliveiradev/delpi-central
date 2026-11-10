import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";

import { itPortalApi, type Server, type ServerInput } from "../../api/itPortalApi";
import { FormErrors } from "../../app/FormErrors";
import {
  ItpActionButton,
  ItpSelectField,
  ItpTextAreaField,
  ItpTextField,
  ItpWideDialog,
} from "../../app/itPortalUi";
import { toApiError, usePortal } from "../../app/PortalContext";
import { queryKeys } from "../../app/queryKeys";
import {
  ADMINISTRATIVE_STATUS_OPTIONS,
  CRITICALITY_OPTIONS,
  ENVIRONMENT_OPTIONS,
  SECRET_WARNING,
  SERVER_FIELD_LABELS,
  SERVER_TYPE_OPTIONS,
  UNIT_OPTIONS,
} from "../../content/labels";

const EMPTY_FORM: ServerInput = {
  name: "",
  hostname: "",
  ip_address: "",
  unit_code: "",
  location: "",
  environment: "",
  server_type: "",
  purpose: "",
  operating_system: "",
  criticality: "",
  administrative_status: "in_operation",
  responsible: "",
  description: "",
};

function toForm(server: Server): ServerInput {
  return {
    name: server.name,
    hostname: server.hostname,
    ip_address: server.ip_address ?? "",
    unit_code: server.unit_code,
    location: server.location ?? "",
    environment: server.environment,
    server_type: server.server_type,
    purpose: server.purpose ?? "",
    operating_system: server.operating_system ?? "",
    criticality: server.criticality,
    administrative_status: server.administrative_status,
    responsible: server.responsible ?? "",
    description: server.description ?? "",
  };
}

export function useInvalidateInventory() {
  const queryClient = useQueryClient();
  return () => {
    void queryClient.invalidateQueries({ queryKey: queryKeys.servers });
    void queryClient.invalidateQueries({ queryKey: queryKeys.dashboard });
    void queryClient.invalidateQueries({ queryKey: queryKeys.actionPlans });
    void queryClient.invalidateQueries({ queryKey: queryKeys.services });
    void queryClient.invalidateQueries({ queryKey: queryKeys.databases });
  };
}

export function ServerFormModal({
  open,
  server,
  onClose,
  onSaved,
}: {
  open: boolean;
  server?: Server | null;
  onClose: () => void;
  onSaved?: (server: Server) => void;
}) {
  const { notifySuccess } = usePortal();
  const invalidate = useInvalidateInventory();
  const [form, setForm] = useState<ServerInput>(() => (server ? toForm(server) : EMPTY_FORM));
  const editing = Boolean(server);

  const mutation = useMutation({
    mutationFn: (input: ServerInput) =>
      server ? itPortalApi.updateServer(server.id, input, server.revision) : itPortalApi.createServer(input),
    onSuccess: (saved) => {
      invalidate();
      notifySuccess(editing ? "Cadastro do servidor atualizado." : `Servidor ${saved.code} cadastrado.`);
      onSaved?.(saved);
      onClose();
    },
  });

  const set = (field: keyof ServerInput) => (value: string) => setForm((prev) => ({ ...prev, [field]: value }));

  const submit = (event: FormEvent) => {
    event.preventDefault();
    mutation.mutate(form);
  };

  const error = mutation.error ? toApiError(mutation.error) : null;

  return (
    <ItpWideDialog
      open={open}
      title={editing ? `Editar ${server?.code}` : "Cadastrar servidor"}
      description="Campos com * são obrigatórios. Hostname é único por unidade e ambiente."
      onClose={onClose}
      footer={
        <div className="itp-form-actions">
          <ItpActionButton variant="ghost" onClick={onClose} disabled={mutation.isPending}>
            Cancelar
          </ItpActionButton>
          <ItpActionButton variant="primary" type="submit" form="itp-server-form" disabled={mutation.isPending}>
            {mutation.isPending ? "Salvando…" : editing ? "Salvar alterações" : "Cadastrar"}
          </ItpActionButton>
        </div>
      }
    >
      <form id="itp-server-form" className="itp-form" onSubmit={submit} noValidate>
        <FormErrors error={error} fieldLabels={SERVER_FIELD_LABELS} />
        <fieldset className="itp-form-grid">
          <legend className="itp-form-legend">Identificação</legend>
          <ItpTextField label={SERVER_FIELD_LABELS.name} value={form.name} onChange={set("name")} required />
          <ItpTextField
            label={SERVER_FIELD_LABELS.hostname}
            hint="Letras, números, hífen e pontos. Ex.: srv-app01.delpi.local"
            value={form.hostname}
            onChange={set("hostname")}
            required
          />
          <ItpTextField
            label={SERVER_FIELD_LABELS.ip_address}
            hint="Opcional. IPv4 ou IPv6."
            value={form.ip_address}
            onChange={set("ip_address")}
          />
          <ItpSelectField
            label={SERVER_FIELD_LABELS.unit_code}
            options={UNIT_OPTIONS}
            value={form.unit_code}
            onChange={set("unit_code")}
            required
          />
          <ItpTextField label={SERVER_FIELD_LABELS.location} value={form.location} onChange={set("location")} />
          <ItpSelectField
            label={SERVER_FIELD_LABELS.environment}
            options={ENVIRONMENT_OPTIONS}
            value={form.environment}
            onChange={set("environment")}
            required
          />
        </fieldset>
        <fieldset className="itp-form-grid">
          <legend className="itp-form-legend">Classificação e operação</legend>
          <ItpSelectField
            label={SERVER_FIELD_LABELS.server_type}
            options={SERVER_TYPE_OPTIONS}
            value={form.server_type}
            onChange={set("server_type")}
            required
          />
          <ItpTextField label={SERVER_FIELD_LABELS.purpose} value={form.purpose} onChange={set("purpose")} />
          <ItpTextField
            label={SERVER_FIELD_LABELS.operating_system}
            value={form.operating_system}
            onChange={set("operating_system")}
          />
          <ItpSelectField
            label={SERVER_FIELD_LABELS.criticality}
            options={CRITICALITY_OPTIONS}
            value={form.criticality}
            onChange={set("criticality")}
            required
          />
          <ItpSelectField
            label={SERVER_FIELD_LABELS.administrative_status}
            hint="Situação informada manualmente — não é monitoramento."
            options={ADMINISTRATIVE_STATUS_OPTIONS}
            value={form.administrative_status}
            onChange={set("administrative_status")}
            required
          />
          <ItpTextField
            label={SERVER_FIELD_LABELS.responsible}
            value={form.responsible}
            onChange={set("responsible")}
          />
        </fieldset>
        <ItpTextAreaField
          label={SERVER_FIELD_LABELS.description}
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
