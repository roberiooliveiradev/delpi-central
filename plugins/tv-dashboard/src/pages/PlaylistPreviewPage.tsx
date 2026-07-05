import { useCallback, useEffect, useState } from "react";
import { ArrowLeft } from "lucide-react";

import { getPreviewPayload, type PresentationPayload } from "../api/tvDashboardApi";
import { PresentationPreview } from "../presentation/PresentationPreview";
import { playlistPath } from "../routing";

type Props = {
  playlistId: string;
  onBack: () => void;
};

export function PlaylistPreviewPage({ playlistId, onBack }: Props) {
  const [payload, setPayload] = useState<PresentationPayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      setPayload(await getPreviewPayload(playlistId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar preview.");
    }
  }, [playlistId]);

  useEffect(() => {
    void load();
  }, [load]);

  if (error) {
    return (
      <div className="td-state">
        {error}
        <button type="button" className="td-btn" onClick={onBack}>
          Voltar
        </button>
      </div>
    );
  }

  if (!payload) return <div className="td-state">Carregando preview…</div>;

  return (
    <div className="td-preview-page">
      <button type="button" className="td-btn td-preview-page__back" onClick={onBack}>
        <ArrowLeft size={16} />
        Voltar ao editor
      </button>
      <PresentationPreview
        payload={payload}
        playlistId={playlistId}
        onRefresh={() => getPreviewPayload(playlistId)}
      />
    </div>
  );
}

export function editorPathForPreview(playlistId: string) {
  return playlistPath(playlistId);
}
