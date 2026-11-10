import { useMutation, useQuery } from "@tanstack/react-query";
import { Link2, Plus } from "lucide-react";
import { useState, type FormEvent } from "react";

import {
  itPortalApi,
  type Integration,
  type ServerNetworkLink,
  type ServerNetworkLinkInput,
  type ServiceDependency,
  type ServiceSummary,
} from "../../api/itPortalApi";
import { AdministrativeStatusBadge, ArchivedBadge, CriticalityBadge, NetworkScopeBadge } from "../../app/badges";
import { FormErrors } from "../../app/FormErrors";
import { formatDateTime, orDash } from "../../app/format";
import { ItpActionButton, ItpSelectField, ItpTextAreaField, ItpTextField, ItpWideDialog } from "../../app/itPortalUi";
import { DataTableSection, type DataTableColumn } from "../../app/itpDataTableUi";
import { toApiError, usePortal } from "../../app/PortalContext";
import { QueryErrorState } from "../../app/QueryStates";
import { queryKeys } from "../../app/queryKeys";
import {
  INTEGRATION_DIRECTION_LABELS,
  INTEGRATION_PROTOCOL_LABELS,
  LINK_FIELD_LABELS,
  SECRET_WARNING,
} from "../../content/labels";
import { IntegrationEndpoint, endpointText } from "../integrations/IntegrationEndpoint";
import { IntegrationFormModal } from "../integrations/IntegrationFormModal";
import { useInvalidateInventory } from "../servers/ServerFormModal";
import { InventoryConfirmDialog } from "./InventoryDialogs";
import { ResourceLink, UnlinkButton } from "./LinkSections";
import { ResourcePicker } from "./ResourcePicker";

// ------------------------------------------------------------ network links

type NetworkLinkOwner = { serverId: string } | { networkId: string };

