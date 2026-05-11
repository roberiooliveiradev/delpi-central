import { useState } from "react";

import { useChatAdmin } from "../../state/hooks/useChatAdmin";

type ChatAdminPageProps = {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
  onBack: () => void;
};

export function ChatAdminPage({ getAccessToken, onBack }: ChatAdminPageProps) {
  const {
    llmStatus,
    documents,
    auditLogs,
    isLoading,
    isMutating,
    successMessage,
    error,
    loadAdminData,
    createDocument,
    deactivateDocument,
    reactivateDocument,
  } = useChatAdmin({ getAccessToken });

  const [title, setTitle] = useState("");
  const [sourceType, setSourceType] = useState("manual");
  const [sourceRef, setSourceRef] = useState("");
  const [content, setContent] = useState("");

  const canSubmitDocument =
    title.trim().length > 0 && sourceType.trim().length > 0 && content.trim().length > 0;

  async function handleCreateDocument() {
    if (!canSubmitDocument || isMutating) {
      return;
    }

    await createDocument({
      title: title.trim(),
      sourceType: sourceType.trim(),
      sourceRef: sourceRef.trim() || undefined,
      content: content.trim(),
    });

    setTitle("");
    setSourceRef("");
    setContent("");
  }

  return (
    <main className="minha-delpi-chat">
      <section className="mdc-admin-shell">
        <header className="mdc-admin-header">
          <div>
            <p className="mdc-chat-eyebrow">Administração</p>
            <h1>Minha DELPI Chat</h1>
            <p>Gestão técnica do provider, documentos e auditoria do módulo.</p>
          </div>

          <div className="mdc-admin-actions">
            <button type="button" onClick={loadAdminData} disabled={isLoading}>
              Atualizar
            </button>
            <button type="button" onClick={onBack}>
              Voltar ao chat
            </button>
          </div>
        </header>

        {error ? (
          <div className="mdc-chat-alert" role="alert">
            {error}
          </div>
        ) : null}

        {successMessage ? (
          <div className="mdc-chat-alert mdc-chat-alert--success" role="status">
            {successMessage}
          </div>
        ) : null}

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
            <h2>Novo documento</h2>

            <form
              className="mdc-admin-form"
              onSubmit={(event) => {
                event.preventDefault();
                void handleCreateDocument();
              }}
            >
              <label>
                <span>Título</span>
                <input
                  value={title}
                  disabled={isMutating}
                  placeholder="Ex.: Visão geral da Minha DELPI"
                  onChange={(event) => setTitle(event.target.value)}
                />
              </label>

              <label>
                <span>Tipo da fonte</span>
                <input
                  value={sourceType}
                  disabled={isMutating}
                  placeholder="manual"
                  onChange={(event) => setSourceType(event.target.value)}
                />
              </label>

              <label>
                <span>Referência da fonte</span>
                <input
                  value={sourceRef}
                  disabled={isMutating}
                  placeholder="seed:minha-delpi-visao-geral"
                  onChange={(event) => setSourceRef(event.target.value)}
                />
              </label>

              <label>
                <span>Conteúdo</span>
                <textarea
                  value={content}
                  disabled={isMutating}
                  rows={8}
                  placeholder="Cole aqui o conteúdo que será indexado no RAG."
                  onChange={(event) => setContent(event.target.value)}
                />
              </label>

              <button type="submit" disabled={!canSubmitDocument || isMutating}>
                {isMutating ? "Processando..." : "Ingerir documento"}
              </button>
            </form>
          </article>

          <article className="mdc-admin-card mdc-admin-card--wide">
            <h2>Documentos de conhecimento</h2>

            {documents.length === 0 ? (
              <p className="mdc-chat-muted">Nenhum documento encontrado.</p>
            ) : (
              <div className="mdc-admin-table-wrap">
                <table className="mdc-admin-table">
                  <thead>
                    <tr>
                      <th>Título</th>
                      <th>Origem</th>
                      <th>Status</th>
                      <th>Atualizado</th>
                      <th>Ação</th>
                    </tr>
                  </thead>
                  <tbody>
                    {documents.map((document) => (
                      <tr key={document.id}>
                        <td>{document.title}</td>
                        <td>{document.sourceRef || document.sourceType}</td>
                        <td>{document.active ? "Ativo" : "Inativo"}</td>
                        <td>{new Date(document.updatedAt).toLocaleString()}</td>
                        <td>
                          {document.active ? (
                            <button
                              type="button"
                              disabled={isMutating}
                              onClick={() => deactivateDocument(document.id)}
                            >
                              Desativar
                            </button>
                          ) : (
                            <button
                              type="button"
                              disabled={isMutating}
                              onClick={() => reactivateDocument(document.id)}
                            >
                              Reativar
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </article>

          <article className="mdc-admin-card mdc-admin-card--wide">
            <h2>Auditoria recente</h2>

            {auditLogs.length === 0 ? (
              <p className="mdc-chat-muted">Nenhum evento encontrado.</p>
            ) : (
              <div className="mdc-admin-table-wrap">
                <table className="mdc-admin-table">
                  <thead>
                    <tr>
                      <th>Ação</th>
                      <th>Contexto</th>
                      <th>Usuário</th>
                      <th>Data</th>
                    </tr>
                  </thead>
                  <tbody>
                    {auditLogs.map((log) => (
                      <tr key={log.id}>
                        <td>{log.action}</td>
                        <td>{log.context || "-"}</td>
                        <td>{log.userId || "-"}</td>
                        <td>{new Date(log.createdAt).toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </article>
        </section>
      </section>
    </main>
  );
}
