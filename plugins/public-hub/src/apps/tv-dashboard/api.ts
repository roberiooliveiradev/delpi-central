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
  slides: PublicSlide[];
};

type ApiEnvelope<T> = { success: boolean; message?: string; data: T };

export async function fetchPublicPresentation(
  token: string,
): Promise<PublicPresentationPayload | null> {
  const res = await fetch(`${API_BASE}/public/present/${encodeURIComponent(token)}`, {
    headers: { Accept: "application/json" },
  });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error("Não foi possível carregar a apresentação.");
  const env = (await res.json()) as ApiEnvelope<PublicPresentationPayload>;
  return env.success === false ? null : env.data;
}

export async function refreshPublicPresentation(
  token: string,
): Promise<PublicPresentationPayload | null> {
  return fetchPublicPresentation(token);
}
