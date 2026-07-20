import { describe, expect, it } from "vitest";

import { toggleHiddenSeriesKey } from "./EssModernMultiLineChart";

describe("toggleHiddenSeriesKey", () => {
  it("oculta e reexibe a série clicada", () => {
    const hidden = toggleHiddenSeriesKey(new Set(), "2024");
    expect(hidden.has("2024")).toBe(true);
    expect(toggleHiddenSeriesKey(hidden, "2024").has("2024")).toBe(false);
  });
});
