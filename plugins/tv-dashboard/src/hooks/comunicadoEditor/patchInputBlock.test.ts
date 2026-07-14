import { describe, expect, it } from "vitest";

import type { ComunicadoBlock, ComunicadoConfig, ComunicadoInputBlock } from "@delpi/tv-dashboard-presentation";

/** Espelha a lógica de patchInputBlock (commit atômico input + dataFilters). */
function applyPatchInputBlock(
  current: ComunicadoConfig,
  blockId: string,
  inputPatch: Partial<ComunicadoInputBlock["input"]>,
): ComunicadoConfig {
  let nextFilters = current.dataFilters;
  const nextBlocks = (current.blocks ?? []).map((item) => {
    if (item.id !== blockId || item.type !== "input") return item;
    const prevKey = String(item.input?.paramKey || "").trim();
    const nextInput = { ...item.input, ...inputPatch };
    const nextKey = String(nextInput.paramKey || "").trim();
    const scope = nextInput.targetScope === "sources" ? "sources" : "slide";
    if (scope === "slide") {
      const filters = { ...(current.dataFilters ?? {}) };
      if (prevKey && prevKey !== nextKey) {
        delete filters[prevKey];
      }
      if (nextKey) {
        const value = nextInput.defaultValue;
        if (value === undefined || value === null || value === "") {
          delete filters[nextKey];
        } else {
          filters[nextKey] = value;
        }
      }
      nextFilters = Object.keys(filters).length > 0 ? filters : undefined;
    }
    return { ...item, input: nextInput } as ComunicadoBlock;
  });
  return {
    ...current,
    blocks: nextBlocks,
    dataFilters: nextFilters,
    version: Math.max(current.version ?? 3, 4),
  };
}

describe("patchInputBlock atomic", () => {
  const input: ComunicadoInputBlock = {
    id: "inp-1",
    type: "input",
    frame: { x: 0, y: 0, w: 20, h: 10 },
    input: { paramKey: "", targetScope: "slide", defaultValue: null },
  };

  it("grava paramKey e dataFilters juntos no mesmo estado", () => {
    const next = applyPatchInputBlock({ version: 4, blocks: [input] }, "inp-1", {
      paramKey: "branch",
      defaultValue: "01",
    });
    const block = next.blocks?.find((item) => item.id === "inp-1");
    expect(block?.type).toBe("input");
    if (block?.type === "input") {
      expect(block.input.paramKey).toBe("branch");
      expect(block.input.defaultValue).toBe("01");
    }
    expect(next.dataFilters).toEqual({ branch: "01" });
  });

  it("não polui dataFilters quando alvo é sources", () => {
    const next = applyPatchInputBlock({ version: 4, blocks: [input] }, "inp-1", {
      targetScope: "sources",
      targetSourceIds: ["src-a"],
      paramKey: "branch",
      defaultValue: "02",
    });
    expect(next.dataFilters).toBeUndefined();
    const block = next.blocks?.[0];
    if (block?.type === "input") {
      expect(block.input.defaultValue).toBe("02");
      expect(block.input.targetSourceIds).toEqual(["src-a"]);
    }
  });

  it("ao trocar paramKey remove a chave antiga de dataFilters", () => {
    const withBranch: ComunicadoInputBlock = {
      ...input,
      input: { paramKey: "branch", targetScope: "slide", defaultValue: "01" },
    };
    const next = applyPatchInputBlock(
      { version: 4, blocks: [withBranch], dataFilters: { branch: "01", periodDays: 30 } },
      "inp-1",
      { paramKey: "periodDays", defaultValue: 7 },
    );
    expect(next.dataFilters).toEqual({ periodDays: 7 });
  });

  it("ao limpar paramKey remove a chave antiga de dataFilters", () => {
    const withBranch: ComunicadoInputBlock = {
      ...input,
      input: { paramKey: "branch", targetScope: "slide", defaultValue: "01" },
    };
    const next = applyPatchInputBlock(
      { version: 4, blocks: [withBranch], dataFilters: { branch: "01" } },
      "inp-1",
      { paramKey: "" },
    );
    expect(next.dataFilters).toBeUndefined();
  });
});
