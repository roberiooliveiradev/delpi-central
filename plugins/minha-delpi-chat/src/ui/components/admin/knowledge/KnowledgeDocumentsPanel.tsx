import { KnowledgeDocumentCard } from "./KnowledgeDocumentCard";
import type {
  DocumentStatusFilter,
  KnowledgeBackendPlaceholders,
  KnowledgeDocumentActions,
  KnowledgeDocumentsState,
} from "./knowledgeTypes";

import "./KnowledgeDocumentsPanel.css";

type KnowledgeDocumentsPanelProps = KnowledgeDocumentsState &
  KnowledgeDocumentActions &
  KnowledgeBackendPlaceholders & {
    canDeleteKnowledgeDocuments: boolean;
    canReindexKnowledgeDocuments: boolean;
  };

export function KnowledgeDocumentsPanel({
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
  deleteDocument,
  deactivateDocument,
  reactivateDocument,
  reindexDocument,
  testDocument,
  canDeleteKnowledgeDocuments,
  canReindexKnowledgeDocuments,
}: KnowledgeDocumentsPanelProps) {
  return (
    <article className="mdc-knowledge-documents">
      <div className="mdc-knowledge-documents__header">
        <div>
          <h2>Base global de conhecimento</h2>
          <p className="mdc-chat-muted">
            Lista apenas documentos globais. Fontes de conversas, agentes e projetos ficam fora deste contexto.
          </p>
        </div>

        <div className="mdc-knowledge-documents__filters">
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
        <div className="mdc-knowledge-documents__list">
          {documents.map((document) => (
            <KnowledgeDocumentCard
              key={document.id}
              document={document}
              isMutating={isMutating}
              deleteDocument={deleteDocument}
              deactivateDocument={deactivateDocument}
              reactivateDocument={reactivateDocument}
              reindexDocument={reindexDocument}
              testDocument={testDocument}
              canDeleteKnowledgeDocuments={canDeleteKnowledgeDocuments}
              canReindexKnowledgeDocuments={canReindexKnowledgeDocuments}
            />
          ))}
        </div>
      )}

      <div className="mdc-knowledge-documents__pagination">
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
  );
}
