import { KnowledgeDocumentsPanel } from "./KnowledgeDocumentsPanel";
import { KnowledgeIngestionPanel } from "./KnowledgeIngestionPanel";
import type {
  KnowledgeBackendPlaceholders,
  KnowledgeDocumentActions,
  KnowledgeDocumentsState,
  KnowledgeIngestionActions,
} from "./knowledgeTypes";

import "./AdminKnowledgeTab.css";

type AdminKnowledgeTabProps = KnowledgeDocumentsState &
  KnowledgeDocumentActions &
  KnowledgeIngestionActions &
  KnowledgeBackendPlaceholders;

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
  testDocument,
}: AdminKnowledgeTabProps) {
  return (
    <section className="mdc-admin-knowledge">
      <KnowledgeIngestionPanel
        isMutating={isMutating}
        createDocument={createDocument}
        uploadDocumentFile={uploadDocumentFile}
      />

      <KnowledgeDocumentsPanel
        documents={documents}
        documentsPagination={documentsPagination}
        documentSearch={documentSearch}
        documentStatus={documentStatus}
        isLoading={isLoading}
        isMutating={isMutating}
        setDocumentSearch={setDocumentSearch}
        setDocumentStatus={setDocumentStatus}
        goToNextDocumentsPage={goToNextDocumentsPage}
        goToPreviousDocumentsPage={goToPreviousDocumentsPage}
        deleteDocument={deleteDocument}
        deactivateDocument={deactivateDocument}
        reactivateDocument={reactivateDocument}
        reindexDocument={reindexDocument}
        testDocument={testDocument}
      />
    </section>
  );
}
