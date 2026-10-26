/** Error mapping for market intelligence (PROC-0076 R1.2). */

import { describe, expect, it } from "vitest";

import {
  mapMarketIntelligenceError,
  MARKET_INTELLIGENCE_CONTENT,
} from "./content";

describe("mapMarketIntelligenceError", () => {
  it("maps license quarantine to a neutral unavailability message", () => {
    const err = { status: 503, code: "source_use_not_approved" };
    expect(mapMarketIntelligenceError(err)).toBe(
      MARKET_INTELLIGENCE_CONTENT.errors.sourceNotApproved,
    );
    expect(mapMarketIntelligenceError(err)).not.toContain("R$");
    expect(mapMarketIntelligenceError(err)).not.toContain("US$");
  });

  it("still maps generic upstream 503 to unavailable", () => {
    expect(
      mapMarketIntelligenceError({
        status: 503,
        code: "external_data_unavailable",
      }),
    ).toBe(MARKET_INTELLIGENCE_CONTENT.errors.unavailable);
  });

  it("maps producer 403 code to quarantine, never to user forbidden", () => {
    const err = { status: 503, code: "source_use_not_approved" };
    expect(mapMarketIntelligenceError(err)).not.toBe(
      MARKET_INTELLIGENCE_CONTENT.errors.forbidden,
    );
  });

  it("keeps distinct 401 and 403 user-facing messages", () => {
    expect(mapMarketIntelligenceError({ status: 401 })).toBe(
      MARKET_INTELLIGENCE_CONTENT.errors.unauthorized,
    );
    expect(mapMarketIntelligenceError({ status: 403 })).toBe(
      MARKET_INTELLIGENCE_CONTENT.errors.forbidden,
    );
  });
});
