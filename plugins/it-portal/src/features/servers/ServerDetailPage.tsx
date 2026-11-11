import { useMutation, useQuery } from "@tanstack/react-query";
import { Archive, ArchiveRestore, Pencil, Plus } from "lucide-react";
import { useState, type ReactNode } from "react";

import { itPortalApi, type Server } from "../../api/itPortalApi";
import { AdministrativeStatusBadge, ArchivedBadge, CriticalityBadge, EnvironmentBadge } from "../../app/badges";
import { formatDateTime, orDash } from "../../app/format";
import {
  ItpActionButton,
  ItpConfirmPanel,
  ItpDialog,
  ItpPageHero,
  ItpPagePath,
  ItpSectionCard,
  ItpStateBanner,
  itpConfirmClassNames,
} from "../../app/itPortalUi";
import { spaNavigate } from "../../app/navigation";
import { toApiError, usePortal } from "../../app/PortalContext";
import { LoadingBlock, QueryErrorState } from "../../app/QueryStates";
import { queryKeys } from "../../app/queryKeys";
import { buildPath } from "../../app/routes";
import { SERVER_FIELD_LABELS, SERVER_TYPE_LABELS, UNIT_LABELS } from "../../content/labels";
import { ActionPlanFormModal } from "../action-plans/ActionPlanModals";
import { ActionPlanTable, useListState } from "../action-plans/ActionPlanTable";
import { ServerAutomaticInventorySection } from "./ServerAutomaticInventorySection";
import { ServerComponentsSections } from "./ServerComponentsSections";
import { ServerFormModal, useInvalidateInventory } from "./ServerFormModal";
import { ServerHistorySection } from "./ServerHistorySection";
import { ServerNotesSection } from "./ServerNotesSection";

type Modal = "edit" | "archive" | "restore" | "new_action" | null;

