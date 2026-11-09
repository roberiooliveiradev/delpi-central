import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const root = dirname(fileURLToPath(import.meta.url));

function read(name: string): string {
  return readFileSync(join(root, name), "utf8");
}

describe("Meeting minute delete affordances", () => {
  it("detail view exposes destructive delete with confirm", () => {
    const source = read("MeetingMinuteDetailPage.tsx");
    expect(source).toMatch(/Excluir ata/);
    expect(source).toMatch(/deleteAta/);
    expect(source).toMatch(/useConfirm/);
    expect(source).toMatch(/canDeleteMeetingMinute/);
    expect(source).toMatch(/dsGhostBtn\("danger"\)/);
  });

  it("editor exposes delete without competing with save primary", () => {
    const source = read("MeetingMinuteEditorPage.tsx");
    expect(source).toMatch(/Excluir ata/);
    expect(source).toMatch(/deleteAta/);
    expect(source).toMatch(/discardUnsaved:\s*true/);
    expect(source).toMatch(/tm-ata-editor__footer-actions/);
  });

  it("list exposes delete for draft rows as sibling of open control", () => {
    const source = read("MeetingMinutesPage.tsx");
    expect(source).toMatch(/Excluir/);
    expect(source).toMatch(/deleteAta/);
    expect(source).toMatch(/tm-atas-row__delete/);
    expect(source).toMatch(/tm-atas-row__open/);
    // Open control is a button; delete is a sibling under <li>, not nested.
    expect(source).toMatch(
      /tm-atas-row__open[\s\S]*?<\/button>\s*\{showDelete \? \(\s*<button/,
    );
  });
});
