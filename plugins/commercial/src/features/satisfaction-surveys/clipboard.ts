export type CopyPayload = { text: string; html?: string };

/**
 * Copia texto (e HTML rico, quando suportado) para a área de transferência.
 * Retorna `true` somente quando o navegador ACEITOU a escrita; `false` permite
 * oferecer cópia manual. Nunca finge sucesso.
 */
export async function copyToClipboard(payload: CopyPayload): Promise<boolean> {
  if (typeof navigator === "undefined" || !navigator.clipboard) return false;
  const ClipboardItemCtor =
    typeof window !== "undefined"
      ? (window as unknown as { ClipboardItem?: typeof ClipboardItem }).ClipboardItem
      : undefined;
  if (payload.html && ClipboardItemCtor && navigator.clipboard.write) {
    try {
      await navigator.clipboard.write([
        new ClipboardItemCtor({
          "text/html": new Blob([payload.html], { type: "text/html" }),
          "text/plain": new Blob([payload.text], { type: "text/plain" }),
        }),
      ]);
      return true;
    } catch {
      // Cai para texto simples: o navegador pode recusar text/html.
    }
  }
  try {
    await navigator.clipboard.writeText(payload.text);
    return true;
  } catch {
    return false;
  }
}
