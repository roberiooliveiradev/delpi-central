/** SHA-256 do conteúdo do arquivo (hex), para detectar duplicatas antes do upload. */
export async function sha256HexFromFile(file: File): Promise<string> {
  const buffer = await file.arrayBuffer();
  const digest = await crypto.subtle.digest("SHA-256", buffer);

  return Array.from(new Uint8Array(digest))
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("");
}

export async function sha256HexFromText(text: string): Promise<string> {
  const encoded = new TextEncoder().encode(text);
  const digest = await crypto.subtle.digest("SHA-256", encoded);

  return Array.from(new Uint8Array(digest))
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("");
}

export function getSourceContentHash(
  metadata: Record<string, unknown> | null | undefined,
): string | null {
  const value = metadata?.contentHash;

  return typeof value === "string" && value.trim() ? value.trim() : null;
}
