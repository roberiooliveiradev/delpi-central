import { useEffect, useState } from "react";

import { acquireAuthenticatedBlobUrl, fetchAuthenticatedBlobUrl } from "./authenticatedBlobUrlCache";

/** Carrega mídia protegida da API e expõe object URL para `<img>` / `<video>`. */
export function useAuthenticatedBlobUrl(apiUrl: string | undefined): {
  src: string | undefined;
  loading: boolean;
  error: boolean;
} {
  const [src, setSrc] = useState<string | undefined>();
  const [loading, setLoading] = useState(() => Boolean(apiUrl));
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!apiUrl) {
      setSrc(undefined);
      setLoading(false);
      setError(false);
      return;
    }

    let cancelled = false;
    const reserved = acquireAuthenticatedBlobUrl(apiUrl);

    if (reserved.blobUrl) {
      setSrc(reserved.blobUrl);
      setLoading(false);
      setError(false);
      return () => {
        cancelled = true;
        reserved.release();
      };
    }

    setLoading(true);
    setError(false);
    setSrc(undefined);

    void fetchAuthenticatedBlobUrl(apiUrl)
      .then((blobUrl) => {
        if (cancelled) return;
        setSrc(blobUrl);
        setLoading(false);
      })
      .catch(() => {
        if (cancelled) return;
        setError(true);
        setLoading(false);
      });

    return () => {
      cancelled = true;
      reserved.release();
    };
  }, [apiUrl]);

  return { src, loading, error };
}
