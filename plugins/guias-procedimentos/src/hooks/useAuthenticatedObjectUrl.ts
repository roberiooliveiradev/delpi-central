import { useEffect, useState } from "react";

import { downloadProtectedBlob } from "../api/guiasProcedimentosApi";
import { HttpRequestError } from "../api/httpClient";

type State = {
  objectUrl: string | null;
  loading: boolean;
  error: string | null;
};

/**
 * Baixa recurso JWT-protegido e expõe blob URL para <img>/<video>.
 */
export function useAuthenticatedObjectUrl(
  src: string | null | undefined,
  enabled = true,
): State {
  const [state, setState] = useState<State>({
    objectUrl: null,
    loading: Boolean(enabled && src),
    error: null,
  });

  useEffect(() => {
    if (!enabled || !src) {
      setState({ objectUrl: null, loading: false, error: null });
      return;
    }

    let cancelled = false;
    let objectUrl: string | null = null;
    setState({ objectUrl: null, loading: true, error: null });

    downloadProtectedBlob(src)
      .then((blob) => {
        if (cancelled) return;
        objectUrl = URL.createObjectURL(blob);
        setState({ objectUrl, loading: false, error: null });
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setState({
          objectUrl: null,
          loading: false,
          error:
            err instanceof HttpRequestError
              ? err.message
              : "Não foi possível carregar o arquivo.",
        });
      });

    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [src, enabled]);

  return state;
}
