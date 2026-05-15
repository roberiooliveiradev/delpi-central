import { useRef, useState } from "react";

import type { AdminKnowledgeDocument } from "../../../data/api/adminTypes";
import type { CreateKnowledgeDocumentPayload, UploadKnowledgeDocumentFilePayload } from "../../../data/api/adminApi";
import "./AdminKnowledgeTab.css";

type DocumentStatusFilter = "all" | "active" | "inactive";

type DocumentsPagination = {
  limit: number;
  offset: number;
  total: number;
  hasNext: boolean;
  hasPrevious: boolean;
};

type AdminKnowledgeTabProps = {
  documents: AdminKnowledgeDocument[];
  documentsPagination: DocumentsPagination;
  documentSearch: string;
  documentStatus: DocumentStatusFilter;
  isLoading: boolean;
  isMutating: boolean;
  setDocumentSearch: (value: string) => void;
  setDocumentStatus: (value: DocumentStatusFilter) => void;
  goToNextDocumentsPage: () => void;
  goToPreviousDocumentsPage: () => void;
  createDocument: (payload: CreateKnowledgeDocumentPayload) => Promise<void>;
  uploadDocumentFile: (payload: UploadKnowledgeDocumentFilePayload) => Promise<void>;
  deleteDocument: (documentId: string) => Promise<void>;
  deactivateDocument: (documentId: string) => Promise<void>;
  reactivateDocument: (documentId: string) => Promise<void>;
  reindexDocument: (documentId: string) => Promise<void>;
};

export function AdminKnowledgeTab({
  documents,
  documentsPagination,
  documentSearch,
  documentStatus,
  isLoading,
  isMutating,
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
}: AdminKnowledgeTabProps) {
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

  return (
    <section className="mdc-admin-knowledge">
      <article className="mdc-admin-knowledge__ingest">
        <div className="mdc-admin-knowledge__card-title">
          <div>
            <p className="mdc-chat-eyebrow">Base global</p>
            <h2>Adicionar conhecimento</h2>
          </div>
          <span className="mdc-admin-knowledge__pill">Global</span>
        </div>

        <p className="mdc-admin-knowledge__description">
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
                {selectedFile ? selectedFile.name : "Selecionar arquivo"}
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

      <article className="mdc-admin-knowledge__list-card">
        <div className="mdc-admin-knowledge__card-header">
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
                setDocumentStatus(event.target.value as DocumentStatusFilter)
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
