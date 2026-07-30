import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));

describe("diagram validation + IO chrome", () => {
  it("agrupa IO em popover e coloca validação no split lateral", () => {
    const section = readFileSync(join(here, "sections/ProcessoDiagramSection.tsx"), "utf8");
    const panel = readFileSync(join(here, "validation/DiagramValidationPanel.tsx"), "utf8");
    const ioMenu = readFileSync(join(here, "DiagramIoMenu.tsx"), "utf8");

    expect(section).toMatch(/DiagramIoMenu/);
    expect(section).toMatch(/delpi-ui-bpmn-workspace__split--with-panel/);
    expect(section).toMatch(/layout=\{validationLayout\}/);
    expect(panel).toMatch(/onCollapse/);
    expect(panel).toMatch(/onClose/);
    expect(panel).toMatch(/delpi-ui-bpmn-validation--rail/);
    expect(section).toMatch(/validationPanelCollapsed/);
    expect(section).toMatch(/setValidationPanelOpen/);
  });
});
