import { describe, expect, it } from "vitest";

import { insertSlideAfterAnchor } from "./insertSlideAfterAnchor";

describe("insertSlideAfterAnchor", () => {
  const a = { id: "a" };
  const b = { id: "b" };
  const c = { id: "c" };
  const n = { id: "n" };

  it("insere abaixo da âncora", () => {
    expect(insertSlideAfterAnchor([a, b, c], n, "a").map((s) => s.id)).toEqual([
      "a",
      "n",
      "b",
      "c",
    ]);
    expect(insertSlideAfterAnchor([a, b, c], n, "c").map((s) => s.id)).toEqual([
      "a",
      "b",
      "c",
      "n",
    ]);
  });

  it("sem âncora ou id inexistente → final", () => {
    expect(insertSlideAfterAnchor([a, b], n, null).map((s) => s.id)).toEqual([
      "a",
      "b",
      "n",
    ]);
    expect(insertSlideAfterAnchor([a, b], n, undefined).map((s) => s.id)).toEqual([
      "a",
      "b",
      "n",
    ]);
    expect(insertSlideAfterAnchor([a, b], n, "missing").map((s) => s.id)).toEqual([
      "a",
      "b",
      "n",
    ]);
  });

  it("remove duplicata do newSlide se já estava no fim (pós-POST)", () => {
    expect(insertSlideAfterAnchor([a, b, n], n, "a").map((s) => s.id)).toEqual([
      "a",
      "n",
      "b",
    ]);
  });

  it("lista vazia → só o novo", () => {
    expect(insertSlideAfterAnchor([], n, null).map((s) => s.id)).toEqual(["n"]);
  });
});
