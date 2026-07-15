/** Path canônico do formulário público (public-hub). */
export const KAIZEN_PUBLIC_SUGGESTION_PATH = "/p/kaizen/sugestao/aberto";

export function resolveKaizenPublicSuggestionUrl(origin?: string): string {
  const base = (origin ?? (typeof window !== "undefined" ? window.location.origin : "")).replace(
    /\/+$/,
    "",
  );
  return `${base}${KAIZEN_PUBLIC_SUGGESTION_PATH}`;
}

/** QR via serviço público (sem dependência npm extra no MFE). */
export function kaizenSuggestionQrImageUrl(url: string, size = 240): string {
  const params = new URLSearchParams({
    size: `${size}x${size}`,
    data: url,
  });
  return `https://api.qrserver.com/v1/create-qr-code/?${params.toString()}`;
}
