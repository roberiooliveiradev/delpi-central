import { describe, expect, it } from "vitest";

import {
  buildProcessTimeline,
  type ProcessoAuditLogEntry,
} from "./processoTimeline";

function entry(
  auditId: string,
  createdAt: string,
  overrides: Partial<ProcessoAuditLogEntry> = {},
): ProcessoAuditLogEntry {
  return {
    audit_id: auditId,
    entity_type: "processo",
    entity_id: "proc-1",
    action: "create",
    created_at: createdAt,
    ...overrides,
  };
}

describe("buildProcessTimeline", () => {
  it("ordena do mais recente para o mais antigo", () => {
    const timeline = buildProcessTimeline([
      entry("a", "2026-08-22T21:30:00.000Z"),
      entry("c", "2026-08-22T21:34:00.000Z"),
      entry("b", "2026-08-22T21:32:00.000Z"),
    ]);

    expect(timeline.map((row) => row.id)).toEqual(["c", "b", "a"]);
    expect(timeline[0]?.occurredAt).toBe("2026-08-22T21:34:00.000Z");
  });

  it("mantém ordem estável quando timestamps empatam", () => {
    const same = "2026-08-22T21:33:00.000Z";
    const timeline = buildProcessTimeline([
      entry("first", same),
      entry("second", same),
    ]);
    expect(timeline).toHaveLength(2);
    expect(new Set(timeline.map((row) => row.id))).toEqual(new Set(["first", "second"]));
  });
});
