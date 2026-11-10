import { useQuery } from "@tanstack/react-query";
import { Archive, ArchiveRestore, Pencil } from "lucide-react";
import { useState } from "react";

import { itPortalApi } from "../../api/itPortalApi";
import {
  AdministrativeStatusBadge,
  ArchivedBadge,
  CriticalityBadge,
  EnvironmentBadge,
  ServiceKindBadge,
} from "../../app/badges";
import { formatDateTime, orDash } from "../../app/format";
import { ItpActionButton, ItpPageHero, ItpPagePath, ItpSectionCard, ItpStateBanner } from "../../app/itPortalUi";
import { spaNavigate } from "../../app/navigation";
import { toApiError, usePortal } from "../../app/PortalContext";
import { LoadingBlock, QueryErrorState } from "../../app/QueryStates";
import { queryKeys } from "../../app/queryKeys";
import { buildPath } from "../../app/routes";
import { SERVICE_FIELD_LABELS, SERVICE_TYPE_LABELS, UNIT_LABELS } from "../../content/labels";
import { HistorySection } from "../history/HistorySection";
import { DependenciesSection, IntegrationsSection } from "../inventory/ConnectivitySections";
import { DetailField as Field, InventoryConfirmDialog } from "../inventory/InventoryDialogs";
import { ConsumersSection, HostingsSection } from "../inventory/LinkSections";
import { ServiceFormModal } from "./ServiceFormModal";

type Modal = "edit" | "archive" | "restore" | null;

