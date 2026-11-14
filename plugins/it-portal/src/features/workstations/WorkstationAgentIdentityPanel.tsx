import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ShieldCheck, ShieldPlus, ShieldX } from "lucide-react";
import { useState } from "react";

import { itPortalApi } from "../../api/itPortalApi";
import { formatDateTime } from "../../app/format";
import { ItpActionButton, ItpConfirmPanel, ItpDialog, ItpSectionCard, itpConfirmClassNames } from "../../app/itPortalUi";
import { usePortal } from "../../app/PortalContext";
import { queryKeys } from "../../app/queryKeys";
import { DetailField } from "../inventory/InventoryDialogs";

const LABEL: Record<string, string> = {
  not_prepared: "Ainda não preparada",
  preparing: "Preparação em andamento",
  prepared: "Preparada, aguardando ativação",
  failed: "Revisão técnica necessária",
  revoked: "Revogada",
};

/** Keycloak: somente client DESABILITADO, nunca o segredo no navegador. */
export function WorkstationAgentIdentityPanel({
  workstationId, canManage, archived,
}: {
  workstationId: string; canManage: boolean; archived: boolean;
}) {
  const { notifySuccess, notifyError } = usePortal();
  const queryClient = useQueryClient();
  const [confirm, setConfirm] = useState(false);
  const [confirmRevoke, setConfirmRevoke] = useState(false);
  const identity = useQuery({
    queryKey: queryKeys.workstationAgentIdentity(workstationId),
    queryFn: ({ signal }) => itPortalApi.getWorkstationAgentIdentity(workstationId, signal),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
  const mutation = useMutation({
    mutationFn: () => itPortalApi.prepareWorkstationAgentIdentity(workstationId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.workstationAgentIdentity(workstationId) });
      setConfirm(false);
      notifySuccess("Identidade criada desabilitada no Keycloak. Ativação ainda pendente.");
    },
    onError: (error) => notifyError(error),
  });
  const revokeMutation = useMutation({
    mutationFn: () => itPortalApi.revokeWorkstationAgentIdentity(workstationId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.workstationAgentIdentity(workstationId) });
      setConfirmRevoke(false);
      notifySuccess("Identidade revogada. Vinculo de inventario bloqueado e Client desabilitado no Keycloak.");
    },
    onError: (error) => {
      setConfirmRevoke(false);
      notifyError(error);
    },
  });
  const current = identity.data;

  return (
    <ItpSectionCard
      title="Identidade do agente"
      subtitle="Preparação individual no Keycloak, sem ativar a coleta ou o acesso remoto."
    >
      {identity.isPending ? <p className="itp-muted">Consultando identidade…</p> : null}
      {identity.isError ? <p role="alert">Não foi possível consultar a identidade do computador.</p> : null}
      {current ? (
        <>
          <dl className="itp-field-list">
            <DetailField label="Estado" value={LABEL[current.state] ?? "Indisponível"} />
            {current.client_id ? (
              <DetailField label="Client ID" value={<span className="itp-code">{current.client_id}</span>} />
            ) : null}
            {current.prepared_at ? <DetailField label="Preparado em" value={formatDateTime(current.prepared_at)} /> : null}
            <DetailField label="Credencial entregue" value="Não" />
            <DetailField label="Coleta automática" value={current.collector_enabled ? "Autorizada em piloto" : "Desabilitada"} />
            {current.revocation_status === "pending" || current.revocation_status === "failed" ? (
              <DetailField label="Revogação" value="Pendente de revisão técnica no Keycloak" />
            ) : null}
          </dl>
          {canManage && current.can_prepare && !archived ? (
            <ItpActionButton onClick={() => setConfirm(true)}>
              <ShieldPlus size={16} strokeWidth={1.75} aria-hidden="true" /> Preparar identidade
            </ItpActionButton>
          ) : (
            <p className="itp-muted">
              O provisionamento automático ainda depende de homologação ou revisão da TI.
            </p>
          )}
          {canManage && current.can_revoke ? (
            <ItpActionButton onClick={() => setConfirmRevoke(true)}>
              <ShieldX size={16} strokeWidth={1.75} aria-hidden="true" /> Revogar identidade
            </ItpActionButton>
          ) : null}
          <p className="itp-muted">
            <ShieldCheck size={14} strokeWidth={1.75} aria-hidden="true" />{" "}
            Esta identidade não concede controle remoto nem distribui senhas pelo Portal.
          </p>
        </>
      ) : null}
      {confirmRevoke && current?.can_revoke ? (
        <ItpDialog
          open
          title="Revogar identidade do computador"
          onClose={() => { if (!revokeMutation.isPending) setConfirmRevoke(false); }}
        >
          <ItpConfirmPanel
            classNames={itpConfirmClassNames}
            message="Revogar o vinculo do inventario e desabilitar este Client no Keycloak? Esta acao sera auditada e interrompera novas coletas no modo por banco."
            confirmLabel="Revogar identidade"
            cancelLabel="Cancelar"
            confirmBusy={revokeMutation.isPending}
            confirmBusyLabel="Revogando…"
            onConfirm={() => revokeMutation.mutate()}
            onCancel={() => setConfirmRevoke(false)}
          />
        </ItpDialog>
      ) : null}
      {confirm && current?.can_prepare ? (
        <ItpDialog
          open
          title="Preparar identidade do computador"
          onClose={() => { if (!mutation.isPending) setConfirm(false); }}
        >
          <ItpConfirmPanel
            classNames={itpConfirmClassNames}
            message="Criar um Client individual e DESABILITADO no Keycloak? Nenhum segredo será exibido ou enviado ao navegador. Esta ação será auditada."
            confirmLabel="Preparar identidade"
            cancelLabel="Cancelar"
            confirmBusy={mutation.isPending}
            confirmBusyLabel="Preparando…"
            onConfirm={() => mutation.mutate()}
            onCancel={() => setConfirm(false)}
          />
        </ItpDialog>
      ) : null}
    </ItpSectionCard>
  );
}
