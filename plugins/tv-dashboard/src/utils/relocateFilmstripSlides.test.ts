import { describe, expect, it } from "vitest";

import type { Slide } from "../api/tvDashboardApi";
import { relocateFilmstripSlides } from "./relocateFilmstripSlides";

function slide(
  partial: Partial<Slide> & Pick<Slide, "id" | "sortOrder">,
): Slide {
  return {
    playlistId: "p1",
    slideType: "native",
    title: partial.id,
    isActive: true,
    durationSec: 10,
    ...partial,
  };
}

describe("relocateFilmstripSlides", () => {
  const base = [
    slide({ id: "a", sortOrder: 0, sectionId: "main" }),
    slide({ id: "b", sortOrder: 1, sectionId: "main" }),
    slide({ id: "c", sortOrder: 2, sectionId: "s1" }),
    slide({ id: "d", sortOrder: 3, sectionId: "s1" }),
  ];

  it("move um slide para o índice-alvo (antes do alvo)", () => {
    const next = relocateFilmstripSlides(base, ["d"], { kind: "index", targetIndex: 0 });
    expect(next.map((item) => item.id)).toEqual(["d", "a", "b", "c"]);
    expect(next[0]?.sectionId).toBe("main");
  });

  it("move bloco multi mantendo ordem relativa", () => {
    const next = relocateFilmstripSlides(base, ["a", "b"], { kind: "index", targetIndex: 3 });
    expect(next.map((item) => item.id)).toEqual(["c", "a", "b", "d"]);
    expect(
      next
        .filter((item) => item.id === "a" || item.id === "b")
        .every((item) => item.sectionId === "s1"),
    ).toBe(true);
  });

  it("no-op ao soltar sobre um item do bloco movido", () => {
    const next = relocateFilmstripSlides(base, ["a", "b"], { kind: "index", targetIndex: 1 });
    expect(next.map((item) => item.id)).toEqual(["a", "b", "c", "d"]);
  });

  it("move bloco para o fim de uma seção", () => {
    const next = relocateFilmstripSlides(base, ["a", "b"], {
      kind: "section",
      sectionId: "s1",
    });
    expect(next.map((item) => item.id)).toEqual(["c", "d", "a", "b"]);
    expect(next.slice(2).every((item) => item.sectionId === "s1")).toBe(true);
  });

  it("seção vazia recebe o bloco no fim da lista remanescente", () => {
    const next = relocateFilmstripSlides(base, ["c", "d"], {
      kind: "section",
      sectionId: "empty",
    });
    expect(next.map((item) => item.id)).toEqual(["a", "b", "c", "d"]);
    expect(
      next
        .filter((item) => item.id === "c" || item.id === "d")
        .every((item) => item.sectionId === "empty"),
    ).toBe(true);
  });
});
