import { describe, expect, it } from "vitest";

import {
  CHAT_OPERATIONAL_HOME_STARTERS,
  CHAT_TEXT_HOME_STARTERS,
} from "./chatHomeStarters";

describe("chatHomeStarters", () => {
  it("separa operacional e textos sem duplicar labels de texto na operacional", () => {
    const textLabels = new Set(CHAT_TEXT_HOME_STARTERS.map((item) => item.label));

    for (const starter of CHAT_OPERATIONAL_HOME_STARTERS) {
      expect(textLabels.has(starter.label)).toBe(false);
    }
  });

  it("operacionais usam placeholders em vez de código fixo", () => {
    const withProduct = CHAT_OPERATIONAL_HOME_STARTERS.filter((s) =>
      s.query.includes("{{productCode}}"),
    );
    const withSearch = CHAT_OPERATIONAL_HOME_STARTERS.filter((s) =>
      s.query.includes("{{searchQuery}}"),
    );

    expect(withProduct.length).toBeGreaterThanOrEqual(3);
    expect(withSearch.length).toBeGreaterThanOrEqual(1);

    for (const starter of CHAT_OPERATIONAL_HOME_STARTERS) {
      expect(starter.query).not.toMatch(/\b10080001\b/);
    }
  });
});
