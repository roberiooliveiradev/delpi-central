import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Clock3,
  Cog,
  RefreshCw,
  Search,
  ShieldCheck,
  SlidersHorizontal,
  X,
} from "lucide-react";
import { Fragment, useEffect, useState } from "react";

import { itPortalApi, type HostService, type HostServiceQuery } from "../../api/itPortalApi";
import { formatDateTime } from "../../app/format";
import { ItpSectionCard } from "../../app/itPortalUi";
import { toApiError } from "../../app/PortalContext";
import { LoadingBlock, QueryErrorState } from "../../app/QueryStates";
import { queryKeys } from "../../app/queryKeys";

const PAGE_SIZE = 25;

const statusLabels: Record<string, string> = {
  running: "Em execução",
  stopped: "Parado",
  paused: "Pausado",
  start_pending: "Iniciando",
  stop_pending: "Parando",
  continue_pending: "Retomando",
  pause_pending: "Pausando",
  unknown: "Desconhecido",
};

const startLabels: Record<string, string> = {
  auto: "Automático",
  manual: "Manual",
  disabled: "Desabilitado",
  boot: "Inicialização",
  system: "Sistema",
  unknown: "Desconhecido",
};

function statusTone(state: string): string {
  if (state === "running") return "running";
  if (state === "stopped") return "stopped";
  if (state === "paused" || state === "pause_pending") return "paused";
  return "transition";
}

function count(value: number | undefined): string {
  return value === undefined ? "—" : value.toLocaleString("pt-BR");
}

function ServiceRow({ service, expanded, onToggle }: {
  service: HostService;
  expanded: boolean;
  onToggle: () => void;
}) {
  const tone = statusTone(service.state);
  return (
    <Fragment>
      <tr className={"itp-scm__row" + (expanded ? " is-expanded" : "") + (!service.is_present ? " is-absent" : "")}>
        <td>
          <div className="itp-scm__service">
            <span className="itp-scm__service-icon" aria-hidden="true"><Cog size={17} strokeWidth={1.8} /></span>
            <div className="itp-scm__service-content">
              <strong className="itp-scm__service-name">{service.display_name}</strong>
              <span className="itp-scm__service-technical" title={service.name}>{service.name}</span>
            </div>
          </div>
        </td>
        <td>
          <span className={"itp-scm__status itp-scm__status--" + tone}>
            <span className="itp-scm__status-dot" aria-hidden="true" />
            {statusLabels[service.state] ?? service.state}
          </span>
        </td>
        <td>
          <span className={"itp-scm__mode" + (service.start_mode === "disabled" ? " is-disabled" : "")}>
            {startLabels[service.start_mode] ?? service.start_mode}
          </span>
        </td>
        <td>
          <span className={"itp-scm__presence" + (!service.is_present ? " is-absent" : "")}>
            <span className="itp-scm__presence-dot" aria-hidden="true" />
            {service.is_present ? "Presente" : "Não encontrado"}
          </span>
        </td>
        <td className="itp-scm__detail-cell">
          <button
            type="button"
            className="itp-scm__detail-button"
            aria-label={(expanded ? "Ocultar" : "Ver") + " detalhes de " + service.display_name}
            aria-expanded={expanded}
            onClick={onToggle}
            title="Consultar detalhes deste serviço"
          >
            <ChevronDown size={17} aria-hidden="true" />
          </button>
        </td>
      </tr>
      {expanded ? (
        <tr className="itp-scm__expanded-row">
          <td colSpan={5}>
            <div className="itp-scm__expanded-content">
              <div className="itp-scm__expanded-description">
                <span className="itp-scm__detail-label">Descrição</span>
                <p>{service.description || "Nenhuma descrição fornecida pelo Windows."}</p>
              </div>
              <div className="itp-scm__expanded-meta">
                <div>
                  <span className="itp-scm__detail-label">Nome técnico</span>
                  <code>{service.name}</code>
                </div>
                <div>
                  <span className="itp-scm__detail-label">Última observação</span>
                  <span>{formatDateTime(service.observed_at)}</span>
                </div>
              </div>
            </div>
          </td>
        </tr>
      ) : null}
    </Fragment>
  );
}

