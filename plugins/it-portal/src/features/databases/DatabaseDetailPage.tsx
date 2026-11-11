import { useQuery } from "@tanstack/react-query";
import { Archive, ArchiveRestore, Pencil } from "lucide-react";
import { useState } from "react";

import { itPortalApi } from "../../api/itPortalApi";
import { AdministrativeStatusBadge, ArchivedBadge, CriticalityBadge, EnvironmentBadge } from "../../app/badges";
import { formatDateTime, orDash } from "../../app/format";
import { ItpActionButton, ItpPageHero, ItpPagePath, ItpSectionCard, ItpStateBanner } from "../../app/itPortalUi";
import { spaNavigate } from "../../app/navigation";
import { toApiError, usePortal } from "../../app/PortalContext";
import { LoadingBlock, QueryErrorState } from "../../app/QueryStates";
import { queryKeys } from "../../app/queryKeys";
import { buildPath } from "../../app/routes";
import { DATABASE_FIELD_LABELS, DBMS_LABELS } from "../../content/labels";
import { HistorySection } from "../history/HistorySection";
import { DetailField as Field, InventoryConfirmDialog } from "../inventory/InventoryDialogs";
import { ConsumersSection } from "../inventory/LinkSections";
import { DatabaseFormModal } from "./DatabaseFormModal";

type Modal = "edit" | "archive" | "restore" | null;

export function DatabaseDetailPage({ databaseId }: { databaseId: string }) {
  const { basePath, capabilities } = usePortal();
  const [modal, setModal] = useState<Modal>(null);
  const databaseQuery = useQuery({
    queryKey: queryKeys.database(databaseId),
    queryFn: ({ signal }) => itPortalApi.getDatabase(databaseId, signal),
  });

  const listHref = buildPath(basePath, "databases");
  const pagePath = (current: string) => (
    <ItpPagePath back={{ label: "Bancos de dados", href: listHref, onNavigate: spaNavigate(listHref) }} current={current} />
  );

  if (databaseQuery.isPending) {
    return (
      <>
        {pagePath("Instância de banco")}
        <LoadingBlock title="Carregando instância" />
      </>
    );
  }
  if (databaseQuery.error || !databaseQuery.data) {
    return (
      <>
        {pagePath("Instância de banco")}
        <QueryErrorState error={toApiError(databaseQuery.error)} onRetry={() => void databaseQuery.refetch()} />
      </>
    );
  }

  const database = databaseQuery.data;
  const canManage = capabilities?.can_manage_databases === true;
  const canSeeServices = capabilities?.can_view_services === true;
  const serverHref = buildPath(basePath, { serverId: database.server_id });

  return (
    <>
      {pagePath(database.name)}
      <ItpPageHero
        variant="immersive"
        aria-label={`Instância de banco ${database.name}`}
        eyebrow={database.code}
        title={database.name}
        description={`${DBMS_LABELS[database.dbms]}${database.version ? ` ${database.version}` : ""} em ${database.server.name}`}
        badge={
          <span className="itp-badge-group">
            {database.archived ? <ArchivedBadge /> : <AdministrativeStatusBadge value={database.administrative_status} />}
            <EnvironmentBadge value={database.environment} />
            <CriticalityBadge value={database.criticality} />
          </span>
        }
        actions={
          canManage ? (
            database.archived ? (
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

      {database.archived ? (
        <ItpStateBanner>
          <p className="itp-state-text">
            Instância arquivada em {formatDateTime(database.archived_at)} por {orDash(database.archived_by_name)}. O
            cadastro e os vínculos estão somente para consulta; restaure-a para editar ou vincular serviços.
          </p>
        </ItpStateBanner>
      ) : null}

      <div className="itp-detail-grid">
        <ItpSectionCard title="Identificação">
          <dl className="itp-field-list">
            <Field label="Código" value={database.code} />
            <Field label={DATABASE_FIELD_LABELS.dbms} value={DBMS_LABELS[database.dbms]} />
            <Field label={DATABASE_FIELD_LABELS.version} value={orDash(database.version)} />
            <Field label={DATABASE_FIELD_LABELS.port} value={database.port ?? "—"} />
            <Field label={DATABASE_FIELD_LABELS.purpose} value={orDash(database.purpose)} />
          </dl>
        </ItpSectionCard>
        <ItpSectionCard title="Hospedagem e operação">
          <dl className="itp-field-list">
            <Field
              label={DATABASE_FIELD_LABELS.server_id}
              value={
                <ItpActionButton
                  variant="link"
                  href={serverHref}
                  title={`Abrir ${database.server.name}`}
                  onClick={spaNavigate(serverHref)}
                >
                  {database.server.name} ({database.server.hostname})
                </ItpActionButton>
              }
            />
            <Field label={DATABASE_FIELD_LABELS.environment} value={<EnvironmentBadge value={database.environment} />} />
            <Field label={DATABASE_FIELD_LABELS.criticality} value={<CriticalityBadge value={database.criticality} />} />
            <Field
              label={DATABASE_FIELD_LABELS.administrative_status}
              value={<AdministrativeStatusBadge value={database.administrative_status} />}
            />
          </dl>
        </ItpSectionCard>
        <ItpSectionCard title="Responsabilidade e registro">
          <dl className="itp-field-list">
            <Field label={DATABASE_FIELD_LABELS.responsible} value={database.responsible} />
            <Field label="Cadastrado" value={`${formatDateTime(database.created_at)} · ${database.created_by_name}`} />
            <Field label="Última alteração" value={`${formatDateTime(database.updated_at)} · ${database.updated_by_name}`} />
          </dl>
        </ItpSectionCard>
      </div>

      <ItpSectionCard title={DATABASE_FIELD_LABELS.technical_notes}>
        <p className="itp-prewrap">
          {database.technical_notes?.trim() ? database.technical_notes : "Sem observações técnicas."}
        </p>
      </ItpSectionCard>

      {canSeeServices ? (
        <ConsumersSection
          owner={{ databaseId: database.id }}
          title="Serviços que utilizam este banco"
          emptyMessage="Nenhum serviço vinculado a esta instância."
          canManage={canManage}
          ownerArchived={database.archived}
        />
      ) : null}

      <HistorySection
        queryKey={queryKeys.databaseHistory(database.id)}
        queryFn={(signal) => itPortalApi.listDatabaseHistory(database.id, signal)}
        subtitle="Últimos 50 eventos auditados desta instância, incluindo vínculos."
        ariaLabel="Histórico da instância de banco"
      />

      {modal === "edit" ? <DatabaseFormModal database={database} onClose={() => setModal(null)} /> : null}
      {modal === "archive" ? (
        <InventoryConfirmDialog
          title="Arquivar instância de banco"
          message={`Arquivar ${database.name}? O cadastro sai do inventário ativo, mas os vínculos e o histórico são preservados.`}
          confirmLabel="Arquivar"
          busyLabel="Arquivando…"
          successMessage={`${database.code} arquivada.`}
          danger
          action={() => itPortalApi.archiveDatabase(database.id, database.revision)}
          onClose={() => setModal(null)}
        />
      ) : null}
      {modal === "restore" ? (
        <InventoryConfirmDialog
          title="Restaurar instância de banco"
          message={`Restaurar ${database.name} ao inventário ativo?`}
          confirmLabel="Restaurar"
          busyLabel="Restaurando…"
          successMessage={`${database.code} restaurada.`}
          action={() => itPortalApi.restoreDatabase(database.id, database.revision)}
          onClose={() => setModal(null)}
        />
      ) : null}
    </>
  );
}
