import type { OrgMembershipFlowModelNode } from "@delpi/plugin-ui/index";

/** Anexa `avatarSrc` aos nós de pessoa a partir do mapa de fotos. */
export function withPersonAvatarSrc(
  nodes: readonly OrgMembershipFlowModelNode[],
  photoByUserId: ReadonlyMap<string, string>,
): OrgMembershipFlowModelNode[] {
  if (photoByUserId.size === 0) return [...nodes];
  return nodes.map((node) => {
    if (node.kind !== "person") return node;
    const src = photoByUserId.get(node.entityId);
    if (!src) return node;
    return { ...node, avatarSrc: src };
  });
}
