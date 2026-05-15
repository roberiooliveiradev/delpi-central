import type { AdminLlmStatus } from "../../../data/api/adminTypes";

type AdminToolsTabProps = {
  llmStatus: AdminLlmStatus | null;
};

export function AdminToolsTab({ llmStatus }: AdminToolsTabProps) {
  return (
    <section className="mdc-admin-grid">
      <article className="mdc-admin-card">
        <h2>Provider LLM</h2>

        {llmStatus ? (
          <dl className="mdc-admin-kv">
            <div>
              <dt>Provider</dt>
              <dd>{llmStatus.provider}</dd>
            </div>
            <div>
              <dt>Modelo</dt>
              <dd>{llmStatus.model}</dd>
            </div>
            <div>
              <dt>Temperatura</dt>
              <dd>{llmStatus.temperature}</dd>
            </div>
            <div>
              <dt>Máx. tokens</dt>
              <dd>{llmStatus.maxTokens}</dd>
            </div>
          </dl>
        ) : (
          <p className="mdc-chat-muted">Carregando provider...</p>
        )}
      </article>

      <article className="mdc-admin-card">
        <h2>Ferramentas e actions</h2>
        <p className="mdc-chat-muted">
          Próxima etapa: listar providers OpenAPI, actions disponíveis e status de uso nas últimas 24h.
        </p>
      </article>
    </section>
  );
}