export function NetworkLinksSection({
  owner,
  title,
  emptyMessage,
  canManage,
  ownerArchived,
}: {
  owner: NetworkLinkOwner;
  title: string;
  emptyMessage: string;
  canManage: boolean;
  ownerArchived: boolean;
}) {
  const [linking, setLinking] = useState(false);
  const [removing, setRemoving] = useState<ServerNetworkLink | null>(null);
  const byServer = "serverId" in owner;
  const ownerId = byServer ? owner.serverId : owner.networkId;

  const linksQuery = useQuery({
    queryKey: byServer ? queryKeys.serverNetworkLinks(ownerId) : queryKeys.networkServerLinks(ownerId),
    queryFn: ({ signal }) =>
      byServer ? itPortalApi.listServerNetworkLinks(ownerId, signal) : itPortalApi.listNetworkServerLinks(ownerId, signal),
  });

  const counterpart: DataTableColumn<ServerNetworkLink> = byServer
    ? {
        key: "network",
        header: "Rede",
        interactive: true,
        render: (row) => (
          <span className="itp-cell-stack">
            <ResourceLink label={row.network.name} target={{ networkId: row.network_id }} title={`Abrir ${row.network.name}`} />
            <span className="itp-muted">
              {row.network.code} · {row.network.cidr}
              {row.network.vlan_id !== null ? ` · VLAN ${row.network.vlan_id}` : ""}
            </span>
          </span>
        ),
      }
    : {
        key: "server",
        header: "Servidor",
        interactive: true,
        render: (row) => (
          <span className="itp-cell-stack">
            <ResourceLink label={row.server.name} target={{ serverId: row.server_id }} title={`Abrir ${row.server.name}`} />
            <span className="itp-muted">
              {row.server.code} · {row.server.hostname}
            </span>
          </span>
        ),
      };

  const columns: DataTableColumn<ServerNetworkLink>[] = [
    counterpart,
    ...(byServer
      ? [
          {
            key: "scope",
            header: "Escopo",
            render: (row: ServerNetworkLink) => <NetworkScopeBadge value={row.network.network_scope} />,
          },
        ]
      : []),
    { key: "ip", header: "IP na rede", render: (row) => orDash(row.ip_address) },
    { key: "interface", header: "Interface", render: (row) => orDash(row.interface_name) },
    {
      key: "status",
      header: "Situação",
      render: (row) => ((byServer ? row.network.archived : row.server.archived) ? <ArchivedBadge /> : "Ativo"),
    },
    { key: "created", header: "Vinculado em", render: (row) => `${formatDateTime(row.created_at)} · ${row.created_by_name}` },
    ...(canManage
      ? [
          {
            key: "actions",
            header: "Ações",
            interactive: true,
            align: "right" as const,
            render: (row: ServerNetworkLink) => (
              <UnlinkButton
                label={`Remover vínculo entre ${row.server.name} e a rede ${row.network.name}`}
                onClick={() => setRemoving(row)}
              />
            ),
          } satisfies DataTableColumn<ServerNetworkLink>,
        ]
      : []),
  ];

  if (linksQuery.error && !linksQuery.data) {
    return <QueryErrorState error={toApiError(linksQuery.error)} onRetry={() => void linksQuery.refetch()} />;
  }

  return (
    <>
      <DataTableSection<ServerNetworkLink>
        title={title}
        columns={columns}
        rows={linksQuery.data ?? []}
        rowKey={(row) => row.id}
        loading={linksQuery.isPending}
        refreshing={linksQuery.isFetching && !linksQuery.isPending}
        emptyMessage={emptyMessage}
        getSearchText={(row) =>
          `${row.network.name} ${row.network.cidr} ${row.server.name} ${row.server.hostname} ${row.ip_address ?? ""}`
        }
        searchPlaceholder={byServer ? "Buscar rede…" : "Buscar servidor…"}
        headerActions={
          canManage && !ownerArchived ? (
            <ItpActionButton variant="primary" onClick={() => setLinking(true)}>
              <Link2 size={16} strokeWidth={1.75} aria-hidden="true" /> {byServer ? "Vincular rede" : "Vincular servidor"}
            </ItpActionButton>
          ) : null
        }
      />
      {linking ? (
        <NetworkLinkFormModal
          owner={owner}
          linkedIds={(linksQuery.data ?? []).map((row) => (byServer ? row.network_id : row.server_id))}
          onClose={() => setLinking(false)}
        />
      ) : null}
      {removing ? (
        <InventoryConfirmDialog
          title="Remover vínculo"
          message={`Remover o vínculo entre o servidor ${removing.server.name} e a rede ${removing.network.name}? Nenhum cadastro é excluído — apenas a associação. A remoção fica registrada no histórico dos dois.`}
          confirmLabel="Remover vínculo"
          busyLabel="Removendo…"
          successMessage="Vínculo removido."
          danger
          action={() => itPortalApi.deleteServerNetworkLink(removing.id)}
          onClose={() => setRemoving(null)}
        />
      ) : null}
    </>
  );
}

const EMPTY_NETWORK_LINK = { ip_address: "", interface_name: "", notes: "" };

