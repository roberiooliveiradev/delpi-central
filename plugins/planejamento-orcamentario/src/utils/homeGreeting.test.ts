import { describe, expect, it } from "vitest";

import {
  firstNameFromDisplayName,
  formatHomeGreeting,
  timeOfDayGreeting,
} from "./homeGreeting";

describe("homeGreeting", () => {
  it("saudação por período do dia", () => {
    expect(timeOfDayGreeting(new Date(2026, 7, 15, 9))).toBe("Bom dia");
    expect(timeOfDayGreeting(new Date(2026, 7, 15, 14))).toBe("Boa tarde");
    expect(timeOfDayGreeting(new Date(2026, 7, 15, 20))).toBe("Boa noite");
  });

  it("extrai primeiro nome", () => {
    expect(firstNameFromDisplayName("Michael Silva")).toBe("Michael");
    expect(firstNameFromDisplayName("  Ana  ")).toBe("Ana");
    expect(firstNameFromDisplayName("")).toBeNull();
    expect(firstNameFromDisplayName(null)).toBeNull();
  });

  it("monta saudação completa", () => {
    expect(formatHomeGreeting("Michael Silva", new Date(2026, 7, 15, 10))).toBe(
      "Bom dia, Michael",
    );
    expect(formatHomeGreeting(null, new Date(2026, 7, 15, 19))).toBe("Boa noite!");
  });
});
