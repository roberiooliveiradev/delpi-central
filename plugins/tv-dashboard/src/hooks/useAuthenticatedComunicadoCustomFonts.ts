import {
  useComunicadoCustomFonts,
  type ComunicadoCustomFontRef,
} from "@delpi/tv-dashboard-presentation";
import { useEffect, useState } from "react";

import { httpGetBlob } from "../api/httpClient";

/** Converte URLs protegidas em blob URLs antes de registrar os @font-face no editor. */
export function useAuthenticatedComunicadoCustomFonts(
  fonts: readonly ComunicadoCustomFontRef[] | undefined,
): void {
  const [resolved, setResolved] = useState<ComunicadoCustomFontRef[]>([]);

  useEffect(() => {
    let cancelled = false;
    const objectUrls: string[] = [];
    void Promise.all(
      (fonts ?? []).map(async (font) => {
        if (!font.url) return font;
        const blob = await httpGetBlob(font.url);
        const url = URL.createObjectURL(blob);
        if (cancelled) {
          URL.revokeObjectURL(url);
          return font;
        }
        objectUrls.push(url);
        return { ...font, url };
      }),
    )
      .then((loaded) => {
        if (!cancelled) setResolved(loaded);
      })
      .catch(() => {
        if (!cancelled) setResolved([]);
      });

    return () => {
      cancelled = true;
      objectUrls.forEach((url) => URL.revokeObjectURL(url));
    };
  }, [fonts]);

  useComunicadoCustomFonts(resolved);
}
