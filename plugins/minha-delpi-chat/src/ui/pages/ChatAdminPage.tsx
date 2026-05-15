import { useRef, useState } from "react";

import { useChatAdmin } from "../../state/hooks/useChatAdmin";

import "./ChatAdminPage.css";

type ChatAdminPageProps = {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
  onBack: () => void;
};

type AdminTab = "knowledge" | "guidelines" | "tools" | "audit";

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

  const [activeTab, setActiveTab] = useState<AdminTab>("knowledge");
  const [title, setTitle] = useState("");
  const [sourceType, setSourceType] = useState("diretriz");
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
        metadata: {
          scope: "global",
          origin: "admin_upload",
        },
      });
    } else {
      await createDocument({
        title: title.trim(),
        sourceType: sourceType.trim(),
        sourceRef: sourceRef.trim() || undefined,
        content: content.trim(),
        metadata: {
          scope: "global",
          origin: "admin_manual",
        },
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

  function renderMetrics() {
    if (!metricsSummary) {
      return null;
    }

    return (
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
          <span>Documentos globais</span>
          <strong>
            {metricsSummary.activeKnowledgeDocuments}/{metricsSummary.knowledgeDocuments}
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
    );
  }

  function renderKnowledgeTab() {
    return (
      <section className="mdc-admin-knowledge-layout">
        <article className="mdc-admin-card mdc-admin-ingest-card">
          <div className="mdc-admin-card-title">
            <div>
              <p className="mdc-chat-eyebrow">Base global</p>
              <h2>Adicionar conhecimento</h2>
            </div>
            <span className="mdc-admin-pill">Global</span>
          </div>

          <p className="mdc-admin-card-description">
            Use esta área somente para documentos que orientam todo o Minha DELPI Chat.
            Anexos de conversas não entram aqui.
          </p>

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

            {ingestMode === "file" ? (
              <label className="mdc-admin-dropzone">
                <span>Arquivo de conhecimento</span>
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
                <strong>
                  {selectedFile ? selectedFile.name : "Selecionar ou arrastar arquivo"}
                </strong>
                <small>
                  {selectedFile
                    ? `${selectedFile.size} bytes`
                    : "Formatos: txt, md, csv, json, docx, xlsx e pdf."}
                </small>
              </label>
            ) : (
              <label>
                <span>Conteúdo</span>
                <textarea
                  value={content}
                  disabled={isMutating}
                  rows={8}
                  placeholder="Cole aqui diretrizes, glossários ou instruções globais."
                  onChange={(event) => setContent(event.target.value)}
                />
              </label>
            )}

            <div className="mdc-admin-form-grid">
              <label>
                <span>Título</span>
                <input
                  value={title}
                  disabled={isMutating}
                  placeholder="Ex.: Diretrizes gerais do atendimento"
                  onChange={(event) => setTitle(event.target.value)}
                />
              </label>

              <label>
                <span>Tipo</span>
                <select
                  value={sourceType}
                  disabled={isMutating}
                  onChange={(event) => setSourceType(event.target.value)}
                >
                  <option value="diretriz">Diretriz</option>
                  <option value="glossario">Glossário</option>
                  <option value="manual">Manual</option>
                  <option value="politica">Política</option>
                  <option value="admin_upload">Upload admin</option>
                </select>
              </label>
            </div>

            <label>
              <span>Referência</span>
              <input
                value={sourceRef}
                disabled={isMutating}
                placeholder="Ex.: global:diretrizes-atendimento"
                onChange={(event) => setSourceRef(event.target.value)}
              />
            </label>

            <button type="submit" disabled={!canSubmitDocument || isMutating}>
              {isMutating ? "Processando..." : "Ingerir na base global"}
            </button>
          </form>
        </article>

        <article className="mdc-admin-card mdc-admin-card--wide">
          <div className="mdc-admin-card-header">
            <div>
              <h2>Base global de conhecimento</h2>
              <p className="mdc-chat-muted">
                Lista apenas documentos globais. Fontes de conversas, agentes e projetos ficam fora deste contexto.
              </p>
            </div>

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
            <p className="mdc-chat-muted">Nenhum documento global encontrado.</p>
          ) : (
            <div className="mdc-admin-document-list">
              {documents.map((document) => (
                <article className="mdc-admin-document-row" key={document.id}>
                  <div>
                    <div className="mdc-admin-document-title">
                      <strong>{document.title}</strong>
                      <span className={document.active ? "is-active" : "is-inactive"}>
                        {document.active ? "Ativo" : "Inativo"}
                      </span>
                    </div>

                    <p>
                      {document.sourceType} · {document.sourceRef || "sem referência"} ·{" "}
                      {document.chunkCount} chunk(s)
                    </p>

                    <small>
                      Atualizado em {new Date(document.updatedAt).toLocaleString()}
                    </small>
                  </div>

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
                      className="mdc-admin-danger-button"
                      disabled={isMutating}
                      onClick={() => {
                        if (
                          window.confirm(
                            `Excluir definitivamente "${document.title}" da base de conhecimento?`,
                          )
                        ) {
                          void deleteDocument(document.id);
                        }
                      }}
                    >
                      Excluir
                    </button>
                  </div>
                </article>
              ))}
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
      </section>
    );
  }

  function renderGuidelinesTab() {
    return (
      <section className="mdc-admin-grid">
        <article className="mdc-admin-card">
          <h2>Diretrizes globais</h2>
          <p className="mdc-chat-muted">
            Próxima etapa: transformar diretrizes em documentos versionados e testáveis.
          </p>

          <div className="mdc-admin-guideline-list">
            <div>
              <strong>Não inventar respostas</strong>
              <span>Ativo</span>
            </div>
            <div>
              <strong>Priorizar fontes globais antes de conhecimento geral</strong>
              <span>Ativo</span>
            </div>
            <div>
              <strong>Executar ferramentas autorizadas quando necessário</strong>
              <span>Ativo</span>
            </div>
          </div>
        </article>

        <article className="mdc-admin-card">
          <h2>Teste de assertividade</h2>
          <p className="mdc-chat-muted">
            Próxima etapa: campo para simular perguntas e verificar quais documentos o RAG usaria.
          </p>

          <textarea
            rows={8}
            disabled
            placeholder="Em breve: escreva uma pergunta de teste para validar a base global."
          />
        </article>
      </section>
    );
  }

  function renderToolsTab() {
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

  function renderAuditTab() {
    return (
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
    );
  }

  return (
    <main className="minha-delpi-chat">
      <section className="mdc-admin-shell">
        <header className="mdc-admin-header mdc-admin-header--clean">
          <div>
            <p className="mdc-chat-eyebrow">Administração</p>
            <h1>Minha DELPI Chat</h1>
            <p>
              Curadoria da base global, diretrizes, ferramentas e auditoria operacional.
            </p>
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

        {renderMetrics()}

        <nav className="mdc-admin-tabs" aria-label="Administração do chat">
          <button
            type="button"
            className={activeTab === "knowledge" ? "is-active" : undefined}
            onClick={() => setActiveTab("knowledge")}
          >
            Conhecimento
          </button>
          <button
            type="button"
            className={activeTab === "guidelines" ? "is-active" : undefined}
            onClick={() => setActiveTab("guidelines")}
          >
            Diretrizes
          </button>
          <button
            type="button"
            className={activeTab === "tools" ? "is-active" : undefined}
            onClick={() => setActiveTab("tools")}
          >
            Ferramentas
          </button>
          <button
            type="button"
            className={activeTab === "audit" ? "is-active" : undefined}
            onClick={() => setActiveTab("audit")}
          >
            Auditoria
          </button>
        </nav>

        {activeTab === "knowledge" ? renderKnowledgeTab() : null}
        {activeTab === "guidelines" ? renderGuidelinesTab() : null}
        {activeTab === "tools" ? renderToolsTab() : null}
        {activeTab === "audit" ? renderAuditTab() : null}
      </section>
    </main>
  );
}
