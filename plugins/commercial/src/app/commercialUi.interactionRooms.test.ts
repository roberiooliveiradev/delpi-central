import { describe, expect, it } from "vitest";

import {
  CommercialEntityUnfurlCard,
  CommercialMentionComposer,
  CommercialMentionMenu,
  CommercialMentionText,
  CommercialMessageThread,
  CommercialReactionBar,
  CommercialRoomHeader,
  CommercialRoomInboxList,
  CommercialRoomSidePanel,
} from "./commercialUi";

describe("commercialUi interaction room factories", () => {
  it("exports the eight collaboration dashboard components", () => {
    expect(typeof CommercialMentionText).toBe("function");
    expect(typeof CommercialMentionMenu).toBe("function");
    expect(typeof CommercialMentionComposer).toBe("function");
    expect(typeof CommercialMessageThread).toBe("function");
    expect(typeof CommercialEntityUnfurlCard).toBe("function");
    expect(typeof CommercialReactionBar).toBe("function");
    expect(typeof CommercialRoomInboxList).toBe("function");
    expect(typeof CommercialRoomHeader).toBe("function");
    expect(typeof CommercialRoomSidePanel).toBe("function");
  });
});
