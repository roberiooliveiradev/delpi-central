import { useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { AuthContext } from "../../state/AuthContext";
import { ApiClient } from "../../data/apiClient";
import { CoreApi } from "../../data/coreApi";

/**
 * Loads the authenticated user's person-profile photo as an object URL.
 * Returns null when there is no photo or on error.
 */
export function useMyPersonProfilePhotoUrl() {
  const { getAccessToken, refreshToken } = useContext(AuthContext);
  const [photoUrl, setPhotoUrl] = useState<string | null>(null);
  const [hasPhoto, setHasPhoto] = useState(false);
  const objectUrlRef = useRef<string | null>(null);

  const coreApi = useMemo(
    () =>
      new CoreApi(
        new ApiClient("", getAccessToken, {
          refreshToken: async () => {
            await refreshToken();
            return Boolean(getAccessToken());
          },
        }),
      ),
    [getAccessToken, refreshToken],
  );

  const revokeCurrent = useCallback(() => {
    if (objectUrlRef.current) {
      URL.revokeObjectURL(objectUrlRef.current);
      objectUrlRef.current = null;
    }
  }, []);

  const reload = useCallback(async () => {
    try {
      const profile = await coreApi.getMyPersonProfile();
      const nextHasPhoto = Boolean(profile.has_photo);
      setHasPhoto(nextHasPhoto);
      if (!nextHasPhoto) {
        revokeCurrent();
        setPhotoUrl(null);
        return;
      }
      const blob = await coreApi.getMyPersonProfilePhotoBlob();
      revokeCurrent();
      const url = URL.createObjectURL(blob);
      objectUrlRef.current = url;
      setPhotoUrl(url);
    } catch {
      revokeCurrent();
      setHasPhoto(false);
      setPhotoUrl(null);
    }
  }, [coreApi, revokeCurrent]);

  useEffect(() => {
    void reload();
    return () => {
      revokeCurrent();
    };
  }, [reload, revokeCurrent]);

  return { photoUrl, hasPhoto, reload };
}
