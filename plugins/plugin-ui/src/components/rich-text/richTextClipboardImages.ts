/**
 * Canonical clipboard image extraction for paste (RichTextEditor + MentionComposer).
 *
 * Interaction-room parity:
 *   files XOR items (uniqueClipboardImageFiles)
 *   + data: imgs in text/html
 *   + async navigator.clipboard.read() for Win Snipping Tool empty FileList
 */
import { resolveFilePreviewKind } from "../preview/resolveFilePreviewKind";

export function isRichTextClipboardImageFile(file: File): boolean {
  return resolveFilePreviewKind({ fileName: file.name, mimeType: file.type }) === "image";
}

function defaultImageName(mime: string): string {
  const ext = mime.split("/")[1]?.split("+")[0] || "png";
  return `clipboard.${ext}`;
}

/** Win/Chromium sometimes exposes File with empty type while the item declares image/png. */
function normalizeClipboardFile(file: File, declaredType?: string): File {
  const type = (file.type || declaredType || "").trim();
  const name = (file.name || "").trim();
  if (type && type === file.type && name) return file;
  const looksImage =
    type.toLowerCase().startsWith("image/") || isRichTextClipboardImageFile(file);
  if (!looksImage) return file;
  const nextType = type.toLowerCase().startsWith("image/")
    ? type
    : file.type || "image/png";
  const nextName = name || defaultImageName(nextType);
  if (nextType === file.type && nextName === file.name) return file;
  return new File([file], nextName, { type: nextType, lastModified: file.lastModified });
}

function clipboardImageFingerprint(file: File): string {
  return `${file.name}|${file.size}|${file.type}|${file.lastModified}`;
}

function pushUniqueImages(out: File[], seen: Set<string>, file: File): void {
  if (!isRichTextClipboardImageFile(file) && !(file.type || "").toLowerCase().startsWith("image/")) {
    return;
  }
  const key = clipboardImageFingerprint(file);
  if (seen.has(key)) return;
  seen.add(key);
  out.push(file);
}

function collectImagesFromFileList(list: FileList | null | undefined): File[] {
  if (!list?.length) return [];
  const out: File[] = [];
  const seen = new Set<string>();
  for (const file of Array.from(list)) {
    pushUniqueImages(out, seen, normalizeClipboardFile(file));
  }
  return out;
}

function collectImagesFromItems(items: DataTransferItemList | null | undefined): File[] {
  if (!items?.length) return [];
  const out: File[] = [];
  const seen = new Set<string>();
  for (const item of Array.from(items)) {
    if (item.kind !== "file") continue;
    const raw = item.getAsFile();
    if (!raw) continue;
    pushUniqueImages(out, seen, normalizeClipboardFile(raw, item.type));
  }
  return out;
}

function dataUrlToImageFile(dataUrl: string, fileName: string): File | null {
  const match = /^data:([^;,]+)?(;base64)?,(.*)$/i.exec(dataUrl.trim());
  if (!match) return null;
  const mime = (match[1] || "image/png").trim() || "image/png";
  if (!mime.startsWith("image/")) return null;
  const isBase64 = Boolean(match[2]);
  const payload = match[3] ?? "";
  try {
    let bytes: Uint8Array;
    if (isBase64) {
      const binary = atob(payload);
      bytes = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i);
    } else {
      bytes = new TextEncoder().encode(decodeURIComponent(payload));
    }
    const name = fileName.includes(".") ? fileName : defaultImageName(mime);
    const part = new Uint8Array(bytes.byteLength);
    part.set(bytes);
    return new File([part], name, { type: mime });
  } catch {
    return null;
  }
}

/**
 * Clipboard images once per capture.
 * Prefer `files`; only fall back to `items` when `files` has no images.
 */
export function uniqueClipboardImageFiles(
  data: DataTransfer | null | undefined,
): File[] {
  if (!data) return [];
  const fromFiles = collectImagesFromFileList(data.files);
  if (fromFiles.length > 0) return fromFiles;
  return collectImagesFromItems(data.items);
}

/** @deprecated Prefer `uniqueClipboardImageFiles` (same behavior). */
export function collectClipboardImageFiles(
  data: DataTransfer | null | undefined,
): File[] {
  return uniqueClipboardImageFiles(data);
}

