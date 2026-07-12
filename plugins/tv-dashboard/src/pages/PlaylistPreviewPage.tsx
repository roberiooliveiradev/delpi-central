import { useCallback, useEffect, useState } from "react";
import { ArrowLeft } from "lucide-react";

import { getPreviewPayload, type PresentationPayload } from "../api/tvDashboardApi";
import { PresentationPreview } from "../presentation/PresentationPreview";
import { playlistPath } from "../routing";

type Props = {
  playlistId: string;
  onBack: () => void;
};

/** Cache de sessão: reabrir prévia não mostra tela vazia «Carregando…». */
const previewPayloadCache = new Map<string, PresentationPayload>();

export function peekPreviewPayloadCache(playlistId: string): PresentationPayload | null {
  return previewPayloadCache.get(playlistId) ?? null;
}

export function rememberPreviewPayloadCache(playlistId: string, payload: PresentationPayload): void {
  previewPayloadCache.set(playlistId, payload);
}

export function clearPreviewPayloadCache(playlistId?: string): void {
  if (playlistId) previewPayloadCache.delete(playlistId);
  else previewPayloadCache.clear();
}

export function PlaylistPreviewPage({ playlistId, onBack }: Props) {
  const [payload, setPayload] = useState<PresentationPayload | null>(
    () => peekPreviewPayloadCache(playlistId),
  );
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const next = await getPreviewPayload(playlistId);
      rememberPreviewPayloadCache(playlistId, next);
      setPayload(next);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar preview.");
    }
  }, [playlistId]);

  useEffect(() => {
    // Troca de playlist: usa cache da nova id (sem apagar a tela se já houver).
    setPayload(peekPreviewPayloadCache(playlistId));
    setError(null);
    void load();
  }, [playlistId, load]);

  return (
    <div className="td-preview-page">
      <button type="button" className="td-btn td-preview-page__back" onClick={onBack}>
        <ArrowLeft size={16} />
        Voltar ao editor
      </button>
      {error ? (
        <div className="td-state td-preview-page__status">
          {error}
          <button type="button" className="td-btn" onClick={onBack}>
            Voltar
          </button>
        </div>
      ) : null}
      {!payload && !error ? (
        <div className="td-state td-preview-page__status" role="status">
          Carregando preview…
        </div>
      ) : null}
      {payload ? (
        <PresentationPreview
          key={playlistId}
          payload={payload}
          playlistId={playlistId}
          onRefresh={() => getPreviewPayload(playlistId)}
        />
      ) : null}
    </div>
  );
}

export function editorPathForPreview(playlistId: string) {
  return playlistPath(playlistId);
}
