import { useMutation } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";

import { itPortalApi, type Integration, type IntegrationInput, type ServiceSummary } from "../../api/itPortalApi";
import { FormErrors } from "../../app/FormErrors";
import { ItpActionButton, ItpSelectField, ItpTextAreaField, ItpTextField, ItpWideDialog } from "../../app/itPortalUi";
import { toApiError, usePortal } from "../../app/PortalContext";
import {
  ADMINISTRATIVE_STATUS_OPTIONS,
  CRITICALITY_OPTIONS,
  INTEGRATION_DIRECTION_OPTIONS,
  INTEGRATION_FIELD_LABELS,
  INTEGRATION_PROTOCOL_OPTIONS,
  SECRET_WARNING,
} from "../../content/labels";
import { ResourcePicker } from "../inventory/ResourcePicker";
import { useInvalidateInventory } from "../servers/ServerFormModal";

type EndpointMode = "service" | "external";
type Endpoint = { mode: EndpointMode; serviceId: string; externalName: string; initial?: ServiceSummary | null };

const ENDPOINT_MODE_OPTIONS = [
  { value: "service", label: "Serviço cadastrado no Portal de TI" },
  { value: "external", label: "Sistema externo (não cadastrado)" },
];

type Details = Omit<
  IntegrationInput,
  "source_service_id" | "source_external_name" | "target_service_id" | "target_external_name"
>;

const EMPTY_DETAILS: Details = {
  name: "",
  protocol: "",
  direction: "",
  purpose: "",
  criticality: "",
  responsible: "",
  administrative_status: "in_operation",
  notes: "",
};

function toEndpoint(service: ServiceSummary | null, externalName: string | null): Endpoint {
  return service
    ? { mode: "service", serviceId: service.id, externalName: "", initial: service }
    : { mode: "external", serviceId: "", externalName: externalName ?? "" };
}

function toDetails(integration: Integration): Details {
  return {
    name: integration.name,
    protocol: integration.protocol,
    direction: integration.direction,
    purpose: integration.purpose ?? "",
    criticality: integration.criticality,
    responsible: integration.responsible,
    administrative_status: integration.administrative_status,
    notes: integration.notes ?? "",
  };
}

function EndpointFields({
  legend,
  endpoint,
  onChange,
  excludeServiceId,
}: {
  legend: string;
  endpoint: Endpoint;
  onChange: (endpoint: Endpoint) => void;
  excludeServiceId: string;
}) {
  const initialOption = endpoint.initial
    ? { value: endpoint.initial.id, label: `${endpoint.initial.code} · ${endpoint.initial.name}` }
    : undefined;
  return (
    <fieldset className="itp-form-grid">
      <legend className="itp-form-legend">{legend}</legend>
      <ItpSelectField
        label={`Tipo da ${legend.toLocaleLowerCase("pt-BR")}`}
        hint="Use «Sistema externo» apenas para sistemas fora do inventário (ex.: SEFAZ, banco parceiro). Não invente aplicações."
        options={ENDPOINT_MODE_OPTIONS}
        value={endpoint.mode}
        onChange={(mode) => onChange({ ...endpoint, mode: (mode || "service") as EndpointMode })}
        required
      />
      {endpoint.mode === "service" ? (
        <ResourcePicker
          kind="service"
          label={`Serviço de ${legend.toLocaleLowerCase("pt-BR")}`}
          value={endpoint.serviceId}
          onChange={(serviceId) => onChange({ ...endpoint, serviceId })}
          excludeIds={excludeServiceId ? [excludeServiceId] : []}
          initialOption={initialOption}
        />
      ) : (
        <ItpTextField
          label={`Nome do sistema externo (${legend.toLocaleLowerCase("pt-BR")})`}
          hint="Nome identificável do sistema. Não informe URLs com credenciais, tokens ou payloads."
          value={endpoint.externalName}
          onChange={(externalName) => onChange({ ...endpoint, externalName })}
          required
        />
      )}
    </fieldset>
  );
}

