import { useCallback, useEffect, useState } from "react";
import { ArrowLeft } from "lucide-react";

import { getPreviewPayload, type PresentationPayload } from "../api/tvDashboardApi";
import { PresentationPreview } from "../presentation/PresentationPreview";
import { playlistPath } from "../routing";
import { readPlaylistShell } from "../utils/editorSessionCache";
import { overlayLiveCustomMessageSlidesOnPreviewPayload } from "../utils/overlayLivePreviewPayload";
import {
  clearPreviewPayloadCache,
  peekPreviewPayloadCache,
  rememberPreviewPayloadCache,
} from "../utils/previewPayloadCache";

type Props = {
  playlistId: string;
  onBack: () => void;
};

export {
  clearPreviewPayloadCache,
  peekPreviewPayloadCache,
  rememberPreviewPayloadCache,
} from "../utils/previewPayloadCache";

function withLiveOverlay(playlistId: string, payload: PresentationPayload): PresentationPayload {
  return overlayLiveCustomMessageSlidesOnPreviewPayload(payload, readPlaylistShell(playlistId));
}

export function PlaylistPreviewPage({ playlistId, onBack }: Props) {
  const [payload, setPayload] = useState<PresentationPayload | null>(() => {
    const cached = peekPreviewPayloadCache(playlistId);
    return cached ? withLiveOverlay(playlistId, cached) : null;
  });
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const next = withLiveOverlay(playlistId, await getPreviewPayload(playlistId));
      rememberPreviewPayloadCache(playlistId, next);
      setPayload(next);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar preview.");
    }
  }, [playlistId]);

  useEffect(() => {
    const cached = peekPreviewPayloadCache(playlistId);
    setPayload(cached ? withLiveOverlay(playlistId, cached) : null);
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
          onRefresh={async (filters) =>
            withLiveOverlay(playlistId, await getPreviewPayload(playlistId, filters))
          }
        />
      ) : null}
    </div>
  );
}

export function editorPathForPreview(playlistId: string) {
  return playlistPath(playlistId);
}
