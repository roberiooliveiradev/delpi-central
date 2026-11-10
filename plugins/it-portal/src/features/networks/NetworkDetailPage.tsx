import { useQuery } from "@tanstack/react-query";
import { Archive, ArchiveRestore, Pencil } from "lucide-react";
import { useState } from "react";

import { itPortalApi } from "../../api/itPortalApi";
import { ArchivedBadge, CriticalityBadge, EnvironmentBadge, NetworkScopeBadge } from "../../app/badges";
import { formatDateTime, orDash } from "../../app/format";
import { ItpActionButton, ItpPageHero, ItpPagePath, ItpSectionCard, ItpStateBanner } from "../../app/itPortalUi";
import { spaNavigate } from "../../app/navigation";
import { toApiError, usePortal } from "../../app/PortalContext";
import { LoadingBlock, QueryErrorState } from "../../app/QueryStates";
import { queryKeys } from "../../app/queryKeys";
import { buildPath } from "../../app/routes";
import { NETWORK_FIELD_LABELS, UNIT_LABELS } from "../../content/labels";
import { HistorySection } from "../history/HistorySection";
import { NetworkLinksSection } from "../inventory/ConnectivitySections";
import { DetailField as Field, InventoryConfirmDialog } from "../inventory/InventoryDialogs";
import { NetworkFormModal } from "./NetworkFormModal";

type Modal = "edit" | "archive" | "restore" | null;

export function NetworkDetailPage({ networkId }: { networkId: string }) {
  const { basePath, capabilities } = usePortal();
  const [modal, setModal] = useState<Modal>(null);
  const networkQuery = useQuery({
    queryKey: queryKeys.network(networkId),
    queryFn: ({ signal }) => itPortalApi.getNetwork(networkId, signal),
  });

  const listHref = buildPath(basePath, "networks");
  const pagePath = (current: string) => (
    <ItpPagePath back={{ label: "Redes", href: listHref, onNavigate: spaNavigate(listHref) }} current={current} />
  );

  if (networkQuery.isPending) {
    return (
      <>
        {pagePath("Rede")}
        <LoadingBlock title="Carregando rede" />
      </>
    );
  }
  if (networkQuery.error || !networkQuery.data) {
    return (
      <>
        {pagePath("Rede")}
        <QueryErrorState error={toApiError(networkQuery.error)} onRetry={() => void networkQuery.refetch()} />
      </>
    );
  }

  const network = networkQuery.data;
  const canManage = capabilities?.can_manage_networks === true;

  return (
    <>
      {pagePath(network.name)}
      <ItpPageHero
        aria-label={`Rede ${network.name}`}
        eyebrow={network.code}
        title={network.name}
        description={`${network.cidr}${network.vlan_id !== null ? ` · VLAN ${network.vlan_id}` : ""}`}
        badge={
          <span className="itp-badge-group">
            {network.archived ? <ArchivedBadge /> : null}
            <NetworkScopeBadge value={network.network_scope} />
            <EnvironmentBadge value={network.environment} />
            <CriticalityBadge value={network.criticality} />
          </span>
        }
        actions={
          canManage ? (
            network.archived ? (
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

      {network.archived ? (
        <ItpStateBanner>
          <p className="itp-state-text">
            Rede arquivada em {formatDateTime(network.archived_at)} por {orDash(network.archived_by_name)}. O cadastro e os
            vínculos existentes estão somente para consulta; restaure-a para editar ou vincular servidores.
          </p>
        </ItpStateBanner>
      ) : null}

      <div className="itp-detail-grid">
        <ItpSectionCard title="Endereçamento">
          <dl className="itp-field-list">
            <Field label="Código" value={network.code} />
            <Field label={NETWORK_FIELD_LABELS.cidr} value={<span className="itp-code">{network.cidr}</span>} />
            <Field label={NETWORK_FIELD_LABELS.gateway} value={orDash(network.gateway)} />
            <Field label={NETWORK_FIELD_LABELS.vlan_id} value={network.vlan_id ?? "—"} />
            <Field label={NETWORK_FIELD_LABELS.network_scope} value={<NetworkScopeBadge value={network.network_scope} />} />
          </dl>
        </ItpSectionCard>
        <ItpSectionCard title="Localização e uso">
          <dl className="itp-field-list">
            <Field label={NETWORK_FIELD_LABELS.unit_code} value={UNIT_LABELS[network.unit_code] ?? network.unit_code} />
            <Field label={NETWORK_FIELD_LABELS.location} value={orDash(network.location)} />
            <Field label={NETWORK_FIELD_LABELS.environment} value={<EnvironmentBadge value={network.environment} />} />
            <Field label={NETWORK_FIELD_LABELS.zone} value={orDash(network.zone)} />
            <Field label={NETWORK_FIELD_LABELS.purpose} value={orDash(network.purpose)} />
          </dl>
        </ItpSectionCard>
        <ItpSectionCard title="Responsabilidade e registro">
          <dl className="itp-field-list">
            <Field label={NETWORK_FIELD_LABELS.criticality} value={<CriticalityBadge value={network.criticality} />} />
            <Field label={NETWORK_FIELD_LABELS.responsible} value={network.responsible} />
            <Field label="Cadastrado" value={`${formatDateTime(network.created_at)} · ${network.created_by_name}`} />
            <Field label="Última alteração" value={`${formatDateTime(network.updated_at)} · ${network.updated_by_name}`} />
          </dl>
        </ItpSectionCard>
      </div>

      <ItpSectionCard title={NETWORK_FIELD_LABELS.notes}>
        <p className="itp-prewrap">{network.notes?.trim() ? network.notes : "Sem observações."}</p>
      </ItpSectionCard>

      <NetworkLinksSection
        owner={{ networkId: network.id }}
        title="Servidores conectados"
        emptyMessage="Nenhum servidor vinculado a esta rede."
        canManage={canManage}
        ownerArchived={network.archived}
      />

      <HistorySection
        queryKey={queryKeys.networkHistory(network.id)}
        queryFn={(signal) => itPortalApi.listNetworkHistory(network.id, signal)}
        subtitle="Últimos 50 eventos auditados desta rede, incluindo vínculos."
        ariaLabel="Histórico da rede"
      />

      {modal === "edit" ? <NetworkFormModal network={network} onClose={() => setModal(null)} /> : null}
      {modal === "archive" ? (
        <InventoryConfirmDialog
          title="Arquivar rede"
          message={`Arquivar ${network.name}? O cadastro sai do inventário ativo, mas os vínculos e o histórico são preservados.`}
          confirmLabel="Arquivar"
          busyLabel="Arquivando…"
          successMessage={`${network.code} arquivada.`}
          danger
          action={() => itPortalApi.archiveNetwork(network.id, network.revision)}
          onClose={() => setModal(null)}
        />
      ) : null}
      {modal === "restore" ? (
        <InventoryConfirmDialog
          title="Restaurar rede"
          message={`Restaurar ${network.name} ao inventário ativo?`}
          confirmLabel="Restaurar"
          busyLabel="Restaurando…"
          successMessage={`${network.code} restaurada.`}
          action={() => itPortalApi.restoreNetwork(network.id, network.revision)}
          onClose={() => setModal(null)}
        />
      ) : null}
    </>
  );
}
