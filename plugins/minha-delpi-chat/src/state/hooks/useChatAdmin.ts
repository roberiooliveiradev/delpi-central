import { useCallback, useEffect, useState } from "react";

import {
  createKnowledgeDocument,
  deactivateKnowledgeDocument,
  getLlmStatus,
  listAuditLogs,
  listKnowledgeDocuments,
  reactivateKnowledgeDocument,
  reindexKnowledgeDocument,
  type CreateKnowledgeDocumentPayload,
} from "../../data/api/adminApi";
import type {
  AdminAuditLog,
  AdminKnowledgeDocument,
  AdminKnowledgeDocumentsResponse,
  AdminLlmStatus,
} from "../../data/api/adminTypes";

type UseChatAdminOptions = {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
};

type DocumentStatusFilter = "all" | "active" | "inactive";

const DEFAULT_DOCUMENTS_RESPONSE: AdminKnowledgeDocumentsResponse = {
  items: [],
  pagination: {
    limit: 10,
    offset: 0,
    total: 0,
    hasNext: false,
    hasPrevious: false,
  },
  filters: {
    search: "",
    active: null,
  },
};

export function useChatAdmin(options: UseChatAdminOptions = {}) {
  const [llmStatus, setLlmStatus] = useState<AdminLlmStatus | null>(null);
  const [documentsResponse, setDocumentsResponse] =
    useState<AdminKnowledgeDocumentsResponse>(DEFAULT_DOCUMENTS_RESPONSE);
  const [auditLogs, setAuditLogs] = useState<AdminAuditLog[]>([]);
  const [documentSearch, setDocumentSearch] = useState("");
  const [documentStatus, setDocumentStatus] = useState<DocumentStatusFilter>("all");
  const [documentOffset, setDocumentOffset] = useState(0);
  const [documentLimit] = useState(10);
  const [isLoading, setIsLoading] = useState(false);
  const [isMutating, setIsMutating] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadAdminData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const [status, docs, logs] = await Promise.all([
        getLlmStatus({ getAccessToken: options.getAccessToken }),
        listKnowledgeDocuments(
          {
            search: documentSearch,
            active: documentStatus,
            limit: documentLimit,
            offset: documentOffset,
          },
          { getAccessToken: options.getAccessToken },
        ),
        listAuditLogs({ getAccessToken: options.getAccessToken }),
      ]);

      setLlmStatus(status);
      setDocumentsResponse(docs);
      setAuditLogs(logs);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar administração.");
    } finally {
      setIsLoading(false);
    }
  }, [
    documentLimit,
    documentOffset,
    documentSearch,
    documentStatus,
    options.getAccessToken,
  ]);

  const updateDocumentSearch = useCallback((value: string) => {
    setDocumentSearch(value);
    setDocumentOffset(0);
  }, []);

  const updateDocumentStatus = useCallback((value: DocumentStatusFilter) => {
    setDocumentStatus(value);
    setDocumentOffset(0);
  }, []);

  const goToNextDocumentsPage = useCallback(() => {
    setDocumentOffset((current) => current + documentLimit);
  }, [documentLimit]);

  const goToPreviousDocumentsPage = useCallback(() => {
    setDocumentOffset((current) => Math.max(0, current - documentLimit));
  }, [documentLimit]);

  const createDocument = useCallback(
    async (payload: CreateKnowledgeDocumentPayload) => {
      setIsMutating(true);
      setError(null);
      setSuccessMessage(null);

      try {
        const result = await createKnowledgeDocument(payload, {
          getAccessToken: options.getAccessToken,
        });

        setSuccessMessage(
          `Documento "${result.title}" ingerido com ${result.chunks} chunk(s).`,
        );

        setDocumentOffset(0);
        await loadAdminData();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erro ao ingerir documento.");
      } finally {
        setIsMutating(false);
      }
    },
    [loadAdminData, options.getAccessToken],
  );

  const deactivateDocument = useCallback(
    async (documentId: string) => {
      setIsMutating(true);
      setError(null);
      setSuccessMessage(null);

      try {
        await deactivateKnowledgeDocument(documentId, {
          getAccessToken: options.getAccessToken,
        });

        setSuccessMessage("Documento desativado com sucesso.");
        await loadAdminData();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erro ao desativar documento.");
      } finally {
        setIsMutating(false);
      }
    },
    [loadAdminData, options.getAccessToken],
  );

  const reactivateDocument = useCallback(
    async (documentId: string) => {
      setIsMutating(true);
      setError(null);
      setSuccessMessage(null);

      try {
        await reactivateKnowledgeDocument(documentId, {
          getAccessToken: options.getAccessToken,
        });

        setSuccessMessage("Documento reativado com sucesso.");
        await loadAdminData();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erro ao reativar documento.");
      } finally {
        setIsMutating(false);
      }
    },
    [loadAdminData, options.getAccessToken],
  );

  const reindexDocument = useCallback(
    async (documentId: string) => {
      setIsMutating(true);
      setError(null);
      setSuccessMessage(null);

      try {
        const result = await reindexKnowledgeDocument(documentId, {
          getAccessToken: options.getAccessToken,
        });

        setSuccessMessage(
          `Documento "${result.title}" reindexado com ${result.chunks} chunk(s).`,
        );

        await loadAdminData();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erro ao reindexar documento.");
      } finally {
        setIsMutating(false);
      }
    },
    [loadAdminData, options.getAccessToken],
  );

  useEffect(() => {
    void loadAdminData();
  }, [loadAdminData]);

  return {
    llmStatus,
    documents: documentsResponse.items as AdminKnowledgeDocument[],
    documentsPagination: documentsResponse.pagination,
    auditLogs,
    documentSearch,
    documentStatus,
    isLoading,
    isMutating,
    successMessage,
    error,
    setDocumentSearch: updateDocumentSearch,
    setDocumentStatus: updateDocumentStatus,
    goToNextDocumentsPage,
    goToPreviousDocumentsPage,
    loadAdminData,
    createDocument,
    deactivateDocument,
    reactivateDocument,
    reindexDocument,
  };
}
