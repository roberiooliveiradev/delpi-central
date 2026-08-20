import { describe, expect, it } from "vitest";

import {
  formatInteractionMessageCreatedAtLabel,
  formatInteractionMessageTime,
} from "./interactionRoomMessageTime";

describe("formatInteractionMessageTime", () => {
  it("retorna vazio para iso ausente", () => {
    expect(formatInteractionMessageTime(null)).toBe("");
    expect(formatInteractionMessageTime(undefined)).toBe("");
  });

  it("formata data válida em pt-BR", () => {
    const label = formatInteractionMessageTime("2026-08-20T12:41:00.000Z");
    expect(label).toMatch(/\d{2}\/\d{2}/);
    expect(label).toMatch(/\d{2}:\d{2}/);
  });
});

describe("formatInteractionMessageCreatedAtLabel", () => {
  const template = "editado às {time}";

  it("só criação quando não há edição", () => {
    const created = formatInteractionMessageTime("2026-08-20T12:41:00.000Z");
    expect(
      formatInteractionMessageCreatedAtLabel(
        "2026-08-20T12:41:00.000Z",
        null,
        template,
      ),
    ).toBe(created);
  });

  it("indica edição e horário da edição", () => {
    const created = formatInteractionMessageTime("2026-08-20T12:41:00.000Z");
    const edited = formatInteractionMessageTime("2026-08-20T14:05:00.000Z");
    expect(
      formatInteractionMessageCreatedAtLabel(
        "2026-08-20T12:41:00.000Z",
        "2026-08-20T14:05:00.000Z",
        template,
      ),
    ).toBe(`${created} · editado às ${edited}`);
  });
});