function NetworkLinkFormModal({
  owner,
  linkedIds,
  onClose,
}: {
  owner: NetworkLinkOwner;
  linkedIds: readonly string[];
  onClose: () => void;
}) {
  const { notifySuccess } = usePortal();
  const invalidate = useInvalidateInventory();
  const byServer = "serverId" in owner;
  const [counterpartId, setCounterpartId] = useState("");
  const [form, setForm] = useState(EMPTY_NETWORK_LINK);

  const mutation = useMutation({
    mutationFn: (input: ServerNetworkLinkInput) => itPortalApi.createServerNetworkLink(input),
    onSuccess: (saved) => {
      invalidate();
      notifySuccess(`${saved.server.name} vinculado à rede ${saved.network.name}.`);
      onClose();
    },
  });

  const submit = (event: FormEvent) => {
    event.preventDefault();
    mutation.mutate({
      server_id: byServer ? owner.serverId : counterpartId,
      network_id: byServer ? counterpartId : owner.networkId,
      ...form,
    });
  };
  const set = (field: keyof typeof EMPTY_NETWORK_LINK) => (value: string) =>
    setForm((prev) => ({ ...prev, [field]: value }));

  return (
    <ItpWideDialog
      open
      title={byServer ? "Vincular rede" : "Vincular servidor"}
      description="Registra que o servidor está conectado à rede. O vínculo pode ser removido depois sem excluir nenhum cadastro."
      onClose={onClose}
      footer={
        <div className="itp-form-actions">
          <ItpActionButton variant="ghost" onClick={onClose} disabled={mutation.isPending}>
            Cancelar
          </ItpActionButton>
          <ItpActionButton variant="primary" type="submit" form="itp-network-link-form" disabled={mutation.isPending}>
            {mutation.isPending ? "Vinculando…" : "Vincular"}
          </ItpActionButton>
        </div>
      }
    >
      <form id="itp-network-link-form" className="itp-form" onSubmit={submit} noValidate>
        <FormErrors error={mutation.error ? toApiError(mutation.error) : null} fieldLabels={LINK_FIELD_LABELS} />
        <fieldset className="itp-form-grid">
          <legend className="itp-form-legend">{byServer ? "Rede" : "Servidor"}</legend>
          <ResourcePicker
            kind={byServer ? "network" : "server"}
            value={counterpartId}
            onChange={setCounterpartId}
            excludeIds={linkedIds}
          />
        </fieldset>
        <fieldset className="itp-form-grid">
          <legend className="itp-form-legend">Conexão</legend>
          <ItpTextField
            label={LINK_FIELD_LABELS.ip_address}
            hint="Opcional. Deve pertencer ao CIDR da rede; não pode ser o endereço de rede nem o de broadcast."
            value={form.ip_address}
            onChange={set("ip_address")}
          />
          <ItpTextField
            label={LINK_FIELD_LABELS.interface_name}
            hint="Opcional. Ex.: eth0, ens192."
            value={form.interface_name}
            onChange={set("interface_name")}
          />
        </fieldset>
        <ItpTextAreaField
          label={LINK_FIELD_LABELS.notes}
          hint={SECRET_WARNING}
          value={form.notes}
          onChange={set("notes")}
          rows={3}
          maxLength={500}
          fullWidth
        />
      </form>
    </ItpWideDialog>
  );
}

// ------------------------------------------------------------- integrations

type IntegrationOwner = { serviceId: string; service: ServiceSummary } | { serverId: string };

export function IntegrationsSection({
  owner,
  title,
  emptyMessage,
  canManage,
  ownerArchived,
}: {
  owner: IntegrationOwner;
  title: string;
  emptyMessage: string;
  canManage: boolean;
  ownerArchived: boolean;
}) {
  const [creating, setCreating] = useState(false);
  const byService = "serviceId" in owner;
  const ownerId = byService ? owner.serviceId : owner.serverId;

  const integrationsQuery = useQuery({
    queryKey: byService ? queryKeys.serviceIntegrations(ownerId) : queryKeys.serverIntegrations(ownerId),
    queryFn: ({ signal }) =>
      byService
        ? itPortalApi.listServiceIntegrations(ownerId, signal)
        : itPortalApi.listServerIntegrations(ownerId, signal),
  });

  const columns: DataTableColumn<Integration>[] = [
    {
      key: "name",
      header: "Integração",
      interactive: true,
      render: (row) => (
        <span className="itp-cell-stack">
          <ResourceLink label={row.name} target={{ integrationId: row.id }} title={`Abrir ${row.name}`} />
          <span className="itp-muted">{row.code}</span>
        </span>
      ),
    },
    { key: "source", header: "Origem", interactive: true, render: (row) => <IntegrationEndpoint integration={row} side="source" /> },
    { key: "target", header: "Destino", interactive: true, render: (row) => <IntegrationEndpoint integration={row} side="target" /> },
    {
      key: "protocol",
      header: "Protocolo",
      render: (row) => (
        <span className="itp-cell-stack">
          <span>{INTEGRATION_PROTOCOL_LABELS[row.protocol]}</span>
          <span className="itp-muted">{INTEGRATION_DIRECTION_LABELS[row.direction]}</span>
        </span>
      ),
    },
    { key: "criticality", header: "Criticidade", render: (row) => <CriticalityBadge value={row.criticality} /> },
    {
      key: "status",
      header: "Situação",
      render: (row) => (row.archived ? <ArchivedBadge /> : <AdministrativeStatusBadge value={row.administrative_status} />),
    },
  ];

  if (integrationsQuery.error && !integrationsQuery.data) {
    return <QueryErrorState error={toApiError(integrationsQuery.error)} onRetry={() => void integrationsQuery.refetch()} />;
  }

  return (
    <>
      <DataTableSection<Integration>
        title={title}
        columns={columns}
        rows={integrationsQuery.data ?? []}
        rowKey={(row) => row.id}
        loading={integrationsQuery.isPending}
        refreshing={integrationsQuery.isFetching && !integrationsQuery.isPending}
        emptyMessage={emptyMessage}
        getSearchText={(row) => `${row.name} ${row.code} ${endpointText(row, "source")} ${endpointText(row, "target")}`}
        searchPlaceholder="Buscar integração…"
        headerActions={
          byService && canManage && !ownerArchived ? (
            <ItpActionButton variant="primary" onClick={() => setCreating(true)}>
              <Plus size={16} strokeWidth={1.75} aria-hidden="true" /> Cadastrar integração
            </ItpActionButton>
          ) : null
        }
      />
      {creating && byService ? (
        <IntegrationFormModal initialSource={owner.service} onClose={() => setCreating(false)} />
      ) : null}
    </>
  );
}

