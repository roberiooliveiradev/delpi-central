import { clampRotationDeg } from "./comunicadoTransform";
import {
  rotatePointPercentAround,
  type GroupScaleHandle,
  type PercentFrame,
} from "./slidePercentRotation";

const MIN_FRAME = 0.05;

/** Transform do grupo no slide (off/ext/rot — espelho PowerPoint no gesto). */
export type GroupTransform = {
  frame: PercentFrame;
  rotation: number;
};

/** Frame + rotação no espaço local do grupo (chOff/chExt efêmero). */
export type LocalMemberFrame = {
  frame: PercentFrame;
  rotation: number;
};

export type StageGroupGesture = {
  memberIds: readonly string[];
  /** Frames locais relativos a `childExtent` (origem = canto NW do grupo). */
  localFrames: ReadonlyMap<string, LocalMemberFrame>;
  /** Extensão das crianças no begin (chExt); escala = group.frame / childExtent. */
  childExtent: PercentFrame;
  group: GroupTransform;
  slideAspect: number;
  resizeHandle: GroupScaleHandle | null;
  /** Gesto partiu do chrome (startFrame ≈ group.frame). */
  dragFromChrome: boolean;
  /** Frame de referência no pointerdown (chrome ou membro). */
  interactionStartFrame: PercentFrame;
  /** `group.rotation` congelada no pointerdown (base do giro). */
  startGroupRotation: number;
  /**
   * Rotação do hit no pointerdown (chrome = group; membro = style.rotation).
   * Delta do pointer = patch.rotation − interactionStartRotation.
   */
  interactionStartRotation: number;
};

export type WorldMemberUpdate = {
  frame: PercentFrame;
  rotation: number;
};

function frameCenter(frame: PercentFrame): { x: number; y: number } {
  return { x: frame.x + frame.w / 2, y: frame.y + frame.h / 2 };
}

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

/**
 * Chrome idle a partir dos membros bakeados.
 * Rotação comum → caixa “local” + CSS rotate; senão AABB visual (rotation 0).
 */
export function resolveGroupChromeFromMembers(input: {
  members: ReadonlyArray<{ frame: PercentFrame; rotation: number }>;
  slideAspect?: number;
  /** Ângulo pai persistido; necessário quando membros têm rotações locais distintas. */
  groupRotation?: number;
}): GroupTransform {
  const members = input.members;
  if (members.length === 0) {
    return { frame: { x: 0, y: 0, w: 0, h: 0 }, rotation: 0 };
  }
  const aspect = input.slideAspect ?? 1;
  const firstRotation = members[0]?.rotation ?? 0;
  const sameRotation = members.every(
    (member) => Math.abs((member.rotation ?? 0) - firstRotation) < 0.05,
  );
  const dominantRotation = members.reduce(
    (dominant, member) =>
      member.frame.w * member.frame.h > dominant.frame.w * dominant.frame.h
        ? member
        : dominant,
    members[0]!,
  ).rotation;
  const groupRotation = Number.isFinite(input.groupRotation)
    ? input.groupRotation!
    : sameRotation
      ? firstRotation
      : dominantRotation;

  /*
   * OBB exato do grupo: transforma os cantos visuais para o espaço sem giro,
   * calcula a união e volta o centro ao mundo. O pivô (0,0) é intencional:
   * uma rotação rígida global preserva a caixa orientada e evita inferir o
   * centro pelo AABB dos frames — essa inferência deslocava o chrome.
   */
  const origin = { x: 0, y: 0 };
  const localPoints: Array<{ x: number; y: number }> = [];
  for (const member of members) {
    const center = frameCenter(member.frame);
    const corners = [
      { x: member.frame.x, y: member.frame.y },
      { x: member.frame.x + member.frame.w, y: member.frame.y },
      { x: member.frame.x + member.frame.w, y: member.frame.y + member.frame.h },
      { x: member.frame.x, y: member.frame.y + member.frame.h },
    ];
    for (const corner of corners) {
      const visual = rotatePointPercentAround(
        corner,
        center,
        member.rotation,
        aspect,
      );
      localPoints.push(
        rotatePointPercentAround(visual, origin, -groupRotation, aspect),
      );
    }
  }
  const localBounds = aabbFromPoints(localPoints);
  const localCenter = frameCenter(localBounds);
  const worldCenter = rotatePointPercentAround(
    localCenter,
    origin,
    groupRotation,
    aspect,
  );
  return {
    frame: {
      x: worldCenter.x - localBounds.w / 2,
      y: worldCenter.y - localBounds.h / 2,
      w: localBounds.w,
      h: localBounds.h,
    },
    rotation: groupRotation,
  };
}

