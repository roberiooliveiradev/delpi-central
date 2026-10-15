import { useEffect, useRef, useState } from "react";

/**
 * Current-user identity for presentation only (avatar + initials).
 *
 * REUSE of the platform-proven contract — the same Core endpoints are
 * already consumed by sibling MFEs (e.g. plugins/supplies):
 *
 *   GET /core-api/me                    → { name }
 *   GET /core-api/me/person-profile     → { has_photo }
 *   GET /core-api/me/person-profile/photo → image blob → object URL
 *
 * Owner of the data is core-api — DÉLIA is a presentation consumer
 * only. The bearer token comes from the Portal host prop and is never
 * stored or logged. Identity data is never persisted, never treated
 * as authorization, and absence of data degrades to a neutral avatar.
 */

export type DeliaCurrentUserIdentity = {
  displayName: string | null;
  imageUrl: string | null;
};

/** Cross-MFE host event reused verbatim — the Portal dispatches it
 *  when the profile photo changes elsewhere in the shell. */
export const DELPI_PERSON_PROFILE_CHANGED_EVENT =
  "DELPI_PERSON_PROFILE_CHANGED";

const ME_PATH = "/core-api/me";
const PERSON_PROFILE_PATH = "/core-api/me/person-profile";
const PERSON_PROFILE_PHOTO_PATH = "/core-api/me/person-profile/photo";

async function authedGet(
  getAccessToken: () => string | undefined,
  path: string,
  signal: AbortSignal,
): Promise<Response> {
  const token = getAccessToken();
  if (!token) throw new Error("no access token");
  const response = await fetch(path, {
    headers: { Authorization: `Bearer ${token}` },
    signal,
  });
  if (!response.ok) throw new Error(`identity read failed ${response.status}`);
  return response;
}

/**
 * Loads the current user's display name and profile photo (as an
 * object URL, revoked on cleanup). Reloads when the host broadcasts a
 * profile change. All failures are silent — identity is decorative.
 */
export function useCurrentUserIdentity(
  getAccessToken?: () => string | undefined,
): DeliaCurrentUserIdentity {
  const [identity, setIdentity] = useState<DeliaCurrentUserIdentity>({
    displayName: null,
    imageUrl: null,
  });

  // The host getter may be an unstable reference — depend on token
  // *availability* and always call the freshest getter via ref.
  const getterRef = useRef(getAccessToken);
  getterRef.current = getAccessToken;
  const tokenAvailable = Boolean(getAccessToken?.());

  useEffect(() => {
    if (!tokenAvailable) return;
    const controller = new AbortController();
    let objectUrl: string | null = null;
    let loadVersion = 0;

    async function load() {
      const version = ++loadVersion;
      const getter = getterRef.current;
      if (!getter) return;

      let nextObjectUrl: string | null = null;
      try {
        const me = (await (
          await authedGet(getter, ME_PATH, controller.signal)
        ).json()) as { name?: unknown };
        const displayName =
          typeof me.name === "string" && me.name.trim()
            ? me.name.trim()
            : null;

        let imageUrl: string | null = null;
        try {
          const profile = (await (
            await authedGet(
              getter,
              PERSON_PROFILE_PATH,
              controller.signal,
            )
          ).json()) as { has_photo?: unknown };
          if (profile.has_photo === true) {
            const blob = await (
              await authedGet(
                getter,
                PERSON_PROFILE_PHOTO_PATH,
                controller.signal,
              )
            ).blob();
            nextObjectUrl = URL.createObjectURL(blob);
            imageUrl = nextObjectUrl;
          }
        } catch {
          // Photo unavailable — initials fallback is honest.
        }

        if (controller.signal.aborted || version !== loadVersion) {
          if (nextObjectUrl) URL.revokeObjectURL(nextObjectUrl);
          return;
        }

        if (objectUrl && objectUrl !== nextObjectUrl) {
          URL.revokeObjectURL(objectUrl);
        }
        objectUrl = nextObjectUrl;
        setIdentity({ displayName, imageUrl });
      } catch {
        if (nextObjectUrl) URL.revokeObjectURL(nextObjectUrl);
        // Name unavailable — neutral avatar fallback is honest.
      }
    }

    void load();
    const onChanged = () => void load();
    window.addEventListener(
      DELPI_PERSON_PROFILE_CHANGED_EVENT,
      onChanged,
    );
    return () => {
      controller.abort();
      window.removeEventListener(
        DELPI_PERSON_PROFILE_CHANGED_EVENT,
        onChanged,
      );
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [tokenAvailable]);

  return identity;
}