export function ServerWindowsServicesSection({ serverId }: { serverId: string }) {
  const [search, setSearch] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [state, setState] = useState("");
  const [startMode, setStartMode] = useState("");
  const [present, setPresent] = useState<"yes" | "no" | "all">("yes");
  const [page, setPage] = useState(1);
  const [expandedService, setExpandedService] = useState<string | null>(null);

  // Evita uma consulta à API a cada caractere digitado.
  useEffect(() => {
    const timer = window.setTimeout(() => setSearchTerm(search.trim()), 300);
    return () => window.clearTimeout(timer);
  }, [search]);

  const query: HostServiceQuery = {
    q: searchTerm || undefined,
    state: state || undefined,
    start_mode: startMode || undefined,
    present,
    page,
    page_size: PAGE_SIZE,
  };

  const result = useQuery({
    queryKey: queryKeys.hostServices(serverId, query),
    queryFn: ({ signal }) => itPortalApi.listHostServices(serverId, query, signal),
  });

  // A API já devolve o total de cada filtro: consultas de 1 item fornecem
  // contadores de TODO o servidor, sem usar só os 25 itens da página.
  const runningQuery: HostServiceQuery = { state: "running", present: "yes", page: 1, page_size: 1 };
  const stoppedQuery: HostServiceQuery = { state: "stopped", present: "yes", page: 1, page_size: 1 };
  const disabledQuery: HostServiceQuery = { start_mode: "disabled", present: "yes", page: 1, page_size: 1 };
  const running = useQuery({
    queryKey: queryKeys.hostServices(serverId, runningQuery),
    queryFn: ({ signal }) => itPortalApi.listHostServices(serverId, runningQuery, signal),
    staleTime: 60_000,
  });
  const stopped = useQuery({
    queryKey: queryKeys.hostServices(serverId, stoppedQuery),
    queryFn: ({ signal }) => itPortalApi.listHostServices(serverId, stoppedQuery, signal),
    staleTime: 60_000,
  });
  const disabled = useQuery({
    queryKey: queryKeys.hostServices(serverId, disabledQuery),
    queryFn: ({ signal }) => itPortalApi.listHostServices(serverId, disabledQuery, signal),
    staleTime: 60_000,
  });

  const payload = result.data;
  const totalPages = Math.max(1, Math.ceil((payload?.total ?? 0) / PAGE_SIZE));
  const first = payload && payload.total ? (page - 1) * PAGE_SIZE + 1 : 0;
  const last = payload ? Math.min(page * PAGE_SIZE, payload.total) : 0;
  const hasFilters = Boolean(search.trim() || state || startMode || present !== "yes");
  const isRefreshing = result.isFetching || running.isFetching || stopped.isFetching || disabled.isFetching;

  function resetFilters() {
    setSearch("");
    setSearchTerm("");
    setState("");
    setStartMode("");
    setPresent("yes");
    setPage(1);
    setExpandedService(null);
  }

  function refresh() {
    void result.refetch();
    void running.refetch();
    void stopped.refetch();
    void disabled.refetch();
  }

  function changePage(next: number) {
    setPage(next);
    setExpandedService(null);
  }

  return (
    <ItpSectionCard title="Inventário dos serviços Windows">
      <section className="itp-scm" aria-label="Painel de serviços Windows">
        <header className="itp-scm__heading">
          <div className="itp-scm__heading-copy">
            <p className="itp-scm__eyebrow"><Activity size={14} aria-hidden="true" /> INVENTÁRIO DO SISTEMA</p>
            <p className="itp-scm__lead">
              Uma visão organizada dos serviços coletados diretamente no Windows Server.
            </p>
            <div className="itp-scm__heading-meta">
              <span className="itp-scm__read-only"><ShieldCheck size={14} aria-hidden="true" /> Somente leitura</span>
              <span className="itp-scm__last-sync"><Clock3 size={14} aria-hidden="true" />
                {payload?.current
                  ? "Última coleta: " + formatDateTime(payload.current.observed_at)
                  : "Aguardando primeira coleta"}
              </span>
            </div>
          </div>
          <button type="button" className="itp-scm__refresh" onClick={refresh} disabled={isRefreshing}
            title="Recarregar dados da API. Não executa nova coleta no servidor.">
            <RefreshCw size={16} className={isRefreshing ? "is-spinning" : ""} aria-hidden="true" />
            Recarregar dados
          </button>
        </header>

        <div className="itp-scm__metrics" aria-label="Resumo do inventário">
          <div className="itp-scm__metric is-total">
            <span className="itp-scm__metric-label">Serviços detectados</span>
            <strong className="itp-scm__metric-value">{count(payload?.current?.service_count)}</strong>
            <span className="itp-scm__metric-hint">Na última coleta completa</span>
          </div>
          <div className="itp-scm__metric is-running">
            <span className="itp-scm__metric-label">Em execução</span>
            <strong className="itp-scm__metric-value">{count(running.data?.total)}</strong>
            <span className="itp-scm__metric-hint">Serviços atuais</span>
          </div>
          <div className="itp-scm__metric is-stopped">
            <span className="itp-scm__metric-label">Parados</span>
            <strong className="itp-scm__metric-value">{count(stopped.data?.total)}</strong>
            <span className="itp-scm__metric-hint">Serviços atuais</span>
          </div>
          <div className="itp-scm__metric is-disabled">
            <span className="itp-scm__metric-label">Desabilitados</span>
            <strong className="itp-scm__metric-value">{count(disabled.data?.total)}</strong>
            <span className="itp-scm__metric-hint">Modo de inicialização</span>
          </div>
        </div>

        <div className="itp-scm__catalog">
          <div className="itp-scm__catalog-heading">
            <div>
              <h3>Explorar serviços</h3>
              <p>Encontre rapidamente um serviço por nome, estado ou inicialização.</p>
            </div>
            <span className="itp-scm__catalog-count" role="status">
              {payload ? count(payload.total) + " resultado(s)" : "Carregando…"}
            </span>
          </div>
          <div className="itp-scm__filters">
            <label className="itp-scm__search-field">
              <span className="itp-scm__field-title">Buscar serviço</span>
              <span className="itp-scm__search-control">
                <Search size={17} aria-hidden="true" />
                <input aria-label="Pesquisar serviço Windows" type="search" value={search}
                  onChange={(event) => { setSearch(event.target.value); changePage(1); }}
                  placeholder="Nome, nome técnico ou descrição" />
                {search ? <button type="button" aria-label="Limpar pesquisa"
                  onClick={() => { setSearch(""); setSearchTerm(""); changePage(1); }}><X size={15} aria-hidden="true" /></button> : null}
              </span>
            </label>
            <label className="itp-scm__filter-field">
              <span className="itp-scm__field-title">Estado</span>
              <select aria-label="Estado do serviço" value={state}
                onChange={(event) => { setState(event.target.value); changePage(1); }}>
                <option value="">Todos os estados</option>
                <option value="running">Em execução</option>
                <option value="stopped">Parado</option>
                <option value="paused">Pausado</option>
                <option value="start_pending">Iniciando</option>
                <option value="stop_pending">Parando</option>
                <option value="unknown">Desconhecido</option>
              </select>
            </label>
            <label className="itp-scm__filter-field">
              <span className="itp-scm__field-title">Inicialização</span>
              <select aria-label="Modo de inicialização" value={startMode}
                onChange={(event) => { setStartMode(event.target.value); changePage(1); }}>
                <option value="">Todos os modos</option>
                <option value="auto">Automático</option>
                <option value="manual">Manual</option>
                <option value="disabled">Desabilitado</option>
                <option value="boot">Inicialização</option>
                <option value="system">Sistema</option>
                <option value="unknown">Desconhecido</option>
              </select>
            </label>
            <label className="itp-scm__filter-field">
              <span className="itp-scm__field-title">Presença</span>
              <select aria-label="Presença no inventário" value={present}
                onChange={(event) => { setPresent(event.target.value as "yes" | "no" | "all"); changePage(1); }}>
                <option value="yes">Atuais</option>
                <option value="no">Não encontrados</option>
                <option value="all">Todos</option>
              </select>
            </label>
          </div>
          {hasFilters ? (
            <button type="button" className="itp-scm__clear" onClick={resetFilters}>
              <SlidersHorizontal size={14} aria-hidden="true" /> Limpar filtros
            </button>
          ) : null}
          {result.isPending ? <LoadingBlock title="Carregando serviços Windows" /> : null}
          {result.error ? <QueryErrorState error={toApiError(result.error)} onRetry={refresh} /> : null}

          {payload ? (
            <>
              <div className="itp-scm__results-header">
                <span>{payload.current
                  ? "Inventário sincronizado · " + count(payload.current.service_count) + " serviços observados"
                  : "Nenhuma coleta completa recebida para este servidor."}</span>
                <span>{first}–{last} de {count(payload.total)}</span>
              </div>
              <div className="itp-scm__table-scroll" tabIndex={0} role="region" aria-label="Relação de serviços Windows">
                <table className="itp-scm__table" aria-label="Inventário de serviços do Windows">
                  <thead>
                    <tr>
                      <th scope="col">Serviço</th>
                      <th scope="col">Estado</th>
                      <th scope="col">Inicialização</th>
                      <th scope="col">Presença</th>
                      <th scope="col"><span className="itp-scm__sr-only">Detalhes</span></th>
                    </tr>
                  </thead>
                  <tbody>
                    {payload.items.map((svc) => (
                      <ServiceRow key={svc.name} service={svc}
                        expanded={expandedService === svc.name}
                        onToggle={() => setExpandedService((current) => current === svc.name ? null : svc.name)} />
                    ))}
                    {payload.items.length === 0 ? (
                      <tr><td colSpan={5}>
                        <div className="itp-scm__empty">
                          <Search size={27} strokeWidth={1.5} aria-hidden="true" />
                          <strong>Nenhum serviço encontrado</strong>
                          <p>{payload.current
                            ? "Nenhum serviço corresponde aos filtros escolhidos."
                            : "Aguardando o primeiro inventário completo do servidor."}</p>
                          {hasFilters ? <button type="button" onClick={resetFilters}>Limpar filtros</button> : null}
                        </div>
                      </td></tr>
                    ) : null}
                  </tbody>
                </table>
              </div>
              <footer className="itp-scm__pagination">
                <span>Exibindo {first} a {last} de {count(payload.total)} serviços</span>
                <div className="itp-scm__page-controls">
                  <button type="button" disabled={page <= 1} aria-label="Página anterior"
                    onClick={() => changePage(page - 1)}><ChevronLeft size={16} aria-hidden="true" /></button>
                  <span aria-live="polite">Página <strong>{page}</strong> de {totalPages}</span>
                  <button type="button" disabled={page >= totalPages} aria-label="Próxima página"
                    onClick={() => changePage(page + 1)}><ChevronRight size={16} aria-hidden="true" /></button>
                </div>
              </footer>
            </>
          ) : null}
        </div>
        <p className="itp-scm__security-note"><ShieldCheck size={15} aria-hidden="true" />
          Consulta de inventário apenas. Nenhum comando é enviado aos serviços do Windows.
        </p>
      </section>
    </ItpSectionCard>
  );
}
