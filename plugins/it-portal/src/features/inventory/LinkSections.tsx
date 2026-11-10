import { useMutation, useQuery } from "@tanstack/react-query";
import { Link2, Unlink } from "lucide-react";
import { useState, type FormEvent } from "react";

import {
  itPortalApi,
  type DatabaseConsumer,
  type DatabaseConsumerInput,
  type ServiceHosting,
  type ServiceHostingInput,
} from "../../api/itPortalApi";
import { ArchivedBadge, CriticalityBadge, EnvironmentBadge, ServiceKindBadge } from "../../app/badges";
import { FormErrors } from "../../app/FormErrors";
import { formatDateTime, orDash } from "../../app/format";
import { ItpActionButton, ItpSelectField, ItpTextAreaField, ItpTextField, ItpWideDialog } from "../../app/itPortalUi";
import { DataTableSection, type DataTableColumn } from "../../app/itpDataTableUi";
import { spaNavigate } from "../../app/navigation";
import { toApiError, usePortal } from "../../app/PortalContext";
import { QueryErrorState } from "../../app/QueryStates";
import { queryKeys } from "../../app/queryKeys";
import { buildPath, type DetailTarget } from "../../app/routes";
import {
  DBMS_LABELS,
  HOSTING_RUNTIME_LABELS,
  HOSTING_RUNTIME_OPTIONS,
  LINK_FIELD_LABELS,
  SECRET_WARNING,
} from "../../content/labels";
import { useInvalidateInventory } from "../servers/ServerFormModal";
import { InventoryConfirmDialog } from "./InventoryDialogs";
import { ResourcePicker } from "./ResourcePicker";

function ResourceLink({ label, target, title }: { label: string; target: DetailTarget; title: string }) {
  const { basePath } = usePortal();
  const href = buildPath(basePath, target);
  return (
    <ItpActionButton variant="link" href={href} title={title} onClick={spaNavigate(href)}>
      {label}
    </ItpActionButton>
  );
}

function UnlinkButton({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <ItpActionButton variant="ghost" aria-label={label} onClick={onClick}>
      <Unlink size={14} strokeWidth={1.75} aria-hidden="true" /> Remover vínculo
    </ItpActionButton>
  );
}

// ------------------------------------------------------------------ hostings

type HostingOwner = { serviceId: string } | { serverId: string };

