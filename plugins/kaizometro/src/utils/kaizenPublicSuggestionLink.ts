/** Path canônico do formulário público (public-hub). */
export const KAIZEN_PUBLIC_SUGGESTION_PATH = "/p/kaizen/sugestao/aberto";

export const KAIZEN_QR_DISPLAY_SIZE = 240;
export const KAIZEN_QR_EXPORT_SIZE = 512;
export const KAIZEN_QR_PNG_FILENAME = "kaizen-formulario-sugestao.png";

export type PublicSuggestionLinkOptions = {
  origin?: string;
  /** Código TOTVS da unidade (`01` | `02`). Obrigatório para link amarrado. */
  branchCode?: string;
};

export function resolveKaizenPublicSuggestionUrl(
  options: PublicSuggestionLinkOptions | string = {},
): string {
  // Compat: chamada antiga com origin string
  const opts: PublicSuggestionLinkOptions =
    typeof options === "string" ? { origin: options } : options;
  const base = (
    opts.origin ?? (typeof window !== "undefined" ? window.location.origin : "")
  ).replace(/\/+$/, "");
  const url = `${base}${KAIZEN_PUBLIC_SUGGESTION_PATH}`;
  const code = (opts.branchCode || "").trim();
  if (code === "01" || code === "02") {
    return `${url}?unidade=${encodeURIComponent(code)}`;
  }
  return url;
}

/** QR via serviço público (sem dependência npm extra no MFE). */
export function kaizenSuggestionQrImageUrl(url: string, size = KAIZEN_QR_DISPLAY_SIZE): string {
  const params = new URLSearchParams({
    size: `${size}x${size}`,
    data: url,
    margin: "12",
    format: "png",
  });
  return `https://api.qrserver.com/v1/create-qr-code/?${params.toString()}`;
}

function triggerBlobDownload(blob: Blob, filename: string): void {
  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = objectUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(objectUrl);
}

/** Baixa o QR do link público como PNG (resolução de exportação). */
export async function downloadKaizenSuggestionQrPng(
  suggestionUrl: string,
  filename = KAIZEN_QR_PNG_FILENAME,
): Promise<void> {
  const qrUrl = kaizenSuggestionQrImageUrl(suggestionUrl, KAIZEN_QR_EXPORT_SIZE);
  const response = await fetch(qrUrl);
  if (!response.ok) {
    throw new Error("Não foi possível gerar o PNG do QR code.");
  }
  const blob = await response.blob();
  if (!blob.type.startsWith("image/") && blob.size < 64) {
    throw new Error("Resposta inválida ao gerar o QR code.");
  }
  triggerBlobDownload(blob, filename);
}
