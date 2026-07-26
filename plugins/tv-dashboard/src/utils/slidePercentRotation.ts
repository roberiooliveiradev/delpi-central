import { clampRotationDeg } from "./comunicadoTransform";

/** Frame mínimo em % — espelho do tipo de apresentação (sem importar o pacote no teste). */
export type PercentFrame = { x: number; y: number; w: number; h: number };

/** União axis-aligned de frames em %. */
export function unionFramesPercent(frames: ReadonlyArray<PercentFrame>): PercentFrame {
  if (frames.length === 0) return { x: 0, y: 0, w: 0, h: 0 };
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  for (const frame of frames) {
    minX = Math.min(minX, frame.x);
    minY = Math.min(minY, frame.y);
    maxX = Math.max(maxX, frame.x + frame.w);
    maxY = Math.max(maxY, frame.y + frame.h);
  }
  return { x: minX, y: minY, w: maxX - minX, h: maxY - minY };
}

function aabbFromPoints(points: ReadonlyArray<{ x: number; y: number }>): PercentFrame {
  if (points.length === 0) return { x: 0, y: 0, w: 0, h: 0 };
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  for (const point of points) {
    minX = Math.min(minX, point.x);
    minY = Math.min(minY, point.y);
    maxX = Math.max(maxX, point.x);
    maxY = Math.max(maxY, point.y);
  }
  return { x: minX, y: minY, w: maxX - minX, h: maxY - minY };
}

/** Centro do bbox unificado dos frames (coords % do slide). */
export function resolveFramesGroupCenter(
  frames: Iterable<PercentFrame>,
): { x: number; y: number } {
  const union = unionFramesPercent([...frames]);
  return { x: union.x + union.w / 2, y: union.y + union.h / 2 };
}

/**
 * Rotaciona um ponto em coords % do slide em torno de um centro.
 * `slideAspect` = largura/altura do palco (ex.: 1920/1080) — x% e y% não são
 * isotrópicos em slides 16:9; sem isso a órbita do grupo “estica” os membros.
 */
export function rotatePointPercentAround(
  point: { x: number; y: number },
  center: { x: number; y: number },
  deltaDeg: number,
  slideAspect = 1,
): { x: number; y: number } {
  const aspect = slideAspect > 0 ? slideAspect : 1;
  const rad = (deltaDeg * Math.PI) / 180;
  const cos = Math.cos(rad);
  const sin = Math.sin(rad);
  const dx = point.x - center.x;
  const dy = (point.y - center.y) / aspect;
  const rx = dx * cos - dy * sin;
  const ry = dx * sin + dy * cos;
  return {
    x: center.x + rx,
    y: center.y + ry * aspect,
  };
}

/** Cantos do frame após `style.rotation` (espaço % com aspecto do slide). */
export function resolveRotatedFrameCorners(
  frame: PercentFrame,
  rotationDeg: number,
  slideAspect = 1,
): Array<{ x: number; y: number }> {
  const cx = frame.x + frame.w / 2;
  const cy = frame.y + frame.h / 2;
  const corners = [
    { x: frame.x, y: frame.y },
    { x: frame.x + frame.w, y: frame.y },
    { x: frame.x + frame.w, y: frame.y + frame.h },
    { x: frame.x, y: frame.y + frame.h },
  ];
  if (!rotationDeg) return corners;
  return corners.map((point) =>
    rotatePointPercentAround(point, { x: cx, y: cy }, rotationDeg, slideAspect),
  );
}

export type GroupRotateMemberUpdate = {
  frame: PercentFrame;
  rotation: number;
};

/**
 * Gira membros em torno do centro do grupo (frame orbita + style.rotation).
 * Paridade PowerPoint/Figma no handle de giro do chrome do grupo.
 */
export function applyGroupRotationDelta(input: {
  startFrames: ReadonlyMap<string, PercentFrame>;
  startRotations: ReadonlyMap<string, number>;
  center: { x: number; y: number };
  deltaDeg: number;
  /** Largura/altura do palco (design). Default 1 = legado isotrópico. */
  slideAspect?: number;
}): Map<string, GroupRotateMemberUpdate> {
  const aspect = input.slideAspect ?? 1;
  const next = new Map<string, GroupRotateMemberUpdate>();
  for (const [id, start] of input.startFrames) {
    const cx = start.x + start.w / 2;
    const cy = start.y + start.h / 2;
    const rotated = rotatePointPercentAround(
      { x: cx, y: cy },
      input.center,
      input.deltaDeg,
      aspect,
    );
    const startRotation = input.startRotations.get(id) ?? 0;
    next.set(id, {
      frame: {
        x: rotated.x - start.w / 2,
        y: rotated.y - start.h / 2,
        w: start.w,
        h: start.h,
      },
      rotation: clampRotationDeg(startRotation + input.deltaDeg),
    });
  }
  return next;
}

