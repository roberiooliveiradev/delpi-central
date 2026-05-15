import { useCallback, useEffect, useState } from "react";

import {
  archiveAdminGuideline,
  createKnowledgeDocument,
  deleteKnowledgeDocument,
  deactivateKnowledgeDocument,
  getAdminMetricsSummary,
  getLlmStatus,
  listAdminGuidelines,
  listAuditLogs,
  listKnowledgeDocuments,
  publishAdminGuideline,
  reactivateKnowledgeDocument,
  reindexKnowledgeDocument,
  saveAdminGuideline,
  uploadKnowledgeDocumentFile,
  type CreateKnowledgeDocumentPayload,
  type SaveAdminGuidelinePayload,
  type UploadKnowledgeDocumentFilePayload,
} from "../../data/api/adminApi";
import type {
  AdminAuditLog,
  AdminGuideline,
  AdminKnowledgeDocument,
  AdminKnowledgeDocumentsResponse,
  AdminLlmStatus,
  AdminMetricsSummary,
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
  const [metricsSummary, setMetricsSummary] = useState<AdminMetricsSummary | null>(null);
  const [documentsResponse, setDocumentsResponse] =
    useState<AdminKnowledgeDocumentsResponse>(DEFAULT_DOCUMENTS_RESPONSE);
  const [auditLogs, setAuditLogs] = useState<AdminAuditLog[]>([]);
  const [guidelines, setGuidelines] = useState<AdminGuideline[]>([]);
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
      const [status, metrics, docs, logs, guidelinesResponse] = await Promise.all([
        getLlmStatus({ getAccessToken: options.getAccessToken }),
        getAdminMetricsSummary({ getAccessToken: options.getAccessToken }),
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
        listAdminGuidelines({ getAccessToken: options.getAccessToken }),
      ]);

      setLlmStatus(status);
      setMetricsSummary(metrics);
      setDocumentsResponse(docs);
      setAuditLogs(logs);
      setGuidelines(guidelinesResponse);
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

  const runAdminMutation = useCallback(
    async (mutation: () => Promise<void>) => {
      setIsMutating(true);
      setError(null);
      setSuccessMessage(null);

      try {
        await mutation();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erro ao executar ação administrativa.");
      } finally {
        setIsMutating(false);
      }
    },
    [],
  );

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
      await runAdminMutation(async () => {
        const result = await createKnowledgeDocument(payload, {
          getAccessToken: options.getAccessToken,
        });

        setSuccessMessage(
          `Documento "${result.title}" ingerido com ${result.chunks} chunk(s).`,
        );

        setDocumentOffset(0);
        await loadAdminData();
      });
    },
    [loadAdminData, options.getAccessToken, runAdminMutation],
  );

  const uploadDocumentFile = useCallback(
    async (payload: UploadKnowledgeDocumentFilePayload) => {
      await runAdminMutation(async () => {
        const result = await uploadKnowledgeDocumentFile(payload, {
          getAccessToken: options.getAccessToken,
        });

        setSuccessMessage(
          `Arquivo "${result.title}" ingerido com ${result.chunks} chunk(s).`,
        );

        setDocumentOffset(0);
        await loadAdminData();
      });
    },
    [loadAdminData, options.getAccessToken, runAdminMutation],
  );

  const deleteDocument = useCallback(
    async (documentId: string) => {
      await runAdminMutation(async () => {
        const result = await deleteKnowledgeDocument(documentId, {
          getAccessToken: options.getAccessToken,
        });

        setSuccessMessage(`Documento "${result.title}" excluído da base.`);
        await loadAdminData();
      });
    },
    [loadAdminData, options.getAccessToken, runAdminMutation],
  );

  const deactivateDocument = useCallback(
    async (documentId: string) => {
      await runAdminMutation(async () => {
        await deactivateKnowledgeDocument(documentId, {
          getAccessToken: options.getAccessToken,
        });

        setSuccessMessage("Documento desativado com sucesso.");
        await loadAdminData();
      });
    },
    [loadAdminData, options.getAccessToken, runAdminMutation],
  );

  const reactivateDocument = useCallback(
    async (documentId: string) => {
      await runAdminMutation(async () => {
        await reactivateKnowledgeDocument(documentId, {
          getAccessToken: options.getAccessToken,
        });

        setSuccessMessage("Documento reativado com sucesso.");
        await loadAdminData();
      });
    },
    [loadAdminData, options.getAccessToken, runAdminMutation],
  );

  const reindexDocument = useCallback(
    async (documentId: string) => {
      await runAdminMutation(async () => {
        const result = await reindexKnowledgeDocument(documentId, {
          getAccessToken: options.getAccessToken,
        });

        setSuccessMessage(
          `Documento "${result.title}" reindexado com ${result.chunks} chunk(s).`,
        );

        await loadAdminData();
      });
    },
    [loadAdminData, options.getAccessToken, runAdminMutation],
  );

  const saveGuideline = useCallback(
    async (payload: SaveAdminGuidelinePayload) => {
      await runAdminMutation(async () => {
        const saved = await saveAdminGuideline(payload, {
          getAccessToken: options.getAccessToken,
        });

        setGuidelines((current) => {
          const exists = current.some((item) => item.id === saved.id);

          if (!exists) {
            return [...current, saved];
          }

          return current.map((item) => (item.id === saved.id ? saved : item));
        });

        setSuccessMessage(`Diretriz "${saved.title}" salva.`);
      });
    },
    [options.getAccessToken, runAdminMutation],
  );

  const publishGuideline = useCallback(
    async (guidelineId: string) => {
      await runAdminMutation(async () => {
        const saved = await publishAdminGuideline(guidelineId, {
          getAccessToken: options.getAccessToken,
        });

        setGuidelines((current) =>
          current.map((item) => (item.id === saved.id ? saved : item)),
        );

        setSuccessMessage(`Diretriz "${saved.title}" publicada.`);
      });
    },
    [options.getAccessToken, runAdminMutation],
  );

  const archiveGuideline = useCallback(
    async (guidelineId: string) => {
      await runAdminMutation(async () => {
        const saved = await archiveAdminGuideline(guidelineId, {
          getAccessToken: options.getAccessToken,
        });

        setGuidelines((current) =>
          current.map((item) => (item.id === saved.id ? saved : item)),
        );

        setSuccessMessage(`Diretriz "${saved.title}" arquivada.`);
      });
    },
    [options.getAccessToken, runAdminMutation],
  );

  useEffect(() => {
    void loadAdminData();
  }, [loadAdminData]);

  return {
    llmStatus,
    metricsSummary,
    documents: documentsResponse.items as AdminKnowledgeDocument[],
    documentsPagination: documentsResponse.pagination,
    auditLogs,
    guidelines,
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
    uploadDocumentFile,
    deleteDocument,
    deactivateDocument,
    reactivateDocument,
    reindexDocument,
    saveGuideline,
    publishGuideline,
    archiveGuideline,
  };
}
