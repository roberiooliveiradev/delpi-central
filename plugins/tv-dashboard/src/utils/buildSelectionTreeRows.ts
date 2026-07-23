import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";
import { sortBlocksByZIndex } from "@delpi/tv-dashboard-presentation";

import { membersOfGroup } from "./comunicadoGrouping";

export type SelectionTreeRow =
  | {
      kind: "group";
      groupId: string;
      /** Membro de maior z (topo visual) — âncora de reorder. */
      anchorId: string;
      memberIds: string[];
      depth: 0;
    }
  | {
      kind: "block";
      block: ComunicadoBlock;
      groupId?: string;
      depth: 0 | 1;
    };

/**
 * Árvore do painel Seleção (z desc): grupo como nó pai + filhos indentados;
 * blocos soltos na raiz.
 */
export function buildSelectionTreeRows(blocks: ComunicadoBlock[]): SelectionTreeRow[] {
  const sortedDesc = [...sortBlocksByZIndex(blocks)].reverse();
  const seenGroups = new Set<string>();
  const rows: SelectionTreeRow[] = [];

  for (const block of sortedDesc) {
    const groupId = block.groupId;
    if (!groupId) {
      rows.push({ kind: "block", block, depth: 0 });
      continue;
    }
    if (seenGroups.has(groupId)) continue;
    seenGroups.add(groupId);
    const members = membersOfGroup(blocks, groupId);
    if (members.length < 2) {
      rows.push({ kind: "block", block, depth: 0 });
      continue;
    }
    const membersDesc = [...sortBlocksByZIndex(members)].reverse();
    rows.push({
      kind: "group",
      groupId,
      anchorId: membersDesc[0]?.id ?? block.id,
      memberIds: membersDesc.map((member) => member.id),
      depth: 0,
    });
    for (const member of membersDesc) {
      rows.push({
        kind: "block",
        block: member,
        groupId,
        depth: 1,
      });
    }
  }

  return rows;
}

export function selectionTreeRowIsActive(
  row: SelectionTreeRow,
  selectedIds: string[],
): boolean {
  if (row.kind === "group") {
    const set = new Set(selectedIds);
    return row.memberIds.length > 0 && row.memberIds.every((id) => set.has(id));
  }
  return selectedIds.includes(row.block.id);
}
