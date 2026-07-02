const API_BASE = "/apps/api-delpi";

export type PublicInspection = {
  productCode: string;
  productDescription: string;
  productUnit: string | null;
  productionOrder: string;
  branch: string | null;
  branchName: string | null;
  inspectedAt: string | null;
  inspectorName: string;
  result: string;
  companyName: string;
};

type ApiEnvelope<T> = {
  success: boolean;
  message?: string;
  data: T;
};

export async function fetchPublicInspection(token: string): Promise<PublicInspection | null> {
  const response = await fetch(
    `${API_BASE}/public/quality-labels/inspection/${encodeURIComponent(token)}`,
    { headers: { Accept: "application/json" } },
  );
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new Error("Não foi possível carregar a inspeção.");
  }
  const envelope = (await response.json()) as ApiEnvelope<PublicInspection>;
  if (envelope.success === false) {
    return null;
  }
  return envelope.data;
}
