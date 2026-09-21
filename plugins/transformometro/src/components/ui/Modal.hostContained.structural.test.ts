import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const dir = dirname(fileURLToPath(import.meta.url));
const modalSource = readFileSync(join(dir, "Modal.tsx"), "utf8");
const confirmSource = readFileSync(join(dir, "ConfirmModal.tsx"), "utf8");
const bpmnFullscreenCss = readFileSync(
  join(dir, "../../../../plugin-ui/src/styles/bpmn/fullscreen.css"),
  "utf8",
);

describe("Transformometro Modal host-contained", () => {
  it("usa createHostContainedModalShell e não createModalShell no body", () => {
    expect(modalSource).toMatch(/createHostContainedModalShell/);
    expect(modalSource).toMatch(/containedLayout:\s*"dialog"/);
    expect(modalSource).toMatch(/variant:\s*"wide"/);
    expect(modalSource).toMatch(/portalScopeClassName:\s*TM_ROOT_CLASS|portalScopeClassName:\s*"dashboard-transformometro"/);
    expect(modalSource).not.toMatch(/createModalShell/);
  });

  it("ConfirmModal usa HostContainedDialog", () => {
    expect(confirmSource).toMatch(/HostContainedDialog/);
    expect(confirmSource).not.toMatch(/createModalShell/);
  });

  it("CSS BPMN não força fixed/480px em todo .dashboard-transformometro .ds-modal", () => {
    expect(bpmnFullscreenCss).not.toMatch(/\.dashboard-transformometro\s+\.ds-modal-overlay/);
    expect(bpmnFullscreenCss).not.toMatch(/\.dashboard-transformometro\s+\.ds-modal\s*\{/);
    expect(bpmnFullscreenCss).toMatch(/\.delpi-ui-flowchart-shell\s+\.ds-modal\s*\{/);
  });
});
