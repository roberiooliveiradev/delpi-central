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
  transitionStyle?: string | null;
  native?: PublicSlideNative;
  external?: { url: string; sandbox?: string | null };
};

export type PublicPresentationPayload = {
  playlist: {
    id: string;
    name: string;
    description?: string | null;
    viewportProfile: string;
    transitionStyle: string;
    globalRefreshSec: number;
    defaultDurationSec: number;
    publicUrl?: string;
  };
  presentationMeta?: {
    nativeErrorAdvanceSec: number;
    heartbeatIntervalSec: number;
  };
  slides: PublicSlide[];
};

export type PublicFilterOverrides = {
  slide?: Record<string, string | number | boolean | null>;
  bySourceId?: Record<string, Record<string, string | number | boolean | null>>;
};

type ApiEnvelope<T> = { success: boolean; message?: string; data: T };

function presentUrl(token: string, filters?: PublicFilterOverrides | null): string {
  const url = new URL(
    `${API_BASE}/public/present/${encodeURIComponent(token)}`,
    typeof window !== "undefined" ? window.location.origin : "http://localhost",
  );
  if (filters) {
    const slide = filters.slide ?? {};
    const bySourceId = filters.bySourceId ?? {};
    const hasSlide = Object.keys(slide).length > 0;
    const hasBySource = Object.keys(bySourceId).length > 0;
    if (hasSlide || hasBySource) {
      url.searchParams.set("filters", JSON.stringify({ slide, bySourceId }));
    }
  }
  return `${url.pathname}${url.search}`;
}

export async function fetchPublicPresentation(
  token: string,
  filters?: PublicFilterOverrides | null,
): Promise<PublicPresentationPayload | null> {
  const res = await fetch(presentUrl(token, filters), {
    headers: { Accept: "application/json" },
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
): Promise<PublicPresentationPayload | null> {
  return fetchPublicPresentation(token, filters);
}

export async function sendPresentationHeartbeat(token: string): Promise<void> {
  await fetch(`${API_BASE}/public/present/${encodeURIComponent(token)}/heartbeat`, {
    method: "POST",
    headers: { Accept: "application/json" },
  });
}
