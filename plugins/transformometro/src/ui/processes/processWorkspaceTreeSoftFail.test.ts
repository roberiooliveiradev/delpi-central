import { describe, expect, it, vi } from "vitest";

import { reloadProcessWorkspaceTree } from "./reloadProcessWorkspaceTree";

describe("reloadProcessWorkspaceTree", () => {
  it("mantém processo quando melhorias falham", async () => {
    const setProcesso = vi.fn();
    const setInstancias = vi.fn();
    const setRevisoes = vi.fn();
    const setTreePartialError = vi.fn();

    await reloadProcessWorkspaceTree({
      fetchProcesso: async () => ({ processo_id: "p1" }),
      fetchInstancias: async () => {
        throw new Error("instancias down");
      },
      fetchRevisoes: async () => ({ items: [{ revisao_id: "r1" }] }),
      setProcesso,
      setInstancias,
      setRevisoes,
      setTreePartialError,
    });

    expect(setProcesso).toHaveBeenCalledWith({ processo_id: "p1" });
    expect(setInstancias).not.toHaveBeenCalled();
    expect(setRevisoes).toHaveBeenCalledWith([{ revisao_id: "r1" }]);
    expect(setTreePartialError).toHaveBeenCalledWith(expect.stringContaining("melhorias"));
  });

  it("zera processo quando o fetch mestre falha", async () => {
    const setProcesso = vi.fn();
    const setInstancias = vi.fn();
    const setRevisoes = vi.fn();
    const setTreePartialError = vi.fn();

    await reloadProcessWorkspaceTree({
      fetchProcesso: async () => {
        throw new Error("fatal");
      },
      fetchInstancias: async () => ({ items: [] }),
      fetchRevisoes: async () => ({ items: [] }),
      setProcesso,
      setInstancias,
      setRevisoes,
      setTreePartialError,
    });

    expect(setProcesso).toHaveBeenCalledWith(null);
    expect(setInstancias).not.toHaveBeenCalled();
    expect(setRevisoes).not.toHaveBeenCalled();
  });
});
