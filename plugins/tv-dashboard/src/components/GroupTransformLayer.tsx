import { Fragment, type CSSProperties, type ReactNode } from "react";
import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

import type { StageGroupGesture } from "../utils/stageGroupGesture";

type MemberRenderArgs = {
  block: ComunicadoBlock;
  localRotation: number;
  wrapStyle: CSSProperties;
};

type Props = {
  gesture: StageGroupGesture;
  /** Blocos mundo (conteúdo); posição visual vem de `gesture.localFrames`. */
  members: ComunicadoBlock[];
  renderMember: (args: MemberRenderArgs) => ReactNode;
  chrome?: ReactNode;
};

/**
 * Um único `transform: rotate` no container — membros em coords locais.
 * Impede giro independente por membro (distorção / posições separadas).
 */
export function GroupTransformLayer({
  gesture,
  members,
  renderMember,
  chrome,
}: Props) {
  const { group, childExtent, localFrames } = gesture;
  const extentW = childExtent.w > 0 ? childExtent.w : 1;
  const extentH = childExtent.h > 0 ? childExtent.h : 1;
  const maxZ = members.reduce(
    (max, block) => Math.max(max, block.style?.zIndex ?? 1),
    1,
  );

  return (
    <div
      className="td-composer__group-layer"
      data-group-layer=""
      style={{
        position: "absolute",
        left: `${group.frame.x}%`,
        top: `${group.frame.y}%`,
        width: `${group.frame.w}%`,
        height: `${group.frame.h}%`,
        transform: group.rotation ? `rotate(${group.rotation}deg)` : undefined,
        transformOrigin: "center center",
        zIndex: maxZ,
      }}
    >
      {members.map((block) => {
        const local = localFrames.get(block.id);
        if (!local) return null;
        const wrapStyle: CSSProperties = {
          position: "absolute",
          left: `${(local.frame.x / extentW) * 100}%`,
          top: `${(local.frame.y / extentH) * 100}%`,
          width: `${(local.frame.w / extentW) * 100}%`,
          height: `${(local.frame.h / extentH) * 100}%`,
          zIndex: block.style?.zIndex ?? 1,
          ...(local.rotation
            ? { transform: `rotate(${local.rotation}deg)`, transformOrigin: "center center" }
            : {}),
        };
        return (
          <Fragment key={block.id}>
            {renderMember({ block, localRotation: local.rotation, wrapStyle })}
          </Fragment>
        );
      })}
      {chrome}
    </div>
  );
}
