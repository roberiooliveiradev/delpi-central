import { describe, expect, it } from "vitest";
import {
  formatDocument,
  formatDurationMs,
  postingLeadTimeLabel,
  resolvePostedAt,
} from "./format";

describe("formatDocument", () => {
  it("apresenta número com 9 dígitos", () => {
    expect(formatDocument("12078", null)).toBe("000012078");
    expect(formatDocument("00012078", "1")).toBe("000012078 / 1");
  });
});

describe("formatDurationMs", () => {
  it("formata minutos, horas e dias", () => {
    expect(formatDurationMs(45_000)).toBe("menos de 1 min");
    expect(formatDurationMs(45 * 60_000)).toBe("45min");
    expect(formatDurationMs(2 * 60 * 60_000 + 15 * 60_000)).toBe("2h 15min");
    expect(formatDurationMs(2 * 24 * 60 * 60_000 + 3 * 60 * 60_000)).toBe("2d 3h");
  });
});

describe("postingLeadTimeLabel", () => {
  it("usa reconciled_at quando status é posted", () => {
    const label = postingLeadTimeLabel({
      status: "posted",
      received_at: "2026-07-20T10:00:00+00:00",
      reconciled_at: "2026-07-20T14:30:00+00:00",
    });
    expect(label).toBe("4h 30min");
  });

  it("cai no histórico quando não há reconciled_at", () => {
    expect(
      resolvePostedAt(
        { status: "posted", received_at: "2026-07-20T10:00:00+00:00", reconciled_at: null },
        [
          {
            event_type: "manual_posted",
            to_status: "posted",
            created_at: "2026-07-21T10:00:00+00:00",
          },
        ],
      ),
    ).toBe("2026-07-21T10:00:00+00:00");
  });

  it("não calcula para status aberto", () => {
    expect(
      postingLeadTimeLabel({
        status: "pending",
        received_at: "2026-07-20T10:00:00+00:00",
        reconciled_at: null,
      }),
    ).toBeNull();
  });
});
