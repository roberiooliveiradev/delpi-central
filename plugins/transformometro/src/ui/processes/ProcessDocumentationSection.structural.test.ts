import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const root = join(dirname(fileURLToPath(import.meta.url)), "../..");

describe("Process Documentation wiring", () => {
  it("expõe seção Documentação no ProcessDetailPage", () => {
    const page = readFileSync(join(root, "ui/pages/ProcessDetailPage.tsx"), "utf8");
    expect(page).toMatch(/ProcessDocumentationSection/);
    expect(page).toMatch(/sectionId="documentacao"/);
  });

  it("não importa Meeting Minutes na seção de documentação", () => {
    const section = readFileSync(
      join(root, "ui/processes/ProcessDocumentationSection.tsx"),
      "utf8",
    );
    expect(section).toMatch(/MessageBodyReadonly/);
    expect(section).not.toMatch(/meeting.?minute|MeetingMinute|tm_meeting/i);
    expect(section).not.toMatch(/importar ata|atas\b/i);
    expect(section).not.toMatch(/mermaid/i);
  });
});
