const API_BASE = "/apps/api-delpi";

type ApiEnvelope<T> = {
  success: boolean;
  message?: string;
  data: T;
};

export type PublicMuralItem = {
  id: string;
  title: string;
  url: string;
  description: string;
  orderIndex: number;
  hasImage: boolean;
  imageUrl: string | null;
};

export type PublicMuralMenu = {
  id?: string;
  title: string;
  subtitle: string;
  publicToken?: string;
  items: PublicMuralItem[];
};

export async function fetchPublicMuralMenu(token: string): Promise<PublicMuralMenu | null> {
  const response = await fetch(
    `${API_BASE}/public/mural-acessos/menu/${encodeURIComponent(token)}`,
    { headers: { Accept: "application/json" } },
  );
  if (response.status === 404) return null;
  if (!response.ok) {
    throw new Error("Não foi possível carregar o mural.");
  }
  const envelope = (await response.json()) as ApiEnvelope<PublicMuralMenu>;
  return envelope.success === false ? null : envelope.data;
}
