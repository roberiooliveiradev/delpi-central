import { useQuery } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { useState } from "react";

import { itPortalApi, type DatabaseInstance, type DatabaseListQuery, type Server } from "../../api/itPortalApi";
import { AdministrativeStatusBadge, ArchivedBadge, CriticalityBadge, EnvironmentBadge } from "../../app/badges";
import { ItpActionButton, ItpSectionCard } from "../../app/itPortalUi";
import { DataTableSection, type DataTableColumn } from "../../app/itpDataTableUi";
import { navigateTo } from "../../app/navigation";
import { toApiError, usePortal } from "../../app/PortalContext";
import { QueryErrorState } from "../../app/QueryStates";
import { queryKeys } from "../../app/queryKeys";
import { buildPath } from "../../app/routes";
import { DBMS_LABELS } from "../../content/labels";
import { DatabaseFormModal } from "../databases/DatabaseFormModal";
import { IntegrationsSection, NetworkLinksSection } from "../inventory/ConnectivitySections";
import { DetailField as Field } from "../inventory/InventoryDialogs";
import { HostingsSection } from "../inventory/LinkSections";

const SERVER_DATABASES_LIMIT = 100;

function serverDatabasesQuery(serverId: string): DatabaseListQuery {
  return { server_id: serverId, archived: "all", sort: "name", page_size: SERVER_DATABASES_LIMIT };
}

function useServerHostings(serverId: string, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.serverHostings(serverId),
    queryFn: ({ signal }) => itPortalApi.listServerHostings(serverId, signal),
    enabled,
  });
}

function useServerDatabases(serverId: string, enabled: boolean) {
  const query = serverDatabasesQuery(serverId);
  return useQuery({
    queryKey: queryKeys.databaseList(query),
    queryFn: ({ signal }) => itPortalApi.listDatabases(query, signal),
    enabled,
  });
}

function countLabel(count: number | undefined, singular: string, plural: string): string {
  if (count === undefined) return "…";
  return `${count} ${count === 1 ? singular : plural}`;
}

/**
 * Cada grupo so monta quando o usuario escolhe seu icone. Alem de reduzir
 * a extensao da tela, evita requisitar dados de secoes nao abertas.
 */
export function ServerComponentsSections({
  server,
  section,
}: {
  server: Server;
  section: "services" | "databases" | "networks" | "integrations";
}) {
  const { capabilities } = usePortal();

  if (section === "networks") {
    return capabilities?.can_view_networks ? (
      <NetworkLinksSection
        owner={{ serverId: server.id }}
        title="Redes vinculadas"
        emptyMessage="Nenhuma rede vinculada a este servidor."
        canManage={capabilities.can_manage_networks}
        ownerArchived={server.archived}
      />
    ) : null;
  }

  if (section === "integrations") {
    return capabilities?.can_view_integrations ? (
      <IntegrationsSection
        owner={{ serverId: server.id }}
        title="Integrações dos serviços hospedados"
        emptyMessage="Nenhuma integração registrada para os serviços hospedados neste servidor."
        canManage={false}
        ownerArchived={server.archived}
      />
    ) : null;
  }

  return <ServerInventorySummary server={server} section={section} />;
}

