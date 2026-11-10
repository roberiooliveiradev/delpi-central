import { useQuery } from "@tanstack/react-query";
import { Archive, ArchiveRestore, Pencil } from "lucide-react";
import { useState } from "react";

import { itPortalApi } from "../../api/itPortalApi";
import { AdministrativeStatusBadge, ArchivedBadge, CriticalityBadge } from "../../app/badges";
import { formatDateTime, orDash } from "../../app/format";
import { ItpActionButton, ItpPageHero, ItpPagePath, ItpSectionCard, ItpStateBanner } from "../../app/itPortalUi";
import { spaNavigate } from "../../app/navigation";
import { toApiError, usePortal } from "../../app/PortalContext";
import { LoadingBlock, QueryErrorState } from "../../app/QueryStates";
import { queryKeys } from "../../app/queryKeys";
import { buildPath } from "../../app/routes";
import {
  INTEGRATION_DIRECTION_LABELS,
  INTEGRATION_FIELD_LABELS,
  INTEGRATION_PROTOCOL_LABELS,
} from "../../content/labels";
import { HistorySection } from "../history/HistorySection";
import { DetailField as Field, InventoryConfirmDialog } from "../inventory/InventoryDialogs";
import { IntegrationEndpoint } from "./IntegrationEndpoint";
import { IntegrationFormModal } from "./IntegrationFormModal";

type Modal = "edit" | "archive" | "restore" | null;

export function IntegrationDetailPage({ integrationId }: { integrationId: string }) {
  const { basePath, capabilities } = usePortal();
  const [modal, setModal] = useState<Modal>(null);
  const integrationQuery = useQuery({
    queryKey: queryKeys.integration(integrationId),
    queryFn: ({ signal }) => itPortalApi.getIntegration(integrationId, signal),
  });

  const listHref = buildPath(basePath, "integrations");
  const pagePath = (current: string) => (
    <ItpPagePath back={{ label: "Integrações", href: listHref, onNavigate: spaNavigate(listHref) }} current={current} />
  );

  if (integrationQuery.isPending) {
    return (
      <>
        {pagePath("Integração")}
        <LoadingBlock title="Carregando integração" />
      </>
    );
  }
  if (integrationQuery.error || !integrationQuery.data) {
    return (
      <>
        {pagePath("Integração")}
        <QueryErrorState error={toApiError(integrationQuery.error)} onRetry={() => void integrationQuery.refetch()} />
      </>
    );
  }

  const integration = integrationQuery.data;
  const canManage = capabilities?.can_manage_integrations === true;

  return (
    <>
      {pagePath(integration.name)}
      <ItpPageHero
        aria-label={`Integração ${integration.name}`}
        eyebrow={integration.code}
        title={integration.name}
        description={`${INTEGRATION_PROTOCOL_LABELS[integration.protocol]} · ${INTEGRATION_DIRECTION_LABELS[integration.direction]}`}
        badge={
          <span className="itp-badge-group">
            {integration.archived ? <ArchivedBadge /> : <AdministrativeStatusBadge value={integration.administrative_status} />}
            <CriticalityBadge value={integration.criticality} />
          </span>
        }
        actions={
          canManage ? (
            integration.archived ? (
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

      {integration.archived ? (
        <ItpStateBanner>
          <p className="itp-state-text">
            Integração arquivada em {formatDateTime(integration.archived_at)} por {orDash(integration.archived_by_name)}. O
            cadastro está somente para consulta; restaure-o para editar.
          </p>
        </ItpStateBanner>
      ) : null}

      <div className="itp-detail-grid">
        <ItpSectionCard title="Pontas">
          <dl className="itp-field-list">
            <Field label="Origem" value={<IntegrationEndpoint integration={integration} side="source" />} />
            <Field label="Destino" value={<IntegrationEndpoint integration={integration} side="target" />} />
            <Field label={INTEGRATION_FIELD_LABELS.direction} value={INTEGRATION_DIRECTION_LABELS[integration.direction]} />
            <Field label={INTEGRATION_FIELD_LABELS.protocol} value={INTEGRATION_PROTOCOL_LABELS[integration.protocol]} />
          </dl>
        </ItpSectionCard>
        <ItpSectionCard title="Operação">
          <dl className="itp-field-list">
            <Field label="Código" value={integration.code} />
            <Field label={INTEGRATION_FIELD_LABELS.purpose} value={orDash(integration.purpose)} />
            <Field label={INTEGRATION_FIELD_LABELS.criticality} value={<CriticalityBadge value={integration.criticality} />} />
            <Field
              label={INTEGRATION_FIELD_LABELS.administrative_status}
              value={<AdministrativeStatusBadge value={integration.administrative_status} />}
            />
          </dl>
        </ItpSectionCard>
        <ItpSectionCard title="Responsabilidade e registro">
          <dl className="itp-field-list">
            <Field label={INTEGRATION_FIELD_LABELS.responsible} value={integration.responsible} />
            <Field label="Cadastrado" value={`${formatDateTime(integration.created_at)} · ${integration.created_by_name}`} />
            <Field label="Última alteração" value={`${formatDateTime(integration.updated_at)} · ${integration.updated_by_name}`} />
          </dl>
        </ItpSectionCard>
      </div>

      <ItpSectionCard title={INTEGRATION_FIELD_LABELS.notes}>
        <p className="itp-prewrap">{integration.notes?.trim() ? integration.notes : "Sem observações."}</p>
      </ItpSectionCard>

      <HistorySection
        queryKey={queryKeys.integrationHistory(integration.id)}
        queryFn={(signal) => itPortalApi.listIntegrationHistory(integration.id, signal)}
        subtitle="Últimos 50 eventos auditados desta integração."
        ariaLabel="Histórico da integração"
      />

      {modal === "edit" ? <IntegrationFormModal integration={integration} onClose={() => setModal(null)} /> : null}
      {modal === "archive" ? (
        <InventoryConfirmDialog
          title="Arquivar integração"
          message={`Arquivar ${integration.name}? O cadastro sai do inventário ativo, mas os serviços envolvidos e o histórico são preservados.`}
          confirmLabel="Arquivar"
          busyLabel="Arquivando…"
          successMessage={`${integration.code} arquivada.`}
          danger
          action={() => itPortalApi.archiveIntegration(integration.id, integration.revision)}
          onClose={() => setModal(null)}
        />
      ) : null}
      {modal === "restore" ? (
        <InventoryConfirmDialog
          title="Restaurar integração"
          message={`Restaurar ${integration.name} ao inventário ativo?`}
          confirmLabel="Restaurar"
          busyLabel="Restaurando…"
          successMessage={`${integration.code} restaurada.`}
          action={() => itPortalApi.restoreIntegration(integration.id, integration.revision)}
          onClose={() => setModal(null)}
        />
      ) : null}
    </>
  );
}