/** Chrome do gesto = GroupTransform atual. */
export function resolveGroupChrome(gesture: StageGroupGesture): GroupTransform {
  return { frame: { ...gesture.group.frame }, rotation: gesture.group.rotation };
}

/**
 * Congela locais (chOff/chExt) e GroupTransform inicial.
 * Única entrada do pipeline de gesto de grupo / multi N>1.
 */
export function beginGroupGesture(input: {
  members: ReadonlyArray<{ id: string; frame: PercentFrame; rotation: number }>;
  slideAspect: number;
  interactionStartFrame?: PercentFrame;
  /** Rotação do hit no pointerdown (chrome deve passar group.rotation). */
  interactionStartRotation?: number;
  /** Ângulo pai persistido no config do slide. */
  groupRotation?: number;
  resizeHandle?: GroupScaleHandle | null;
}): StageGroupGesture | null {
  if (input.members.length < 2) return null;
  const aspect = input.slideAspect > 0 ? input.slideAspect : 1;
  const startChrome = resolveGroupChromeFromMembers({
    members: input.members.map((member) => ({
      frame: member.frame,
      rotation: member.rotation,
    })),
    slideAspect: aspect,
    groupRotation: input.groupRotation,
  });
  const childExtent = { ...startChrome.frame };
  if (!(childExtent.w > 0) || !(childExtent.h > 0)) return null;

  const groupCenter = frameCenter(childExtent);
  const localFrames = new Map<string, LocalMemberFrame>();
  const memberIds: string[] = [];

  for (const member of input.members) {
    memberIds.push(member.id);
    const centerWorld = frameCenter(member.frame);
    const centerLocal = rotatePointPercentAround(
      centerWorld,
      groupCenter,
      -startChrome.rotation,
      aspect,
    );
    localFrames.set(member.id, {
      frame: {
        x: centerLocal.x - member.frame.w / 2 - childExtent.x,
        y: centerLocal.y - member.frame.h / 2 - childExtent.y,
        w: member.frame.w,
        h: member.frame.h,
      },
      rotation: (member.rotation ?? 0) - startChrome.rotation,
    });
  }

  const interactionStartFrame = input.interactionStartFrame
    ? { ...input.interactionStartFrame }
    : { ...childExtent };
  const dragFromChrome =
    Math.abs(interactionStartFrame.x - childExtent.x) < 0.05 &&
    Math.abs(interactionStartFrame.y - childExtent.y) < 0.05 &&
    Math.abs(interactionStartFrame.w - childExtent.w) < 0.05 &&
    Math.abs(interactionStartFrame.h - childExtent.h) < 0.05;
  const interactionStartRotation =
    input.interactionStartRotation ??
    (dragFromChrome
      ? startChrome.rotation
      : (input.members.find(
          (member) =>
            input.interactionStartFrame &&
            Math.abs(member.frame.x - input.interactionStartFrame.x) < 0.05 &&
            Math.abs(member.frame.y - input.interactionStartFrame.y) < 0.05,
        )?.rotation ?? startChrome.rotation));

  return {
    memberIds,
    localFrames,
    childExtent,
    group: { frame: { ...childExtent }, rotation: startChrome.rotation },
    slideAspect: aspect,
    resizeHandle: input.resizeHandle ?? null,
    dragFromChrome,
    interactionStartFrame,
    startGroupRotation: startChrome.rotation,
    interactionStartRotation,
  };
}

/** Move: desloca só `group.frame` (dx/dy a partir do frame de interação). */
export function applyGroupMove(
  gesture: StageGroupGesture,
  workingFrame: PercentFrame,
): StageGroupGesture {
  const dx = workingFrame.x - gesture.interactionStartFrame.x;
  const dy = workingFrame.y - gesture.interactionStartFrame.y;
  return {
    ...gesture,
    group: {
      ...gesture.group,
      frame: {
        ...gesture.group.frame,
        x: gesture.childExtent.x + dx,
        y: gesture.childExtent.y + dy,
      },
    },
  };
}

/** Rotate: só `group.rotation` (absoluto no espaço do gesto). */
export function applyGroupRotate(
  gesture: StageGroupGesture,
  nextGroupRotationDeg: number,
): StageGroupGesture {
  return {
    ...gesture,
    group: {
      ...gesture.group,
      rotation: clampRotationDeg(nextGroupRotationDeg),
    },
  };
}

/**
 * Scale: `workingFrame` é o próximo group.frame (chrome) ou frame do membro.
 * Cantos: escala uniforme. Bordas: eixos livres.
 */