function ServerInventorySummary({
  server,
  section,
}: {
  server: Server;
  section: "services" | "databases";
}) {
  const { capabilities } = usePortal();
  const canSeeServices = section === "services" && capabilities?.can_view_services === true;
  const canSeeDatabases = section === "databases" && capabilities?.can_view_databases === true;
  const hostings = useServerHostings(server.id, canSeeServices);
  const databases = useServerDatabases(server.id, canSeeDatabases);

  if (!canSeeServices && !canSeeDatabases) return null;

  const activeHostings = hostings.data?.filter((row) => !row.service.archived);
  const criticalServices = activeHostings?.filter((row) => ["high", "critical"].includes(row.service.criticality));
  const activeDatabases = databases.data?.items.filter((row) => !row.archived);

  return (
    <>
      <ItpSectionCard
        title={canSeeServices ? "Serviços vinculados" : "Bancos vinculados"}
        subtitle="Vínculos do inventário manual, independentes da coleta automática."
      >
        <dl className="itp-field-list">
          {canSeeServices ? (
            <>
              <Field
                label="Serviços em execução"
                value={hostings.isError ? "Indisponível" : countLabel(activeHostings?.length, "serviço ativo", "serviços ativos")}
              />
              <Field
                label="Serviços de criticidade alta ou crítica"
                value={hostings.isError ? "Indisponível" : countLabel(criticalServices?.length, "serviço", "serviços")}
              />
            </>
          ) : null}
          {canSeeDatabases ? (
            <Field
              label="Bancos de dados hospedados"
              value={databases.isError ? "Indisponível" : countLabel(activeDatabases?.length, "instância ativa", "instâncias ativas")}
            />
          ) : null}
        </dl>
      </ItpSectionCard>

      {canSeeServices ? (
        <HostingsSection
          owner={{ serverId: server.id }}
          title="Serviços hospedados"
          emptyMessage="Nenhum serviço vinculado a este servidor."
          canManage={capabilities?.can_manage_services === true}
          ownerArchived={server.archived}
        />
      ) : null}
      {canSeeDatabases ? <ServerDatabasesSection server={server} /> : null}
    </>
  );
}

function ServerDatabasesSection({ server }: { server: Server }) {
  const { basePath, capabilities } = usePortal();
  const [creating, setCreating] = useState(false);
  const databases = useServerDatabases(server.id, true);
  const canCreate = capabilities?.can_manage_databases === true && !server.archived;

  const columns: DataTableColumn<DatabaseInstance>[] = [
    { key: "code", header: "Código", render: (row) => <span className="itp-code">{row.code}</span> },
    { key: "name", header: "Instância", render: (row) => <strong>{row.name}</strong> },
    {
      key: "dbms",
      header: "SGBD",
      render: (row) => `${DBMS_LABELS[row.dbms]}${row.version ? ` ${row.version}` : ""}`,
    },
    { key: "port", header: "Porta", render: (row) => row.port ?? "—" },
    { key: "environment", header: "Ambiente", render: (row) => <EnvironmentBadge value={row.environment} /> },
    { key: "criticality", header: "Criticidade", render: (row) => <CriticalityBadge value={row.criticality} /> },
    {
      key: "status",
      header: "Situação",
      render: (row) => (row.archived ? <ArchivedBadge /> : <AdministrativeStatusBadge value={row.administrative_status} />),
    },
    { key: "consumers", header: "Serviços", align: "right", render: (row) => row.consumer_count },
  ];

  if (databases.error && !databases.data) {
    return <QueryErrorState error={toApiError(databases.error)} onRetry={() => void databases.refetch()} />;
  }
  const total = databases.data?.total ?? 0;

  return (
    <>
      <DataTableSection<DatabaseInstance>
        title="Bancos de dados associados"
        hint={
          total > SERVER_DATABASES_LIMIT
            ? `Exibindo ${SERVER_DATABASES_LIMIT} de ${total}. Use a área Bancos de dados para ver todos.`
            : undefined
        }
        columns={columns}
        rows={databases.data?.items ?? []}
        rowKey={(row) => row.id}
        loading={databases.isPending}
        refreshing={databases.isFetching && !databases.isPending}
        emptyMessage="Nenhuma instância de banco hospedada neste servidor."
        getSearchText={(row) => `${row.code} ${row.name} ${DBMS_LABELS[row.dbms]} ${row.version ?? ""}`}
        searchPlaceholder="Buscar instância…"
        onRowClick={(row) => navigateTo(buildPath(basePath, { databaseId: row.id }))}
        headerActions={
          canCreate ? (
            <ItpActionButton variant="primary" onClick={() => setCreating(true)}>
              <Plus size={16} strokeWidth={1.75} aria-hidden="true" /> Cadastrar instância
            </ItpActionButton>
          ) : null
        }
      />
      {creating ? <DatabaseFormModal presetServerId={server.id} onClose={() => setCreating(false)} /> : null}
    </>
  );
}
