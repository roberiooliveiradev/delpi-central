import type { ComunicadoCustomFontRef } from "@delpi/tv-dashboard-presentation";
import { useEffect, useState } from "react";

import { isAdminProtectedMediaUrl } from "../api/browserSafeMediaUrl";
import { httpGetBlob } from "../api/httpClient";

/**
 * Converte URLs protegidas em blob URLs — sem registrar @font-face.
 * O palco canônico (`RichComunicadoStage.customFonts`) registra pelo owner.
 * URLs públicas passam intactas (o fetch autenticado vazaria o Bearer).
 */
export function useResolvedAuthenticatedComunicadoCustomFonts(
  fonts: readonly ComunicadoCustomFontRef[] | undefined,
): ComunicadoCustomFontRef[] {
  const [blobUrlByOriginal, setBlobUrlByOriginal] = useState<Record<string, string>>({});

  useEffect(() => {
    const protectedFonts = (fonts ?? []).filter(
      (font) => font.url && isAdminProtectedMediaUrl(font.url),
    );
    if (protectedFonts.length === 0) {
      setBlobUrlByOriginal({});
      return;
    }
    let cancelled = false;
    const objectUrls: string[] = [];
    void Promise.all(
      protectedFonts.map(async (font) => {
        const originalUrl = font.url as string;
        const blob = await httpGetBlob(originalUrl);
        const blobUrl = URL.createObjectURL(blob);
        if (cancelled) {
          URL.revokeObjectURL(blobUrl);
          return null;
        }
        objectUrls.push(blobUrl);
        return [originalUrl, blobUrl] as const;
      }),
    )
      .then((entries) => {
        if (cancelled) return;
        setBlobUrlByOriginal(
          Object.fromEntries(entries.filter((entry): entry is readonly [string, string] => entry != null)),
        );
      })
      .catch(() => {
        if (!cancelled) setBlobUrlByOriginal({});
      });

    return () => {
      cancelled = true;
      objectUrls.forEach((url) => URL.revokeObjectURL(url));
    };
  }, [fonts]);

  return (fonts ?? []).map((font) =>
    font.url && blobUrlByOriginal[font.url]
      ? { ...font, url: blobUrlByOriginal[font.url] }
      : font,
  );
}

