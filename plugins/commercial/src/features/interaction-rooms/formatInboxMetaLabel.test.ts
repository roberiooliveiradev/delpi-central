import { describe, expect, it } from "vitest";

import { formatInboxMetaLabel } from "./formatInboxMetaLabel";

const now = new Date("2026-08-19T12:00:00-03:00");

describe("formatInboxMetaLabel", () => {
  it("mostra hora de hoje sem offset GMT", () => {
    const label = formatInboxMetaLabel("2026-08-19T07:12:43.335410-03:00", { now });
    expect(label).toMatch(/^\d{2}:\d{2}$/);
    expect(label).not.toMatch(/GMT/);
  });

  it("usa o rótulo de ontem", () => {
    expect(
      formatInboxMetaLabel("2026-08-18T15:54:00-03:00", {
        now,
        yesterdayLabel: "Ontem",
      }),
    ).toBe("Ontem");
  });

  it("usa data curta no mesmo ano e completa em outro ano", () => {
    expect(formatInboxMetaLabel("2026-01-05T10:00:00-03:00", { now })).toMatch(
      /^\d{2}\/\d{2}$/,
    );
    expect(formatInboxMetaLabel("2025-12-31T10:00:00-03:00", { now })).toMatch(
      /^\d{2}\/\d{2}\/\d{4}$/,
    );
  });

  it("ignora ISO inválido", () => {
    expect(formatInboxMetaLabel("not-a-date", { now })).toBe("");
    expect(formatInboxMetaLabel(null, { now })).toBe("");
  });
});
