import type {
  AssistantContextualHighlight,
  AssistantOnboardingPayload,
} from "../data/api/chatTypes";

const CACHE_PREFIX = "minha-delpi-chat:home-catalog:";

export type HomeCatalogCache = {
  onboarding: AssistantOnboardingPayload | null;
  highlights: AssistantContextualHighlight[];
};

function cacheKey(profileId: string | null | undefined): string {
  return `${CACHE_PREFIX}${profileId?.trim() || "default"}`;
}

export function readHomeCatalogCache(
  profileId: string | null | undefined,
): HomeCatalogCache | null {
  if (typeof sessionStorage === "undefined") {
    return null;
  }

  try {
    const raw = sessionStorage.getItem(cacheKey(profileId));

    if (!raw) {
      return null;
    }

    return JSON.parse(raw) as HomeCatalogCache;
  } catch {
    return null;
  }
}

export function writeHomeCatalogCache(
  profileId: string | null | undefined,
  payload: HomeCatalogCache,
): void {
  if (typeof sessionStorage === "undefined") {
    return;
  }

  try {
    sessionStorage.setItem(cacheKey(profileId), JSON.stringify(payload));
  } catch {
    /* ignore quota / privacy mode */
  }
}

export function readStoredOnboardingProfileId(): string | null {
  try {
    return localStorage.getItem("minha-delpi-chat:onboarding-profile");
  } catch {
    return null;
  }
}
