import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

import type {
  DataQueryCompileResult,
  DataQueryDraft,
} from "../domain/dataQueryTypes";

export async function applyDataQueryDraftsAtomically(
  drafts: readonly DataQueryDraft[],
  validate: (draft: DataQueryDraft) => Promise<DataQueryCompileResult>,
  commit: (
    patches: ReadonlyArray<{ blockId: string; patch: Partial<ComunicadoBlock> }>,
  ) => void,
): Promise<string[]> {
  const dirty = drafts.filter((draft) => draft.dirty);
  if (dirty.length === 0) return [];
  const validated = await Promise.all(dirty.map(validate));
  const invalid = validated.find((result) =>
    result.diagnostics.some((item) => item.severity === "error"),
  );
  if (invalid) {
    throw new Error(
      invalid.diagnostics.find((item) => item.severity === "error")?.message ||
        "Consulta M inválida.",
    );
  }
  commit(
    dirty.map((draft, index) => ({
      blockId: draft.sourceId,
      patch: {
        dataTransform: {
          version: 2,
          language: "m-delpi-v1",
          script: validated[index]?.canonicalScript ?? draft.script,
        },
      } as Partial<ComunicadoBlock>,
    })),
  );
  return dirty.map((draft) => draft.sourceId);
}
