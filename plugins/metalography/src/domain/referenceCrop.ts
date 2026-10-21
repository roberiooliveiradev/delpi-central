export type CropRect = { x: number; y: number; w: number; h: number };

export type CropCanvasSize = { cw: number; ch: number; sx: number; sy: number };

export function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

export function fitCanvas(width: number, height: number, maxCanvas = 2400): CropCanvasSize {
  const scale = Math.min(1, maxCanvas / Math.max(width, height, 1));
  const cw = Math.max(1, Math.round(width * scale));
  const ch = Math.max(1, Math.round(height * scale));
  return { cw, ch, sx: cw / width, sy: ch / height };
}

export function clampCrop(crop: CropRect, cw: number, ch: number): CropRect {
  const x = clamp(crop.x, 0, cw - 1);
  const y = clamp(crop.y, 0, ch - 1);
  return {
    x,
    y,
    w: clamp(crop.w, 1, cw - x),
    h: clamp(crop.h, 1, ch - y),
  };
}

export function cropPointerMode(
  point: { x: number; y: number },
  crop: CropRect,
  size: { cw: number; ch: number },
): string {
  const right = crop.x + crop.w;
  const bottom = crop.y + crop.h;
  const tolerance = Math.max(10, Math.min(34, Math.min(size.cw, size.ch) * 0.035));
  const nearLeft = Math.abs(point.x - crop.x) <= tolerance;
  const nearRight = Math.abs(point.x - right) <= tolerance;
  const nearTop = Math.abs(point.y - crop.y) <= tolerance;
  const nearBottom = Math.abs(point.y - bottom) <= tolerance;
  const full = crop.x <= tolerance && crop.y <= tolerance && right >= size.cw - tolerance && bottom >= size.ch - tolerance;
  let sides = "";
  if (nearTop) sides += "n";
  else if (nearBottom) sides += "s";
  if (nearLeft) sides += "w";
  else if (nearRight) sides += "e";
  if (sides) return sides;
  const inside = point.x >= crop.x && point.x <= right && point.y >= crop.y && point.y <= bottom;
  return inside && !full ? "move" : "new";
}

export function nextCrop(
  mode: string,
  start: CropRect,
  origin: { x: number; y: number },
  point: { x: number; y: number },
  size: { cw: number; ch: number },
): CropRect {
  const dx = point.x - origin.x;
  const dy = point.y - origin.y;
  if (mode === "new") {
    return {
      x: Math.min(origin.x, point.x),
      y: Math.min(origin.y, point.y),
      w: Math.abs(dx),
      h: Math.abs(dy),
    };
  }
  if (mode === "move") {
    return {
      x: clamp(start.x + dx, 0, size.cw - start.w),
      y: clamp(start.y + dy, 0, size.ch - start.h),
      w: start.w,
      h: start.h,
    };
  }
  let left = start.x;
  let right = start.x + start.w;
  let top = start.y;
  let bottom = start.y + start.h;
  const minSize = Math.max(8, Math.min(size.cw, size.ch) * 0.015);
  if (mode.includes("w")) left = clamp(start.x + dx, 0, right - minSize);
  if (mode.includes("e")) right = clamp(start.x + start.w + dx, left + minSize, size.cw);
  if (mode.includes("n")) top = clamp(start.y + dy, 0, bottom - minSize);
  if (mode.includes("s")) bottom = clamp(start.y + start.h + dy, top + minSize, size.ch);
  return { x: left, y: top, w: right - left, h: bottom - top };
}

export function sourceRect(crop: CropRect, size: CropCanvasSize): CropRect {
  return {
    x: crop.x / size.sx,
    y: crop.y / size.sy,
    w: crop.w / size.sx,
    h: crop.h / size.sy,
  };
}
