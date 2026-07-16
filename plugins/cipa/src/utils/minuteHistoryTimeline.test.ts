import { describe, expect, it } from "vitest";

import { buildMinuteHistoryTimeline } from "./minuteHistoryTimeline";

const versions = [
  {
    id: "v1",
    version_number: 1,
    created_at: "2026-07-16T18:26:24-03:00",
    change_reason: "Criação inicial",
  },
  {
    id: "v2",
    version_number: 2,
    created_at: "2026-07-16T18:59:43-03:00",
    change_reason: "Ata reaberta para edição pelo gestor.",
  },
];

const audit = [
  { id: "a1", action: "create", created_at: "2026-07-16T18:26:24-03:00" },
  { id: "a2", action: "sign", created_at: "2026-07-16T18:45:52-03:00" },
  { id: "a3", action: "create_version", created_at: "2026-07-16T18:59:43-03:00" },
  { id: "a4", action: "edit", created_at: "2026-07-16T19:01:44-03:00" },
];

describe("buildMinuteHistoryTimeline", () => {
  it("versões formam o tronco, mais recente primeiro", () => {
    const items = buildMinuteHistoryTimeline(versions, []);
    const trunk = items.filter((item) => item.branchKey === "main");
    expect(trunk.map((item) => item.id)).toEqual(["version-v2", "version-v1"]);
    expect(trunk[0].title).toBe("Versão 2");
    expect(trunk[0].detail).toBe("Ata reaberta para edição pelo gestor.");
    expect(trunk[0].timeLabel).toBe("16/07/2026 18:59");
  });

  it("eventos de auditoria viram branches da versão vigente no instante", () => {
    const items = buildMinuteHistoryTimeline(versions, audit);
    const byId = new Map(items.map((item) => [item.id, item]));

    expect(byId.get("audit-a1")?.parentId).toBe("version-v1");
    expect(byId.get("audit-a2")?.parentId).toBe("version-v1");
    expect(byId.get("audit-a3")?.parentId).toBe("version-v2");
    expect(byId.get("audit-a4")?.parentId).toBe("version-v2");
    expect(byId.get("audit-a4")?.branchKey).toBe("audit");
  });

  it("rotula ações conhecidas e aplica tom", () => {
    const items = buildMinuteHistoryTimeline(versions, audit);
    const byId = new Map(items.map((item) => [item.id, item]));

    expect(byId.get("audit-a2")?.title).toBe("Assinatura registrada");
    expect(byId.get("audit-a2")?.tone).toBe("success");
    expect(byId.get("audit-a3")?.title).toBe("Nova versão criada");
    expect(byId.get("audit-a3")?.tone).toBe("warning");
  });

  it("evento anterior a qualquer versão cai na primeira versão", () => {
    const items = buildMinuteHistoryTimeline(versions, [
      { id: "a0", action: "edit", created_at: "2026-07-16T18:00:00-03:00" },
    ]);
    const event = items.find((item) => item.id === "audit-a0");
    expect(event?.parentId).toBe("version-v1");
  });

  it("sem versões, auditoria vira raiz linear", () => {
    const items = buildMinuteHistoryTimeline([], audit.slice(0, 1));
    expect(items).toHaveLength(1);
    expect(items[0].parentId).toBeNull();
  });
});
