/** PRC-REF-023-UI-FIX-03 — contrato da timeline oficial (snake_case da
 * Engineering API) → apresentação única para os dois MFEs. */

import { describe, expect, it } from "vitest";
import {
  prcFormatTimelineDate,
  prcTimelineItemViews,
  type PrcTimelineEventLike,
} from "./prcProductRegistration";

const FIXTURE: PrcTimelineEventLike[] = [
  {
    id: "e6",
    sequence_number: 6,
    event_type: "correction_returned",
    actor_subject: "u-analyst",
    actor_display_name: "Analista Eng",
    actor_email: null,
    occurred_at: "2026-11-10T14:05:00Z",
    reason: "Revise o Part Number do fornecedor 000123.",
    metadata: { channel: "portal-engineering" },
    previous_status: "under_review",
    next_status: "needs_correction",
  },
  {
    id: "e1",
    sequence_number: 1,
    event_type: "submitted",
    actor_subject: "u-requester",
    actor_display_name: "Solicitante X",
    occurred_at: "2026-11-09T09:00:00Z",
    reason: null,
    metadata: {},
    next_status: "submitted",
  },
  {
    id: "e2",
    sequence_number: 2,
    event_type: "started",
    actor_subject: "u-analyst",
    occurred_at: "2026-11-09T10:00:00Z",
    metadata: null,
    previous_status: "submitted",
    next_status: "in_progress",
  },
];

describe("prcTimelineItemViews — UI-FIX-03", () => {
  it("interpreta snake_case oficial, ordena por sequence_number e rotula", () => {
    const items = prcTimelineItemViews(FIXTURE);
    expect(items.map((i) => i.id)).toEqual(["e1", "e2", "e6"]);
    expect(items[0].title).toBe("Solicitação enviada");
    expect(items[1].title).toBe("Atendimento iniciado");
    expect(items[2].title).toBe("Devolvida para correção");
  });

  it("não emite Invalid Date e formata pt-BR", () => {
    const items = prcTimelineItemViews(FIXTURE);
    for (const i of items) {
      expect(i.timeLabel).not.toContain("Invalid Date");
      expect(i.timeLabel).not.toBe("Data indisponível");
    }
  });

  it("data ausente/inválida preserva o evento com fallback neutro", () => {
    const items = prcTimelineItemViews([
      { ...FIXTURE[0], occurred_at: "" },
      { ...FIXTURE[1], occurred_at: "not-a-date" },
    ]);
    expect(items).toHaveLength(2);
    expect(items[0].timeLabel).toBe("Data indisponível");
    expect(items[1].timeLabel).toBe("Data indisponível");
  });

  it("expõe transição previous→next, motivo, autor e canal", () => {
    const items = prcTimelineItemViews(FIXTURE);
    const ret = items.find((i) => i.id === "e6")!;
    expect(ret.transition).toContain("Devolvida para correção");
    expect(ret.reasonText).toContain("Part Number");
    expect(ret.actorLabel).toBe("Analista Eng");
    expect(ret.channel).toBe("portal-engineering");
    expect(ret.metaText).toContain("canal portal-engineering");
  });

  it("evento sem label conhecido cai no código bruto; sem reason/meta ok", () => {
    const items = prcTimelineItemViews([
      { ...FIXTURE[0], event_type: "custom.internal", reason: undefined },
    ]);
    expect(items[0].title).toBe("custom.internal");
    expect(items[0].reasonText).toBeNull();
  });

  it("prcFormatTimelineDate cobre null/undefined/inválido", () => {
    expect(prcFormatTimelineDate(null)).toBe("Data indisponível");
    expect(prcFormatTimelineDate(undefined)).toBe("Data indisponível");
    expect(prcFormatTimelineDate("xx")).toBe("Data indisponível");
    expect(prcFormatTimelineDate("2026-01-01T00:00:00Z")).not.toBe(
      "Data indisponível",
    );
  });
});
