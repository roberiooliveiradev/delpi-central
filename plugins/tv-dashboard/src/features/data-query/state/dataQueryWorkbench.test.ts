import { describe, expect, it, vi } from "vitest";

import type {
  DataQueryCompileResult,
  DataQueryDraft,
} from "../domain/dataQueryTypes";
import {
  dataQueryDraftReducer,
  INITIAL_WORKBENCH_STATE,
} from "./dataQueryDraftReducer";
import { reconcileSelectedStepName } from "./dataQuerySelection";
import { applyDataQueryDraftsAtomically } from "./dataQueryTransaction";

function result(name: string, script = `let ${name} = Table.Skip(Fonte, 0) in ${name}`) {
  return {
    profile: "m-delpi-v1",
    canonicalScript: script,
    scriptHash: "sha256:test",
    outputStepName: name,
    steps: [{ name, operation: "Table.Skip", label: name, formula: "Table.Skip(Fonte, 0)" }],
    diagnostics: [],
    referencedQueries: [],
  } satisfies DataQueryCompileResult;
}

function draft(sourceId: string, dirty = true): DataQueryDraft {
  return {
    sourceId,
    queryName: sourceId,
    legacySteps: [],
    script: `let ${sourceId} = Table.Skip(Fonte, 0) in ${sourceId}`,
    compiled: result(sourceId),
    selectedStepName: sourceId,
    dirty,
  };
}

describe("workbench M transacional", () => {
  it("persiste múltiplas consultas em um único commit atômico", async () => {
    const commit = vi.fn();
    const validate = vi.fn(async (item: DataQueryDraft) => result(item.sourceId));
    const changed = await applyDataQueryDraftsAtomically(
      [draft("A"), draft("B"), draft("C", false)],
      validate,
      commit,
    );
    expect(changed).toEqual(["A", "B"]);
    expect(validate).toHaveBeenCalledTimes(2);
    expect(commit).toHaveBeenCalledTimes(1);
    expect(commit.mock.calls[0]?.[0]).toHaveLength(2);
  });

  it("não persiste nada quando validação falha (cancelamento implícito)", async () => {
    const commit = vi.fn();
    const invalid = {
      ...result("A"),
      diagnostics: [
        {
          code: "m.syntax",
          severity: "error" as const,
          message: "Inválido",
          range: {
            startLine: 2,
            startColumn: 5,
            endLine: 2,
            endColumn: 8,
            startOffset: 4,
            endOffset: 7,
          },
        },
      ],
    };
    await expect(
      applyDataQueryDraftsAtomically([draft("A")], async () => invalid, commit),
    ).rejects.toThrow("Inválido");
    expect(commit).not.toHaveBeenCalled();
  });

  it("ignora resposta antiga e conserva seleção por stepName", () => {
    const initial = {
      ...INITIAL_WORKBENCH_STATE,
      activeQueryId: "q",
      draftByQueryId: { q: draft("q", false) },
      compile: { status: "loading" as const, value: null, error: null, sequence: 2 },
    };
    const stale = dataQueryDraftReducer(initial, {
      type: "compiled",
      queryId: "q",
      sequence: 1,
      result: result("Antiga"),
      dirty: true,
    });
    expect(stale).toBe(initial);
    expect(
      reconcileSelectedStepName("B", [
        { name: "A", label: "A", operation: "x", formula: "x" },
        { name: "B", label: "B", operation: "x", formula: "x" },
      ]),
    ).toBe("B");
  });
});
