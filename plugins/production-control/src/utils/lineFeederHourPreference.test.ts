// @vitest-environment jsdom

import { afterEach, describe, expect, it } from "vitest";
import {
  LINE_FEEDER_DEFAULT_HOURS,
  readPreferredLineFeederHours,
  savePreferredLineFeederHours,
} from "./lineFeederHourPreference";

afterEach(() => window.localStorage.clear());

describe("horas de coleta do alimentador (#1195)", () => {
  it("preserva as horas da filial depois do reload", () => {
    savePreferredLineFeederHours("02", 5.5);
    expect(readPreferredLineFeederHours("02")).toBe(5.5);
    expect(readPreferredLineFeederHours("01")).toBe(LINE_FEEDER_DEFAULT_HOURS);
  });

  it("ignora valores fora do contrato atual de 0 a 24 horas", () => {
    for (const invalid of [0, -2, 25, Infinity, NaN]) {
      savePreferredLineFeederHours("02", invalid);
    }
    expect(readPreferredLineFeederHours("02")).toBe(LINE_FEEDER_DEFAULT_HOURS);
    window.localStorage.setItem("production-control:line-feeder:hours:v1:02", "999");
    expect(readPreferredLineFeederHours("02")).toBe(LINE_FEEDER_DEFAULT_HOURS);
  });
});