export function IntegrationFormModal({
  integration,
  initialSource,
  onClose,
  onSaved,
}: {
  integration?: Integration | null;
  initialSource?: ServiceSummary | null;
  onClose: () => void;
  onSaved?: (integration: Integration) => void;
}) {
  const { notifySuccess } = usePortal();
  const invalidate = useInvalidateInventory();
  const editing = Boolean(integration);
  const [details, setDetails] = useState<Details>(() => (integration ? toDetails(integration) : EMPTY_DETAILS));
  const [source, setSource] = useState<Endpoint>(() =>
    integration
      ? toEndpoint(integration.source_service, integration.source_external_name)
      : initialSource
        ? toEndpoint(initialSource, null)
        : { mode: "service", serviceId: "", externalName: "" },
  );
  const [target, setTarget] = useState<Endpoint>(() =>
    integration
      ? toEndpoint(integration.target_service, integration.target_external_name)
      : { mode: "service", serviceId: "", externalName: "" },
  );

  const mutation = useMutation({
    mutationFn: (input: IntegrationInput) =>
      integration
        ? itPortalApi.updateIntegration(integration.id, input, integration.revision)
        : itPortalApi.createIntegration(input),
    onSuccess: (saved) => {
      invalidate();
      notifySuccess(editing ? "Cadastro da integração atualizado." : `Integração ${saved.code} cadastrada.`);
      onSaved?.(saved);
      onClose();
    },
  });

  const set = (field: keyof Details) => (value: string) => setDetails((prev) => ({ ...prev, [field]: value }));
  const submit = (event: FormEvent) => {
    event.preventDefault();
    mutation.mutate({
      ...details,
      source_service_id: source.mode === "service" ? source.serviceId || null : null,
      source_external_name: source.mode === "external" ? source.externalName : null,
      target_service_id: target.mode === "service" ? target.serviceId || null : null,
      target_external_name: target.mode === "external" ? target.externalName : null,
    });
  };

  return (
    <ItpWideDialog
      open
      title={editing ? `Editar ${integration?.code}` : "Cadastrar integração"}
      description="Registra uma troca de dados entre serviços, ou entre um serviço e um sistema externo. Pelo menos uma ponta deve ser um serviço cadastrado. Não registre credenciais, tokens nem payloads."
      onClose={onClose}
      footer={
        <div className="itp-form-actions">
          <ItpActionButton variant="ghost" onClick={onClose} disabled={mutation.isPending}>
            Cancelar
          </ItpActionButton>
          <ItpActionButton variant="primary" type="submit" form="itp-integration-form" disabled={mutation.isPending}>
            {mutation.isPending ? "Salvando…" : editing ? "Salvar alterações" : "Cadastrar"}
          </ItpActionButton>
        </div>
      }
    >
      <form id="itp-integration-form" className="itp-form" onSubmit={submit} noValidate>
        <FormErrors error={mutation.error ? toApiError(mutation.error) : null} fieldLabels={INTEGRATION_FIELD_LABELS} />
        <fieldset className="itp-form-grid">
          <legend className="itp-form-legend">Identificação</legend>
          <ItpTextField label={INTEGRATION_FIELD_LABELS.name} value={details.name} onChange={set("name")} required />
          <ItpSelectField
            label={INTEGRATION_FIELD_LABELS.protocol}
            options={INTEGRATION_PROTOCOL_OPTIONS}
            value={details.protocol}
            onChange={set("protocol")}
            required
          />
          <ItpSelectField
            label={INTEGRATION_FIELD_LABELS.direction}
            hint="«Origem → destino» quando a origem envia ou chama o destino; «Bidirecional» quando os dois lados trocam dados."
            options={INTEGRATION_DIRECTION_OPTIONS}
            value={details.direction}
            onChange={set("direction")}
            required
          />
        </fieldset>
        <EndpointFields legend="Origem" endpoint={source} onChange={setSource} excludeServiceId={target.mode === "service" ? target.serviceId : ""} />
        <EndpointFields legend="Destino" endpoint={target} onChange={setTarget} excludeServiceId={source.mode === "service" ? source.serviceId : ""} />
        <fieldset className="itp-form-grid">
          <legend className="itp-form-legend">Operação e responsabilidade</legend>
          <ItpSelectField
            label={INTEGRATION_FIELD_LABELS.criticality}
            options={CRITICALITY_OPTIONS}
            value={details.criticality}
            onChange={set("criticality")}
            required
          />
          <ItpSelectField
            label={INTEGRATION_FIELD_LABELS.administrative_status}
            hint="Situação informada manualmente — não é monitoramento."
            options={ADMINISTRATIVE_STATUS_OPTIONS}
            value={details.administrative_status}
            onChange={set("administrative_status")}
            required
          />
          <ItpTextField
            label={INTEGRATION_FIELD_LABELS.responsible}
            hint="Pessoa ou equipe responsável."
            value={details.responsible}
            onChange={set("responsible")}
            required
          />
          <ItpTextField
            label={INTEGRATION_FIELD_LABELS.purpose}
            hint="Opcional. Ex.: envio de notas fiscais, sincronização de cadastro."
            value={details.purpose}
            onChange={set("purpose")}
          />
        </fieldset>
        <ItpTextAreaField
          label={INTEGRATION_FIELD_LABELS.notes}
          hint={SECRET_WARNING}
          value={details.notes}
          onChange={set("notes")}
          rows={3}
          maxLength={4000}
          fullWidth
        />
      </form>
    </ItpWideDialog>
  );
}
