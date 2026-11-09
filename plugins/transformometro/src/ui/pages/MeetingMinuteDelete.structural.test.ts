import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const root = dirname(fileURLToPath(import.meta.url));

function read(name: string): string {
  return readFileSync(join(root, name), "utf8");
}

describe("Meeting minute delete affordances", () => {
  it("detail hero exposes destructive delete with confirm", () => {
    const source = read("MeetingMinuteDetailPage.tsx");
    expect(source).toMatch(/Excluir ata/);
    expect(source).toMatch(/deleteAta/);
    expect(source).toMatch(/useConfirm/);
    expect(source).toMatch(/canDeleteMeetingMinute/);
    expect(source).toMatch(/dsGhostBtn\("danger"\)/);
    // Only in PageHeader actions (hero), not duplicated in aside.
    expect(source.match(/Excluir ata/g)?.length).toBe(1);
  });

  it("editor does not expose delete", () => {
    const source = read("MeetingMinuteEditorPage.tsx");
    expect(source).not.toMatch(/Excluir ata/);
    expect(source).not.toMatch(/deleteAta/);
    expect(source).toMatch(/Salvar rascunho/);
  });

  it("list does not expose delete", () => {
    const source = read("MeetingMinutesPage.tsx");
    expect(source).not.toMatch(/Excluir/);
    expect(source).not.toMatch(/deleteAta/);
    expect(source).not.toMatch(/tm-atas-row__delete/);
    expect(source).toMatch(/tm-atas-row/);
  });
});
