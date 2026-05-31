import { describe, expect, it } from "vitest";

import {
  CHAT_HOME_STARTERS,
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

  it("mantém CHAT_HOME_STARTERS como união para compatibilidade", () => {
    expect(CHAT_HOME_STARTERS.length).toBe(
      CHAT_OPERATIONAL_HOME_STARTERS.length + CHAT_TEXT_HOME_STARTERS.length,
    );
  });
});
