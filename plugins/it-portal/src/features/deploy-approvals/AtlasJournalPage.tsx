import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { itPortalApi, type AtlasDeployEnvironment, type AtlasJournalEntry, type AtlasJournalQuery } from "../../api/itPortalApi";
import { ItpPageHero } from "../../app/itPortalUi";
import { toApiError } from "../../app/PortalContext";
import { LoadingBlock, QueryErrorState } from "../../app/QueryStates";
import { queryKeys } from "../../app/queryKeys";
import "./AtlasJournalPage.css";

const PAGE_SIZE = 10;
const STATUS: Record<string, string> = {
  pending_approval: "Aguardando análise",
  approved: "Aprovada",
  revoked: "Revogada",
  expired: "Expirada",
  executing: "Executando",
  verified: "Verificada",
  failed_needs_operator: "Requer operador",
  rolled_back: "Revertida",
};

function dateLabel(value: string): string {
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "Data indisponível";
  return new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" }).format(d);
}

function stateLabel(value: AtlasJournalEntry): string {
  return value.expired && value.status === "pending_approval"
    ? "Prazo expirado"
    : (STATUS[value.status] ?? "Estado desconhecido");
}

function Identifier({ name, value }: { name: string; value: string | null }) {
  return <div className="itp-atlas-journal__identity"><dt>{name}</dt><dd>{value ?? "Não informado"}</dd></div>;
}

