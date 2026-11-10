import { useMutation } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";

import { itPortalApi, type Service, type ServiceInput } from "../../api/itPortalApi";
import { FormErrors } from "../../app/FormErrors";
import { ItpActionButton, ItpSelectField, ItpTextAreaField, ItpTextField, ItpWideDialog } from "../../app/itPortalUi";
import { toApiError, usePortal } from "../../app/PortalContext";
import {
  ADMINISTRATIVE_STATUS_OPTIONS,
  CRITICALITY_OPTIONS,
  ENVIRONMENT_OPTIONS,
  SECRET_WARNING,
  SERVICE_FIELD_LABELS,
  SERVICE_KIND_HINT,
  SERVICE_KIND_OPTIONS,
  SERVICE_TYPE_OPTIONS,
  UNIT_OPTIONS,
} from "../../content/labels";
import { useInvalidateInventory } from "../servers/ServerFormModal";

const EMPTY_FORM: ServiceInput = {
  name: "",
  description: "",
  service_kind: "",
  service_type: "",
  technology: "",
  environment: "",
  unit_code: "",
  port: "",
  criticality: "",
  responsible: "",
  administrative_status: "in_operation",
};

function toForm(service: Service): ServiceInput {
  return {
    name: service.name,
    description: service.description ?? "",
    service_kind: service.service_kind,
    service_type: service.service_type,
    technology: service.technology ?? "",
    environment: service.environment,
    unit_code: service.unit_code,
    port: service.port === null ? "" : String(service.port),
    criticality: service.criticality,
    responsible: service.responsible,
    administrative_status: service.administrative_status,
  };
}

export function ServiceFormModal({
  service,
  onClose,
  onSaved,
}: {
  service?: Service | null;
  onClose: () => void;
  onSaved?: (service: Service) => void;
}) {
  const { notifySuccess } = usePortal();
  const invalidate = useInvalidateInventory();
  const [form, setForm] = useState<ServiceInput>(() => (service ? toForm(service) : EMPTY_FORM));
  const editing = Boolean(service);

  const mutation = useMutation({
    mutationFn: (input: ServiceInput) =>
      service ? itPortalApi.updateService(service.id, input, service.revision) : itPortalApi.createService(input),
    onSuccess: (saved) => {
      invalidate();
      notifySuccess(editing ? "Cadastro do serviço atualizado." : `Serviço ${saved.code} cadastrado.`);
      onSaved?.(saved);
      onClose();
    },
  });

  const set = (field: keyof ServiceInput) => (value: string) => setForm((prev) => ({ ...prev, [field]: value }));
  const submit = (event: FormEvent) => {
    event.preventDefault();
    mutation.mutate(form);
  };

  return (
    <ItpWideDialog
      open
      title={editing ? `Editar ${service?.code}` : "Cadastrar serviço"}
      description="Campos com * são obrigatórios. O nome é único por unidade e ambiente. Não registre senhas, tokens ou credenciais."
      onClose={onClose}
      footer={
        <div className="itp-form-actions">
          <ItpActionButton variant="ghost" onClick={onClose} disabled={mutation.isPending}>
            Cancelar
          </ItpActionButton>
          <ItpActionButton variant="primary" type="submit" form="itp-service-form" disabled={mutation.isPending}>
            {mutation.isPending ? "Salvando…" : editing ? "Salvar alterações" : "Cadastrar"}
          </ItpActionButton>
        </div>
      }
    >
      <form id="itp-service-form" className="itp-form" onSubmit={submit} noValidate>
        <FormErrors error={mutation.error ? toApiError(mutation.error) : null} fieldLabels={SERVICE_FIELD_LABELS} />
        <fieldset className="itp-form-grid">
          <legend className="itp-form-legend">Identificação</legend>
          <ItpTextField label={SERVICE_FIELD_LABELS.name} value={form.name} onChange={set("name")} required />
          <ItpSelectField
            label={SERVICE_FIELD_LABELS.service_kind}
            hint={SERVICE_KIND_HINT}
            options={SERVICE_KIND_OPTIONS}
            value={form.service_kind}
            onChange={set("service_kind")}
            required
          />
          <ItpSelectField
            label={SERVICE_FIELD_LABELS.service_type}
            options={SERVICE_TYPE_OPTIONS}
            value={form.service_type}
            onChange={set("service_type")}
            required
          />
          <ItpTextField
            label={SERVICE_FIELD_LABELS.technology}
            hint="Opcional. Ex.: Python/FastAPI, Java, IIS, Nginx."
            value={form.technology}
            onChange={set("technology")}
          />
          <ItpSelectField
            label={SERVICE_FIELD_LABELS.unit_code}
            options={UNIT_OPTIONS}
            value={form.unit_code}
            onChange={set("unit_code")}
            required
          />
          <ItpSelectField
            label={SERVICE_FIELD_LABELS.environment}
            options={ENVIRONMENT_OPTIONS}
            value={form.environment}
            onChange={set("environment")}
            required
          />
        </fieldset>
        <fieldset className="itp-form-grid">
          <legend className="itp-form-legend">Operação e responsabilidade</legend>
          <ItpTextField
            label={SERVICE_FIELD_LABELS.port}
            hint="Opcional. Porta principal de acesso (1–65535)."
            value={form.port}
            onChange={set("port")}
          />
          <ItpSelectField
            label={SERVICE_FIELD_LABELS.criticality}
            options={CRITICALITY_OPTIONS}
            value={form.criticality}
            onChange={set("criticality")}
            required
          />
          <ItpSelectField
            label={SERVICE_FIELD_LABELS.administrative_status}
            hint="Situação informada manualmente — não é monitoramento."
            options={ADMINISTRATIVE_STATUS_OPTIONS}
            value={form.administrative_status}
            onChange={set("administrative_status")}
            required
          />
          <ItpTextField
            label={SERVICE_FIELD_LABELS.responsible}
            hint="Pessoa ou equipe responsável."
            value={form.responsible}
            onChange={set("responsible")}
            required
          />
        </fieldset>
        <ItpTextAreaField
          label={SERVICE_FIELD_LABELS.description}
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
