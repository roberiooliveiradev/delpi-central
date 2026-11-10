import { useMutation } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";

import { itPortalApi, type Network, type NetworkInput } from "../../api/itPortalApi";
import { FormErrors } from "../../app/FormErrors";
import { ItpActionButton, ItpSelectField, ItpTextAreaField, ItpTextField, ItpWideDialog } from "../../app/itPortalUi";
import { toApiError, usePortal } from "../../app/PortalContext";
import {
  CRITICALITY_OPTIONS,
  ENVIRONMENT_OPTIONS,
  NETWORK_FIELD_LABELS,
  NETWORK_SCOPE_HINT,
  NETWORK_SCOPE_OPTIONS,
  SECRET_WARNING,
  UNIT_OPTIONS,
} from "../../content/labels";
import { useInvalidateInventory } from "../servers/ServerFormModal";

const EMPTY_FORM: NetworkInput = {
  name: "",
  cidr: "",
  vlan_id: "",
  gateway: "",
  unit_code: "",
  location: "",
  purpose: "",
  environment: "",
  zone: "",
  network_scope: "corporate",
  criticality: "",
  responsible: "",
  notes: "",
};

function toForm(network: Network): NetworkInput {
  return {
    name: network.name,
    cidr: network.cidr,
    vlan_id: network.vlan_id === null ? "" : String(network.vlan_id),
    gateway: network.gateway ?? "",
    unit_code: network.unit_code,
    location: network.location ?? "",
    purpose: network.purpose ?? "",
    environment: network.environment,
    zone: network.zone ?? "",
    network_scope: network.network_scope,
    criticality: network.criticality,
    responsible: network.responsible,
    notes: network.notes ?? "",
  };
}

export function NetworkFormModal({
  network,
  onClose,
  onSaved,
}: {
  network?: Network | null;
  onClose: () => void;
  onSaved?: (network: Network) => void;
}) {
  const { notifySuccess } = usePortal();
  const invalidate = useInvalidateInventory();
  const [form, setForm] = useState<NetworkInput>(() => (network ? toForm(network) : EMPTY_FORM));
  const editing = Boolean(network);

  const mutation = useMutation({
    mutationFn: (input: NetworkInput) =>
      network ? itPortalApi.updateNetwork(network.id, input, network.revision) : itPortalApi.createNetwork(input),
    onSuccess: (saved) => {
      invalidate();
      notifySuccess(editing ? "Cadastro da rede atualizado." : `Rede ${saved.code} cadastrada.`);
      onSaved?.(saved);
      onClose();
    },
  });

  const set = (field: keyof NetworkInput) => (value: string) => setForm((prev) => ({ ...prev, [field]: value }));
  const submit = (event: FormEvent) => {
    event.preventDefault();
    mutation.mutate(form);
  };

  return (
    <ItpWideDialog
      open
      title={editing ? `Editar ${network?.code}` : "Cadastrar rede"}
      description="Campos com * são obrigatórios. Cadastro manual — o Portal de TI não faz varredura de rede. Não registre senhas, tokens ou credenciais."
      onClose={onClose}
      footer={
        <div className="itp-form-actions">
          <ItpActionButton variant="ghost" onClick={onClose} disabled={mutation.isPending}>
            Cancelar
          </ItpActionButton>
          <ItpActionButton variant="primary" type="submit" form="itp-network-form" disabled={mutation.isPending}>
            {mutation.isPending ? "Salvando…" : editing ? "Salvar alterações" : "Cadastrar"}
          </ItpActionButton>
        </div>
      }
    >
      <form id="itp-network-form" className="itp-form" onSubmit={submit} noValidate>
        <FormErrors error={mutation.error ? toApiError(mutation.error) : null} fieldLabels={NETWORK_FIELD_LABELS} />
        <fieldset className="itp-form-grid">
          <legend className="itp-form-legend">Endereçamento</legend>
          <ItpTextField label={NETWORK_FIELD_LABELS.name} value={form.name} onChange={set("name")} required />
          <ItpTextField
            label={NETWORK_FIELD_LABELS.cidr}
            hint="Endereço de rede com prefixo. Ex.: 10.0.1.0/24 ou 2001:db8::/64."
            value={form.cidr}
            onChange={set("cidr")}
            required
          />
          <ItpTextField
            label={NETWORK_FIELD_LABELS.gateway}
            hint="Opcional. Deve pertencer ao CIDR."
            value={form.gateway}
            onChange={set("gateway")}
          />
          <ItpTextField
            label={NETWORK_FIELD_LABELS.vlan_id}
            hint="Opcional. Número entre 1 e 4094."
            value={form.vlan_id}
            onChange={set("vlan_id")}
          />
          <ItpSelectField
            label={NETWORK_FIELD_LABELS.network_scope}
            hint={NETWORK_SCOPE_HINT}
            options={NETWORK_SCOPE_OPTIONS}
            value={form.network_scope}
            onChange={set("network_scope")}
            required
          />
        </fieldset>
        <fieldset className="itp-form-grid">
          <legend className="itp-form-legend">Localização e uso</legend>
          <ItpSelectField
            label={NETWORK_FIELD_LABELS.unit_code}
            options={UNIT_OPTIONS}
            value={form.unit_code}
            onChange={set("unit_code")}
            required
          />
          <ItpTextField
            label={NETWORK_FIELD_LABELS.location}
            hint="Opcional. Ex.: Datacenter matriz, rack 2."
            value={form.location}
            onChange={set("location")}
          />
          <ItpSelectField
            label={NETWORK_FIELD_LABELS.environment}
            options={ENVIRONMENT_OPTIONS}
            value={form.environment}
            onChange={set("environment")}
            required
          />
          <ItpTextField
            label={NETWORK_FIELD_LABELS.zone}
            hint="Opcional. Ex.: DMZ, servidores, gestão."
            value={form.zone}
            onChange={set("zone")}
          />
          <ItpTextField
            label={NETWORK_FIELD_LABELS.purpose}
            hint="Opcional. Ex.: rede dos servidores de aplicação."
            value={form.purpose}
            onChange={set("purpose")}
          />
        </fieldset>
        <fieldset className="itp-form-grid">
          <legend className="itp-form-legend">Responsabilidade</legend>
          <ItpSelectField
            label={NETWORK_FIELD_LABELS.criticality}
            options={CRITICALITY_OPTIONS}
            value={form.criticality}
            onChange={set("criticality")}
            required
          />
          <ItpTextField
            label={NETWORK_FIELD_LABELS.responsible}
            hint="Pessoa ou equipe responsável."
            value={form.responsible}
            onChange={set("responsible")}
            required
          />
        </fieldset>
        <ItpTextAreaField
          label={NETWORK_FIELD_LABELS.notes}
          hint={SECRET_WARNING}
          value={form.notes}
          onChange={set("notes")}
          rows={3}
          maxLength={4000}
          fullWidth
        />
      </form>
    </ItpWideDialog>
  );
}
