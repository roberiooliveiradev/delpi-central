import { describe, expect, it } from "vitest";

import { parseMentionText } from "./parseMentionText";

describe("parseMentionText", () => {
  it("returns empty for empty text", () => {
    expect(parseMentionText("")).toEqual([]);
  });

  it("keeps plain text as a single segment", () => {
    expect(parseMentionText("Sem menção")).toEqual([
      { type: "text", value: "Sem menção" },
    ]);
  });

  it("highlights bare @tokens", () => {
    expect(parseMentionText("Oi @Ana, ok?")).toEqual([
      { type: "text", value: "Oi " },
      { type: "mention", value: "@Ana" },
      { type: "text", value: ", ok?" },
    ]);
  });

  it("prefers structured labels (longest first) and attaches item", () => {
    const items = [
      { kind: "user", label: "@Ana Silva", id: "u1" },
      { kind: "order", label: "102942", id: "o1" },
    ];
    const segments = parseMentionText("Falar com @Ana Silva do pedido 102942", items);
    expect(segments).toEqual([
      { type: "text", value: "Falar com " },
      {
        type: "mention",
        value: "@Ana Silva",
        item: items[0],
      },
      { type: "text", value: " do pedido " },
      {
        type: "mention",
        value: "102942",
        item: items[1],
      },
    ]);
  });

  it("still marks bare @ when no matching item", () => {
    const segments = parseMentionText("Ping @ghost", [
      { kind: "user", label: "@Ana" },
    ]);
    expect(segments).toEqual([
      { type: "text", value: "Ping " },
      { type: "mention", value: "@ghost" },
    ]);
  });
});
