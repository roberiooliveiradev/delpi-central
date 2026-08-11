export const CODIGO_ETICA_PUBLIC_PATH = "/p/codigo-etica/codigo/aberto";

export function resolveCodigoEticaPublicUrl(origin?: string): string {
  const base = (
    origin ?? (typeof window !== "undefined" ? window.location.origin : "")
  ).replace(/\/+$/, "");
  return `${base}${CODIGO_ETICA_PUBLIC_PATH}`;
}
