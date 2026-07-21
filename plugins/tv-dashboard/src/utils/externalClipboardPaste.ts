import {
  createBlock,
  createCanvasTableBlock,
  type ComunicadoBlock,
} from "@delpi/tv-dashboard-presentation";

/**
 * Marcador do payload interno no `text/plain` do SO (colar entre abas/sessões).
 * O Windows costuma normalizar `\n` → `\r\n` no clipboard — nunca exigir newline exato.
 */
export const DELPI_TV_BLOCKS_CLIPBOARD_MARKER = "__DELPI_TV_BLOCKS_V1__";
export const DELPI_TV_BLOCKS_CLIPBOARD_PREFIX = `${DELPI_TV_BLOCKS_CLIPBOARD_MARKER}\n`;

export type ExternalPastePlan =
  | { kind: "internal-blocks"; blocks: ComunicadoBlock[] }
  | { kind: "images"; files: File[] }
  | { kind: "blocks"; blocks: ComunicadoBlock[] }
  | { kind: "empty" };

/** Normaliza BOM + CRLF (clipboard Windows) antes de detectar/parsear payload Delpi. */
export function normalizeClipboardText(text: string): string {
  return text.replace(/^\uFEFF/, "").replace(/\r\n/g, "\n").replace(/\r/g, "\n").trim();
}

export function looksLikeInternalBlocksPayload(text: string): boolean {
  return normalizeClipboardText(text).startsWith(DELPI_TV_BLOCKS_CLIPBOARD_MARKER);
}

function stripHtmlToText(html: string): string {
  const doc = new DOMParser().parseFromString(html, "text/html");
  doc.querySelectorAll("script,style,noscript").forEach((node) => node.remove());
  return (doc.body?.textContent ?? "").replace(/\u00a0/g, " ").replace(/\s+\n/g, "\n").trim();
}

function cssColor(value: string | null | undefined): string | undefined {
  if (!value) return undefined;
  const trimmed = value.trim();
  if (!trimmed || trimmed === "transparent" || trimmed === "rgba(0, 0, 0, 0)") return undefined;
  return trimmed;
}

function offsetFrame(index: number, base = { x: 8, y: 12, w: 40, h: 18 }) {
  const col = index % 3;
  const row = Math.floor(index / 3);
  return {
    x: Math.min(70, base.x + col * 28),
    y: Math.min(70, base.y + row * 22),
    w: base.w,
    h: base.h,
  };
}

/**
 * TSV/CSV simples (Excel, Sheets) → tabela no palco.
 */
export function tryParseTabularText(text: string): ComunicadoBlock | null {
  const normalized = text.replace(/\r\n/g, "\n").replace(/\r/g, "\n").trim();
  if (!normalized) return null;
  const lines = normalized.split("\n").filter((line) => line.length > 0);
  if (lines.length < 2) return null;
  const delimiter = lines[0].includes("\t") ? "\t" : lines[0].includes(";") ? ";" : null;
  if (!delimiter) return null;
  const rows = lines.map((line) => line.split(delimiter).map((cell) => cell.trim()));
  const cols = Math.max(...rows.map((row) => row.length));
  if (cols < 2) return null;
  const table = createCanvasTableBlock(rows.length, cols);
  table.cells = rows.map((row) => {
    const padded = [...row];
    while (padded.length < cols) padded.push("");
    return padded.slice(0, cols);
  });
  table.headerRow = true;
  return table;
}

/**
 * HTML externo (Slides/Docs/web) → formas com texto + blocos de texto.
 * Heurística: nós com fundo/borda viram forma; resto vira texto empilhado.
 */
