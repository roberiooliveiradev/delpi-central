import type { AdminKnowledgeDocument } from "../../../../data/api/adminTypes";
import type {
  CreateKnowledgeDocumentPayload,
  UploadKnowledgeDocumentFilePayload,
} from "../../../../data/api/adminApi";

export type DocumentStatusFilter = "all" | "active" | "inactive";

export type DocumentsPagination = {
  limit: number;
  offset: number;
  total: number;
  hasNext: boolean;
  hasPrevious: boolean;
};

export type KnowledgeIngestionMode = "text" | "file";

export type KnowledgeDocumentActions = {
  deleteDocument: (documentId: string) => Promise<void>;
  deactivateDocument: (documentId: string) => Promise<void>;
  reactivateDocument: (documentId: string) => Promise<void>;
  reindexDocument: (documentId: string) => Promise<void>;
};

export type KnowledgeBackendPlaceholders = {
  testDocument?: (documentId: string) => Promise<void>;
  publishDocumentVersion?: (documentId: string) => Promise<void>;
  archiveDocumentVersion?: (documentId: string) => Promise<void>;
  restoreDocumentVersion?: (documentId: string, versionId: string) => Promise<void>;
};

export type KnowledgeIngestionActions = {
  createDocument: (payload: CreateKnowledgeDocumentPayload) => Promise<void>;
  uploadDocumentFile: (payload: UploadKnowledgeDocumentFilePayload) => Promise<void>;
};

export type KnowledgeDocumentsState = {
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
};
