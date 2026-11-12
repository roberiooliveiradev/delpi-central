import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { itPortalApi, type HostServiceQuery } from "../../api/itPortalApi";
import { formatDateTime } from "../../app/format";
import { ItpSectionCard } from "../../app/itPortalUi";
import { toApiError } from "../../app/PortalContext";
import { LoadingBlock, QueryErrorState } from "../../app/QueryStates";
import { queryKeys } from "../../app/queryKeys";

const statusLabels: Record<string, string> = {
  running: "Em execução", stopped: "Parado", paused: "Pausado",
  start_pending: "Iniciando", stop_pending: "Parando", unknown: "Desconhecido",
};
const startLabels: Record<string, string> = {
  auto: "Automático", manual: "Manual", disabled: "Desabilitado",
  boot: "Inicialização", system: "Sistema", unknown: "Desconhecido",
};

export function ServerWindowsServicesSection({ serverId }: { serverId: string }) {
  const [q, setQ] = useState("");
  const [state, setState] = useState("");
  const [startMode, setStartMode] = useState("");
  const [present, setPresent] = useState<"yes" | "no" | "all">("yes");
  const [page, setPage] = useState(1);
  const query: HostServiceQuery = {
    q: q.trim() || undefined, state: state || undefined,
    start_mode: startMode || undefined, present, page, page_size: 25,
  };
  const result = useQuery({
    queryKey: queryKeys.hostServices(serverId, query),
    queryFn: ({ signal }) => itPortalApi.listHostServices(serverId, query, signal),
  });
  const payload = result.data;
  const totalPages = payload ? Math.max(1, Math.ceil(payload.total / 25)) : 1;
  return (
    <ItpSectionCard title="Inventário dos serviços Windows">
      <p className="itp-muted">Consulta automática e somente leitura. Nenhuma ação de iniciar, parar ou reiniciar está disponível nesta etapa.</p>
      <div className="itp-row-actions" style={{ flexWrap: "wrap", gap: 12, marginTop: 12, marginBottom: 12 }}>
        <label>Pesquisar serviço
          <input aria-label="Pesquisar serviço Windows" type="search" value={q}
            onChange={(event) => { setQ(event.target.value); setPage(1); }}
            placeholder="Nome ou descrição curta" />
        </label>
        <label>Estado
          <select aria-label="Estado do serviço" value={state}
            onChange={(event) => { setState(event.target.value); setPage(1); }}>
            <option value="">Todos</option>
            <option value="running">Em execução</option>
            <option value="stopped">Parado</option>
            <option value="paused">Pausado</option>
          </select>
        </label>
        <label>Inicialização
          <select aria-label="Modo de inicialização" value={startMode}
            onChange={(event) => { setStartMode(event.target.value); setPage(1); }}>
            <option value="">Todos</option>
            <option value="auto">Automático</option>
            <option value="manual">Manual</option>
            <option value="disabled">Desabilitado</option>
          </select>
        </label>
        <label>Presença
          <select aria-label="Presença no inventário" value={present}
            onChange={(event) => { setPresent(event.target.value as "yes" | "no" | "all"); setPage(1); }}>
            <option value="yes">Atuais</option>
            <option value="no">Não encontrados</option>
            <option value="all">Todos</option>
          </select>
        </label>
      </div>
      {result.isPending ? <LoadingBlock title="Carregando serviços Windows" /> : null}
      {result.error ? <QueryErrorState error={toApiError(result.error)} onRetry={() => void result.refetch()} /> : null}
      {payload ? (
        <>
          <p className="itp-muted" role="status">
            {payload.current
              ? `Última coleta: ${formatDateTime(payload.current.observed_at)} · ${payload.current.service_count} serviços observados.`
              : "Nenhuma coleta completa recebida para este servidor."}
            {" "}Resultados: {payload.total}.
          </p>
          <div style={{ overflowX: "auto", marginTop: 12 }}>
            <table className="itp-table" aria-label="Inventário de serviços do Windows">
              <thead><tr><th>Serviço</th><th>Nome técnico</th><th>Estado</th><th>Inicialização</th><th>Presença</th></tr></thead>
              <tbody>
                {payload.items.map((svc) => (
                  <tr key={svc.name}>
                    <td><strong>{svc.display_name}</strong>{svc.description ? <p className="itp-muted">{svc.description}</p> : null}</td>
                    <td>{svc.name}</td>
                    <td>{statusLabels[svc.state] ?? svc.state}</td>
                    <td>{startLabels[svc.start_mode] ?? svc.start_mode}</td>
                    <td>{svc.is_present ? "Presente" : "Não encontrado"}</td>
                  </tr>
                ))}
                {payload.items.length === 0 ? <tr><td colSpan={5}>Nenhum serviço encontrado para os filtros escolhidos.</td></tr> : null}
              </tbody>
            </table>
          </div>
          <div className="itp-row-actions" style={{ gap: 12, marginTop: 12 }}>
            <button type="button" disabled={page <= 1} onClick={() => setPage((n) => n - 1)}>Anterior</button>
            <span aria-live="polite">Página {page} de {totalPages}</span>
            <button type="button" disabled={page >= totalPages} onClick={() => setPage((n) => n + 1)}>Próxima</button>
          </div>
        </>
      ) : null}
    </ItpSectionCard>
  );
}