export function blocksFromExternalHtml(html: string): ComunicadoBlock[] {
  if (!html.trim()) return [];

  // Payload Delpi embutido em text/html (alguns browsers) — nunca virar tipografia.
  const stripped = stripHtmlToText(html);
  if (looksLikeInternalBlocksPayload(stripped)) {
    return parseInternalBlocksPayload(stripped) ?? [];
  }

  const doc = new DOMParser().parseFromString(html, "text/html");
  doc.querySelectorAll("script,style,noscript").forEach((node) => node.remove());

  const blocks: ComunicadoBlock[] = [];
  const seen = new Set<string>();

  const candidates = Array.from(
    doc.body?.querySelectorAll("div,section,article,td,th,p,h1,h2,h3,li,span") ?? [],
  );

  for (const el of candidates) {
    if (!(el instanceof HTMLElement)) continue;
    const text = (el.innerText ?? el.textContent ?? "").replace(/\u00a0/g, " ").trim();
    if (!text || text.length > 400) continue;
    if (looksLikeInternalBlocksPayload(text)) continue;
    const key = text.toLowerCase();
    if (seen.has(key)) continue;

    const style = el.getAttribute("style") ?? "";
    const bg =
      cssColor(el.style?.backgroundColor) ??
      cssColor(style.match(/background(?:-color)?\s*:\s*([^;]+)/i)?.[1]);
    const border =
      cssColor(el.style?.borderColor) ??
      cssColor(style.match(/border(?:-color)?\s*:\s*([^;]+)/i)?.[1]);
    const hasBox =
      Boolean(bg) ||
      Boolean(border) ||
      /border-radius/i.test(style) ||
      el.tagName === "TD" ||
      el.tagName === "TH";

    // Evita capturar o body inteiro / wrappers gigantes.
    if (el === doc.body) continue;
    const childBoxes = el.querySelectorAll("div,td,th,section").length;
    if (childBoxes > 8) continue;

    seen.add(key);
    const index = blocks.length;
    if (hasBox && text.length <= 280) {
      const shape = createBlock("shape", text, "rounded-rect");
      shape.frame = offsetFrame(index, { x: 6, y: 10, w: 28, h: 20 });
      shape.style = {
        ...shape.style,
        fill: bg ?? "#e8f4fc",
        stroke: border ?? "#89c2e8",
        color: "#0f172a",
        fontSize: text.length > 80 ? 12 : 14,
      };
      blocks.push(shape);
    } else if (
      el.tagName === "H1" ||
      el.tagName === "H2" ||
      el.tagName === "H3" ||
      (el.tagName === "P" && text.length <= 200)
    ) {
      const type = el.tagName.startsWith("H") ? "heading" : "text";
      const block = createBlock(type, text);
      block.frame = offsetFrame(index, {
        x: 8,
        y: 8,
        w: type === "heading" ? 84 : 70,
        h: type === "heading" ? 12 : 10,
      });
      blocks.push(block);
    }

    if (blocks.length >= 12) break;
  }

  if (blocks.length === 0) {
    const plain = stripped;
    if (plain) {
      if (looksLikeInternalBlocksPayload(plain)) return [];
      const tabular = tryParseTabularText(plain);
      if (tabular) return [tabular];
      const block = createBlock(plain.length > 80 ? "text" : "heading", plain.slice(0, 2000));
      return [block];
    }
  }

  return blocks;
}

export function blocksFromPlainText(text: string): ComunicadoBlock[] {
  const trimmed = normalizeClipboardText(text.replace(/\u00a0/g, " "));
  if (!trimmed) return [];
  // Nunca materializar o payload interno como tipografia no palco.
  if (looksLikeInternalBlocksPayload(trimmed)) return [];

  const tabular = tryParseTabularText(trimmed);
  if (tabular) return [tabular];

  const type = trimmed.includes("\n") || trimmed.length > 120 ? "text" : "heading";
  return [createBlock(type, trimmed.slice(0, 4000))];
}

export function parseInternalBlocksPayload(text: string): ComunicadoBlock[] | null {
  const normalized = normalizeClipboardText(text);
  if (!normalized.startsWith(DELPI_TV_BLOCKS_CLIPBOARD_MARKER)) return null;
  const raw = normalized.slice(DELPI_TV_BLOCKS_CLIPBOARD_MARKER.length).replace(/^\n+/, "");
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed) || parsed.length === 0) return null;
    const blocks = parsed.filter(
      (item): item is ComunicadoBlock =>
        Boolean(item) && typeof item === "object" && typeof (item as ComunicadoBlock).type === "string",
    );
    return blocks.length > 0 ? blocks : null;
  } catch {
    return null;
  }
}

export function serializeInternalBlocksPayload(blocks: ComunicadoBlock[]): string {
  return `${DELPI_TV_BLOCKS_CLIPBOARD_PREFIX}${JSON.stringify(blocks)}`;
}

