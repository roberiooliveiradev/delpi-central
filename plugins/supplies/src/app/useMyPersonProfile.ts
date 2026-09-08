import { useCallback, useEffect, useRef, useState } from "react";

import {
  getMyPersonProfile,
  getMyPersonProfilePhotoBlob,
  type PersonProfile,
} from "../api/personProfileApi";
import { DELPI_PERSON_PROFILE_CHANGED_EVENT } from "./personProfileEvents";

/**
 * Loads Core person-profile (cargo/contatos + foto) for the authenticated user.
 * Reloads when the host Portal notifies photo/profile changes on `window`.
 */
export function useMyPersonProfile(enabled = true) {
  const [profile, setProfile] = useState<PersonProfile | null>(null);
  const [photoUrl, setPhotoUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(enabled);
  const objectUrlRef = useRef<string | null>(null);
  const requestIdRef = useRef(0);

  const revokeCurrent = useCallback(() => {
    if (objectUrlRef.current) {
      URL.revokeObjectURL(objectUrlRef.current);
      objectUrlRef.current = null;
    }
  }, []);

  const reload = useCallback(async () => {
    if (!enabled) {
      setProfile(null);
      revokeCurrent();
      setPhotoUrl(null);
      setLoading(false);
      return;
    }
    const requestId = ++requestIdRef.current;
    setLoading(true);
    try {
      const next = await getMyPersonProfile();
      if (requestId !== requestIdRef.current) return;
      setProfile(next);
      if (!next.has_photo) {
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
      setProfile(null);
      revokeCurrent();
      setPhotoUrl(null);
    } finally {
      if (requestId === requestIdRef.current) setLoading(false);
    }
  }, [enabled, revokeCurrent]);

  useEffect(() => {
    void reload();
    return () => {
      requestIdRef.current += 1;
      revokeCurrent();
    };
  }, [reload, revokeCurrent]);

  useEffect(() => {
    if (!enabled) return;
    const onChanged = () => {
      void reload();
    };
    window.addEventListener(DELPI_PERSON_PROFILE_CHANGED_EVENT, onChanged);
    return () => {
      window.removeEventListener(DELPI_PERSON_PROFILE_CHANGED_EVENT, onChanged);
    };
  }, [enabled, reload]);

  return {
    profile,
    photoUrl,
    hasPhoto: Boolean(photoUrl),
    loading,
    reload,
  };
}
