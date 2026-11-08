import { describe, expect, it } from "vitest";

import {
  demandMywegRecordId,
  demandOrderTableLabel,
  isMywegDemandLine,
} from "./demandOrderLabel";

describe("demandOrderLabel", () => {
  it("marca linha MyWEG por source ou planning", () => {
    expect(isMywegDemandLine({ source: "myweg" })).toBe(true);
    expect(isMywegDemandLine({ planning: true })).toBe(true);
    expect(isMywegDemandLine({ source: "protheus" })).toBe(false);
  });

  it("na tabela mostra Necessidade WEG sem UUID", () => {
    const label = demandOrderTableLabel({
      source: "myweg",
      sales_order: "MyWEG",
      line_item: "e595dda4-6ada-4132-9d73-5dac11111111",
    });
    expect(label).toBe("Necessidade WEG");
    expect(label).not.toContain("e595dda4");
  });

  it("pedido Protheus permanece pedido/item", () => {
    expect(
      demandOrderTableLabel({
        source: "protheus",
        sales_order: "045123",
        line_item: "01",
      }),
    ).toBe("045123/01");
  });

  it("expõe o record_id só via helper de detalhe", () => {
    expect(demandMywegRecordId({ line_item: "e595dda4-6ada-4132-9d73-5dac" })).toBe(
      "e595dda4-6ada-4132-9d73-5dac",
    );
  });
});
