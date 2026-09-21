import { formatPortalGreeting } from "@delpi/plugin-ui/index";
import { useEffect, useState } from "react";

import { PORTAL_WELCOME } from "../../constants/portalExperience";
import { fetchMeProfile, greetingFirstNameFromProfile } from "../../data/api/meApi";

export function usePortalGreeting(getAccessToken?: () => string | undefined): string {
  const [firstName, setFirstName] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    void fetchMeProfile(getAccessToken, controller.signal)
      .then((profile) => {
        setFirstName(greetingFirstNameFromProfile(profile));
      })
      .catch(() => {
        if (!controller.signal.aborted) setFirstName(null);
      });
    return () => controller.abort();
  }, [getAccessToken]);

  return formatPortalGreeting({
    firstName,
    fallback: PORTAL_WELCOME,
  });
}
