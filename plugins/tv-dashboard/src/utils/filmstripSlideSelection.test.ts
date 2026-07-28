import { describe, expect, it } from "vitest";

import {
  ensureFilmstripSlideInSelection,
  resolveFilmstripSlideSelection,
  type FilmstripSlideSelection,
} from "./filmstripSlideSelection";

const ORDER = ["a", "b", "c", "d", "e"];

function sel(
  selectedIds: string[],
  primaryId: string | null = selectedIds[0] ?? null,
  rangeAnchorId: string | null = primaryId,
): FilmstripSlideSelection {
  return { selectedIds, primaryId, rangeAnchorId };
}

describe("resolveFilmstripSlideSelection", () => {
  it("clique simples substitui a seleção", () => {
    expect(
      resolveFilmstripSlideSelection({
        orderedIds: ORDER,
        previous: sel(["a", "b"], "b", "a"),
        targetId: "d",
      }),
    ).toEqual(sel(["d"], "d", "d"));
  });

  it("Shift seleciona o intervalo a partir da âncora", () => {
    expect(
      resolveFilmstripSlideSelection({
        orderedIds: ORDER,
        previous: sel(["b"], "b", "b"),
        targetId: "d",
        modifiers: { range: true },
      }),
    ).toEqual({
      selectedIds: ["b", "c", "d"],
      primaryId: "d",
      rangeAnchorId: "b",
    });
  });

  it("Shift inverso também cobre o intervalo", () => {
    expect(
      resolveFilmstripSlideSelection({
        orderedIds: ORDER,
        previous: sel(["d"], "d", "d"),
        targetId: "b",
        modifiers: { range: true },
      }),
    ).toEqual({
      selectedIds: ["b", "c", "d"],
      primaryId: "b",
      rangeAnchorId: "d",
    });
  });

  it("toggle adiciona e remove sem esvaziar a seleção", () => {
    const withC = resolveFilmstripSlideSelection({
      orderedIds: ORDER,
      previous: sel(["a"], "a", "a"),
      targetId: "c",
      modifiers: { toggle: true },
    });
    expect(withC.selectedIds).toEqual(["a", "c"]);
    expect(withC.primaryId).toBe("c");

    const removed = resolveFilmstripSlideSelection({
      orderedIds: ORDER,
      previous: withC,
      targetId: "a",
      modifiers: { toggle: true },
    });
    expect(removed.selectedIds).toEqual(["c"]);
    expect(removed.primaryId).toBe("c");

    const alone = resolveFilmstripSlideSelection({
      orderedIds: ORDER,
      previous: removed,
      targetId: "c",
      modifiers: { toggle: true },
    });
    expect(alone).toEqual(sel(["c"], "c", "c"));
  });
});

describe("ensureFilmstripSlideInSelection", () => {
  it("não remove o alvo se já estiver selecionado", () => {
    expect(
      ensureFilmstripSlideInSelection({
        orderedIds: ORDER,
        previous: sel(["b"], "b", "b"),
        targetId: "b",
      }),
    ).toEqual({
      selectedIds: ["b"],
      primaryId: "b",
      rangeAnchorId: "b",
    });
  });

  it("inclui o alvo quando ainda não está na seleção", () => {
    expect(
      ensureFilmstripSlideInSelection({
        orderedIds: ORDER,
        previous: sel(["a"], "a", "a"),
        targetId: "c",
      }).selectedIds,
    ).toEqual(["a", "c"]);
  });
});
