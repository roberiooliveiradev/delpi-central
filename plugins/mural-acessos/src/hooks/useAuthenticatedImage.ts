import { useEffect, useState } from "react";

import { fetchAuthenticatedImage } from "../api/muralAcessosApi";

export function useAuthenticatedImage(imageUrl: string | null): string | null {
  const [objectUrl, setObjectUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!imageUrl) {
      setObjectUrl(null);
      return;
    }

    let revoked = false;
    let created: string | null = null;

    void fetchAuthenticatedImage(imageUrl)
      .then((url) => {
        if (revoked) {
          URL.revokeObjectURL(url);
          return;
        }
        created = url;
        setObjectUrl(url);
      })
      .catch(() => {
        if (!revoked) setObjectUrl(null);
      });

    return () => {
      revoked = true;
      if (created) URL.revokeObjectURL(created);
    };
  }, [imageUrl]);

  return objectUrl;
}