export function AtlasJournalPage() {
  const [environment, setEnvironment] = useState<"" | AtlasDeployEnvironment>("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<string | null>(null);
  const filters: AtlasJournalQuery = {
    environment: environment || undefined, status: status || undefined,
    page, page_size: PAGE_SIZE,
  };
  const list = useQuery({
    queryKey: queryKeys.atlasDeployments(filters),
    queryFn: ({ signal }) => itPortalApi.listAtlasDeployments(filters, signal),
    retry: false,
  });
  const detail = useQuery({
    queryKey: queryKeys.atlasDeployment(selected ?? ""),
    queryFn: ({ signal }) => itPortalApi.getAtlasDeployment(selected!, signal),
    enabled: Boolean(selected),
    retry: false,
  });
  const total = list.data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const rows = list.data?.items ?? [];

  return (
    <>
      <ItpPageHero
        variant="immersive"
        aria-label="Implantações ATLAS"
        eyebrow="Governança de mudanças"
        title="Implantações ATLAS"
        description="Consulte propostas registradas, versões assinadas e histórico de decisões. Esta área não executa nem aprova implantações."
      />
      <section className="itp-atlas-journal" aria-label="Solicitações de implantação">
        <div className="itp-atlas-journal__notice" role="status">
          <strong>Consulta somente leitura.</strong> O ATLAS ainda não executa implantações.
          O deploy manual pelo terminal permanece disponível aos desenvolvedores autorizados.
        </div>
        <div className="itp-atlas-journal__toolbar">
          <label>
            Ambiente
            <select value={environment} onChange={(event) => {
              setEnvironment(event.target.value as "" | AtlasDeployEnvironment);
              setPage(1); setSelected(null);
            }}>
              <option value="">Todos</option>
              <option value="prod">Produção</option>
              <option value="hml">Homologação</option>
            </select>
          </label>
          <label>
            Situação
            <select value={status} onChange={(event) => {
              setStatus(event.target.value);
              setPage(1); setSelected(null);
            }}>
              <option value="">Todas</option>
              {Object.entries(STATUS).map(([key, label]) => <option key={key} value={key}>{label}</option>)}
            </select>
          </label>
          <span className="itp-atlas-journal__count" aria-live="polite">
            {list.isPending ? "Carregando registros" : total + " solicitação(ões)"}
          </span>
        </div>
        {list.isPending ? <LoadingBlock title="Consultando journal ATLAS" /> :
          list.error ? <QueryErrorState error={toApiError(list.error)} onRetry={() => void list.refetch()} /> :
          rows.length === 0 ? (
            <div className="itp-atlas-journal__empty">
              <strong>Nenhuma solicitação encontrada.</strong>
              <p>A consulta não cria implantações nem gera propostas fictícias.</p>
            </div>
          ) : (
            <div className="itp-atlas-journal__table-wrap">
              <table className="itp-atlas-journal__table">
                <thead>
                  <tr>
                    <th scope="col">Serviço / versão</th>
                    <th scope="col">Ambiente</th>
                    <th scope="col">Situação</th>
                    <th scope="col">Solicitada em</th>
                    <th scope="col">Consulta</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((item) => (
                    <tr key={item.id}>
                      <td>
                        <strong>Public Hub</strong>
                        <code title={item.target_commit_sha}>{item.target_commit_sha.slice(0, 12)}</code>
                      </td>
                      <td>{item.environment === "prod" ? "Produção" : "Homologação"}</td>
                      <td><span className="itp-atlas-journal__status">{stateLabel(item)}</span></td>
                      <td>{dateLabel(item.created_at)}</td>
                      <td>
                        <button type="button" className="itp-atlas-journal__detail-button"
                          aria-label={"Ver detalhes da proposta " + item.id}
                          onClick={() => setSelected(item.id)}>Ver detalhes</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        {!list.isPending && !list.error && total > PAGE_SIZE ? (
          <div className="itp-atlas-journal__pager">
            <button type="button" disabled={page <= 1}
              onClick={() => { setPage((p) => p - 1); setSelected(null); }}>Anterior</button>
            <span>Página {page} de {totalPages}</span>
            <button type="button" disabled={page >= totalPages}
              onClick={() => { setPage((p) => p + 1); setSelected(null); }}>Próxima</button>
          </div>
        ) : null}
      </section>
      {selected ? (
        <section className="itp-atlas-journal itp-atlas-journal__detail" aria-label="Detalhes da proposta">
          <div className="itp-atlas-journal__detail-header">
            <div>
              <span className="itp-atlas-journal__eyebrow">Auditoria de implantação</span>
              <h2>Identidade da versão</h2>
            </div>
            <button type="button" onClick={() => setSelected(null)}>Fechar detalhes</button>
          </div>
          {detail.isPending ? <LoadingBlock title="Carregando evidências da proposta" /> :
            detail.error ? <QueryErrorState error={toApiError(detail.error)} onRetry={() => void detail.refetch()} /> :
            detail.data ? (
              <>
                <div className="itp-atlas-journal__summary">
                  <span>{detail.data.environment === "prod" ? "Produção" : "Homologação"}</span>
                  <strong>{stateLabel(detail.data)}</strong>
                  <span>Válida até {dateLabel(detail.data.expires_at)}</span>
                </div>
                <dl className="itp-atlas-journal__identities">
                  <Identifier name="Solicitação" value={detail.data.id} />
                  <Identifier name="Solicitante (Core)" value={detail.data.requester_subject} />
                  <Identifier name="Commit alvo" value={detail.data.target_commit_sha} />
                  <Identifier name="Commit anterior" value={detail.data.base_commit_sha} />
                  <Identifier name="Manifesto OCI assinado" value={detail.data.manifest_digest} />
                  <Identifier name="Imagem anterior" value={detail.data.previous_image_id} />
                  <Identifier name="Imagem solicitada" value={detail.data.target_image_id} />
                  <Identifier name="Identificador imutável da proposta" value={detail.data.binding_sha256} />
                </dl>
                <h3>Histórico registrado</h3>
                {detail.data.events.length === 0 ? <p>Nenhum evento registrado.</p> : (
                  <ol className="itp-atlas-journal__events">
                    {detail.data.events.map((event) => (
                      <li key={event.sequence}>
                        <strong>{STATUS[event.event_type] ?? event.event_type}</strong>
                        <span>{dateLabel(event.occurred_at)} · responsável {event.actor_subject ?? "sistema"}</span>
                      </li>
                    ))}
                  </ol>
                )}
                <p className="itp-atlas-journal__read-only-footer">
                  A consulta não representa aprovação, validação atual do host ou autorização de deploy.
                </p>
              </>
            ) : null}
        </section>
      ) : null}
    </>
  );
}
