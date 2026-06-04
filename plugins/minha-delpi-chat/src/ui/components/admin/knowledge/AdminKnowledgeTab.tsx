import { AdminTabHeader } from "../shared/AdminTabHeader";
import { KnowledgeDocumentsPanel } from "./KnowledgeDocumentsPanel";
import { KnowledgeIngestionPanel } from "./KnowledgeIngestionPanel";
import { KnowledgeSummaryStrip } from "./KnowledgeSummaryStrip";
import type { AdminRbacSummary } from "../../../../data/api/adminTypes";
import type { AdminKnowledgeDocumentsSummary } from "../../../../data/api/adminTypes";
import type {
  DocumentStatusFilter,
  KnowledgeBackendPlaceholders,
  KnowledgeDocumentActions,
  KnowledgeDocumentsState,
  KnowledgeIngestionActions,
} from "./knowledgeTypes";

import "./AdminKnowledgeTab.css";

type AdminKnowledgeTabProps = KnowledgeDocumentsState &
  KnowledgeDocumentActions &
  KnowledgeIngestionActions &
  KnowledgeBackendPlaceholders & {
    rbac?: AdminRbacSummary | null;
    documentSummary?: AdminKnowledgeDocumentsSummary | null;
    onDocumentStatusFilterChange?: (filter: DocumentStatusFilter) => void;
  };

export function AdminKnowledgeTab({
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
  createDocument,
  uploadDocumentFile,
  previewIngestion,
  ingestionPreview,
  deleteDocument,
  deactivateDocument,
  reactivateDocument,
  reindexDocument,
  updateDocumentMetadata,
  testDocument,
  rbac,
  documentSummary,
  onDocumentStatusFilterChange,
}: AdminKnowledgeTabProps) {
  const canManageKnowledge = Boolean(
    rbac?.capabilities.canDeleteKnowledgeDocuments ||
      rbac?.capabilities.canReindexKnowledgeDocuments,
  );
  const canDeleteKnowledgeDocuments = Boolean(
    rbac?.capabilities.canDeleteKnowledgeDocuments,
  );
  const canReindexKnowledgeDocuments = Boolean(
    rbac?.capabilities.canReindexKnowledgeDocuments,
  );

  return (
    <section className="mdc-admin-knowledge">
      <AdminTabHeader
        eyebrow="Conhecimento"
        title="Base de conhecimento"
        description="Documentos globais do chat, ingestão e curadoria. Anexos de conversa não entram nesta base."
        summary={
          <KnowledgeSummaryStrip
            summary={documentSummary}
            activeFilter={documentStatus}
            isLoading={isLoading}
            onFilterChange={onDocumentStatusFilterChange}
          />
        }
      />

      <div className="mdc-admin-knowledge__body mdc-admin-split">
      <div className="mdc-admin-split__aside">
        <KnowledgeIngestionPanel
          isMutating={isMutating}
          createDocument={createDocument}
          uploadDocumentFile={uploadDocumentFile}
          previewIngestion={previewIngestion}
          ingestionPreview={ingestionPreview}
          canManageKnowledge={canManageKnowledge}
        />
      </div>

      <div className="mdc-admin-split__main">
        <KnowledgeDocumentsPanel
        documents={documents}
        documentsPagination={documentsPagination}
        documentSearch={documentSearch}
        documentStatus={documentStatus}
        documentCategory={documentCategory}
        documentNamespace={documentNamespace}
        documentDomain={documentDomain}
        documentTag={documentTag}
        documentSourceType={documentSourceType}
        documentFacets={documentFacets}
        isLoading={isLoading}
        isMutating={isMutating}
        setDocumentSearch={setDocumentSearch}
        setDocumentStatus={setDocumentStatus}
        setDocumentCategory={setDocumentCategory}
        setDocumentNamespace={setDocumentNamespace}
        setDocumentDomain={setDocumentDomain}
        setDocumentTag={setDocumentTag}
        setDocumentSourceType={setDocumentSourceType}
        resetDocumentCuratorialFilters={resetDocumentCuratorialFilters}
        goToNextDocumentsPage={goToNextDocumentsPage}
        goToPreviousDocumentsPage={goToPreviousDocumentsPage}
        deleteDocument={deleteDocument}
        deactivateDocument={deactivateDocument}
        reactivateDocument={reactivateDocument}
        reindexDocument={reindexDocument}
        updateDocumentMetadata={updateDocumentMetadata}
        testDocument={testDocument}
        canManageMetadata={canManageKnowledge}
        canDeleteKnowledgeDocuments={canDeleteKnowledgeDocuments}
        canReindexKnowledgeDocuments={canReindexKnowledgeDocuments}
        />
      </div>
      </div>
    </section>
  );
}
