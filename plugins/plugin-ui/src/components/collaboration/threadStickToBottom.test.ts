import { describe, expect, it } from "vitest";

import {
  remainingThreadScrollPx,
  shouldStickThreadToBottom,
} from "./threadStickToBottom";

describe("shouldStickThreadToBottom", () => {
  it("gruda no fundo quando a folga é até 64px", () => {
    const near = { scrollTop: 936, scrollHeight: 1000, clientHeight: 64 };
    expect(remainingThreadScrollPx(near)).toBe(0);
    expect(shouldStickThreadToBottom(near)).toBe(true);
    expect(
      shouldStickThreadToBottom({
        scrollTop: 800,
        scrollHeight: 1000,
        clientHeight: 136,
      }),
    ).toBe(true);
    expect(
      shouldStickThreadToBottom({
        scrollTop: 100,
        scrollHeight: 1000,
        clientHeight: 200,
      }),
    ).toBe(false);
  });

  it("assume fundo quando o elemento ainda não existe", () => {
    expect(shouldStickThreadToBottom(null)).toBe(true);
  });
});