// ------------------------------------------------------ service dependencies

type DependencyRow = ServiceDependency & { relation: "requires" | "required_by"; counterpart: ServiceSummary };

const RELATION_OPTIONS = [
  { value: "requires", label: "Este serviço depende do serviço selecionado" },
  { value: "required_by", label: "O serviço selecionado depende deste serviço" },
];

export function DependenciesSection({
  service,
  canManage,
  ownerArchived,
}: {
  service: ServiceSummary;
  canManage: boolean;
  ownerArchived: boolean;
}) {
  const [linking, setLinking] = useState(false);
  const [removing, setRemoving] = useState<DependencyRow | null>(null);

  const dependenciesQuery = useQuery({
    queryKey: queryKeys.serviceDependencies(service.id),
    queryFn: ({ signal }) => itPortalApi.listServiceDependencies(service.id, signal),
  });

  const rows: DependencyRow[] = (dependenciesQuery.data ?? []).map((row) =>
    row.dependent_service_id === service.id
      ? { ...row, relation: "requires", counterpart: row.required_service }
      : { ...row, relation: "required_by", counterpart: row.dependent_service },
  );

  const columns: DataTableColumn<DependencyRow>[] = [
    {
      key: "relation",
      header: "Relação",
      render: (row) => (row.relation === "requires" ? "Depende de" : "É requisito de"),
    },
    {
      key: "service",
      header: "Serviço",
      interactive: true,
      render: (row) => (
        <span className="itp-cell-stack">
          <ResourceLink label={row.counterpart.name} target={{ serviceId: row.counterpart.id }} title={`Abrir ${row.counterpart.name}`} />
          <span className="itp-muted">{row.counterpart.code}</span>
        </span>
      ),
    },
    { key: "criticality", header: "Criticidade", render: (row) => <CriticalityBadge value={row.counterpart.criticality} /> },
    { key: "status", header: "Situação", render: (row) => (row.counterpart.archived ? <ArchivedBadge /> : "Ativo") },
    { key: "notes", header: "Observações", render: (row) => orDash(row.notes) },
    ...(canManage
      ? [
          {
            key: "actions",
            header: "Ações",
            interactive: true,
            align: "right" as const,
            render: (row: DependencyRow) => (
              <UnlinkButton
                label={`Remover dependência entre ${row.dependent_service.name} e ${row.required_service.name}`}
                onClick={() => setRemoving(row)}
              />
            ),
          } satisfies DataTableColumn<DependencyRow>,
        ]
      : []),
  ];

  if (dependenciesQuery.error && !dependenciesQuery.data) {
    return <QueryErrorState error={toApiError(dependenciesQuery.error)} onRetry={() => void dependenciesQuery.refetch()} />;
  }

  return (
    <>
      <DataTableSection<DependencyRow>
        title="Dependências operacionais"
        columns={columns}
        rows={rows}
        rowKey={(row) => row.id}
        loading={dependenciesQuery.isPending}
        refreshing={dependenciesQuery.isFetching && !dependenciesQuery.isPending}
        emptyMessage="Nenhuma dependência operacional registrada. Registre apenas dependências confirmadas — o Portal não presume dependências."
        getSearchText={(row) => `${row.counterpart.name} ${row.counterpart.code}`}
        searchPlaceholder="Buscar serviço…"
        headerActions={
          canManage && !ownerArchived ? (
            <ItpActionButton variant="primary" onClick={() => setLinking(true)}>
              <Link2 size={16} strokeWidth={1.75} aria-hidden="true" /> Registrar dependência
            </ItpActionButton>
          ) : null
        }
      />
      {linking ? (
        <DependencyFormModal service={service} existing={rows} onClose={() => setLinking(false)} />
      ) : null}
      {removing ? (
        <InventoryConfirmDialog
          title="Remover dependência"
          message={`Remover a dependência de ${removing.dependent_service.name} em relação a ${removing.required_service.name}? Nenhum serviço é excluído — apenas a relação. A remoção fica registrada no histórico dos dois.`}
          confirmLabel="Remover dependência"
          busyLabel="Removendo…"
          successMessage="Dependência removida."
          danger
          action={() => itPortalApi.deleteServiceDependency(removing.id)}
          onClose={() => setRemoving(null)}
        />
      ) : null}
    </>
  );
}

