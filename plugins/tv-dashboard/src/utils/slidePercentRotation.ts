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

const ROTATION_EPS = 0.05;

/**
 * Chrome do grupo: quando todos os membros compartilham a mesma rotação,
 * recupera o bbox “local” (pré-giro) e aplica `rotate` no overlay — senão os
 * controles ficam axis-aligned enquanto o conteúdo gira (CSS no wrap).
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
  const rotations = members.map((member) => member.rotation);
  const shared = rotations[0] ?? 0;
  const sameRotation = rotations.every((value) => Math.abs(value - shared) < ROTATION_EPS);
  if (!sameRotation || Math.abs(shared) < ROTATION_EPS) {
    return {
      frame: unionFramesPercent(members.map((member) => member.frame)),
      rotation: 0,
    };
  }
  const center = resolveFramesGroupCenter(members.map((member) => member.frame));
  const localFrames = members.map((member) => {
    const cx = member.frame.x + member.frame.w / 2;
    const cy = member.frame.y + member.frame.h / 2;
    const local = rotatePointPercentAround({ x: cx, y: cy }, center, -shared, aspect);
    return {
      x: local.x - member.frame.w / 2,
      y: local.y - member.frame.h / 2,
      w: member.frame.w,
      h: member.frame.h,
    };
  });
  return {
    frame: unionFramesPercent(localFrames),
    rotation: clampRotationDeg(shared),
  };
}