/**
 * Chrome do grupo: AABB visual dos membros (cantos após CSS rotate).
 * Sem `transform` no overlay — o giro CSS no chrome desalinhava o ângulo e
 * distorcia o bbox “local” reconstruído por inversa.
 */
export function resolveGroupSelectionChrome(input: {
  members: ReadonlyArray<{ frame: PercentFrame; rotation: number }>;
  slideAspect?: number;
}): { frame: PercentFrame; rotation: number } {
  const members = input.members;
  if (members.length === 0) {
    return { frame: { x: 0, y: 0, w: 0, h: 0 }, rotation: 0 };
  }
  const aspect = input.slideAspect ?? 1;
  const points: Array<{ x: number; y: number }> = [];
  for (const member of members) {
    points.push(
      ...resolveRotatedFrameCorners(member.frame, member.rotation, aspect),
    );
  }
  return { frame: aabbFromPoints(points), rotation: 0 };
}

export type GroupScaleHandle = "nw" | "n" | "ne" | "e" | "se" | "s" | "sw" | "w";

function oppositeCorner(
  union: PercentFrame,
  handle: GroupScaleHandle,
): { x: number; y: number } {
  const right = union.x + union.w;
  const bottom = union.y + union.h;
  switch (handle) {
    case "se":
      return { x: union.x, y: union.y };
    case "sw":
      return { x: right, y: union.y };
    case "ne":
      return { x: union.x, y: bottom };
    case "nw":
      return { x: right, y: bottom };
    case "e":
      return { x: union.x, y: union.y + union.h / 2 };
    case "w":
      return { x: right, y: union.y + union.h / 2 };
    case "s":
      return { x: union.x + union.w / 2, y: union.y };
    case "n":
      return { x: union.x + union.w / 2, y: bottom };
    default:
      return { x: union.x, y: union.y };
  }
}

const MIN_FRAME = 0.05;

/**
 * Escala proporcional do grupo a partir da mudança do bbox unificado.
 * Cantos: escala uniforme (mantém proporção). Bordas: escala só no eixo.
 */
export function applyGroupScaleFromUnionDelta(input: {
  startFrames: ReadonlyMap<string, PercentFrame>;
  startUnion: PercentFrame;
  nextUnion: PercentFrame;
  handle: GroupScaleHandle;
  /** Cantos travam proporção; bordas podem ser livres. */
  lockAspect: boolean;
}): Map<string, PercentFrame> {
  const { startFrames, startUnion, nextUnion, handle, lockAspect } = input;
  const next = new Map<string, PercentFrame>();
  if (!(startUnion.w > 0) || !(startUnion.h > 0)) {
    for (const [id, frame] of startFrames) next.set(id, { ...frame });
    return next;
  }

  let scaleX = nextUnion.w / startUnion.w;
  let scaleY = nextUnion.h / startUnion.h;
  const isCorner =
    handle === "nw" || handle === "ne" || handle === "se" || handle === "sw";
  if (lockAspect || isCorner) {
    // Escala uniforme: usa o fator do eixo dominante da mudança do union.
    const dw = Math.abs(nextUnion.w - startUnion.w);
    const dh = Math.abs(nextUnion.h - startUnion.h);
    const scale = dw >= dh ? scaleX : scaleY;
    scaleX = scale;
    scaleY = scale;
  }

  const fixed = oppositeCorner(startUnion, handle);
  for (const [id, start] of startFrames) {
    const w = Math.max(MIN_FRAME, start.w * scaleX);
    const h = Math.max(MIN_FRAME, start.h * scaleY);
    const x = fixed.x + (start.x - fixed.x) * scaleX;
    const y = fixed.y + (start.y - fixed.y) * scaleY;
    next.set(id, { x, y, w, h });
  }
  return next;
}
