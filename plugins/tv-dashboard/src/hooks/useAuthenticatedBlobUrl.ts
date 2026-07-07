import { useEffect, useState } from "react";

import { httpGetBlob } from "../api/httpClient";

/** Carrega mídia protegida da API e expõe object URL para `<img>` / `<video>`. */
export function useAuthenticatedBlobUrl(apiUrl: string | undefined): {
  src: string | undefined;
  loading: boolean;
  error: boolean;
} {
  const [src, setSrc] = useState<string | undefined>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!apiUrl) {
      setSrc(undefined);
      setLoading(false);
      setError(false);
      return;
    }

    let cancelled = false;
    let objectUrl: string | undefined;
    setLoading(true);
    setError(false);
    setSrc(undefined);

    void httpGetBlob(apiUrl)
      .then((blob) => {
        if (cancelled) return;
        objectUrl = URL.createObjectURL(blob);
        setSrc(objectUrl);
        setLoading(false);
      })
      .catch(() => {
        if (cancelled) return;
        setError(true);
        setLoading(false);
      });

    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [apiUrl]);

  return { src, loading, error };
}
