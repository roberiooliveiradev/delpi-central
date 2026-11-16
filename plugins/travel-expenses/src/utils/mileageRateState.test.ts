import { describe, expect, it } from "vitest";
import {
  emptyMileageRateLookup,
  mileageRateLabel,
  rateForDate,
  type MileageRateLookup,
} from "./mileageRateState";

describe("mileage rate feedback (ticket #1597)", () => {
  const selectedDate = "2026-11-16";

  it("shows a date instruction rather than infinite loading if blank", () => {
    expect(mileageRateLabel(emptyMileageRateLookup, "")).toBe("Informe a data da despesa");
    expect(rateForDate(emptyMileageRateLookup, "")).toBeNull();
  });

  it("shows loading only while rate has not been obtained", () => {
    const pending: MileageRateLookup = { date: selectedDate, status: "loading", rate: null, error: null };
    expect(mileageRateLabel(pending, selectedDate)).toBe("Consultando tarifa…");
  });

  it("shows a validated rate", () => {
    const resolved: MileageRateLookup = { date: selectedDate, status: "success", rate: 1.20, error: null };
    expect(rateForDate(resolved, selectedDate)).toBe(1.20);
    expect(mileageRateLabel(resolved, selectedDate).replace(/\s/g, " ")).toBe("R$ 1,20/km");
  });

  it("never reuses a rate fetched for a previous date", () => {
    const resolved: MileageRateLookup = { date: "2026-11-15", status: "success", rate: 1.20, error: null };
    expect(rateForDate(resolved, selectedDate)).toBeNull();
    expect(mileageRateLabel(resolved, selectedDate)).toBe("Consultando tarifa…");
  });

  it("surfaces errors and rejects invalid API rate values", () => {
    const failed: MileageRateLookup = { date: selectedDate, status: "error", rate: null, error: "Falha HTTP 500" };
    expect(mileageRateLabel(failed, selectedDate)).toBe("Tarifa indisponível");
    const invalid: MileageRateLookup = { date: selectedDate, status: "success", rate: 0, error: null };
    expect(rateForDate(invalid, selectedDate)).toBeNull();
    expect(mileageRateLabel(invalid, selectedDate)).toBe("Tarifa indisponível");
  });
});
