import { useCallback, useEffect, useState } from "react";

import {
  deactivateKnowledgeDocument,
  getLlmStatus,
  listAuditLogs,
  listKnowledgeDocuments,
  reactivateKnowledgeDocument,
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

  const deactivateDocument = useCallback(
    async (documentId: string) => {
      setIsMutating(true);
      setError(null);

      try {
        await deactivateKnowledgeDocument(documentId, {
          getAccessToken: options.getAccessToken,
        });

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

      try {
        await reactivateKnowledgeDocument(documentId, {
          getAccessToken: options.getAccessToken,
        });

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
    error,
    loadAdminData,
    deactivateDocument,
    reactivateDocument,
  };
}