function Field({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="itp-field">
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}

export function ServerDetailPage({ serverId }: { serverId: string }) {
  const { basePath, capabilities } = usePortal();
  const [modal, setModal] = useState<Modal>(null);

  const serverQuery = useQuery({
    queryKey: queryKeys.server(serverId),
    queryFn: ({ signal }) => itPortalApi.getServer(serverId, signal),
  });

  const serversHref = buildPath(basePath, "servers");
  const pagePath = (current: string) => (
    <ItpPagePath
      back={{ label: "Servidores", href: serversHref, onNavigate: spaNavigate(serversHref) }}
      current={current}
    />
  );

  if (serverQuery.isPending) {
    return (
      <>
        {pagePath("Servidor")}
        <LoadingBlock title="Carregando servidor" />
      </>
    );
  }
  if (serverQuery.error || !serverQuery.data) {
    return (
      <>
        {pagePath("Servidor")}
        <QueryErrorState error={toApiError(serverQuery.error)} onRetry={() => void serverQuery.refetch()} />
      </>
    );
  }

  const server = serverQuery.data;
  const canManage = capabilities?.can_manage_servers === true;
  const canManageActions = capabilities?.can_manage_action_plans === true;

  return (
    <>
      {pagePath(server.name)}
      <ItpPageHero
        variant="immersive"
        aria-label={`Servidor ${server.name}`}
        eyebrow={server.code}
        title={server.name}
        description={server.hostname}
        badge={
          <span className="itp-badge-group">
            {server.archived ? <ArchivedBadge /> : <AdministrativeStatusBadge value={server.administrative_status} />}
            <EnvironmentBadge value={server.environment} />
            <CriticalityBadge value={server.criticality} />
          </span>
        }
        actions={
          canManage ? (
            server.archived ? (
              <ItpActionButton onClick={() => setModal("restore")}>
                <ArchiveRestore size={16} strokeWidth={1.75} aria-hidden="true" /> Restaurar
              </ItpActionButton>
            ) : (
              <span className="itp-row-actions">
                <ItpActionButton variant="primary" onClick={() => setModal("edit")}>
                  <Pencil size={16} strokeWidth={1.75} aria-hidden="true" /> Editar
                </ItpActionButton>
                <ItpActionButton onClick={() => setModal("archive")}>
                  <Archive size={16} strokeWidth={1.75} aria-hidden="true" /> Arquivar
                </ItpActionButton>
              </span>
            )
          ) : null
        }
      />

      {server.archived ? (
        <ItpStateBanner>
          <p className="itp-state-text">
            Servidor arquivado em {formatDateTime(server.archived_at)} por {orDash(server.archived_by_name)}. O
            cadastro está somente para consulta; restaure-o para editar, anotar ou criar planos de ação.
          </p>
        </ItpStateBanner>
      ) : null}

      <div className="itp-detail-grid">
        <ItpSectionCard title="Identificação">
          <dl className="itp-field-list">
            <Field label="Código" value={server.code} />
            <Field label={SERVER_FIELD_LABELS.hostname} value={server.hostname} />
            <Field label={SERVER_FIELD_LABELS.ip_address} value={orDash(server.ip_address)} />
            <Field label={SERVER_FIELD_LABELS.unit_code} value={UNIT_LABELS[server.unit_code] ?? server.unit_code} />
            <Field label={SERVER_FIELD_LABELS.location} value={orDash(server.location)} />
          </dl>
        </ItpSectionCard>
        <ItpSectionCard title="Operação">
          <dl className="itp-field-list">
            <Field label={SERVER_FIELD_LABELS.environment} value={<EnvironmentBadge value={server.environment} />} />
            <Field label={SERVER_FIELD_LABELS.server_type} value={SERVER_TYPE_LABELS[server.server_type]} />
            <Field label={SERVER_FIELD_LABELS.purpose} value={orDash(server.purpose)} />
            <Field label={SERVER_FIELD_LABELS.operating_system} value={orDash(server.operating_system)} />
            <Field label={SERVER_FIELD_LABELS.criticality} value={<CriticalityBadge value={server.criticality} />} />
            <Field
              label={SERVER_FIELD_LABELS.administrative_status}
              value={<AdministrativeStatusBadge value={server.administrative_status} />}
            />
          </dl>
        </ItpSectionCard>
        <ItpSectionCard title="Responsabilidade e registro">
          <dl className="itp-field-list">
            <Field label={SERVER_FIELD_LABELS.responsible} value={orDash(server.responsible)} />
            <Field label="Cadastrado" value={`${formatDateTime(server.created_at)} · ${server.created_by_name}`} />
            <Field label="Última alteração" value={`${formatDateTime(server.updated_at)} · ${server.updated_by_name}`} />
          </dl>
        </ItpSectionCard>
      </div>

      <ItpSectionCard title={SERVER_FIELD_LABELS.description}>
        <p className="itp-prewrap">{server.description?.trim() ? server.description : "Sem descrição."}</p>
      </ItpSectionCard>

      {capabilities?.can_view_action_plans ? (
        <ServerActionPlans
          server={server}
          canCreate={canManageActions && !server.archived}
          onCreate={() => setModal("new_action")}
        />
      ) : null}

      <ServerComponentsSections server={server} />

      <ServerAutomaticInventorySection serverId={server.id} />

      <ServerNotesSection server={server} />
      <ServerHistorySection serverId={server.id} />

      {modal === "edit" ? <ServerFormModal open server={server} onClose={() => setModal(null)} /> : null}
      {modal === "archive" || modal === "restore" ? (
        <ArchiveDialog server={server} mode={modal} onClose={() => setModal(null)} />
      ) : null}
      {modal === "new_action" ? (
        <ActionPlanFormModal open serverId={server.id} onClose={() => setModal(null)} />
      ) : null}
    </>
  );
}

function ServerActionPlans({ server, canCreate, onCreate }: { server: Server; canCreate: boolean; onCreate: () => void }) {
  const list = useListState("due_date");
  return (
    <ActionPlanTable
      title="Planos de ação"
      query={{
        server_id: server.id,
        sort: list.sort,
        direction: list.direction,
        page: list.page,
        page_size: list.pageSize,
      }}
      showServer={false}
      emptyMessage="Nenhum plano de ação para este servidor."
      onPageChange={list.setPage}
      onPageSizeChange={list.onPageSizeChange}
      onSortChange={list.onSortChange}
      headerActions={
        canCreate ? (
          <ItpActionButton variant="primary" onClick={onCreate}>
            <Plus size={16} strokeWidth={1.75} aria-hidden="true" /> Novo plano
          </ItpActionButton>
        ) : null
      }
    />
  );
}

function ArchiveDialog({
  server,
  mode,
  onClose,
}: {
  server: Server;
  mode: "archive" | "restore";
  onClose: () => void;
}) {
  const { notifySuccess, notifyError } = usePortal();
  const invalidate = useInvalidateInventory();
  const archiving = mode === "archive";

  const mutation = useMutation({
    mutationFn: () =>
      archiving ? itPortalApi.archiveServer(server.id, server.revision) : itPortalApi.restoreServer(server.id, server.revision),
    onSuccess: () => {
      invalidate();
      notifySuccess(archiving ? `${server.code} arquivado.` : `${server.code} restaurado.`);
      onClose();
    },
    onError: (error) => {
      notifyError(error);
      onClose();
    },
  });

  return (
    <ItpDialog
      open
      title={archiving ? "Arquivar servidor" : "Restaurar servidor"}
      onClose={() => (mutation.isPending ? undefined : onClose())}
    >
      <ItpConfirmPanel
        classNames={itpConfirmClassNames}
        message={
          archiving
            ? `Arquivar ${server.name} (${server.hostname})? O cadastro sai do inventário ativo, mas notas, planos e histórico são preservados. Servidores com planos de ação abertos não podem ser arquivados.`
            : `Restaurar ${server.name} (${server.hostname}) ao inventário ativo?`
        }
        confirmLabel={archiving ? "Arquivar" : "Restaurar"}
        cancelLabel="Cancelar"
        confirmBusy={mutation.isPending}
        confirmBusyLabel={archiving ? "Arquivando…" : "Restaurando…"}
        variant={archiving ? "danger" : "default"}
        onConfirm={() => mutation.mutate()}
        onCancel={onClose}
      />
    </ItpDialog>
  );
}
