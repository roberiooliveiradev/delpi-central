import { useCallback, useEffect, useRef, useState } from "react";

import { listPlaylistMedia, type MediaAsset } from "../../api/tvDashboardApi";
import type { EditorVideoPosterAssets } from "../../components/slideCardPreview";

/**
 * Metadado `hasPoster` dos vídeos da programação para hidratar `posterUrl` no editor.
 *
 * Carrega a biblioteca de vídeos uma vez por playlist; assets aplicados no editor
 * (upload, biblioteca, drop) são registrados para sobreviver a undo/reconstrução.
 */
export function useEditorVideoPosterAssets(playlistId: string) {
  const [posterAssets, setPosterAssets] = useState<EditorVideoPosterAssets>(null);
  const posterAssetsRef = useRef<EditorVideoPosterAssets>(null);
  const registeredRef = useRef(new Map<string, boolean>());

  const commit = useCallback((next: EditorVideoPosterAssets) => {
    posterAssetsRef.current = next;
    setPosterAssets(next);
  }, []);

  useEffect(() => {
    if (!playlistId) return;
    let cancelled = false;
    listPlaylistMedia(playlistId, "video")
      .then((items) => {
        if (cancelled) return;
        const next = new Set(items.filter((asset) => asset.hasPoster).map((asset) => asset.id));
        for (const [assetId, hasPoster] of registeredRef.current) {
          if (hasPoster) next.add(assetId);
          else next.delete(assetId);
        }
        commit(next);
      })
      .catch(() => {
        // Poster is optional: unknown metadata keeps posterUrl unsynthesized.
      });
    return () => {
      cancelled = true;
      registeredRef.current = new Map();
      commit(null);
    };
  }, [commit, playlistId]);

  const registerMediaAsset = useCallback(
    (asset: MediaAsset) => {
      if (asset.mediaKind !== "video") return;
      const hasPoster = Boolean(asset.hasPoster);
      registeredRef.current.set(asset.id, hasPoster);
      const current = posterAssetsRef.current;
      if (!current || current.has(asset.id) === hasPoster) return;
      const next = new Set(current);
      if (hasPoster) next.add(asset.id);
      else next.delete(asset.id);
      commit(next);
    },
    [commit],
  );

  return { posterAssets, posterAssetsRef, registerMediaAsset };
}
