import { useEffect, useState } from "react";

import { fetchMyPersonProfilePhotoBlob } from "../data/api/directoryUsersApi";

/** Blob URL da foto do usuário autenticado (core person-profile). */
export function useMyPersonProfilePhotoUrl(
  enabled: boolean,
  getAccessToken?: () => string | undefined,
): string | null {
  const [url, setUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!enabled) {
      setUrl(null);
      return;
    }
    const controller = new AbortController();
    let objectUrl: string | null = null;
    void fetchMyPersonProfilePhotoBlob(getAccessToken, controller.signal)
      .then((blob) => {
        if (controller.signal.aborted || !blob) return;
        objectUrl = URL.createObjectURL(blob);
        setUrl(objectUrl);
      })
      .catch(() => {
        if (!controller.signal.aborted) setUrl(null);
      });
    return () => {
      controller.abort();
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [enabled, getAccessToken]);

  return url;
}