export function HostingsSection({
  owner,
  title,
  emptyMessage,
  canManage,
  ownerArchived,
}: {
  owner: HostingOwner;
  title: string;
  emptyMessage: string;
  canManage: boolean;
  ownerArchived: boolean;
}) {
  const [linking, setLinking] = useState(false);
  const [removing, setRemoving] = useState<ServiceHosting | null>(null);
  const byService = "serviceId" in owner;
  const ownerId = byService ? owner.serviceId : owner.serverId;

  const hostingsQuery = useQuery({
    queryKey: byService ? queryKeys.serviceHostings(ownerId) : queryKeys.serverHostings(ownerId),
    queryFn: ({ signal }) =>
      byService ? itPortalApi.listServiceHostings(ownerId, signal) : itPortalApi.listServerHostings(ownerId, signal),
  });

  const counterpart: DataTableColumn<ServiceHosting> = byService
    ? {
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
      }
    : {
        key: "service",
        header: "Serviço",
        interactive: true,
        render: (row) => (
          <span className="itp-cell-stack">
            <ResourceLink label={row.service.name} target={{ serviceId: row.service_id }} title={`Abrir ${row.service.name}`} />
            <span className="itp-muted">{row.service.code}</span>
          </span>
        ),
      };

  const columns: DataTableColumn<ServiceHosting>[] = [
    counterpart,
    ...(byService
      ? []
      : [
          {
            key: "kind",
            header: "Natureza",
            render: (row: ServiceHosting) => <ServiceKindBadge value={row.service.service_kind} />,
          },
          {
            key: "criticality",
            header: "Criticidade",
            render: (row: ServiceHosting) => <CriticalityBadge value={row.service.criticality} />,
          },
        ]),
    { key: "runtime", header: "Execução", render: (row) => HOSTING_RUNTIME_LABELS[row.runtime] },
    { key: "instance", header: "Instância", render: (row) => orDash(row.instance_name) },
    {
      key: "status",
      header: "Situação",
      render: (row) => ((byService ? row.server.archived : row.service.archived) ? <ArchivedBadge /> : "Ativo"),
    },
    { key: "created", header: "Vinculado em", render: (row) => `${formatDateTime(row.created_at)} · ${row.created_by_name}` },
    ...(canManage
      ? [
          {
            key: "actions",
            header: "Ações",
            interactive: true,
            align: "right" as const,
            render: (row: ServiceHosting) => (
              <UnlinkButton
                label={`Remover vínculo entre ${row.service.name} e ${row.server.name}`}
                onClick={() => setRemoving(row)}
              />
            ),
          } satisfies DataTableColumn<ServiceHosting>,
        ]
      : []),
  ];

  if (hostingsQuery.error && !hostingsQuery.data) {
    return <QueryErrorState error={toApiError(hostingsQuery.error)} onRetry={() => void hostingsQuery.refetch()} />;
  }

  return (
    <>
      <DataTableSection<ServiceHosting>
        title={title}
        columns={columns}
        rows={hostingsQuery.data ?? []}
        rowKey={(row) => row.id}
        loading={hostingsQuery.isPending}
        refreshing={hostingsQuery.isFetching && !hostingsQuery.isPending}
        emptyMessage={emptyMessage}
        getSearchText={(row) => `${row.service.name} ${row.service.code} ${row.server.name} ${row.server.hostname}`}
        searchPlaceholder={byService ? "Buscar servidor…" : "Buscar serviço…"}
        headerActions={
          canManage && !ownerArchived ? (
            <ItpActionButton variant="primary" onClick={() => setLinking(true)}>
              <Link2 size={16} strokeWidth={1.75} aria-hidden="true" /> {byService ? "Vincular servidor" : "Vincular serviço"}
            </ItpActionButton>
          ) : null
        }
      />
      {linking ? (
        <HostingFormModal
          owner={owner}
          linkedIds={(hostingsQuery.data ?? []).map((row) => (byService ? row.server_id : row.service_id))}
          onClose={() => setLinking(false)}
        />
      ) : null}
      {removing ? (
        <InventoryConfirmDialog
          title="Remover vínculo"
          message={`Remover o vínculo entre ${removing.service.name} e o servidor ${removing.server.name}? Nenhum cadastro é excluído — apenas a associação. A remoção fica registrada no histórico dos dois.`}
          confirmLabel="Remover vínculo"
          busyLabel="Removendo…"
          successMessage="Vínculo removido."
          danger
          action={() => itPortalApi.deleteHosting(removing.id)}
          onClose={() => setRemoving(null)}
        />
      ) : null}
    </>
  );
}

const EMPTY_HOSTING = { runtime: "", instance_name: "", notes: "" };

