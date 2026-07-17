import { act, renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { ComunicadoDataSourceBlock } from "@delpi/tv-dashboard-presentation";
import type { DataQueryApi } from "../data/dataQueryApi";
import type { DataQueryCompileResult } from "../domain/dataQueryTypes";
import { useDataQueryWorkbench } from "./useDataQueryWorkbench";

function query(id: string): ComunicadoDataSourceBlock {
  return {
    id,
    type: "data_source",
    frame: { x: 0, y: 0, w: 10, h: 10 },
    dataBinding: { operationId: `op_${id}`, label: id },
    dataTransform: {
      version: 2,
      language: "m-delpi-v1",
      script: `let ${id} = Table.Skip(Fonte, 0) in ${id}`,
    },
  } as ComunicadoDataSourceBlock;
}

describe("useDataQueryWorkbench concorrência", () => {
  it("aborta compile anterior ao trocar consulta", async () => {
    const signals: AbortSignal[] = [];
    const resolvers: Array<(value: DataQueryCompileResult) => void> = [];
    const compile = vi.fn(
      (_input: unknown, signal?: AbortSignal) =>
        new Promise<DataQueryCompileResult>((resolve, reject) => {
          resolvers.push(resolve);
          if (signal) {
            signals.push(signal);
            signal.addEventListener("abort", () =>
              reject(new DOMException("Abortado", "AbortError")),
            );
          }
        }),
    );
    const api = {
      compile,
      mutate: vi.fn(),
      preview: vi.fn(),
      capabilities: vi.fn(),
      functions: vi.fn(),
    } as unknown as DataQueryApi;
    const queries = [query("q1"), query("q2")];
    const { result } = renderHook(() =>
      useDataQueryWorkbench({
        open: true,
        queries,
        config: { blocks: queries },
        playlistId: "playlist",
        api,
      }),
    );
    await waitFor(() => expect(compile).toHaveBeenCalledTimes(1));
    act(() => result.current.dispatch({ type: "select_query", queryId: "q2" }));
    await waitFor(() => expect(compile).toHaveBeenCalledTimes(2));
    expect(signals[0]?.aborted).toBe(true);
    expect(signals[1]?.aborted).toBe(false);
    await act(async () => {
      resolvers[1]?.({
        profile: "m-delpi-v1",
        canonicalScript: "let q2 = Table.Skip(Fonte, 0) in q2",
        scriptHash: "sha256:q2",
        outputStepName: "q2",
        steps: [
          {
            name: "q2",
            operation: "Table.Skip",
            label: "q2",
            formula: "Table.Skip(Fonte, 0)",
          },
        ],
        diagnostics: [],
        referencedQueries: [],
        completionContext: { steps: ["q2"], columns: [], queries: [], items: [] },
        syntaxTokens: [],
      });
    });
  });
});
