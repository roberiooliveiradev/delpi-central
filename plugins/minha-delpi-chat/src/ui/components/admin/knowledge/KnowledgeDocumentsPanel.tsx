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
    canManageMetadata: boolean;
    canDeleteKnowledgeDocuments: boolean;
    canReindexKnowledgeDocuments: boolean;
  };

function FacetSelect({
  label,
  value,
  options,
  disabled,
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
  disabled?: boolean;
  onChange: (value: string) => void;
}) {
  return (
    <label>
      <span>{label}</span>
      <select value={value} disabled={disabled} onChange={(event) => onChange(event.target.value)}>
        <option value="">Todos</option>
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  );
}

export function KnowledgeDocumentsPanel({
  documents,
  documentsPagination,
  documentSearch,
  documentStatus,
  documentCategory,
  documentNamespace,
  documentDomain,
  documentTag,
  documentSourceType,
  documentFacets,
  isLoading,
  isMutating,
  setDocumentSearch,
  setDocumentStatus,
  setDocumentCategory,
  setDocumentNamespace,
  setDocumentDomain,
  setDocumentTag,
  setDocumentSourceType,
  resetDocumentCuratorialFilters,
  goToNextDocumentsPage,
  goToPreviousDocumentsPage,
  deleteDocument,
  deactivateDocument,
  reactivateDocument,
  reindexDocument,
  updateDocumentMetadata,
  testDocument,
  canManageMetadata,
  canDeleteKnowledgeDocuments,
  canReindexKnowledgeDocuments,
}: KnowledgeDocumentsPanelProps) {
  const hasCuratorialFilters = Boolean(
    documentCategory || documentNamespace || documentDomain || documentTag || documentSourceType,
  );

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
            placeholder="Buscar por título, categoria, tags..."
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

          <FacetSelect
            label="Categoria"
            value={documentCategory}
            options={documentFacets.categories}
            disabled={isLoading}
            onChange={setDocumentCategory}
          />

          <FacetSelect
            label="Namespace"
            value={documentNamespace}
            options={documentFacets.namespaces}
            disabled={isLoading}
            onChange={setDocumentNamespace}
          />

          <FacetSelect
            label="Domínio"
            value={documentDomain}
            options={documentFacets.domains}
            disabled={isLoading}
            onChange={setDocumentDomain}
          />

          <FacetSelect
            label="Tag"
            value={documentTag}
            options={documentFacets.tags}
            disabled={isLoading}
            onChange={setDocumentTag}
          />

          <FacetSelect
            label="Tipo de fonte"
            value={documentSourceType}
            options={documentFacets.sourceTypes}
            disabled={isLoading}
            onChange={setDocumentSourceType}
          />

          {hasCuratorialFilters ? (
            <button
              type="button"
              className="mdc-knowledge-documents__clear-filters"
              disabled={isLoading}
              onClick={resetDocumentCuratorialFilters}
            >
              Limpar filtros curadoriais
            </button>
          ) : null}
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
              updateDocumentMetadata={updateDocumentMetadata}
              testDocument={testDocument}
              canManageMetadata={canManageMetadata}
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