/** HTML-only paste: one File per unique data: image src (ignores http(s)/file://). */
export function extractClipboardHtmlImageFiles(html: string | null | undefined): File[] {
  const source = (html ?? "").trim();
  if (!source || !/<img\b/i.test(source)) return [];
  const out: File[] = [];
  const seen = new Set<string>();

  if (typeof DOMParser !== "undefined") {
    try {
      const doc = new DOMParser().parseFromString(source, "text/html");
      for (const img of Array.from(doc.querySelectorAll("img"))) {
        const src = (img.getAttribute("src") || "").trim();
        if (!src.startsWith("data:")) continue;
        if (seen.has(src)) continue;
        seen.add(src);
        const file = dataUrlToImageFile(src, img.getAttribute("alt") || "image");
        if (file) out.push(file);
      }
      return out;
    } catch {
      /* fall through to regex */
    }
  }

  const re = /<img\b[^>]*\bsrc\s*=\s*["'](data:image\/[^"']+)["'][^>]*>/gi;
  let match: RegExpExecArray | null;
  while ((match = re.exec(source))) {
    const src = match[1];
    if (!src || seen.has(src)) continue;
    seen.add(src);
    const file = dataUrlToImageFile(src, "image");
    if (file) out.push(file);
  }
  return out;
}

/**
 * Sync image files from a paste DataTransfer.
 * Prefer files XOR items, then data: images in text/html.
 */
export function collectPasteImageFiles(data: DataTransfer | null | undefined): File[] {
  if (!data) return [];
  const fromClipboard = uniqueClipboardImageFiles(data);
  if (fromClipboard.length > 0) return fromClipboard;
  return extractClipboardHtmlImageFiles(data.getData("text/html"));
}

/** True when clipboard types/items suggest an image even if File is not exposed yet. */
export function clipboardLooksLikeImagePaste(data: DataTransfer | null | undefined): boolean {
  if (!data) return false;
  const types = Array.from(data.types || []).map((type) => type.toLowerCase());
  if (types.some((type) => type.startsWith("image/"))) return true;
  for (const item of Array.from(data.items || [])) {
    if ((item.type || "").toLowerCase().startsWith("image/")) return true;
  }
  // Chromium/Win Snipping Tool: often only "Files" with an empty FileList in the sync paste.
  if (types.includes("files") && !(data.files && data.files.length > 0)) {
    const text = (data.getData("text/plain") || "").trim();
    const html = data.getData("text/html") || "";
    if (!text && !/<p\b|<div\b|<span\b|<br\b/i.test(html)) return true;
  }
  const html = data.getData("text/html") || "";
  return /<img\b/i.test(html);
}

/**
 * When to block the default paste and try `navigator.clipboard.read()`.
 * Do not steal Word/HTML prose pastes that only mention &lt;img&gt;.
 */
export function shouldTryAsyncClipboardImageRead(
  data: DataTransfer | null | undefined,
): boolean {
  if (!data) return false;
  const types = Array.from(data.types || []).map((type) => type.toLowerCase());
  if (types.some((type) => type.startsWith("image/"))) return true;
  for (const item of Array.from(data.items || [])) {
    if ((item.type || "").toLowerCase().startsWith("image/")) return true;
  }
  if (!(data.files && data.files.length > 0) && types.includes("files")) {
    const text = (data.getData("text/plain") || "").trim();
    const html = data.getData("text/html") || "";
    if (!text && !/<p\b|<div\b|<span\b|<br\b/i.test(html)) return true;
  }
  return false;
}

/**
 * Async fallback when paste DataTransfer has no File (Win Snipping Tool / Edge).
 * Must be called during a user gesture; clipboardData snapshot should already be consumed sync.
 */
export async function readClipboardImageFiles(): Promise<File[]> {
  const clipboard = typeof navigator !== "undefined" ? navigator.clipboard : undefined;
  if (!clipboard || typeof clipboard.read !== "function") return [];
  try {
    const items = await clipboard.read();
    const out: File[] = [];
    const seen = new Set<string>();
    for (const item of items) {
      for (const type of item.types) {
        if (!type.toLowerCase().startsWith("image/")) continue;
        const blob = await item.getType(type);
        const file = new File([blob], defaultImageName(type), { type });
        pushUniqueImages(out, seen, file);
      }
    }
    return out;
  } catch {
    return [];
  }
}
