import { describe, expect, it } from "vitest";

import {
  decodeDelinquencyCustomerKey,
  encodeDelinquencyCustomerKey,
  formatDelinquencyCustomerOptionLabel,
} from "./delinquencyCustomers";

describe("delinquencyCustomers", () => {
  it("round-trips customer keys", () => {
    expect(encodeDelinquencyCustomerKey("000001", "01")).toBe("000001|01");
    expect(decodeDelinquencyCustomerKey("000001|01")).toEqual({
      customerCode: "000001",
      store: "01",
    });
  });

  it("rejects malformed keys", () => {
    expect(decodeDelinquencyCustomerKey("")).toBeNull();
    expect(decodeDelinquencyCustomerKey("000001")).toBeNull();
    expect(decodeDelinquencyCustomerKey("|01")).toBeNull();
  });

  it("formats option labels with short name fallback", () => {
    expect(
      formatDelinquencyCustomerOptionLabel({
        customerCode: "000001",
        store: "01",
        customerName: "WEG EQUIPAMENTOS ELETRICOS SA",
        shortName: "WEG",
        totalTitles: 0,
        onTimeTitles: 0,
        lateTitles: 0,
        totalAmount: 0,
        lateAmount: 0,
        onTimePctByCount: 0,
        onTimePctByAmount: 0,
      }),
    ).toBe("WEG (000001/01)");
  });
});
