import { ChatNativeTextInput } from "../../shared/chatNativeFormFields";
import { KnowledgeDocumentCard } from "./KnowledgeDocumentCard";
import { ChatAdminNativeSelectField } from "../shared/chatAdminFormFields";
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
  id,
  label,
  value,
  options,
  disabled,
  onChange,
}: {
  id: string;
  label: string;
  value: string;
  options: string[];
  disabled?: boolean;
  onChange: (value: string) => void;
}) {
  return (
    <ChatAdminNativeSelectField
      id={id}
      label={label}
      span={false}
      value={value}
      disabled={disabled}
      placeholderOption="Todos"
      options={options.map((option) => ({ value: option, label: option }))}
      onChange={onChange}
    />
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
    <article className="mdc-admin-panel mdc-knowledge-documents">
      <header className="mdc-admin-panel__intro">
        <h2>Base global de conhecimento</h2>
        <p className="mdc-chat-muted">
          Lista apenas documentos globais. Fontes de conversas, agentes e projetos ficam fora deste
          contexto.
        </p>
      </header>

      <div className="mdc-admin-filter-bar" aria-label="Filtros da base global">
        <label className="mdc-admin-field mdc-admin-filter-bar__search">
          <span>Buscar</span>
          <ChatNativeTextInput
            value={documentSearch}
            placeholder="Título, categoria, tags..."
            onChange={(event) => setDocumentSearch(event.target.value)}
          />
        </label>

        <div className="mdc-admin-filter-bar__row">
          <ChatAdminNativeSelectField
            id="knowledge-documents-status"
            label="Status"
            span={false}
            value={documentStatus}
            options={[
              { value: "all", label: "Todos" },
              { value: "active", label: "Ativos" },
              { value: "inactive", label: "Inativos" },
            ]}
            onChange={(value) => setDocumentStatus(value as DocumentStatusFilter)}
          />

          <FacetSelect
            id="knowledge-documents-category"
            label="Categoria"
            value={documentCategory}
            options={documentFacets.categories}
            disabled={isLoading}
            onChange={setDocumentCategory}
          />

          <FacetSelect
            id="knowledge-documents-namespace"
            label="Namespace"
            value={documentNamespace}
            options={documentFacets.namespaces}
            disabled={isLoading}
            onChange={setDocumentNamespace}
          />

          <FacetSelect
            id="knowledge-documents-domain"
            label="Domínio"
            value={documentDomain}
            options={documentFacets.domains}
            disabled={isLoading}
            onChange={setDocumentDomain}
          />

          <FacetSelect
            id="knowledge-documents-tag"
            label="Tag"
            value={documentTag}
            options={documentFacets.tags}
            disabled={isLoading}
            onChange={setDocumentTag}
          />

          <FacetSelect
            id="knowledge-documents-source-type"
            label="Tipo de fonte"
            value={documentSourceType}
            options={documentFacets.sourceTypes}
            disabled={isLoading}
            onChange={setDocumentSourceType}
          />

          {hasCuratorialFilters ? (
            <button
              type="button"
              className="mdc-admin-btn mdc-admin-filter-bar__clear"
              disabled={isLoading}
              onClick={resetDocumentCuratorialFilters}
            >
              Limpar filtros
            </button>
          ) : null}
        </div>
      </div>

      {documents.length === 0 ? (
        <p className="mdc-chat-muted">Nenhum documento global encontrado.</p>
      ) : (
        <div className="mdc-admin-entity-list mdc-knowledge-documents__list">
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

      <footer className="mdc-admin-panel__footer">
        <span>
          Exibindo {documents.length} de {documentsPagination.total} documento(s)
        </span>

        <div className="mdc-admin-panel__footer-actions">
          <button
            type="button"
            className="mdc-admin-btn"
            disabled={!documentsPagination.hasPrevious || isLoading}
            onClick={goToPreviousDocumentsPage}
          >
            Anterior
          </button>
          <button
            type="button"
            className="mdc-admin-btn mdc-admin-btn--primary"
            disabled={!documentsPagination.hasNext || isLoading}
            onClick={goToNextDocumentsPage}
          >
            Próxima
          </button>
        </div>
      </footer>
    </article>
  );
}
