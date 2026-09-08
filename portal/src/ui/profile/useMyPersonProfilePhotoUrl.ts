import { useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { AuthContext } from "../../state/AuthContext";
import { ApiClient } from "../../data/apiClient";
import { CoreApi } from "../../data/coreApi";
import { DELPI_PERSON_PROFILE_PHOTO_CHANGED_EVENT } from "./personProfilePhotoEvents";

/**
 * Loads the authenticated user's person-profile photo as an object URL.
 * Reloads when the photo is changed elsewhere in the portal (profile editor).
 */
export function useMyPersonProfilePhotoUrl() {
  const { getAccessToken, refreshToken } = useContext(AuthContext);
  const [photoUrl, setPhotoUrl] = useState<string | null>(null);
  const [hasPhoto, setHasPhoto] = useState(false);
  const objectUrlRef = useRef<string | null>(null);
  const requestIdRef = useRef(0);

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
    const requestId = ++requestIdRef.current;
    try {
      const profile = await coreApi.getMyPersonProfile();
      if (requestId !== requestIdRef.current) return;
      const nextHasPhoto = Boolean(profile.has_photo);
      setHasPhoto(nextHasPhoto);
      if (!nextHasPhoto) {
        revokeCurrent();
        setPhotoUrl(null);
        return;
      }
      const blob = await coreApi.getMyPersonProfilePhotoBlob();
      if (requestId !== requestIdRef.current) return;
      revokeCurrent();
      const url = URL.createObjectURL(blob);
      objectUrlRef.current = url;
      setPhotoUrl(url);
    } catch {
      if (requestId !== requestIdRef.current) return;
      revokeCurrent();
      setHasPhoto(false);
      setPhotoUrl(null);
    }
  }, [coreApi, revokeCurrent]);

  useEffect(() => {
    void reload();
    return () => {
      requestIdRef.current += 1;
      revokeCurrent();
    };
  }, [reload, revokeCurrent]);

  useEffect(() => {
    const onChanged = () => {
      void reload();
    };
    window.addEventListener(DELPI_PERSON_PROFILE_PHOTO_CHANGED_EVENT, onChanged);
    return () => {
      window.removeEventListener(
        DELPI_PERSON_PROFILE_PHOTO_CHANGED_EVENT,
        onChanged,
      );
    };
  }, [reload]);

  return { photoUrl, hasPhoto, reload };
}
