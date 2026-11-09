import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const dir = dirname(fileURLToPath(import.meta.url));

function read(name: string): string {
  return readFileSync(join(dir, name), "utf8");
}

describe("Meeting minutes realtime wiring", () => {
  it("lista assina catalog:meeting_minute", () => {
    const source = read("MeetingMinutesPage.tsx");
    expect(source).toMatch(/useTransformometroCatalogWatch/);
    expect(source).toMatch(/catalogId:\s*"meeting_minute"/);
  });

  it("detalhe assina meeting_minute e trata exclusão remota", () => {
    const source = read("MeetingMinuteDetailPage.tsx");
    expect(source).toMatch(/useTransformometroEntityWatch/);
    expect(source).toMatch(/entityType:\s*"meeting_minute"/);
    expect(source).toMatch(/resolveCollaborativeEntityUpdate/);
    expect(source).toMatch(/action === "delete"/);
  });

  it("editor protege dirty e envia expected_updated_at", () => {
    const source = read("MeetingMinuteEditorPage.tsx");
    expect(source).toMatch(/useTransformometroEntityWatch/);
    expect(source).toMatch(/expected_updated_at/);
    expect(source).toMatch(/remoteBlocked/);
    expect(source).toMatch(/resolveCollaborativeEntityUpdate/);
  });
});
