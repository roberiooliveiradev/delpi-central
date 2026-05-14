import { useRef, useState } from "react";

import { useChatAdmin } from "../../state/hooks/useChatAdmin";

import "./ChatAdminPage.css";

type ChatAdminPageProps = {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
  onBack: () => void;
};

export function ChatAdminPage({ getAccessToken, onBack }: ChatAdminPageProps) {
  const {
    llmStatus,
    metricsSummary,
    documents,
    documentsPagination,
    auditLogs,
    documentSearch,
    documentStatus,
    isLoading,
    isMutating,
    successMessage,
    error,
    loadAdminData,
    setDocumentSearch,
    setDocumentStatus,
    goToNextDocumentsPage,
    goToPreviousDocumentsPage,
    createDocument,
    uploadDocumentFile,
    deleteDocument,
    deactivateDocument,
    reactivateDocument,
    reindexDocument,
  } = useChatAdmin({ getAccessToken });

  const [title, setTitle] = useState("");
  const [sourceType, setSourceType] = useState("manual");
  const [sourceRef, setSourceRef] = useState("");
  const [content, setContent] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [ingestMode, setIngestMode] = useState<"text" | "file">("file");
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const canSubmitDocument =
    title.trim().length > 0 &&
    sourceType.trim().length > 0 &&
    (ingestMode === "text" ? content.trim().length > 0 : Boolean(selectedFile));

  async function handleCreateDocument() {
    if (!canSubmitDocument || isMutating) {
      return;
    }

    if (ingestMode === "file") {
      if (!selectedFile) {
        return;
      }

      await uploadDocumentFile({
        file: selectedFile,
        title: title.trim() || selectedFile.name,
        sourceType: sourceType.trim() || "admin_upload",
        sourceRef: sourceRef.trim() || undefined,
      });
    } else {
      await createDocument({
        title: title.trim(),
        sourceType: sourceType.trim(),
        sourceRef: sourceRef.trim() || undefined,
        content: content.trim(),
      });
    }

    setTitle("");
    setSourceRef("");
    setContent("");
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
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

        {metricsSummary ? (
          <section className="mdc-admin-metrics" aria-label="Resumo operacional">
            <article className="mdc-admin-metric-card">
              <span>Sessões</span>
              <strong>{metricsSummary.sessions}</strong>
            </article>

            <article className="mdc-admin-metric-card">
              <span>Mensagens</span>
              <strong>{metricsSummary.messages}</strong>
            </article>

            <article className="mdc-admin-metric-card">
              <span>Documentos ativos</span>
              <strong>
                {metricsSummary.activeKnowledgeDocuments}/
                {metricsSummary.knowledgeDocuments}
              </strong>
            </article>

            <article className="mdc-admin-metric-card">
              <span>Chunks</span>
              <strong>{metricsSummary.knowledgeChunks}</strong>
            </article>

            <article className="mdc-admin-metric-card">
              <span>Auditorias</span>
              <strong>{metricsSummary.auditLogs}</strong>
            </article>

            <article className="mdc-admin-metric-card">
              <span>Tools 24h</span>
              <strong>{metricsSummary.recentToolCalls24h}</strong>
            </article>

            <article className="mdc-admin-metric-card">
              <span>Erros 24h</span>
              <strong>{metricsSummary.recentErrors24h}</strong>
            </article>
          </section>
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
              <div className="mdc-admin-segmented" role="tablist" aria-label="Modo de ingestão">
                <button
                  type="button"
                  className={ingestMode === "file" ? "is-active" : undefined}
                  onClick={() => setIngestMode("file")}
                >
                  Arquivo
                </button>
                <button
                  type="button"
                  className={ingestMode === "text" ? "is-active" : undefined}
                  onClick={() => setIngestMode("text")}
                >
                  Texto
                </button>
              </div>
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

              {ingestMode === "file" ? (
                <label>
                  <span>Arquivo</span>
                  <input
                    ref={fileInputRef}
                    type="file"
                    disabled={isMutating}
                    accept=".pdf,.txt,.md,.doc,.docx,.xls,.xlsx,.csv,.json"
                    onChange={(event) => {
                      const file = event.target.files?.[0] ?? null;
                      setSelectedFile(file);

                      if (file && !title.trim()) {
                        setTitle(file.name);
                      }
                    }}
                  />
                  {selectedFile ? (
                    <small>
                      Selecionado: {selectedFile.name} ({selectedFile.size} bytes)
                    </small>
                  ) : (
                    <small>Formatos: txt, md, csv, json, docx, xlsx e pdf.</small>
                  )}
                </label>
              ) : (
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
              )}

              <button type="submit" disabled={!canSubmitDocument || isMutating}>
                {isMutating ? "Processando..." : "Ingerir documento"}
              </button>
            </form>
          </article>

          <article className="mdc-admin-card mdc-admin-card--wide">
            <div className="mdc-admin-card-header">
              <h2>Documentos de conhecimento</h2>

              <div className="mdc-admin-filters">
                <input
                  value={documentSearch}
                  placeholder="Buscar por título, tipo ou referência"
                  onChange={(event) => setDocumentSearch(event.target.value)}
                />

                <select
                  value={documentStatus}
                  onChange={(event) =>
                    setDocumentStatus(event.target.value as "all" | "active" | "inactive")
                  }
                >
                  <option value="all">Todos</option>
                  <option value="active">Ativos</option>
                  <option value="inactive">Inativos</option>
                </select>
              </div>
            </div>

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
                      <th>Chunks</th>
                      <th>Atualizado</th>
                      <th>Ações</th>
                    </tr>
                  </thead>
                  <tbody>
                    {documents.map((document) => (
                      <tr key={document.id}>
                        <td>{document.title}</td>
                        <td>{document.sourceRef || document.sourceType}</td>
                        <td>{document.active ? "Ativo" : "Inativo"}</td>
                        <td>{document.chunkCount}</td>
                        <td>{new Date(document.updatedAt).toLocaleString()}</td>
                        <td>
                          <div className="mdc-admin-row-actions">
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

                            <button
                              type="button"
                              disabled={isMutating}
                              onClick={() => reindexDocument(document.id)}
                            >
                              Reindexar
                            </button>

                            <button
                              type="button"
                              disabled={isMutating}
                              onClick={() => {
                                if (window.confirm(`Excluir definitivamente "${document.title}" da base de conhecimento?`)) {
                                  void deleteDocument(document.id);
                                }
                              }}
                            >
                              Excluir
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <div className="mdc-admin-pagination">
              <span>
                Exibindo {documents.length} de {documentsPagination.total} documento(s)
              </span>

              <div>
                <button
                  type="button"
                  disabled={!documentsPagination.hasPrevious || isLoading}
                  onClick={goToPreviousDocumentsPage}
                >
                  Anterior
                </button>
                <button
                  type="button"
                  disabled={!documentsPagination.hasNext || isLoading}
                  onClick={goToNextDocumentsPage}
                >
                  Próxima
                </button>
              </div>
            </div>
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
                      <th>Ações</th>
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
