import { describe, expect, it } from "vitest";

import {
  firstNameFromDisplay,
  formatPortalGreeting,
  portalDayPeriodGreeting,
} from "./portalGreeting";

describe("portalGreeting", () => {
  it("extrai o primeiro nome e recusa vazio", () => {
    expect(firstNameFromDisplay("João Silva Santos")).toBe("João");
    expect(firstNameFromDisplay("  Ana  ")).toBe("Ana");
    expect(firstNameFromDisplay("")).toBeNull();
    expect(firstNameFromDisplay("   ")).toBeNull();
    expect(firstNameFromDisplay(null)).toBeNull();
    expect(firstNameFromDisplay(undefined)).toBeNull();
  });

  it("usa hora injetada para o período do dia", () => {
    expect(portalDayPeriodGreeting(new Date(2026, 8, 21, 8, 0, 0))).toBe("Bom dia");
    expect(portalDayPeriodGreeting(new Date(2026, 8, 21, 12, 0, 0))).toBe("Boa tarde");
    expect(portalDayPeriodGreeting(new Date(2026, 8, 21, 17, 59, 0))).toBe("Boa tarde");
    expect(portalDayPeriodGreeting(new Date(2026, 8, 21, 18, 0, 0))).toBe("Boa noite");
  });

  it("compõe período + primeiro nome", () => {
    expect(
      formatPortalGreeting({
        firstName: "Robério",
        now: new Date(2026, 8, 21, 9, 0, 0),
      }),
    ).toBe("Bom dia, Robério");
    expect(
      formatPortalGreeting({
        displayName: "Ana Souza",
        now: new Date(2026, 8, 21, 15, 0, 0),
      }),
    ).toBe("Boa tarde, Ana");
  });

  it("usa fallback digno quando o nome falta", () => {
    expect(
      formatPortalGreeting({
        now: new Date(2026, 8, 21, 21, 0, 0),
        fallback: "Bem-vindo ao Portal Transforma+",
      }),
    ).toBe("Bem-vindo ao Portal Transforma+");
    expect(formatPortalGreeting({ firstName: "  ", now: new Date(2026, 8, 21, 8, 0, 0) })).toBe(
      "Bom dia",
    );
    expect(formatPortalGreeting({ displayName: null, now: new Date(2026, 8, 21, 20, 0, 0) })).toBe(
      "Boa noite",
    );
  });

  it("não trata e-mail como primeiro nome quando só o displayName vazio existe", () => {
    expect(formatPortalGreeting({ firstName: null, fallback: "Bem-vindo ao Portal Transforma+" })).toBe(
      "Bem-vindo ao Portal Transforma+",
    );
  });
});
