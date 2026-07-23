import {
  COMUNICADO_FRAME_MIN_SIZE_PCT,
  type ComunicadoFrame,
} from "@delpi/tv-dashboard-presentation";

export type ResizeHandleMode =
  | "resize-nw"
  | "resize-n"
  | "resize-ne"
  | "resize-e"
  | "resize-se"
  | "resize-s"
  | "resize-sw"
  | "resize-w";

export type GenericResizeHandle = "nw" | "n" | "ne" | "e" | "se" | "s" | "sw" | "w";

const MIN_SIZE = COMUNICADO_FRAME_MIN_SIZE_PCT;

function isResizeHandleMode(mode: string): mode is ResizeHandleMode {
  return mode.startsWith("resize-");
}

/** Converte handle curto (`se`) ou modo de bloco (`resize-se`). */
export function normalizeResizeHandle(modeOrHandle: string): GenericResizeHandle | null {
  const raw = modeOrHandle.startsWith("resize-")
    ? modeOrHandle.slice("resize-".length)
    : modeOrHandle;
  if (
    raw === "nw" ||
    raw === "n" ||
    raw === "ne" ||
    raw === "e" ||
    raw === "se" ||
    raw === "s" ||
    raw === "sw" ||
    raw === "w"
  ) {
    return raw;
  }
  return null;
}

/**
 * Resize de frame em % com Shift = manter proporção (âncora no lado/canto oposto).
 * `aspectRatio` = w/h do frame no início do arrasto.
 */
export function resizeFrameWithOptionalAspect(
  frame: ComunicadoFrame,
  dx: number,
  dy: number,
  modeOrHandle: string,
  aspectRatio: number,
  lockAspect: boolean,
): ComunicadoFrame {
  const handle = normalizeResizeHandle(modeOrHandle);
  if (!handle) return frame;

  if (!lockAspect || !(aspectRatio > 0)) {
    return resizeFrameFree(frame, dx, dy, handle);
  }

  return resizeFrameLocked(frame, dx, dy, handle, aspectRatio);
}

function resizeFrameFree(
  frame: ComunicadoFrame,
  dx: number,
  dy: number,
  handle: GenericResizeHandle,
): ComunicadoFrame {
  const right = frame.x + frame.w;
  const bottom = frame.y + frame.h;
  switch (handle) {
    case "se":
      return {
        ...frame,
        w: Math.max(MIN_SIZE, frame.w + dx),
        h: Math.max(MIN_SIZE, frame.h + dy),
      };
    case "e":
      return { ...frame, w: Math.max(MIN_SIZE, frame.w + dx) };
    case "s":
      return { ...frame, h: Math.max(MIN_SIZE, frame.h + dy) };
    case "n": {
      const h = Math.max(MIN_SIZE, frame.h - dy);
      return { ...frame, y: bottom - h, h };
    }
    case "w": {
      const w = Math.max(MIN_SIZE, frame.w - dx);
      return { ...frame, x: right - w, w };
    }
    case "ne": {
      const w = Math.max(MIN_SIZE, frame.w + dx);
      const h = Math.max(MIN_SIZE, frame.h - dy);
      return { ...frame, y: bottom - h, w, h };
    }
    case "nw": {
      const w = Math.max(MIN_SIZE, frame.w - dx);
      const h = Math.max(MIN_SIZE, frame.h - dy);
      return { x: right - w, y: bottom - h, w, h };
    }
    case "sw": {
      const w = Math.max(MIN_SIZE, frame.w - dx);
      const h = Math.max(MIN_SIZE, frame.h + dy);
      return { ...frame, x: right - w, w, h };
    }
    default:
      return frame;
  }
}

function resizeFrameLocked(
  frame: ComunicadoFrame,
  dx: number,
  dy: number,
  handle: GenericResizeHandle,
  aspectRatio: number,
): ComunicadoFrame {
  const ar = aspectRatio;
  const right = frame.x + frame.w;
  const bottom = frame.y + frame.h;
  const cx = frame.x + frame.w / 2;
  const cy = frame.y + frame.h / 2;

  const byDominantCorner = (candW: number, candH: number, driveDx: number, driveDy: number) => {
    let w = Math.max(MIN_SIZE, candW);
    let h = Math.max(MIN_SIZE, candH);
    if (Math.abs(driveDx) >= Math.abs(driveDy)) {
      h = w / ar;
    } else {
      w = h * ar;
    }
    w = Math.max(MIN_SIZE, w);
    h = Math.max(MIN_SIZE, h);
    return { w, h };
  };

  switch (handle) {
    case "se": {
      const { w, h } = byDominantCorner(frame.w + dx, frame.h + dy, dx, dy);
      return { x: frame.x, y: frame.y, w, h };
    }
    case "nw": {
      const { w, h } = byDominantCorner(frame.w - dx, frame.h - dy, -dx, -dy);
      return { x: right - w, y: bottom - h, w, h };
    }
    case "ne": {
      const { w, h } = byDominantCorner(frame.w + dx, frame.h - dy, dx, -dy);
      return { x: frame.x, y: bottom - h, w, h };
    }
    case "sw": {
      const { w, h } = byDominantCorner(frame.w - dx, frame.h + dy, -dx, dy);
      return { x: right - w, y: frame.y, w, h };
    }
    case "e": {
      const w = Math.max(MIN_SIZE, frame.w + dx);
      const h = w / ar;
      return { x: frame.x, y: cy - h / 2, w, h };
    }
    case "w": {
      const w = Math.max(MIN_SIZE, frame.w - dx);
      const h = w / ar;
      return { x: right - w, y: cy - h / 2, w, h };
    }
    case "s": {
      const h = Math.max(MIN_SIZE, frame.h + dy);
      const w = h * ar;
      return { x: cx - w / 2, y: frame.y, w, h };
    }
    case "n": {
      const h = Math.max(MIN_SIZE, frame.h - dy);
      const w = h * ar;
      return { x: cx - w / 2, y: bottom - h, w, h };
    }
    default:
      return frame;
  }
}

export { isResizeHandleMode };
