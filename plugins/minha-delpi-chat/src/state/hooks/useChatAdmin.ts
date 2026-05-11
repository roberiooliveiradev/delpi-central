import { useCallback, useEffect, useState } from "react";

import {
  createKnowledgeDocument,
  deactivateKnowledgeDocument,
  getLlmStatus,
  listAuditLogs,
  listKnowledgeDocuments,
  reactivateKnowledgeDocument,
  type CreateKnowledgeDocumentPayload,
} from "../../data/api/adminApi";
import type {
  AdminAuditLog,
  AdminKnowledgeDocument,
  AdminLlmStatus,
} from "../../data/api/adminTypes";

type UseChatAdminOptions = {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
};

export function useChatAdmin(options: UseChatAdminOptions = {}) {
  const [llmStatus, setLlmStatus] = useState<AdminLlmStatus | null>(null);
  const [documents, setDocuments] = useState<AdminKnowledgeDocument[]>([]);
  const [auditLogs, setAuditLogs] = useState<AdminAuditLog[]>([]);
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
        listKnowledgeDocuments({ getAccessToken: options.getAccessToken }),
        listAuditLogs({ getAccessToken: options.getAccessToken }),
      ]);

      setLlmStatus(status);
      setDocuments(docs);
      setAuditLogs(logs);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar administração.");
    } finally {
      setIsLoading(false);
    }
  }, [options.getAccessToken]);

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

  useEffect(() => {
    void loadAdminData();
  }, [loadAdminData]);

  return {
    llmStatus,
    documents,
    auditLogs,
    isLoading,
    isMutating,
    successMessage,
    error,
    loadAdminData,
    createDocument,
    deactivateDocument,
    reactivateDocument,
  };
}