export function applyGroupScale(
  gesture: StageGroupGesture,
  workingFrame: PercentFrame,
  options?: { lockAspect?: boolean },
): StageGroupGesture {
  const handle = gesture.resizeHandle ?? "se";
  const lockAspect = options?.lockAspect ?? true;
  const startUnion = gesture.childExtent;
  let nextUnion: PercentFrame;

  if (gesture.dragFromChrome) {
    nextUnion = { ...workingFrame };
  } else {
    const startMember = gesture.interactionStartFrame;
    const scaleX =
      startMember.w > 0 ? workingFrame.w / startMember.w : 1;
    const scaleY =
      startMember.h > 0 ? workingFrame.h / startMember.h : 1;
    const isCorner =
      handle === "nw" || handle === "ne" || handle === "se" || handle === "sw";
    let sx = scaleX;
    let sy = scaleY;
    if (lockAspect || isCorner) {
      const dw = Math.abs(workingFrame.w - startMember.w);
      const dh = Math.abs(workingFrame.h - startMember.h);
      const scale = dw >= dh ? scaleX : scaleY;
      sx = scale;
      sy = scale;
    }
    const fixed = oppositeCorner(startUnion, handle);
    nextUnion = {
      x: fixed.x + (startUnion.x - fixed.x) * sx,
      y: fixed.y + (startUnion.y - fixed.y) * sy,
      w: Math.max(MIN_FRAME, startUnion.w * sx),
      h: Math.max(MIN_FRAME, startUnion.h * sy),
    };
  }

  if (lockAspect || handle === "nw" || handle === "ne" || handle === "se" || handle === "sw") {
    if (startUnion.w > 0 && startUnion.h > 0) {
      let scaleX = nextUnion.w / startUnion.w;
      let scaleY = nextUnion.h / startUnion.h;
      const dw = Math.abs(nextUnion.w - startUnion.w);
      const dh = Math.abs(nextUnion.h - startUnion.h);
      const scale = dw >= dh ? scaleX : scaleY;
      scaleX = scale;
      scaleY = scale;
      const fixed = oppositeCorner(startUnion, handle);
      nextUnion = {
        x: fixed.x + (startUnion.x - fixed.x) * scaleX,
        y: fixed.y + (startUnion.y - fixed.y) * scaleY,
        w: Math.max(MIN_FRAME, startUnion.w * scaleX),
        h: Math.max(MIN_FRAME, startUnion.h * scaleY),
      };
    }
  }

  return {
    ...gesture,
    group: {
      ...gesture.group,
      frame: nextUnion,
    },
  };
}

/**
 * Única resolução world — live e release.
 * local → scale(ext/chExt) → rotate(group) em torno do centro do grupo.
 */
export function resolveWorldFrames(
  gesture: StageGroupGesture,
): Map<string, WorldMemberUpdate> {
  const { childExtent, group, slideAspect, localFrames } = gesture;
  const next = new Map<string, WorldMemberUpdate>();
  const scaleX = childExtent.w > 0 ? group.frame.w / childExtent.w : 1;
  const scaleY = childExtent.h > 0 ? group.frame.h / childExtent.h : 1;
  const groupCenter = frameCenter(group.frame);

  for (const [id, local] of localFrames) {
    const w = Math.max(MIN_FRAME, local.frame.w * scaleX);
    const h = Math.max(MIN_FRAME, local.frame.h * scaleY);
    const unrotated: PercentFrame = {
      x: group.frame.x + local.frame.x * scaleX,
      y: group.frame.y + local.frame.y * scaleY,
      w,
      h,
    };
    const centerLocal = frameCenter(unrotated);
    const centerWorld = rotatePointPercentAround(
      centerLocal,
      groupCenter,
      group.rotation,
      slideAspect,
    );
    next.set(id, {
      frame: {
        x: centerWorld.x - w / 2,
        y: centerWorld.y - h / 2,
        w,
        h,
      },
      rotation: clampRotationDeg(local.rotation + group.rotation),
    });
  }
  return next;
}

/** Atalho: begin → rotate → resolve (menu 90° / multi). */
export function applyGroupRotationOnce(input: {
  members: ReadonlyArray<{ id: string; frame: PercentFrame; rotation: number }>;
  deltaDeg: number;
  slideAspect: number;
  groupRotation?: number;
}): Map<string, WorldMemberUpdate> {
  const gesture = beginGroupGesture({
    members: input.members,
    slideAspect: input.slideAspect,
    groupRotation: input.groupRotation,
  });
  if (!gesture) return new Map();
  const rotated = applyGroupRotate(
    gesture,
    gesture.group.rotation + input.deltaDeg,
  );
  return resolveWorldFrames(rotated);
}
