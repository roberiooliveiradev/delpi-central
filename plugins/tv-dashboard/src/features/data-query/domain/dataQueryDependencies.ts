import type { DataQueryDraft } from "./dataQueryTypes";

export type DataQueryDependencyEdge = {
  sourceId: string;
  sourceName: string;
  targetName: string;
};

/** Projeta somente metadata do compile; não interpreta o script M. */
export function dataQueryDependencyEdges(
  drafts: readonly DataQueryDraft[],
): DataQueryDependencyEdge[] {
  return drafts.flatMap((draft) =>
    (draft.compiled?.referencedQueries ?? []).map((targetName) => ({
      sourceId: draft.sourceId,
      sourceName: draft.queryName,
      targetName,
    })),
  );
}
