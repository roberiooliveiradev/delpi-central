import { describe, expect, it } from "vitest";

import {
  shouldPatchStreamStatusForSources,
  shouldPatchStreamStatusForToolCalls,
} from "./chatStreamStatusGuards";

describe("chatStreamStatusGuards", () => {
  it("não atualiza status para sources vazias (small talk / direct answer)", () => {
    expect(shouldPatchStreamStatusForSources([])).toBe(false);
    expect(
      shouldPatchStreamStatusForSources([
        { scope: "web_search", sourceRef: "https://example.com" },
      ]),
    ).toBe(true);
  });

  it("não atualiza status para tool_calls vazios", () => {
    expect(shouldPatchStreamStatusForToolCalls([])).toBe(false);
    expect(
      shouldPatchStreamStatusForToolCalls([{ name: "web_search", arguments: {} }]),
    ).toBe(true);
  });
});