export function ServiceDetailPage({ serviceId }: { serviceId: string }) {
  const { basePath, capabilities } = usePortal();
  const [modal, setModal] = useState<Modal>(null);
  const serviceQuery = useQuery({
    queryKey: queryKeys.service(serviceId),
    queryFn: ({ signal }) => itPortalApi.getService(serviceId, signal),
  });

  const listHref = buildPath(basePath, "services");
  const pagePath = (current: string) => (
    <ItpPagePath back={{ label: "Serviços", href: listHref, onNavigate: spaNavigate(listHref) }} current={current} />
  );

  if (serviceQuery.isPending) {
    return (
      <>
        {pagePath("Serviço")}
        <LoadingBlock title="Carregando serviço" />
      </>
    );
  }
  if (serviceQuery.error || !serviceQuery.data) {
    return (
      <>
        {pagePath("Serviço")}
        <QueryErrorState error={toApiError(serviceQuery.error)} onRetry={() => void serviceQuery.refetch()} />
      </>
    );
  }

  const service = serviceQuery.data;
  const canManage = capabilities?.can_manage_services === true;
  const canSeeDatabases = capabilities?.can_view_databases === true;
  const canManageConsumers = capabilities?.can_manage_databases === true;

  return (
    <>
      {pagePath(service.name)}
      <ItpPageHero
        aria-label={`Serviço ${service.name}`}
        eyebrow={service.code}
        title={service.name}
        description={`${SERVICE_TYPE_LABELS[service.service_type]}${service.technology ? ` · ${service.technology}` : ""}`}
        badge={
          <span className="itp-badge-group">
            {service.archived ? <ArchivedBadge /> : <AdministrativeStatusBadge value={service.administrative_status} />}
            <ServiceKindBadge value={service.service_kind} />
            <EnvironmentBadge value={service.environment} />
            <CriticalityBadge value={service.criticality} />
          </span>
        }
        actions={
          canManage ? (
            service.archived ? (
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

      {service.archived ? (
        <ItpStateBanner>
          <p className="itp-state-text">
            Serviço arquivado em {formatDateTime(service.archived_at)} por {orDash(service.archived_by_name)}. O cadastro e
            os vínculos existentes estão somente para consulta; restaure-o para editar ou criar novos vínculos.
          </p>
        </ItpStateBanner>
      ) : null}

      <div className="itp-detail-grid">
        <ItpSectionCard title="Identificação">
          <dl className="itp-field-list">
            <Field label="Código" value={service.code} />
            <Field label={SERVICE_FIELD_LABELS.service_kind} value={<ServiceKindBadge value={service.service_kind} />} />
            <Field label={SERVICE_FIELD_LABELS.service_type} value={SERVICE_TYPE_LABELS[service.service_type]} />
            <Field label={SERVICE_FIELD_LABELS.technology} value={orDash(service.technology)} />
            <Field label={SERVICE_FIELD_LABELS.unit_code} value={UNIT_LABELS[service.unit_code] ?? service.unit_code} />
          </dl>
        </ItpSectionCard>
        <ItpSectionCard title="Operação">
          <dl className="itp-field-list">
            <Field label={SERVICE_FIELD_LABELS.environment} value={<EnvironmentBadge value={service.environment} />} />
            <Field label={SERVICE_FIELD_LABELS.port} value={service.port ?? "—"} />
            <Field label={SERVICE_FIELD_LABELS.criticality} value={<CriticalityBadge value={service.criticality} />} />
            <Field
              label={SERVICE_FIELD_LABELS.administrative_status}
              value={<AdministrativeStatusBadge value={service.administrative_status} />}
            />
          </dl>
        </ItpSectionCard>
        <ItpSectionCard title="Responsabilidade e registro">
          <dl className="itp-field-list">
            <Field label={SERVICE_FIELD_LABELS.responsible} value={service.responsible} />
            <Field label="Cadastrado" value={`${formatDateTime(service.created_at)} · ${service.created_by_name}`} />
            <Field label="Última alteração" value={`${formatDateTime(service.updated_at)} · ${service.updated_by_name}`} />
          </dl>
        </ItpSectionCard>
      </div>

      <ItpSectionCard title={SERVICE_FIELD_LABELS.description}>
        <p className="itp-prewrap">{service.description?.trim() ? service.description : "Sem descrição."}</p>
      </ItpSectionCard>

      <HostingsSection
        owner={{ serviceId: service.id }}
        title="Servidores onde executa"
        emptyMessage="Nenhum servidor vinculado a este serviço."
        canManage={canManage}
        ownerArchived={service.archived}
      />
      {canSeeDatabases ? (
        <ConsumersSection
          owner={{ serviceId: service.id }}
          title="Bancos de dados utilizados"
          emptyMessage="Nenhuma instância de banco vinculada a este serviço."
          canManage={canManageConsumers}
          ownerArchived={service.archived}
        />
      ) : null}
      {capabilities?.can_view_integrations ? (
        <IntegrationsSection
          owner={{ serviceId: service.id, service }}
          title="Integrações"
          emptyMessage="Nenhuma integração registrada para este serviço."
          canManage={capabilities.can_manage_integrations}
          ownerArchived={service.archived}
        />
      ) : null}
      <DependenciesSection service={service} canManage={canManage} ownerArchived={service.archived} />

      <HistorySection
        queryKey={queryKeys.serviceHistory(service.id)}
        queryFn={(signal) => itPortalApi.listServiceHistory(service.id, signal)}
        subtitle="Últimos 50 eventos auditados deste serviço, incluindo vínculos."
        ariaLabel="Histórico do serviço"
      />

      {modal === "edit" ? <ServiceFormModal service={service} onClose={() => setModal(null)} /> : null}
      {modal === "archive" ? (
        <InventoryConfirmDialog
          title="Arquivar serviço"
          message={`Arquivar ${service.name}? O cadastro sai do inventário ativo, mas os vínculos e o histórico são preservados.`}
          confirmLabel="Arquivar"
          busyLabel="Arquivando…"
          successMessage={`${service.code} arquivado.`}
          danger
          action={() => itPortalApi.archiveService(service.id, service.revision)}
          onClose={() => setModal(null)}
        />
      ) : null}
      {modal === "restore" ? (
        <InventoryConfirmDialog
          title="Restaurar serviço"
          message={`Restaurar ${service.name} ao inventário ativo?`}
          confirmLabel="Restaurar"
          busyLabel="Restaurando…"
          successMessage={`${service.code} restaurado.`}
          action={() => itPortalApi.restoreService(service.id, service.revision)}
          onClose={() => setModal(null)}
        />
      ) : null}
    </>
  );
}
