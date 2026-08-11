export const CANAL_DENUNCIA_PUBLIC_PATH = "/p/canal-denuncia/denuncia/aberto";

export function resolveCanalDenunciaPublicUrl(origin?: string): string {
  const base = (
    origin ?? (typeof window !== "undefined" ? window.location.origin : "")
  ).replace(/\/+$/, "");
  return `${base}${CANAL_DENUNCIA_PUBLIC_PATH}`;
}
