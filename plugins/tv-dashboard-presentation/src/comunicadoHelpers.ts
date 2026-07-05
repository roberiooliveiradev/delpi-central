import type { CSSProperties } from "react";

import type {
  ComunicadoBackground,
  ComunicadoBlock,
  ComunicadoConfig,
  ComunicadoFrame,
} from "./comunicadoTypes";

export function newBlockId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `block-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

const DEFAULT_BACKGROUND: ComunicadoBackground = { type: "color", value: "#0f172a" };

export function defaultFrame(type: ComunicadoBlock["type"]): ComunicadoFrame {
  if (type === "heading") return { x: 5, y: 12, w: 90, h: 18 };
  if (type === "text") return { x: 5, y: 34, w: 90, h: 14 };
  if (type === "image") return { x: 10, y: 22, w: 80, h: 56 };
  return { x: 5, y: 15, w: 90, h: 70 };
}

export function defaultStyle(type: ComunicadoBlock["type"]) {
  if (type === "heading") {
    return { fontSize: 56, color: "#ffffff", textAlign: "center" as const, fontWeight: "bold" as const };
  }
  if (type === "text") {
    return { fontSize: 28, color: "#cbd5e1", textAlign: "center" as const, fontWeight: "normal" as const };
  }
  if (type === "image" || type === "video") {
    return { objectFit: "contain" as const };
  }
  return {};
}

export function createBlock(type: ComunicadoBlock["type"], content = ""): ComunicadoBlock {
  const base = {
    id: newBlockId(),
    type,
    frame: defaultFrame(type),
    style: defaultStyle(type),
  };
  if (type === "heading" || type === "text") {
    return { ...base, type, content };
  }
  return { ...base, type };
}

export function parseComunicadoConfig(raw: Record<string, unknown> | undefined | null): ComunicadoConfig {
  const cfg = raw ?? {};
  const blocks = Array.isArray(cfg.blocks) ? (cfg.blocks as ComunicadoBlock[]) : [];
  if (blocks.length > 0) {
    return {
      version: Number(cfg.version) || 2,
      headline: String(cfg.headline ?? ""),
      subtitle: String(cfg.subtitle ?? ""),
      background: normalizeBackground(cfg.background),
      blocks: blocks.map(normalizeBlock),
    };
  }
  const headline = String(cfg.headline ?? "Comunicado");
  const subtitle = String(cfg.subtitle ?? "");
  return {
    version: 2,
    headline,
    subtitle,
    background: DEFAULT_BACKGROUND,
    blocks: [
      createBlock("heading", headline),
      ...(subtitle ? [createBlock("text", subtitle)] : []),
    ],
  };
}

export function serializeComunicadoConfig(config: ComunicadoConfig): Record<string, unknown> {
  const headingBlock = config.blocks?.find((b) => b.type === "heading");
  const textBlock = config.blocks?.find((b) => b.type === "text");
  return {
    version: 2,
    headline: headingBlock && "content" in headingBlock ? headingBlock.content : config.headline ?? "Comunicado",
    subtitle: textBlock && "content" in textBlock ? textBlock.content : config.subtitle ?? "",
    background: config.background ?? DEFAULT_BACKGROUND,
    blocks: (config.blocks ?? []).map((block) => ({
      id: block.id,
      type: block.type,
      frame: block.frame,
      style: block.style ?? {},
      ...(block.type === "heading" || block.type === "text"
        ? { content: "content" in block ? block.content : "" }
        : { assetId: "assetId" in block ? block.assetId : undefined }),
    })),
  };
}

function normalizeBackground(value: unknown): ComunicadoBackground {
  if (!value || typeof value !== "object") return DEFAULT_BACKGROUND;
  const bg = value as Record<string, unknown>;
  if (bg.type === "image") {
    return {
      type: "image",
      assetId: typeof bg.assetId === "string" ? bg.assetId : undefined,
      url: typeof bg.url === "string" ? bg.url : undefined,
      value: typeof bg.value === "string" ? bg.value : undefined,
    };
  }
  const color = typeof bg.value === "string" && bg.value.trim() ? bg.value : "#0f172a";
  return { type: "color", value: color };
}

function normalizeBlock(value: unknown): ComunicadoBlock {
  if (!value || typeof value !== "object") {
    return createBlock("text", "");
  }
  const block = value as Record<string, unknown>;
  const type = (block.type as ComunicadoBlock["type"]) ?? "text";
  const frame = normalizeFrame(block.frame);
  const style = (block.style as ComunicadoBlock["style"]) ?? defaultStyle(type);
  const id = typeof block.id === "string" ? block.id : newBlockId();
  if (type === "heading" || type === "text") {
    return {
      id,
      type,
      frame,
      style,
      content: String(block.content ?? ""),
    };
  }
  return {
    id,
    type,
    frame,
    style,
    assetId: typeof block.assetId === "string" ? block.assetId : undefined,
    url: typeof block.url === "string" ? block.url : undefined,
  };
}

function normalizeFrame(value: unknown): ComunicadoFrame {
  if (!value || typeof value !== "object") return defaultFrame("text");
  const frame = value as Record<string, unknown>;
  const num = (key: keyof ComunicadoFrame, fallback: number) => {
    const raw = frame[key];
    const parsed = typeof raw === "number" ? raw : Number(raw);
    return Number.isFinite(parsed) ? parsed : fallback;
  };
  return {
    x: Math.max(0, Math.min(100, num("x", 5))),
    y: Math.max(0, Math.min(100, num("y", 10))),
    w: Math.max(5, Math.min(100, num("w", 90))),
    h: Math.max(5, Math.min(100, num("h", 20))),
  };
}

export function frameStyle(frame: ComunicadoFrame): CSSProperties {
  return {
    left: `${frame.x}%`,
    top: `${frame.y}%`,
    width: `${frame.w}%`,
    height: `${frame.h}%`,
  };
}

export function hasRichComunicado(data: ComunicadoScreenDataLike): boolean {
  return Array.isArray(data.blocks) && data.blocks.length > 0;
}

export type ComunicadoScreenDataLike = {
  blocks?: ComunicadoBlock[];
  headline?: string;
  subtitle?: string;
};