function collectImageFiles(data: DataTransfer): File[] {
  const files: File[] = [];
  if (data.files?.length) {
    for (const file of Array.from(data.files)) {
      if (file.type.startsWith("image/")) files.push(file);
    }
  }
  if (files.length === 0 && data.items) {
    for (const item of Array.from(data.items)) {
      if (item.kind === "file" && item.type.startsWith("image/")) {
        const file = item.getAsFile();
        if (file) files.push(file);
      }
    }
  }
  return files;
}

/**
 * Há conteúdo externo no DataTransfer (Google Slides, web, imagem…)?
 * Usado para NÃO cair no clipboard interno da sessão quando o SO trouxe
 * payload que ainda não viramos bloco (ex.: PNG só na Clipboard API).
 */
export function hasExternalClipboardPayload(data: DataTransfer | null | undefined): boolean {
  if (!data) return false;

  const images = collectImageFiles(data);
  if (images.length > 0) return true;

  const plain = data.getData("text/plain") ?? "";
  if (plain.trim() && !looksLikeInternalBlocksPayload(plain)) return true;

  const html = data.getData("text/html") ?? "";
  if (html.trim()) {
    const htmlPlain = stripHtmlToText(html);
    if (htmlPlain && looksLikeInternalBlocksPayload(htmlPlain)) return false;
    // HTML do Slides/Docs conta como externo mesmo sem texto extraível (recorte virá via read()).
    return true;
  }

  if (data.items) {
    for (const item of Array.from(data.items)) {
      if (item.kind === "file" && item.type.startsWith("image/")) return true;
      if (item.kind === "string" && (item.type === "text/html" || item.type === "text/plain")) {
        // Tipos presentes sem getData preenchido (alguns browsers no paste) — tratar como externo.
        if (item.type === "text/html") return true;
      }
    }
  }

  return false;
}

/**
 * Prioridade: blocos internos → imagens → HTML estruturado → texto/TSV.
 * Google Slides costuma oferecer PNG da seleção + HTML; preferimos a imagem
 * quando não há payload interno (reprodução fiel do recorte).
 */
export function planExternalClipboardPaste(data: DataTransfer | null | undefined): ExternalPastePlan {
  if (!data) return { kind: "empty" };

  const plain = data.getData("text/plain") ?? "";
  const html = data.getData("text/html") ?? "";

  const internalFromPlain = parseInternalBlocksPayload(plain);
  if (internalFromPlain && internalFromPlain.length > 0) {
    return { kind: "internal-blocks", blocks: internalFromPlain };
  }
  // Marcador Delpi presente (ex.: CRLF) mas parse falhou — não virar texto; caller usa memória.
  if (looksLikeInternalBlocksPayload(plain)) {
    return { kind: "empty" };
  }

  const htmlPlain = html.trim() ? stripHtmlToText(html) : "";
  const internalFromHtml = htmlPlain ? parseInternalBlocksPayload(htmlPlain) : null;
  if (internalFromHtml && internalFromHtml.length > 0) {
    return { kind: "internal-blocks", blocks: internalFromHtml };
  }
  if (htmlPlain && looksLikeInternalBlocksPayload(htmlPlain)) {
    return { kind: "empty" };
  }

  const images = collectImageFiles(data);
  if (images.length > 0) {
    return { kind: "images", files: images };
  }

  if (html.trim()) {
    const fromHtml = blocksFromExternalHtml(html);
    if (fromHtml.length > 0) return { kind: "blocks", blocks: fromHtml };
  }

  if (plain.trim()) {
    const fromText = blocksFromPlainText(plain);
    if (fromText.length > 0) return { kind: "blocks", blocks: fromText };
  }

  return { kind: "empty" };
}

export function nextZIndex(blocks: ComunicadoBlock[]): number {
  let max = 1;
  for (const block of blocks) {
    const z = block.style?.zIndex;
    if (typeof z === "number" && z > max) max = z;
  }
  return max + 1;
}

export function assignPasteStack(blocks: ComunicadoBlock[], existing: ComunicadoBlock[]): ComunicadoBlock[] {
  let z = nextZIndex(existing);
  return blocks.map((block, index) => ({
    ...block,
    style: { ...block.style, zIndex: z + index },
  }));
}
