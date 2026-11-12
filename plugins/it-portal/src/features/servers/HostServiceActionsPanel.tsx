import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, Play, RotateCw, Square, X } from "lucide-react";
import { useEffect, useState } from "react";

import { itPortalApi, type HostService, type HostServiceAction } from "../../api/itPortalApi";
import { toApiError } from "../../app/PortalContext";
import { queryKeys } from "../../app/queryKeys";

type ControlAction = "start" | "stop" | "restart";
const labels: Record<ControlAction, string> = {
  start: "Iniciar", stop: "Interromper", restart: "Reiniciar",
};
const errors: Record<string, string> = {
  access_denied: "A conta do agente não possui permissão para esta ação.",
  service_not_found: "O serviço não foi encontrado no Windows.",
  not_allowed: "O serviço não está autorizado para controle remoto.",
  precondition_failed: "O estado do serviço mudou antes da execução.",
  dependent_services: "Existem serviços dependentes em execução. Nenhum deles será interrompido automaticamente.",
  timeout: "O serviço não confirmou a mudança dentro do limite.",
  execution_failed: "O Windows não conseguiu concluir a operação.",
  disabled: "O Windows não permite iniciar um serviço desabilitado.",
};

export function HostServiceActionsPanel({
  serverId, service, canControl,
}: {
  serverId: string;
  service: HostService;
  canControl: boolean;
}) {
  const client = useQueryClient();
  const [selected, setSelected] = useState<ControlAction | null>(null);
  const [actionId, setActionId] = useState<string | null>(null);
  const [failure, setFailure] = useState<string | null>(null);

  const actionQuery = useQuery({
    queryKey: ["it-portal", "host-service-action", serverId, actionId],
    queryFn: ({ signal }) => itPortalApi.getHostServiceAction(serverId, actionId!, signal),
    enabled: Boolean(actionId),
    refetchInterval: (query) => {
      const value = query.state.data?.status;
      return value === "queued" || value === "running" || !value ? 1_000 : false;
    },
    retry: 1,
  });
  const run = useMutation({
    mutationFn: (action: ControlAction) =>
      itPortalApi.requestHostServiceAction(serverId, service.service_key, action, crypto.randomUUID()),
    onSuccess: (job) => {
      setSelected(null);
      setFailure(null);
      setActionId(job.id);
    },
    onError: (error) => {
      setFailure(toApiError(error).message);
    },
  });
  const job: HostServiceAction | undefined = actionQuery.data;
  const busy = run.isPending || job?.status === "queued" || job?.status === "running";
  const finalState = job?.status;

  useEffect(() => {
    if (finalState === "succeeded") {
      void client.invalidateQueries({ queryKey: ["it-portal", "servers", serverId, "windows-host-services"] });
      void client.invalidateQueries({ queryKey: queryKeys.history(serverId) });
    }
  }, [client, serverId, finalState]);

  // O backend tambem valida a identidade, a allowlist e o estado atual.
  if (!canControl || !service.control_allowed) return null;
  const actions: { name: ControlAction; allowed: boolean; icon: typeof Play }[] = [
    { name: "start", allowed: service.state === "stopped" && service.start_mode !== "disabled", icon: Play },
    { name: "stop", allowed: service.state === "running" && service.can_stop, icon: Square },
    { name: "restart", allowed: service.state === "running" && service.can_stop, icon: RotateCw },
  ];

  return (
    <section className="itp-scm__control" aria-label={"Ações remotas de " + service.display_name}>
      <div className="itp-scm__control-heading">
        <div>
          <strong>Controle remoto</strong>
          <p>O resultado será confirmado diretamente pelo servidor Windows.</p>
        </div>
        <span className="itp-scm__control-live"><span aria-hidden="true" /> Canal seguro</span>
      </div>
      <div className="itp-scm__control-actions">
        {actions.map(({ name, allowed, icon: Icon }) => (
          <button key={name} type="button"
            className={"itp-scm__control-button" + (name === "stop" ? " is-stop" : "")}
            disabled={!allowed || busy || Boolean(selected)}
            onClick={() => { setSelected(name); setFailure(null); setActionId(null); }}>
            <Icon size={15} strokeWidth={1.8} aria-hidden="true" />
            {labels[name]}
          </button>
        ))}
      </div>
      {selected ? (
        <div className="itp-scm__confirm" role="group" aria-label={"Confirmar " + labels[selected]}>
          <AlertTriangle size={19} strokeWidth={1.7} aria-hidden="true" />
          <div>
            <strong>{labels[selected]} {service.display_name}?</strong>
            <p>{selected === "start"
              ? "A solicitação será enviada imediatamente ao servidor."
              : "Esta ação pode interromper sistemas e usuários conectados. Confirme somente se estiver autorizado."}</p>
          </div>
          <div className="itp-scm__confirm-buttons">
            <button type="button" onClick={() => setSelected(null)} disabled={run.isPending}>Cancelar</button>
            <button type="button" className="is-confirm" disabled={run.isPending}
              onClick={() => run.mutate(selected)}>Confirmar ação</button>
          </div>
        </div>
      ) : null}
      {failure ? (
        <p className="itp-scm__control-feedback is-error" role="alert">
          {failure} <button aria-label="Dispensar mensagem" type="button" onClick={() => setFailure(null)}><X size={14} /></button>
        </p>
      ) : null}
      {job ? (
        <div className={"itp-scm__control-feedback is-" + job.status} role="status">
          {job.status === "queued" ? "Solicitação enviada. Aguardando o agente Windows..." :
            job.status === "running" ? "O Windows está executando a ação..." :
            job.status === "succeeded" ? "Concluído e confirmado pelo Windows. Estado: " + (job.state_after === "running" ? "Em execução" : "Parado") :
            job.status === "timeout" ? "Não foi possível confirmar o resultado. Verifique no servidor antes de tentar novamente." :
            "Não foi possível executar: " + (errors[job.error_code ?? ""] ?? "Consulte o histórico para mais informações.")}
        </div>
      ) : null}
      {actionId && actionQuery.isError ? (
        <p className="itp-scm__control-feedback is-error" role="alert">
          Comunicação indisponível. Confira o estado no Windows antes de reenviar.
          <button type="button" onClick={() => void actionQuery.refetch()}>Verificar novamente</button>
        </p>
      ) : null}
    </section>
  );
}
