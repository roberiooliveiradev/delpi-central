import {
  serializeInputFilterOverridesQuery,
  type InputFilterContributions,
} from "@delpi/tv-dashboard-presentation";

const API_BASE = "/apps/tv-dashboard-api";

export type PublicSlideNative = {
  screenKey: string;
  config: Record<string, unknown>;
  data: Record<string, unknown>;
};

export type PublicSlide = {
  id: string;
  sortOrder: number;
  slideType: "native" | "external";
  durationSec: number;
  title: string;
  sectionId?: string | null;
  transitionStyle?: string | null;
  native?: PublicSlideNative;
  external?: { url: string; sandbox?: string | null };
};

export type PublicPresentationSection = {
  id: string;
  name: string;
  sortOrder: number;
  isActive?: boolean;
};

export type PublicPresentationPayload = {
  playlist: {
    id: string;
    name: string;
    description?: string | null;
    viewportProfile: string;
    viewportWidth?: number | null;
    viewportHeight?: number | null;
    transitionStyle: string;
    globalRefreshSec: number;
    defaultDurationSec: number;
    playbackMode?: "presentation" | "meeting";
    publicUrl?: string;
  };
  presentationMeta?: {
    nativeErrorAdvanceSec: number;
    heartbeatIntervalSec: number;
  };
  sections?: PublicPresentationSection[];
  slides: PublicSlide[];
};

export type PublicFilterOverrides = InputFilterContributions;

type ApiEnvelope<T> = { success: boolean; message?: string; data: T };

function presentUrl(
  token: string,
  filters?: PublicFilterOverrides | null,
  cacheBust?: string | null,
): string {
  const url = new URL(
    `${API_BASE}/public/present/${encodeURIComponent(token)}`,
    typeof window !== "undefined" ? window.location.origin : "http://localhost",
  );
  const query = filters ? serializeInputFilterOverridesQuery(filters) : null;
  if (query) {
    url.searchParams.set("filters", query);
  }
  if (cacheBust) {
    url.searchParams.set("_rev", cacheBust);
  }
  return `${url.pathname}${url.search}`;
}

export async function fetchPublicPresentation(
  token: string,
  filters?: PublicFilterOverrides | null,
  options?: { cacheBust?: string | null; cache?: RequestCache },
): Promise<PublicPresentationPayload | null> {
  const res = await fetch(presentUrl(token, filters, options?.cacheBust), {
    headers: { Accept: "application/json" },
    cache: options?.cache ?? "default",
  });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error("Não foi possível carregar a apresentação.");
  const env = (await res.json()) as ApiEnvelope<PublicPresentationPayload>;
  if (env.success === false || !env.data || !Array.isArray(env.data.slides)) return null;
  return env.data;
}

export async function refreshPublicPresentation(
  token: string,
  filters?: PublicFilterOverrides | null,
  revision?: string | null,
): Promise<PublicPresentationPayload | null> {
  return fetchPublicPresentation(token, filters, {
    cacheBust: revision ?? String(Date.now()),
    cache: "no-store",
  });
}

export async function sendPresentationHeartbeat(token: string): Promise<void> {
  await fetch(`${API_BASE}/public/present/${encodeURIComponent(token)}/heartbeat`, {
    method: "POST",
    headers: { Accept: "application/json" },
  });
}
