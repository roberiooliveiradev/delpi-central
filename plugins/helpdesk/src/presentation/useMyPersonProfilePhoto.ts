import { useCallback, useEffect, useRef, useState } from "react";

import {
  getMyPersonProfile,
  getMyPersonProfilePhotoBlob,
} from "../api/personProfileApi";
import {
  DELPI_PERSON_PROFILE_CHANGED_EVENT,
  DELPI_PERSON_PROFILE_PHOTO_CHANGED_EVENT,
} from "../api/personProfileEvents";

/** Foto do usuário autenticado na Minha DELPI (Core person-profile). */
export function useMyPersonProfilePhoto() {
  const [photoUrl, setPhotoUrl] = useState<string | null>(null);
  const objectUrlRef = useRef<string | null>(null);
  const requestIdRef = useRef(0);

  const revokeCurrent = useCallback(() => {
    if (objectUrlRef.current) {
      URL.revokeObjectURL(objectUrlRef.current);
      objectUrlRef.current = null;
    }
  }, []);

  const reload = useCallback(async () => {
    const requestId = ++requestIdRef.current;
    try {
      const profile = await getMyPersonProfile();
      if (requestId !== requestIdRef.current) return;
      if (!profile.has_photo) {
        revokeCurrent();
        setPhotoUrl(null);
        return;
      }
      const blob = await getMyPersonProfilePhotoBlob();
      if (requestId !== requestIdRef.current) return;
      revokeCurrent();
      const url = URL.createObjectURL(blob);
      objectUrlRef.current = url;
      setPhotoUrl(url);
    } catch {
      if (requestId !== requestIdRef.current) return;
      revokeCurrent();
      setPhotoUrl(null);
    }
  }, [revokeCurrent]);

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
    window.addEventListener(DELPI_PERSON_PROFILE_CHANGED_EVENT, onChanged);
    window.addEventListener(DELPI_PERSON_PROFILE_PHOTO_CHANGED_EVENT, onChanged);
    return () => {
      window.removeEventListener(DELPI_PERSON_PROFILE_CHANGED_EVENT, onChanged);
      window.removeEventListener(DELPI_PERSON_PROFILE_PHOTO_CHANGED_EVENT, onChanged);
    };
  }, [reload]);

  return photoUrl;
}
