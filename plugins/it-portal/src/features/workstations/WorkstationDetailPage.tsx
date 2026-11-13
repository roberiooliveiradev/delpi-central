import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Archive, ArchiveRestore, Pencil } from "lucide-react";
import { useState } from "react";

import { itPortalApi, type Workstation } from "../../api/itPortalApi";
import { AdministrativeStatusBadge, ArchivedBadge } from "../../app/badges";
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
import {
  UNIT_LABELS,
  WORKSTATION_FIELD_LABELS,
  WORKSTATION_KIND_LABELS,
} from "../../content/labels";
import { HistorySection } from "../history/HistorySection";
import { DetailField } from "../inventory/InventoryDialogs";
import { WorkstationFormModal } from "./WorkstationFormModal";
import { WorkstationOwnerStatus } from "./WorkstationOwnerStatus";
import { WorkstationSnapshotPanel } from "./WorkstationSnapshotPanel";

type ActionDialog = "archive" | "restore";

function WorkstationStateDialog({
  workstation,
  action,
  onClose,
}: {
  workstation: Workstation;
  action: ActionDialog;
  onClose: () => void;
}) {
  const queryClient = useQueryClient();
  const { notifySuccess, notifyError } = usePortal();
  const archiving = action === "archive";
  const mutation = useMutation({
    mutationFn: () =>
      archiving
        ? itPortalApi.archiveWorkstation(workstation.id, workstation.revision)
        : itPortalApi.restoreWorkstation(workstation.id, workstation.revision),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.workstations });
      notifySuccess(archiving ? "Computador arquivado." : "Computador restaurado.");
      onClose();
    },
    onError: (error) => notifyError(error),
  });

  return (
    <ItpDialog
      open
      title={archiving ? "Arquivar computador" : "Restaurar computador"}
      onClose={() => { if (!mutation.isPending) onClose(); }}
    >
      <ItpConfirmPanel
        classNames={itpConfirmClassNames}
        message={
          archiving
            ? `Arquivar ${workstation.name}? O registro deixará o inventário ativo, mas seu histórico será preservado.`
            : `Restaurar ${workstation.name} ao inventário ativo? Se já existir outra máquina ativa com o mesmo hostname nesta unidade, a operação será recusada.`
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

export function WorkstationDetailPage({ workstationId }: { workstationId: string }) {
  const { basePath, capabilities } = usePortal();
  const [modal, setModal] = useState<"edit" | ActionDialog | null>(null);
  const workstationQuery = useQuery({
    queryKey: queryKeys.workstation(workstationId),
    queryFn: ({ signal }) => itPortalApi.getWorkstation(workstationId, signal),
  });

  const listHref = buildPath(basePath, "workstations");
  const pagePath = (current: string) => (
    <ItpPagePath
      back={{ label: "Computadores", href: listHref, onNavigate: spaNavigate(listHref) }}
      current={current}
    />
  );

  if (workstationQuery.isPending) {
    return (
      <>
        {pagePath("Computador")}
        <LoadingBlock title="Carregando computador" />
      </>
    );
  }
  if (workstationQuery.error || !workstationQuery.data) {
    return (
      <>
        {pagePath("Computador")}
        <QueryErrorState
          error={toApiError(workstationQuery.error)}
          onRetry={() => void workstationQuery.refetch()}
        />
      </>
    );
  }

  const workstation = workstationQuery.data;
  const canManage = capabilities?.can_manage_computers === true;

  return (
    <>
      {pagePath(workstation.name)}
      <ItpPageHero
        variant="immersive"
        aria-label={`Computador ${workstation.name}`}
        eyebrow={workstation.code}
        title={workstation.name}
        description={workstation.hostname}
        badge={
          <span className="itp-badge-group">
            {workstation.archived
              ? <ArchivedBadge />
              : <AdministrativeStatusBadge value={workstation.administrative_status} />}
          </span>
        }
        actions={
          canManage ? (
            workstation.archived ? (
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
      {workstation.archived ? (
        <ItpStateBanner>
          <p className="itp-state-text">
            Computador arquivado em {formatDateTime(workstation.archived_at)} por {orDash(workstation.archived_by_name)}.
            O cadastro está somente para consulta até ser restaurado.
          </p>
        </ItpStateBanner>
      ) : null}

      <div className="itp-detail-grid">
        <ItpSectionCard title="Identificação">
          <dl className="itp-field-list">
            <DetailField label="Código" value={<span className="itp-code">{workstation.code}</span>} />
            <DetailField label={WORKSTATION_FIELD_LABELS.hostname} value={workstation.hostname} />
            <DetailField label={WORKSTATION_FIELD_LABELS.ip_address} value={orDash(workstation.ip_address)} />
            <DetailField label={WORKSTATION_FIELD_LABELS.device_kind} value={WORKSTATION_KIND_LABELS[workstation.device_kind]} />
            <DetailField label={WORKSTATION_FIELD_LABELS.unit_code} value={UNIT_LABELS[workstation.unit_code] ?? workstation.unit_code} />
          </dl>
        </ItpSectionCard>
        <ItpSectionCard title="Localização e operação">
          <dl className="itp-field-list">
            <DetailField label={WORKSTATION_FIELD_LABELS.department} value={orDash(workstation.department)} />
            <DetailField label={WORKSTATION_FIELD_LABELS.location} value={orDash(workstation.location)} />
            <DetailField label={WORKSTATION_FIELD_LABELS.responsible} value={<WorkstationOwnerStatus userId={workstation.responsible_user_id} snapshot={workstation.responsible} />} />
            <DetailField label={WORKSTATION_FIELD_LABELS.operating_system} value={orDash(workstation.operating_system)} />
            <DetailField
              label={WORKSTATION_FIELD_LABELS.administrative_status}
              value={<AdministrativeStatusBadge value={workstation.administrative_status} />}
            />
          </dl>
        </ItpSectionCard>
        <ItpSectionCard title="Registro e responsabilidade">
          <dl className="itp-field-list">
            <DetailField label="Cadastrado em" value={formatDateTime(workstation.created_at)} />
            <DetailField label="Cadastrado por" value={workstation.created_by_name} />
            <DetailField label="Última alteração" value={formatDateTime(workstation.updated_at)} />
            <DetailField label="Alterado por" value={workstation.updated_by_name} />
            <DetailField label="Versão do cadastro" value={workstation.revision} />
          </dl>
        </ItpSectionCard>
      </div>

      <ItpSectionCard title="Observações do cadastro">
        <p className="itp-prewrap">{workstation.description?.trim() || "Nenhuma observação registrada."}</p>
      </ItpSectionCard>

      <WorkstationSnapshotPanel workstationId={workstation.id} />

      <ItpSectionCard
        title="Suporte remoto"
        subtitle="Etapa futura do Delpi Remote."
      >
        <p className="itp-muted">
          A coleta automática exige ativação individual e validação do agente. O acesso remoto
          ainda não foi implementado; não existe controle de teclado, mouse ou arquivos nesta etapa.
        </p>
      </ItpSectionCard>

      <HistorySection
        queryKey={queryKeys.workstationHistory(workstation.id)}
        queryFn={(signal) => itPortalApi.listWorkstationHistory(workstation.id, signal)}
        subtitle="Últimos 50 eventos de cadastro deste computador."
        ariaLabel="Histórico do computador"
      />

      {modal === "edit" ? (
        <WorkstationFormModal
          workstation={workstation}
          onClose={() => setModal(null)}
        />
      ) : null}
      {modal === "archive" || modal === "restore" ? (
        <WorkstationStateDialog
          workstation={workstation}
          action={modal}
          onClose={() => setModal(null)}
        />
      ) : null}
    </>
  );
}