function HostingFormModal({
  owner,
  linkedIds,
  onClose,
}: {
  owner: HostingOwner;
  linkedIds: readonly string[];
  onClose: () => void;
}) {
  const { notifySuccess } = usePortal();
  const invalidate = useInvalidateInventory();
  const byService = "serviceId" in owner;
  const [counterpartId, setCounterpartId] = useState("");
  const [form, setForm] = useState(EMPTY_HOSTING);

  const mutation = useMutation({
    mutationFn: (input: ServiceHostingInput) => itPortalApi.createHosting(input),
    onSuccess: (saved) => {
      invalidate();
      notifySuccess(`${saved.service.name} vinculado a ${saved.server.name}.`);
      onClose();
    },
  });

  const submit = (event: FormEvent) => {
    event.preventDefault();
    mutation.mutate({
      service_id: byService ? owner.serviceId : counterpartId,
      server_id: byService ? counterpartId : owner.serverId,
      ...form,
    });
  };
  const set = (field: keyof typeof EMPTY_HOSTING) => (value: string) => setForm((prev) => ({ ...prev, [field]: value }));

  return (
    <ItpWideDialog
      open
      title={byService ? "Vincular servidor" : "Vincular serviço"}
      description="Registra onde o serviço executa. O vínculo pode ser removido depois sem excluir nenhum cadastro."
      onClose={onClose}
      footer={
        <div className="itp-form-actions">
          <ItpActionButton variant="ghost" onClick={onClose} disabled={mutation.isPending}>
            Cancelar
          </ItpActionButton>
          <ItpActionButton variant="primary" type="submit" form="itp-hosting-form" disabled={mutation.isPending}>
            {mutation.isPending ? "Vinculando…" : "Vincular"}
          </ItpActionButton>
        </div>
      }
    >
      <form id="itp-hosting-form" className="itp-form" onSubmit={submit} noValidate>
        <FormErrors error={mutation.error ? toApiError(mutation.error) : null} fieldLabels={LINK_FIELD_LABELS} />
        <fieldset className="itp-form-grid">
          <legend className="itp-form-legend">{byService ? "Servidor" : "Serviço"}</legend>
          <ResourcePicker
            kind={byService ? "server" : "service"}
            value={counterpartId}
            onChange={setCounterpartId}
            excludeIds={linkedIds}
          />
        </fieldset>
        <fieldset className="itp-form-grid">
          <legend className="itp-form-legend">Instância em execução</legend>
          <ItpSelectField
            label={LINK_FIELD_LABELS.runtime}
            hint="Como o serviço roda neste servidor. Um container é a forma de execução, não a aplicação."
            options={HOSTING_RUNTIME_OPTIONS}
            value={form.runtime}
            onChange={set("runtime")}
            required
          />
          <ItpTextField
            label={LINK_FIELD_LABELS.instance_name}
            hint="Opcional. Ex.: nome do container ou do serviço do Windows."
            value={form.instance_name}
            onChange={set("instance_name")}
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

// ----------------------------------------------------------------- consumers

type ConsumerOwner = { databaseId: string } | { serviceId: string };

export function ConsumersSection({
  owner,
  title,
  emptyMessage,
  canManage,
  ownerArchived,
}: {
  owner: ConsumerOwner;
  title: string;
  emptyMessage: string;
  canManage: boolean;
  ownerArchived: boolean;
}) {
  const [linking, setLinking] = useState(false);
  const [removing, setRemoving] = useState<DatabaseConsumer | null>(null);
  const byDatabase = "databaseId" in owner;
  const ownerId = byDatabase ? owner.databaseId : owner.serviceId;

  const consumersQuery = useQuery({
    queryKey: byDatabase ? queryKeys.databaseConsumers(ownerId) : queryKeys.serviceDatabases(ownerId),
    queryFn: ({ signal }) =>
      byDatabase
        ? itPortalApi.listDatabaseConsumers(ownerId, signal)
        : itPortalApi.listServiceDatabases(ownerId, signal),
  });

  const columns: DataTableColumn<DatabaseConsumer>[] = [
    byDatabase
      ? {
          key: "service",
          header: "Serviço",
          interactive: true,
          render: (row) => (
            <span className="itp-cell-stack">
              <ResourceLink label={row.service.name} target={{ serviceId: row.service_id }} title={`Abrir ${row.service.name}`} />
              <span className="itp-muted">{row.service.code}</span>
            </span>
          ),
        }
      : {
          key: "database",
          header: "Instância de banco",
          interactive: true,
          render: (row) => (
            <span className="itp-cell-stack">
              <ResourceLink
                label={row.database.name}
                target={{ databaseId: row.database_instance_id }}
                title={`Abrir ${row.database.name}`}
              />
              <span className="itp-muted">
                {row.database.code} · {DBMS_LABELS[row.database.dbms]}
              </span>
            </span>
          ),
        },
    {
      key: "environment",
      header: "Ambiente",
      render: (row) => <EnvironmentBadge value={byDatabase ? row.service.environment : row.database.environment} />,
    },
    {
      key: "criticality",
      header: "Criticidade",
      render: (row) => <CriticalityBadge value={byDatabase ? row.service.criticality : row.database.criticality} />,
    },
    {
      key: "status",
      header: "Situação",
      render: (row) => ((byDatabase ? row.service.archived : row.database.archived) ? <ArchivedBadge /> : "Ativo"),
    },
    { key: "notes", header: "Observações", render: (row) => orDash(row.notes) },
    ...(canManage
      ? [
          {
            key: "actions",
            header: "Ações",
            interactive: true,
            align: "right" as const,
            render: (row: DatabaseConsumer) => (
              <UnlinkButton
                label={`Remover vínculo entre ${row.service.name} e ${row.database.name}`}
                onClick={() => setRemoving(row)}
              />
            ),
          } satisfies DataTableColumn<DatabaseConsumer>,
        ]
      : []),
  ];

  if (consumersQuery.error && !consumersQuery.data) {
    return <QueryErrorState error={toApiError(consumersQuery.error)} onRetry={() => void consumersQuery.refetch()} />;
  }

  return (
    <>
      <DataTableSection<DatabaseConsumer>
        title={title}
        columns={columns}
        rows={consumersQuery.data ?? []}
        rowKey={(row) => row.id}
        loading={consumersQuery.isPending}
        refreshing={consumersQuery.isFetching && !consumersQuery.isPending}
        emptyMessage={emptyMessage}
        getSearchText={(row) => `${row.service.name} ${row.service.code} ${row.database.name} ${row.database.code}`}
        searchPlaceholder={byDatabase ? "Buscar serviço…" : "Buscar banco…"}
        headerActions={
          canManage && !ownerArchived ? (
            <ItpActionButton variant="primary" onClick={() => setLinking(true)}>
              <Link2 size={16} strokeWidth={1.75} aria-hidden="true" /> {byDatabase ? "Vincular serviço" : "Vincular banco"}
            </ItpActionButton>
          ) : null
        }
      />
      {linking ? (
        <ConsumerFormModal
          owner={owner}
          linkedIds={(consumersQuery.data ?? []).map((row) => (byDatabase ? row.service_id : row.database_instance_id))}
          onClose={() => setLinking(false)}
        />
      ) : null}
      {removing ? (
        <InventoryConfirmDialog
          title="Remover vínculo"
          message={`Remover o vínculo entre ${removing.service.name} e a instância ${removing.database.name}? Nenhum cadastro é excluído — apenas a associação. A remoção fica registrada no histórico dos dois.`}
          confirmLabel="Remover vínculo"
          busyLabel="Removendo…"
          successMessage="Vínculo removido."
          danger
          action={() => itPortalApi.deleteConsumer(removing.id)}
          onClose={() => setRemoving(null)}
        />
      ) : null}
    </>
  );
}

function ConsumerFormModal({
  owner,
  linkedIds,
  onClose,
}: {
  owner: ConsumerOwner;
  linkedIds: readonly string[];
  onClose: () => void;
}) {
  const { notifySuccess } = usePortal();
  const invalidate = useInvalidateInventory();
  const byDatabase = "databaseId" in owner;
  const [counterpartId, setCounterpartId] = useState("");
  const [notes, setNotes] = useState("");

  const mutation = useMutation({
    mutationFn: (input: DatabaseConsumerInput) => itPortalApi.createConsumer(input),
    onSuccess: (saved) => {
      invalidate();
      notifySuccess(`${saved.service.name} vinculado a ${saved.database.name}.`);
      onClose();
    },
  });

  const submit = (event: FormEvent) => {
    event.preventDefault();
    mutation.mutate({
      database_instance_id: byDatabase ? owner.databaseId : counterpartId,
      service_id: byDatabase ? counterpartId : owner.serviceId,
      notes,
    });
  };

  return (
    <ItpWideDialog
      open
      title={byDatabase ? "Vincular serviço consumidor" : "Vincular banco de dados"}
      description="Registra que o serviço usa esta instância de banco. Não informe usuários, senhas ou strings de conexão."
      onClose={onClose}
      footer={
        <div className="itp-form-actions">
          <ItpActionButton variant="ghost" onClick={onClose} disabled={mutation.isPending}>
            Cancelar
          </ItpActionButton>
          <ItpActionButton variant="primary" type="submit" form="itp-consumer-form" disabled={mutation.isPending}>
            {mutation.isPending ? "Vinculando…" : "Vincular"}
          </ItpActionButton>
        </div>
      }
    >
      <form id="itp-consumer-form" className="itp-form" onSubmit={submit} noValidate>
        <FormErrors error={mutation.error ? toApiError(mutation.error) : null} fieldLabels={LINK_FIELD_LABELS} />
        <fieldset className="itp-form-grid">
          <legend className="itp-form-legend">{byDatabase ? "Serviço" : "Instância de banco"}</legend>
          <ResourcePicker
            kind={byDatabase ? "service" : "database"}
            value={counterpartId}
            onChange={setCounterpartId}
            excludeIds={linkedIds}
          />
        </fieldset>
        <ItpTextAreaField
          label={LINK_FIELD_LABELS.notes}
          hint={`Opcional. Ex.: uso somente leitura. ${SECRET_WARNING}`}
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
