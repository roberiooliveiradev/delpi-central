import { KnowledgeDocumentsPanel } from "./KnowledgeDocumentsPanel";
import { KnowledgeIngestionPanel } from "./KnowledgeIngestionPanel";
import type { AdminRbacSummary } from "../../../../data/api/adminTypes";
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
  KnowledgeBackendPlaceholders & {
    rbac?: AdminRbacSummary | null;
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
  testDocument,
  rbac,
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
      <KnowledgeIngestionPanel
        isMutating={isMutating}
        createDocument={createDocument}
        uploadDocumentFile={uploadDocumentFile}
        canManageKnowledge={canManageKnowledge}
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
        canDeleteKnowledgeDocuments={canDeleteKnowledgeDocuments}
        canReindexKnowledgeDocuments={canReindexKnowledgeDocuments}
      />
    </section>
  );
}
