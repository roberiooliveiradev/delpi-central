/** @vitest-environment node */

import { describe, expect, it } from "vitest";

import { nextBoardIndex, previousBoardIndex, rotationIntervalMs } from "./boardNavigation";

describe("boardNavigation", () => {
  it("avança e volta ao início após a última notícia", () => {
    expect(nextBoardIndex(0, 3)).toBe(1);
    expect(nextBoardIndex(2, 3)).toBe(0);
  });

  it("volta ao último ao navegar anterior a partir do primeiro", () => {
    expect(previousBoardIndex(0, 3)).toBe(2);
  });

  it("respeita duração configurada com mínimo de 1s", () => {
    expect(rotationIntervalMs(8)).toBe(8000);
    expect(rotationIntervalMs(0)).toBe(1000);
  });
});