function DependencyFormModal({
  service,
  existing,
  onClose,
}: {
  service: ServiceSummary;
  existing: readonly DependencyRow[];
  onClose: () => void;
}) {
  const { notifySuccess } = usePortal();
  const invalidate = useInvalidateInventory();
  const [relation, setRelation] = useState("requires");
  const linkedIds = existing.filter((row) => row.relation === relation).map((row) => row.counterpart.id);
  const [counterpartId, setCounterpartId] = useState("");
  const [notes, setNotes] = useState("");

  const mutation = useMutation({
    mutationFn: () =>
      itPortalApi.createServiceDependency({
        dependent_service_id: relation === "requires" ? service.id : counterpartId,
        required_service_id: relation === "requires" ? counterpartId : service.id,
        notes,
      }),
    onSuccess: (saved) => {
      invalidate();
      notifySuccess(`${saved.dependent_service.name} depende de ${saved.required_service.name}.`);
      onClose();
    },
  });

  const submit = (event: FormEvent) => {
    event.preventDefault();
    mutation.mutate();
  };

  return (
    <ItpWideDialog
      open
      title="Registrar dependência operacional"
      description="Use quando um serviço deixa de funcionar sem o outro. Integrações (troca de dados) e hospedagem são registradas separadamente."
      onClose={onClose}
      footer={
        <div className="itp-form-actions">
          <ItpActionButton variant="ghost" onClick={onClose} disabled={mutation.isPending}>
            Cancelar
          </ItpActionButton>
          <ItpActionButton variant="primary" type="submit" form="itp-dependency-form" disabled={mutation.isPending}>
            {mutation.isPending ? "Registrando…" : "Registrar"}
          </ItpActionButton>
        </div>
      }
    >
      <form id="itp-dependency-form" className="itp-form" onSubmit={submit} noValidate>
        <FormErrors error={mutation.error ? toApiError(mutation.error) : null} fieldLabels={LINK_FIELD_LABELS} />
        <fieldset className="itp-form-grid">
          <legend className="itp-form-legend">Relação</legend>
          <ItpSelectField
            label="Sentido da dependência"
            options={RELATION_OPTIONS}
            value={relation}
            onChange={(value) => setRelation(value || "requires")}
            required
          />
          <ResourcePicker
            kind="service"
            value={counterpartId}
            onChange={setCounterpartId}
            excludeIds={[service.id, ...linkedIds]}
          />
        </fieldset>
        <ItpTextAreaField
          label={LINK_FIELD_LABELS.notes}
          hint={`Opcional. Ex.: autenticação depende do provedor de identidade. ${SECRET_WARNING}`}
          value={notes}
          onChange={setNotes}
          rows={3}
          maxLength={500}
          fullWidth
        />
      </form>
    </ItpWideDialog>
  );
}
