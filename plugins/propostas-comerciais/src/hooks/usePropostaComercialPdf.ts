import { useCallback, useEffect, useRef, useState } from "react";

import {
  openPropostaComercialPdf,
  previewPropostaComercialPdf,
} from "../api/propostasComerciaisApi";
import type { PropostaComercialPdfExportOverrides } from "../types/propostasComerciais";

type UsePropostaComercialPdfResult = {
  exportModalOpen: boolean;
  loading: boolean;
  error: string | null;
  previewUrl: string | null;
  openExportModal: () => void;
  closeExportModal: () => void;
  clearPreview: () => void;
  previewPdf: (overrides: PropostaComercialPdfExportOverrides) => Promise<void>;
  exportPdf: (overrides: PropostaComercialPdfExportOverrides) => Promise<void>;
  clearError: () => void;
};

export function usePropostaComercialPdf(propostaInterna: string): UsePropostaComercialPdfResult {
  const [exportModalOpen, setExportModalOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const previewUrlRef = useRef<string | null>(null);

  const revokePreviewUrl = useCallback(() => {
    if (previewUrlRef.current) {
      window.URL.revokeObjectURL(previewUrlRef.current);
      previewUrlRef.current = null;
    }
    setPreviewUrl(null);
  }, []);

  useEffect(() => {
    return () => {
      if (previewUrlRef.current) {
        window.URL.revokeObjectURL(previewUrlRef.current);
      }
    };
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const openExportModal = useCallback(() => {
    setError(null);
    revokePreviewUrl();
    setExportModalOpen(true);
  }, [revokePreviewUrl]);

  const closeExportModal = useCallback(() => {
    setExportModalOpen(false);
    setError(null);
    revokePreviewUrl();
  }, [revokePreviewUrl]);

  const clearPreview = useCallback(() => {
    revokePreviewUrl();
  }, [revokePreviewUrl]);

  const previewPdf = useCallback(
    async (overrides: PropostaComercialPdfExportOverrides) => {
      try {
        setLoading(true);
        setError(null);
        revokePreviewUrl();
        const { objectUrl } = await previewPropostaComercialPdf(propostaInterna, overrides);
        previewUrlRef.current = objectUrl;
        setPreviewUrl(objectUrl);
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Não foi possível gerar a pré-visualização do PDF.";
        setError(message);
      } finally {
        setLoading(false);
      }
    },
    [propostaInterna, revokePreviewUrl],
  );

  const exportPdf = useCallback(
    async (overrides: PropostaComercialPdfExportOverrides) => {
      try {
        setLoading(true);
        setError(null);
        await openPropostaComercialPdf(propostaInterna, overrides);
        setExportModalOpen(false);
        revokePreviewUrl();
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Não foi possível gerar o PDF da proposta.";
        setError(message);
      } finally {
        setLoading(false);
      }
    },
    [propostaInterna, revokePreviewUrl],
  );

  return {
    exportModalOpen,
    loading,
    error,
    previewUrl,
    openExportModal,
    closeExportModal,
    clearPreview,
    previewPdf,
    exportPdf,
    clearError,
  };
}
