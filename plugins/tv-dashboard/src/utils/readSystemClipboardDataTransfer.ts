/**
 * Lê o clipboard do SO como DataTransfer (imagens + texto).
 * Canônico para colar / Alterar imagem ▸ área de transferência.
 */
export async function readSystemClipboardDataTransfer(): Promise<DataTransfer | null> {
  if (typeof navigator === "undefined" || !navigator.clipboard) return null;
  try {
    if (navigator.clipboard.read) {
      const items = await navigator.clipboard.read();
      return buildDataTransferFromClipboardItems(items);
    }
    const text = await navigator.clipboard.readText();
    const dt = new DataTransfer();
    dt.setData("text/plain", text);
    return dt;
  } catch {
    try {
      const text = await navigator.clipboard.readText();
      const dt = new DataTransfer();
      dt.setData("text/plain", text);
      return dt;
    } catch {
      return null;
    }
  }
}

async function buildDataTransferFromClipboardItems(items: ClipboardItems): Promise<DataTransfer> {
  const dt = new DataTransfer();
  for (const item of items) {
    for (const type of item.types) {
      if (type.startsWith("image/")) {
        const blob = await item.getType(type);
        const ext = type.split("/")[1] || "png";
        dt.items.add(new File([blob], `clipboard.${ext}`, { type }));
      } else if (type === "text/plain" || type === "text/html") {
        const blob = await item.getType(type);
        const text = await blob.text();
        dt.setData(type, text);
      }
    }
  }
  return dt;
}
