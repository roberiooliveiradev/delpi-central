import { useCallback, useEffect, useState } from "react";

import {
  archiveAdminGuideline,
  createKnowledgeDocument,
  deleteKnowledgeDocument,
  deactivateKnowledgeDocument,
  getAdminMetricsSummary,
  getLlmStatus,
  listAdminGuidelines,
  listKnowledgeDocuments,
  updateKnowledgeDocumentMetadata,
  publishAdminGuideline,
  reactivateKnowledgeDocument,
  reindexKnowledgeDocument,
  saveAdminGuideline,
  uploadKnowledgeDocumentFile,
  previewKnowledgeIngestion,
  type CreateKnowledgeDocumentPayload,
  type SaveAdminGuidelinePayload,
  type PreviewKnowledgeIngestionPayload,
  type UploadKnowledgeDocumentFilePayload,
} from "../../data/api/adminApi";
import type {
  AdminGuideline,
  AdminKnowledgeCuratorialFacets,
  AdminKnowledgeDocument,
  AdminKnowledgeDocumentsResponse,
  AdminKnowledgeIngestionPreviewResponse,
  AdminLlmStatus,
  AdminMetricsSummary,
  UpdateKnowledgeDocumentMetadataPayload,
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
    category: "",
    namespace: "",
    domain: "",
    tag: "",
    sourceType: "",
  },
  facets: {
    categories: [],
    namespaces: [],
    domains: [],
    tags: [],
    sourceTypes: [],
  },
};

const EMPTY_FACETS: AdminKnowledgeCuratorialFacets = {
  categories: [],
  namespaces: [],
  domains: [],
  tags: [],
  sourceTypes: [],
};

