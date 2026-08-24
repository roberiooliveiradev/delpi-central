/** Link público do mapa de entrega servido pelo public-hub (`/p/{app}/{page}/{token}`). */
export const DELIVERY_MAP_PUBLIC_TOKEN = "aberto";

export function buildDeliveryMapPublicUrl(
  branch: string,
  options?: { origin?: string; search?: string | null },
): string {
  const base = (options?.origin ?? window.location.origin).replace(/\/$/, "");
  const params = new URLSearchParams({ branch });
  const search = options?.search?.trim();
  if (search) params.set("q", search);
  return `${base}/p/production-control/delivery-map/${DELIVERY_MAP_PUBLIC_TOKEN}?${params}`;
}

export { copyText } from "./operatorCockpitLink";