export function useChatAdmin(options: UseChatAdminOptions = {}) {
  const [llmStatus, setLlmStatus] = useState<AdminLlmStatus | null>(null);
  const [metricsSummary, setMetricsSummary] = useState<AdminMetricsSummary | null>(null);
  const [metricsHours, setMetricsHours] = useState(24);
  const [documentsResponse, setDocumentsResponse] =
    useState<AdminKnowledgeDocumentsResponse>(DEFAULT_DOCUMENTS_RESPONSE);
  const [guidelines, setGuidelines] = useState<AdminGuideline[]>([]);
  const [documentSearch, setDocumentSearch] = useState("");
  const [documentStatus, setDocumentStatus] = useState<DocumentStatusFilter>("all");
  const [documentCategory, setDocumentCategory] = useState("");
  const [documentNamespace, setDocumentNamespace] = useState("");
  const [documentDomain, setDocumentDomain] = useState("");
  const [documentTag, setDocumentTag] = useState("");
  const [documentSourceType, setDocumentSourceType] = useState("");
  const [documentFacets, setDocumentFacets] =
    useState<AdminKnowledgeCuratorialFacets>(EMPTY_FACETS);
  const [documentOffset, setDocumentOffset] = useState(0);
  const [documentLimit] = useState(10);
  const [isLoading, setIsLoading] = useState(false);
  const [isMutating, setIsMutating] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [ingestionPreview, setIngestionPreview] =
    useState<AdminKnowledgeIngestionPreviewResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  function formatPipelineSummary(
    pipeline?: { chunksAfterDedup?: number; duplicatesRemoved?: number; chunkStrategy?: string },
  ): string {
    if (!pipeline) {
      return "";
    }

    const parts = [
      `${pipeline.chunksAfterDedup ?? 0} chunk(s)`,
      pipeline.chunkStrategy ? `estratégia ${pipeline.chunkStrategy}` : null,
    ];

    if ((pipeline.duplicatesRemoved ?? 0) > 0) {
      parts.push(`${pipeline.duplicatesRemoved} duplicata(s) removida(s)`);
    }

    return parts.filter(Boolean).join(" · ");
  }

  const loadAdminData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const [status, metrics, docs, guidelinesResponse] = await Promise.all([
        getLlmStatus({ getAccessToken: options.getAccessToken }),
        getAdminMetricsSummary(metricsHours, { getAccessToken: options.getAccessToken }),
        listKnowledgeDocuments(
          {
            search: documentSearch,
            active: documentStatus,
            category: documentCategory || undefined,
            namespace: documentNamespace || undefined,
            domain: documentDomain || undefined,
            tag: documentTag || undefined,
            sourceType: documentSourceType || undefined,
            limit: documentLimit,
            offset: documentOffset,
          },
          { getAccessToken: options.getAccessToken },
        ),
        listAdminGuidelines({ getAccessToken: options.getAccessToken }),
      ]);

      setLlmStatus(status);
      setMetricsSummary(metrics);
      setDocumentsResponse(docs);
      setDocumentFacets(docs.facets ?? EMPTY_FACETS);
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
    documentCategory,
    documentNamespace,
    documentDomain,
    documentTag,
    documentSourceType,
    metricsHours,
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

  const resetDocumentCuratorialFilters = useCallback(() => {
    setDocumentCategory("");
    setDocumentNamespace("");
    setDocumentDomain("");
    setDocumentTag("");
    setDocumentSourceType("");
    setDocumentOffset(0);
  }, []);

  const updateDocumentCategory = useCallback((value: string) => {
    setDocumentCategory(value);
    setDocumentOffset(0);
  }, []);

  const updateDocumentNamespace = useCallback((value: string) => {
    setDocumentNamespace(value);
    setDocumentOffset(0);
  }, []);

  const updateDocumentDomain = useCallback((value: string) => {
    setDocumentDomain(value);
    setDocumentOffset(0);
  }, []);

  const updateDocumentTag = useCallback((value: string) => {
    setDocumentTag(value);
    setDocumentOffset(0);
  }, []);

  const updateDocumentSourceType = useCallback((value: string) => {
    setDocumentSourceType(value);
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

        if (result.duplicate) {
          setSuccessMessage(
            `Documento "${result.title}" já existia na base (mesmo conteúdo/referência). Nenhum chunk novo foi criado.`,
          );
        } else {
          const pipelineSummary = formatPipelineSummary(result.pipeline);
          setSuccessMessage(
            pipelineSummary
              ? `Documento "${result.title}" ingerido (${pipelineSummary}).`
              : `Documento "${result.title}" ingerido com ${result.chunks} chunk(s).`,
          );
        }

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

        if (result.duplicate) {
          setSuccessMessage(
            `Arquivo "${result.title}" já existia na base (mesmo conteúdo/referência).`,
          );
        } else {
          const pipelineSummary = formatPipelineSummary(result.pipeline);
          setSuccessMessage(
            pipelineSummary
              ? `Arquivo "${result.title}" ingerido (${pipelineSummary}).`
              : `Arquivo "${result.title}" ingerido com ${result.chunks} chunk(s).`,
          );
        }

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

  const updateDocumentMetadata = useCallback(
    async (documentId: string, payload: UpdateKnowledgeDocumentMetadataPayload) => {
      await runAdminMutation(async () => {
        const updated = await updateKnowledgeDocumentMetadata(documentId, payload, {
          getAccessToken: options.getAccessToken,
        });

        setSuccessMessage(`Metadados de "${updated.title}" atualizados.`);
        await loadAdminData();
      });
    },
    [loadAdminData, options.getAccessToken, runAdminMutation],
  );

  const previewIngestion = useCallback(
    async (payload: PreviewKnowledgeIngestionPayload) => {
      setError(null);

      try {
        const preview = await previewKnowledgeIngestion(payload, {
          getAccessToken: options.getAccessToken,
        });
        setIngestionPreview(preview);
      } catch (err) {
        setIngestionPreview(null);
        setError(err instanceof Error ? err.message : "Erro ao pré-visualizar ingestão.");
      }
    },
    [options.getAccessToken],
  );

  const reindexDocument = useCallback(
    async (documentId: string) => {
      await runAdminMutation(async () => {
        const result = await reindexKnowledgeDocument(documentId, {
          getAccessToken: options.getAccessToken,
        });

        const pipelineSummary = formatPipelineSummary(result.pipeline);
        setSuccessMessage(
          pipelineSummary
            ? `Documento "${result.title}" reindexado (${pipelineSummary}).`
            : `Documento "${result.title}" reindexado com ${result.chunks} chunk(s).`,
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
    metricsHours,
    setMetricsHours,
    documents: documentsResponse.items as AdminKnowledgeDocument[],
    documentsPagination: documentsResponse.pagination,
    guidelines,
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
    successMessage,
    ingestionPreview,
    error,
    setDocumentSearch: updateDocumentSearch,
    setDocumentStatus: updateDocumentStatus,
    setDocumentCategory: updateDocumentCategory,
    setDocumentNamespace: updateDocumentNamespace,
    setDocumentDomain: updateDocumentDomain,
    setDocumentTag: updateDocumentTag,
    setDocumentSourceType: updateDocumentSourceType,
    resetDocumentCuratorialFilters,
    goToNextDocumentsPage,
    goToPreviousDocumentsPage,
    loadAdminData,
    createDocument,
    uploadDocumentFile,
    previewIngestion,
    deleteDocument,
    deactivateDocument,
    reactivateDocument,
    reindexDocument,
    updateDocumentMetadata,
    saveGuideline,
    publishGuideline,
    archiveGuideline,
  };
}
